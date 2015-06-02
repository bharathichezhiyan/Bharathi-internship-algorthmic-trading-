create table cash_trade
(
  record_indicator enum("RM","PO"),
  segmant enum("CASH"),
  trade_number bigint unsigned not null,
  trade_times bigint unsigned not null,
  symbol char(10) not null,
  series char(2) not null,
  trade_price int unsigned not null,
  trade_quantity int unsigned not null,
  buy_order_number bigint unsigned not null,
  buy_algo_indicator tinyint(1) not null,
  buy_client_indentity_flag tinyint(1) not null,
  sell_order_number bigint unsigned not  null,
  sell_algo_indicator tinyint(1) not null,
  sell_client_identity_flag tinyint(1) not null,
  primary key(trade_number,trade_times)
);
