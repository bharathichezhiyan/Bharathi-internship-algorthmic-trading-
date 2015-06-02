#!/usr/bin/env python

"""
Limit order book simulation for Indian security exchange.
"""
# Copyright (c) 2015, Bharathi Raja Asoka Chakravarthi
import rbtree
import copy
import csv
import datetime
import gzip
import logging
import numpy as np
import odict
import os
import pandas
import sys
import time


col_names = \
  ['record_indicator',
   'segment',
   'order_number',
   'trans_date',
   'trans_time',
   'buy_sell_indicator',
   'activity_type',
   'symbol',
   'series',
   'volume_disclosed',
   'volume_original',
   'limit_price',
   'trigger_price',
   'mkt_flag',
   'on_stop_flag',
   'io_flag',
   'algo_ind',
   'client_id_flag']

# Some aliases for bids and asks:
BID = BUY = 'B'
ASK = SELL = 'S'

in_format = \
"""
Format: %s <firm name> <output directory> <input file names>
""" % sys.argv[0]
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print in_format
        sys.exit(0)
    else:
        firm_name, output_dir = sys.argv[1:3]
        file_name_list = sys.argv[3:]
        
    start = time.time()
    level = logging.WARNING
    format = '%(asctime)s %(name)s %(levelname)s [%(funcName)s] %(message)s'
    logging.basicConfig(level=level, format=format)

    # Remove root log handlers:
    for h in logging.root.handlers:
        logging.root.removeHandler(h)
    # Set up output files:
    events_log_file = os.path.join(output_dir, 'events-' + firm_name + '.log')
    daily_stats_log_file = os.path.join(output_dir, 'daily_stats-' + firm_name + '.log')

    lob = LimitOrderBook(show_output=False, sparse_events=True,
                              events_log_file=events_log_file,
                              stats_log_file=None,
                              daily_stats_log_file=daily_stats_log_file)



    for file_name in sorted(file_name_list):
        tp = pandas.read_csv(file_name,
                             names=col_names,
                             iterator=True,
                             compression=None)
        while True:
            try:
                data = tp.get_chunk(500)
            except StopIteration:
                break
            else:
                # Process orders that occurred before a certain cutoff time:
                #if data.irow(0)['trans_time'] > '09:25:00.000000':
                #    break        
                lob.process(data)

    lob.record_daily_stats(lob.day)
    lob.print_daily_stats()
    print 'Processing time:              ', (time.time()-start)


