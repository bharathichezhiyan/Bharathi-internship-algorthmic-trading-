# Program to convert the CASH Order .dat file to comma seperated file
# by Bharathi Raja Asoka Chakravarthi,
# Research Associate(Intern),
# under Dr.Sumit Kumar, IIM-Udaipur
import time
from time import strptime
from datetime import datetime

time_adjust=(datetime(1980,1,1,0,0,0)-\
             datetime(1970,1,1,0,0,0)).total_seconds()

fname=raw_input('Enter the file name: ')# getting file name from user
dotpos=fname.find('.') # seperating name by '.' delimiter to create output file name
host=fname[0:dotpos] # output filename as of inputfile name with out extension
ofname=host+".csv" # output filename with extension of .csv
try:
    input_file=open(fname,'r') #opening the input file
    output_file=open(ofname,'w') #opening the output file
except:
    print "file cannot be opened" # exception handling
    exit()
for line in input_file: # reading line by line
    line=line.rstrip() #to clear unwanted space
    record_indicator=line[0:2] #first two values in line is assingned to record_indicator
    segment=line[2:6]
    trade_number=line[6:22]
    #trade_time=line[22:36]
    transcation_time_f=int(line[22:36])/65536.0+time_adjust

    trade_time=datetime.strftime(datetime.utcfromtimestamp(transcation_time_f),'%H:%M:%S.%f')

    symbol=line[36:46]
    series=line[46:48]
    trade_price=line[48:54]+"."+line[54:56]
    trade_quantity=line[56:64]
    buy_order_number=line[64:80]
    buy_algo_indicator=line[80]
    buy_client_identity_flag=line[81]
    sell_order_number=line[82:98]
    sell_algo_indicator=line[98]
    sell_client_identity_flag=line[99]
    #creating a string of variable seperated by comma","
    stringi=record_indicator+","+segment+","+trade_number+","+trade_time+ \
             ","+symbol+","+series+","+trade_price+ \
             ","+trade_quantity+","+buy_order_number+","+buy_algo_indicator+\
             ","+buy_client_identity_flag+","+sell_order_number+","+sell_algo_indicator+","+sell_client_identity_flag
    output_file.write(stringi+"\n");
    
input_file.close() #closing input file
output_file.close() #closing output file
