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
    order_number=line[6:22]

    #transcation_time=line[22:36]
     
    transcation_time_f=int(line[22:36])/65536.0+time_adjust
    transcation_time=datetime.strftime(datetime.utcfromtimestamp(transcation_time_f),'%H:%M:%S.%f')


    buy_sell=line[36]
    activity_type=line[37]
    symbol=line[38:48]
    series=line[48:50]
    volume_disclosed=line[50:58]
    volume_original=line[58:66]
    limit_price=line[66:72]+"."+line[72:74]
    trigger_price=line[74:80]+"."+line[80:82]
    market_order_flag=line[82]
    stop_loss_flag=line[83]
    io_flag=line[84]
    algo_indicator=line[85]
    client_identity_flag=line[86]
    #creating a string of variable seperated by comma","
    stringi=record_indicator+","+segment+","+order_number+","+transcation_time+ \
             ","+buy_sell+","+activity_type+","+symbol+","+series+","+volume_disclosed+ \
             ","+volume_original+","+limit_price+","+trigger_price+","+market_order_flag+\
             ","+stop_loss_flag+","+io_flag+","+algo_indicator+","+client_identity_flag
    output_file.write(stringi+"\n");
    
input_file.close() #closing input file
output_file.close() #closing output file