class LimitOrderBook(object):
    """
    Limit order book for Indian exchange.
    """
    def __init__(self, show_output=True, sparse_events=True, events_log_file='events.log',
                 stats_log_file='stats.log', daily_stats_log_file='daily_stats.log'):
        self.logger = logging.getLogger('lob')

        self._show_output = show_output
        
        self._book_data = {}
        self._book_data[BID] = {}
        self._book_data[ASK] = {}
        self._book_prices = {}
        self._book_prices[BID] = rbtree.rbtree()
        self._book_prices[ASK] = rbtree.rbtree()
        
        self._init_price_level_stats = {
            'volume_original_total': 0,
            'volume_disclosed_total': 0}        
        self._price_level_stats = {}
        self._price_level_stats[BID] = {}
        self._price_level_stats[ASK] = {}


        self._init_last_book_best_values = \
            {'best_bid_price': 0.0,
             'best_bid_volume_original': 0,
             'best_ask_price': 0.0,
             'best_ask_volume_original': 0}
        self._last_book_best_values = \
            copy.copy(self._init_last_book_best_values)


        self._book_orders_to_price = {}
        self._event_counter = 1
        self._sparse_events = sparse_events
        self._original_event_counter = 1
        self._events_log_file = events_log_file
        if events_log_file:
            self._events_log_fh = open(events_log_file, 'w')
            self._events_log_writer = csv.writer(self._events_log_fh)
        self._stats_log_file = stats_log_file
        if stats_log_file:
            self._stats_log_fh = open(stats_log_file, 'w')
            self._stats_log_writer = csv.writer(self._stats_log_fh)

        self._daily_stats_log_file = daily_stats_log_file
        if daily_stats_log_file:
            self._daily_stats_log_fh = open(daily_stats_log_file, 'w')
            self._daily_stats_log_writer = csv.writer(self._daily_stats_log_fh)
        self._init_daily_stats = {
            'num_orders': 0,
            'num_trades': 0,
            'trade_volume_total': 0.0,
            'trade_price_mean': 0.0,
            'trade_price_std': 0.0,
            'mean_order_interarrival_time': 0.0}
        self._curr_daily_stats = copy.copy(self._init_daily_stats)
        self._last_order_time = 0.0
        self.day = None
        self._order_interarrival_time = {}
        self._curr_order_interarrival_time = None

    def __del__(self):

        
        try:
            self._events_log_fh.close()            
        except:
            pass
        try:
            self._stats_log_fh.close()
        except:
            pass
        try:
            self._daily_stats_log_fh.close()
        except:
            pass
        
    def clear_book(self):

        self.logger.info('clearing outstanding limit orders')
        for d in self._book_data.keys():
            self._book_data[d].clear()
            self._book_prices[d].clear()
            self._price_level_stats[d].clear()
            self.day = None
        self._book_orders_to_price.clear()

    def process(self, df):
                 
        for row in df.iterrows():
            order = row[1].to_dict()
            self.logger.info('processing order: %i (%s, %s)' % (order['order_number'],
                                                                order['trans_date'],
                                                                order['trans_time']))

            trans_date = datetime.datetime.strptime(order['trans_date'], '%m/%d/%Y')
            if self.day != trans_date.day:

                if self._daily_stats_log_file and self.day is not None:
                   self.record_daily_stats(self.day)

                self.logger.info('new day - book reset')
                self.clear_book()
                self.day = trans_date.day
                self.logger.info('setting day: %s' % self.day)

                self._last_order_time = \
                  datetime.datetime.strptime(order['trans_date']+' '+\
                                             order['trans_time'],
                                             '%m/%d/%Y %H:%M:%S.%f')        

                self._curr_daily_stats = \
                    copy.copy(self._init_daily_stats)

                self._last_book_best_values = \
                    copy.copy(self._init_last_book_best_values)
                    
 
            if order['activity_type'] == 1:
                self.add(order, 'Y')
            elif order['activity_type'] == 3:
                self.cancel(order)
            elif order['activity_type'] == 4:
   
                if order['mkt_flag'] == 'Y':
                    self.add(order, 'Y')
                else:    
                    self.modify(order)
            else:
                raise ValueError('unrecognized activity type %i' % \
                                 order['activity_type'])                

    def create_level(self, indicator, price):
        
        od = odict.odict()
        self._book_data[indicator][price] = od
        self._book_prices[indicator][price] = True        
        self._price_level_stats[indicator][price] = \
            copy.copy(self._init_price_level_stats)
        self.logger.info('created new price level: %s, %f' % (indicator, price))
        return od

    def delete_level(self, indicator, price):
               
        self._book_data[indicator].pop(price)
        del self._book_prices[indicator][price]
        self._price_level_stats[indicator].pop(price)
        self.logger.info('deleted price level: %s, %f' % (indicator, price))


    def add_order(self, order):
 
        order_number = order['order_number']
        indicator = order['buy_sell_indicator']
        price = order['limit_price']
        od = self.price_level(indicator, price)

        if od is None:
            self.logger.info('no matching price level found')
            od = self.create_level(indicator, price)
        
        od[order_number] = order
        self._book_orders_to_price[order_number] = od
        self._price_level_stats[indicator][price]['volume_original_total'] += \
            order['volume_original']
        self._price_level_stats[indicator][price]['volume_disclosed_total'] += \
            order['volume_disclosed']
            
        self.logger.info('added order: %s, %s, %s' % \
                            (order_number, indicator, price))    
            

    def delete_order(self, order):
 
        order_number = order['order_number']
        try:            
            od = self._book_orders_to_price.pop(order_number)
        except:
            self.logger.info('order not found: %s' % order_number)
        else:
            order = od.pop(order_number)
            indicator = order['buy_sell_indicator']
            price = order['limit_price']

            self._price_level_stats[indicator][price]['volume_original_total'] -= \
                order['volume_original']
            self._price_level_stats[indicator][price]['volume_disclosed_total'] -= \
                order['volume_disclosed']

            self.logger.info('deleted order: %s, %s, %s' % \
                             (order_number, indicator, price))    
            
          
            if not od:
                self.delete_level(indicator, price)
            

    def best_bid_price(self):
       
        try:
            best_price = self._book_prices[BID].max()
        except:
            return None
        else:
            return best_price
        
    def best_bid_data(self):
       
        best_bid_price = self.best_bid_price()
        if best_bid_price is not None:
            volume_original_total = \
                self._price_level_stats[BID][best_bid_price]['volume_original_total']
            volume_disclosed_total = \
                self._price_level_stats[BID][best_bid_price]['volume_disclosed_total']
        else:
            volume_original_total = volume_disclosed_total = 0
        return best_bid_price, volume_original_total, volume_disclosed_total
    
    def best_ask_price(self):

        try:
            best_price = self._book_prices[ASK].min()
        except:
            return None
        else:
            return best_price

    def best_ask_data(self):
        
        best_ask_price = self.best_ask_price()
        if best_ask_price is not None:
            volume_original_total = \
                self._price_level_stats[ASK][best_ask_price]['volume_original_total']
            volume_disclosed_total = \
                self._price_level_stats[ASK][best_ask_price]['volume_disclosed_total']
        else:
            volume_original_total = volume_disclosed_total = 0
        return best_ask_price, volume_original_total, volume_disclosed_total
        
    def price_level(self, indicator, price):

        try:
            book = self._book_data[indicator]
        except KeyError:
            raise ValueError('invalid buy/sell indicator')

        try:
            od = book[price]
        except KeyError:
           
            return None
        else:
           
            return od

    def record_event(self, **event):
            if event['is_original'] == 'Y':
            self._original_event_counter += 1
            self._curr_daily_stats['num_orders'] += 1


            date_time = datetime.datetime.strptime(event['date']+' '+\
                                                   event['time'],
                                                   '%m/%d/%Y %H:%M:%S.%f')
            curr_interarrival_time = \
                (date_time-self._last_order_time).total_seconds()
            self._last_order_time = date_time
            if self._curr_daily_stats['num_orders'] == 1:
                self._curr_daily_stats['mean_order_interarrival_time'] = \
                    curr_interarrival_time
            else:
                N = float(self._curr_daily_stats['num_orders'])
                N_prev = N-1
                self._curr_daily_stats['mean_order_interarrival_time'] = \
                    self._curr_daily_stats['mean_order_interarrival_time']*(N_prev/N)+\
                    curr_interarrival_time/N
                    
        if event['action'] == 'trade':


            self._curr_daily_stats['num_trades'] += 1


            self._curr_daily_stats['trade_volume_total'] += \
                event['volume_original']

            if self._curr_daily_stats['num_trades'] == 1:                
                self._curr_daily_stats['trade_price_mean'] = \
                    event['price']
            else:
                N = float(self._curr_daily_stats['num_trades'])
                N_prev = N-1
                self._curr_daily_stats['trade_price_mean'] = \
                    (self._curr_daily_stats['trade_price_mean']*N_prev+\
                    event['price'])/N
                self._curr_daily_stats['trade_price_std'] = \
                  np.sqrt((self._curr_daily_stats['trade_price_std']**2*N_prev+\
                          (event['price']-self._curr_daily_stats['trade_price_mean'])**2)/N)

        if self._show_output:
            print '----------------------------------------'

            # Print last event:
            print self.event_to_row(event)
            
            # Print queue states:
            print 'sell queue:'
            self.print_book(SELL)
            print 'buy queue:'
            self.print_book(BUY)

        if self._events_log_file:


            if self._sparse_events:
                best_keys = ['best_bid_price', 'best_ask_price',
                            'best_bid_volume_original',
                            'best_ask_volume_original']
                if event['action'] == 'trade' or \
                    any([event[k] != self._last_book_best_values[k] for k in best_keys]):                
                    row = self.event_to_row(event)
                    self._events_log_writer.writerow(row)

                    # Update the last best values:
                    for k in best_keys:
                        self._last_book_best_values[k] = event[k]
            else:
                row = self.event_to_row(event)
                self._events_log_writer.writerow(row)
                
                
    def record_stats(self, t, d):

        
        if self._stats_log_file:
            row = [t, d,
                   self._curr_daily_stats['num_orders'],
                   self._curr_daily_stats['num_trades'],
                   self._curr_daily_stats['trade_volume_total'],
                   self._curr_daily_stats['trade_price_mean'],
                   self._curr_daily_stats['trade_price_std'],
                   self._curr_daily_stats['mean_order_interarrival_time']]
            self._stats_log_writer.writerow(row)


    def record_daily_stats(self, d):


        if self._daily_stats_log_file:
            row = [d,
                   self._curr_daily_stats['num_orders'],
                   self._curr_daily_stats['num_trades'],
                   self._curr_daily_stats['trade_volume_total'],
                   self._curr_daily_stats['trade_price_mean'],
                   self._curr_daily_stats['trade_price_std'],
                   self._curr_daily_stats['mean_order_interarrival_time']]
            self._daily_stats_log_writer.writerow(row)
            
           
    def add(self, new_order, is_original):


        best_bid_price, best_bid_volume_original, best_bid_volume_disclosed = \
          self.best_bid_data()
        best_ask_price, best_ask_volume_original, best_ask_volume_disclosed = \
          self.best_ask_data()
        event = \
          dict(time=new_order['trans_time'],
               date=new_order['trans_date'],
               order_number=new_order['order_number'],
               indicator=new_order['buy_sell_indicator'],
               mkt_flag=new_order['mkt_flag'],
               io_flag=new_order['io_flag'],
               action='add',
               is_original=is_original,               
               price=new_order['limit_price'],               
               volume_original=new_order['volume_original'],
               volume_disclosed=new_order['volume_disclosed'],
               best_bid_price=best_bid_price,
               best_bid_volume_original=best_bid_volume_original,
               best_ask_price=best_ask_price,
               best_ask_volume_original=best_ask_volume_original)


        new_indicator = new_order['buy_sell_indicator']
        volume_original = new_order['volume_original']
        volume_disclosed = new_order['volume_disclosed']

        self.logger.info('attempting add of order: %s, %s, %s, %f, %d, %d' % \
                         (new_order['order_number'], new_indicator, new_order['mkt_flag'],
                         new_order['limit_price'], volume_original,
                         volume_disclosed))

        if new_order['mkt_flag'] == 'Y':
            while volume_original > 0:

                if new_indicator == BUY:
                    buy_order = new_order
                    best_price = self.best_ask_price()
                    if best_price is None:
                        self.logger.info('no sell limit orders in book yet '
                                         '- stopping processing of market buy order')
                        break
                    od = self.price_level(ASK, best_price) 
                elif new_indicator == SELL:
                    sell_order = new_order
                    best_price = self.best_bid_price()
                    if best_price is None:
                        self.logger.info('no buy limit orders in book yet '
                                         '- stopping processing of market sell order')
                        break
                    od = self.price_level(BID, best_price)
                else:
                    RuntimeError('invalid buy/sell indicator')


                if new_indicator == BUY and best_price > new_order['limit_price']:
                    self.logger.info('best ask exceeds specified buy price')
                    break
                if new_indicator == SELL and best_price < new_order['limit_price']:
                    self.logger.info('best bid is below specified sell price')
                    break

                order_number_list = []
                for order_number in od.keys():
                    if od[order_number]['volume_disclosed'] == 0:
                        order_number_list.append(order_number)
                for order_number in od.keys():
                    if od[order_number]['volume_disclosed'] > 0:
                        order_number_list.append(order_number)
                        

                for order_number in order_number_list:
                    curr_order = od[order_number]
                    if curr_order['buy_sell_indicator'] == BUY:
                        buy_order = curr_order
                    elif curr_order['buy_sell_indicator'] == SELL:
                        sell_order = curr_order
                    else:
                        RuntimeError('invalid buy/sell indicator')

                    if curr_order['volume_original'] == volume_original:
                        self.logger.info('current limit order original volume '
                                         'vs. arriving market order original volume: '
                                         '%s = %s' % \
                                         (curr_order['volume_original'],
                                          volume_original))

                        self.record_event(**event)

                        event['action'] = 'trade'
                        event['price'] = best_price
                        event['volume_original'] = volume_original
                        event['volume_disclosed'] = volume_disclosed
                        self.record_event(**event)


                        self.record_stats(event['time'], event['date'])
                        
                        self.delete_order(curr_order) 
                        volume_original = 0.0                 
                        break

                    elif curr_order['volume_original'] > volume_original:
                        self.logger.info('current limit order original volume '
                                         'vs. arriving market order original volume: '
                                         '%s > %s' % \
                                         (curr_order['volume_original'],
                                          volume_original))   

                        self.record_event(**event)

                        event['action'] = 'trade'
                        event['price'] = best_price
                        event['volume_original'] = volume_original
                        event['volume_disclosed'] = volume_disclosed
                        self.record_event(**event)


                        self.record_stats(event['time'], event['date'])
                        
                        if new_order['io_flag'] == 'N':
                            self.logger.info('Non-IOC order - residual volume preserved')
                            curr_order['volume_original'] -= volume_original
                            self._price_level_stats[curr_order['buy_sell_indicator']][curr_order['limit_price']]['volume_original_total'] \
                                -= volume_original
                        else:
                            self.logger.info('IOC order - residual volume discarded')
                        volume_original = 0.0
                        break

                    elif curr_order['volume_original'] < volume_original:
                        self.logger.info('current limit order original volume '
                                         'vs. arriving market order original volume: '
                                         '%s < %s' % \
                                         (curr_order['volume_original'],
                                          volume_original))                  
                        trade = dict(trade_price=best_price,
                                     trade_quantity=curr_order['volume_original'],
                                     buy_order_number=buy_order['order_number'],
                                     sell_order_number=sell_order['order_number'])

                        self.record_event(**event)

                        event['action'] = 'trade'
                        event['price'] = best_price
                        event['volume_original'] = curr_order['volume_original']
                        event['volume_disclosed'] = curr_order['volume_disclosed']
                        self.record_event(**event)

                    
                        self.record_stats(event['time'], event['date'])
                        
                        volume_original -= curr_order['volume_original']
                        self.delete_order(curr_order)
                    else:

                       
                        pass

        elif new_order['mkt_flag'] == 'N':


            price = new_order['limit_price']
            marketable = True
            best_ask_price = self.best_ask_price()
            best_bid_price = self.best_bid_price()
            if new_indicator == BUY and best_ask_price is not None \
                   and price >= best_ask_price:
                self.logger.info('buy order is marketable')
                best_price = best_ask_price;
            elif new_indicator == SELL and best_bid_price is not None \
                   and price <= best_bid_price:
                self.logger.info('sell order is marketable')
                best_price = best_bid_price;
            else:
                marketable = False


            if not marketable:
                self.logger.info('order is not marketable')
                self.record_event(**event)
                self.add_order(new_order)
                

            else:


                while volume_original > 0.0:
                
                    if new_indicator == BUY:
                        buy_order = new_order                    
                        best_price = self.best_ask_price()
                        if best_price is None:
                            self.logger.info('no sell limit orders in book yet '
                                             '- stopping processing of limit buy order')
                            self.add_order(new_order)
                            break
                        od = self.price_level(ASK, best_price)
                    elif new_indicator == SELL:
                        sell_order = new_order
                        best_price = self.best_bid_price()
                        if best_price is None:
                            self.logger.info('no buy limit orders in book yet '
                                             '- stopping processing of limit sell order')
                            self.add_order(new_order)
                        od = self.price_level(BID, best_price)
                    else:
                        RuntimeError('invalid buy/sell indicator')

                    if new_indicator == BUY and best_price > new_order['limit_price']:
                        self.logger.info('best ask exceeds specified buy price')
                        if new_order['io_flag'] == 'N':
                            new_order['volume_original'] = volume_original
                            self.add(new_order, 'N')
                        break
                    if new_indicator == SELL and best_price < new_order['limit_price']:
                        self.logger.info('best bid is below specified sell price')
                        if new_order['io_flag'] == 'N':
                            new_order['volume_original'] = volume_original
                            self.add(new_order, 'N')
                        break


                    if od is not None:
                        for order_number in od.keys():
                            if od[order_number]['volume_disclosed'] == 0:
                                order_number_list.append(order_number)
                        for order_number in od.keys():
                            if od[order_number]['volume_disclosed'] > 0:
                                order_number_list.append(order_number)

                    for order_number in order_number_list: 
                        curr_order = od[order_number]
                        if new_indicator == BUY:
                            sell_order = curr_order
                        elif new_indicator == SELL:
                            buy_order = curr_order
                        else:
                            RuntimeError('invalid buy/sell indicator')


                        if curr_order['volume_original'] == volume_original:
                            self.logger.info('current limit order original volume '
                                             'vs. arriving limit order original volume: '
                                             '%s = %s' % \
                                             (curr_order['volume_original'],
                                              volume_original))


                            self.record_event(**event)


                            event['action'] = 'trade'
                            event['price'] = best_price
                            event['volume_original'] = volume_original
                            event['volume_disclosed'] = volume_disclosed
                            self.record_event(**event)

                            self.delete_order(curr_order)
                            volume_original = 0.0
                            break
                        

                        elif curr_order['volume_original'] > volume_original:
                            self.logger.info('current limit order original volume '
                                             'vs. arriving limit order original volume: '
                                             '%s > %s' % \
                                             (curr_order['volume_original'],
                                              volume_original))


                            self.record_event(**event)


                            event['action'] = 'trade'
                            event['price'] = best_price
                            event['volume_original'] = volume_original
                            event['volume_disclosed'] = volume_disclosed
                            self.record_event(**event)


                            self.record_stats(event['time'], event['date'])
                            
                            if new_order['io_flag'] == 'N':
                                self.logger.info('Non-IOC order - residual volume preserved')  
                                curr_order['volume_original'] -= volume_original
                                self._price_level_stats[curr_order['buy_sell_indicator']][curr_order['limit_price']]['volume_original_total'] \
                                  -= volume_original
    
                            else:
                                self.logger.info('IOC order - residual volume discarded')
                            volume_original = 0.0
                            break


                        elif curr_order['volume_original'] < volume_original:
                            self.logger.info('current limit order original volume '
                                             'vs. arriving limit order original volume: '
                                             '%s < %s' % \
                                             (curr_order['volume_original'],
                                              volume_original))

                            self.record_event(**event)


                            event['action'] = 'trade'
                            event['price'] = best_price
                            event['volume_original'] = curr_order['volume_original']
                            event['volume_disclosed'] = curr_order['volume_disclosed']
                            self.record_event(**event)


                            self.record_stats(event['time'], event['date'])
                            
                            volume_original -= curr_order['volume_original']
                            self.delete_order(curr_order) 
                        else:

                            pass                                            
        else:
            raise RuntimeError('invalid market order flag')


    def modify(self, new_order):


        best_bid_price, best_bid_volume_original, best_bid_volume_disclosed = \
          self.best_bid_data()
        best_ask_price, best_ask_volume_original, best_ask_volume_disclosed = \
          self.best_ask_data()
        event = \
          dict(time=new_order['trans_time'],
               date=new_order['trans_date'],
               order_number=new_order['order_number'],
               indicator=new_order['buy_sell_indicator'],
               mkt_flag=new_order['mkt_flag'],
               io_flag=new_order['io_flag'],
               is_original='Y',
               action='modify',               
               price=new_order['limit_price'],               
               volume_original=new_order['volume_original'],
               volume_disclosed=new_order['volume_disclosed'],
               best_bid_price=best_bid_price,
               best_bid_volume_original=best_bid_volume_original,
               best_ask_price=best_ask_price,
               best_ask_volume_original=best_ask_volume_original)

        self.logger.info('attempting modify of order: %s, %s' % \
                         (new_order['order_number'],
                          new_order['buy_sell_indicator']))
        

        if new_order['mkt_flag'] == 'Y':
            raise ValueError('cannot modify market order')

        book = self._book_data[new_order['buy_sell_indicator']]
        try:
            od = self._book_orders_to_price[new_order['order_number']]
        except:
            self.logger.info('order number %s not found' % new_order['order_number'])
        else:
            old_order = od[new_order['order_number']]
            
            # If the modify changes the price of an order, remove it and
            # then add the modified order to the appropriate price level queue:
            if new_order['limit_price'] != old_order['limit_price']:
                self.logger.info('modified order %i price from %f to %f: ' % \
                                 (new_order['order_number'],
                                  old_order['limit_price'],
                                  new_order['limit_price']))
                self.delete_order(old_order)                                   
                self.add(new_order, 'N')

            # If the modify reduces the original or disclosed volume of an
            # order, update it without altering where it is in the price level queue:
            elif new_order['volume_original'] < old_order['volume_original'] or \
                new_order['volume_disclosed'] < old_order['volume_disclosed']:
                self.logger.info('modified order %i (original, disclosed) volume '                    
                                 'from (%i, %i) to (%i, %i)' % \
                                 (new_order['order_number'],
                                  old_order['volume_original'], old_order['volume_disclosed'],
                                  new_order['volume_original'], new_order['volume_disclosed']))
                od[new_order['order_number']] = new_order


                self._price_level_stats[new_order['buy_sell_indicator']][new_order['limit_price']]['volume_original_total'] \
                    += -old_order['volume_original']+new_order['volume_original']
                self._price_level_stats[new_order['buy_sell_indicator']][new_order['limit_price']]['volume_disclosed_total'] \
                    += -old_order['volume_disclosed']+new_order['volume_disclosed']                
                

            elif new_order['volume_original'] > old_order['volume_original'] or \
                new_order['volume_disclosed'] > old_order['volume_disclosed']:
                self.logger.info('modified order %i (original, disclosed) volume '
                                 'from (%i, %i) to (%i, %i)' % \
                                 (new_order['order_number'],
                                  old_order['volume_original'], old_order['volume_disclosed'],
                                  new_order['volume_original'], new_order['volume_disclosed']))
                new_order_modified = new_order.copy()
                new_order_modified['volume_original'] -= old_order['volume_original']
                new_order_modified['volume_disclosed'] -= old_order['volume_disclosed']
                self.add(new_order_modified, 'N')


                self._price_level_stats[new_order['buy_sell_indicator']][new_order['limit_price']]['volume_original_total'] \
                    += -old_order['volume_original']+new_order['volume_original']
                self._price_level_stats[new_order['buy_sell_indicator']][new_order['limit_price']]['volume_disclosed_total'] \
                    += -old_order['volume_disclosed']+new_order['volume_disclosed']                

            else:
                self.logger.info('undefined modify scenario')
                            
        self.record_event(**event)
        self.record_stats(event['time'], event['date'])
    def cancel(self, order):

                
        best_bid_price, best_bid_volume_original, best_bid_volume_disclosed = \
          self.best_bid_data()
        best_ask_price, best_ask_volume_original, best_ask_volume_disclosed = \
          self.best_ask_data()
        event = \
          dict(time=order['trans_time'],
               date=order['trans_date'],
               order_number=order['order_number'],
               indicator=order['buy_sell_indicator'],
               mkt_flag=order['mkt_flag'],
               io_flag=order['io_flag'],
               action='cancel',               
               is_original='Y',               
               price=order['limit_price'],               
               volume_original=order['volume_original'],
               volume_disclosed=order['volume_disclosed'],
               best_bid_price=best_bid_price,
               best_bid_volume_original=best_bid_volume_original,
               best_ask_price=best_ask_price,
               best_ask_volume_original=best_ask_volume_original)

        self.logger.info('attempting cancel of order %s' % order['order_number'])

        # Filter out cancellation orders that are listed as market orders:
        if order['mkt_flag'] == 'Y':
            self.logger.info('cannot cancel market order %s' % order['order_number'])
        else:
            self.delete_order(order)
        self.record_event(**event)
        self.record_stats(event['time'], event['date'])
              
        
    def print_book(self, indicator):


        book = self._book_data[indicator]
        prices = self._book_prices[indicator]
        for price in prices.keys():
            print '%06.2f: ' % price,            
            for order_number in book[price]:
                order = book[price][order_number]
                print '(%s,%s)' % (order['volume_original'], order['volume_disclosed']),
            print ''
    def event_to_row(self, event):

        
        row = [event['time'],
               event['date'],
               event['order_number'],
               event['indicator'],
               event['mkt_flag'],
               event['action'],
               event['is_original'],               
               event['price'],               
               event['volume_original'],
               event['volume_disclosed'],
               event['best_bid_price'],
               event['best_bid_volume_original'],
               event['best_ask_price'],
               event['best_ask_volume_original']]
        return row
    
    def print_daily_stats(self):

        print '--------------------------------------------'
        print 'Number of orders:             ', self._curr_daily_stats['num_orders']
        print 'Number of trades:             ', self._curr_daily_stats['num_trades']
        print 'Total trade volume:           ', self._curr_daily_stats['trade_volume_total']
        print 'Mean trade price:             ', self._curr_daily_stats['trade_price_mean']
        print 'Trade price STD:              ', self._curr_daily_stats['trade_price_std']
        print 'Mean order interarrival time: ', self._curr_daily_stats['mean_order_interarrival_time']