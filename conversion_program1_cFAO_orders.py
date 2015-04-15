# Program to convert the FAO Order .dat file to comma seperated file
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
    order_date=line[12:14]+"/"+line[10:12]+"/"+line[6:10] 
   #order_date=line[6:14]
    
    transcation_time_f=int(line[22:36])/65536.0+time_adjust
    #transcation_time_f=((((float(line[22:36])/65535)/60)/60)/24)
    #transcation_time=str(transcation_time_f)
    transcation_time=datetime.strftime(datetime.utcfromtimestamp(transcation_time_f),'%H:%M:%S.%f')
    buy_sell=line[36]
    activity_type=line[37]
    symbol=line[38:48]
    instrument=line[48:54]
    #expiry_date=line[54:63]
    mon=str(strptime(line[56:59],'%b').tm_mon)
     
    expiry_date=mon+"/"+line[54:56]+"/"+line[59:63]

    strike_price=line[63:71]
    option_type=line[71:73]
    volume_disclosed=line[73:81]
    volume_orginal=line[81:89]
    limit_price=line[89:95]+"."+line[96:97]
    trigger_price=line[97:103]+"."+line[103:105]
    mkt_flag=line[105]
    on_stop_flag=line[106]
    io_flag=line[107]
    spread_type=line[108]
    algo_indicator=line[109]
    client_identity_flag=line[110]

    #creating a string of variable seperated by comma","
    stringi=record_indicator+","+segment+","+order_number+","+order_date+","+transcation_time+\
             ","+buy_sell+","+activity_type+","+symbol+","+instrument+","+expiry_date+\
             ","+strike_price+","+option_type+","+volume_disclosed+\
             ","+volume_orginal+","+limit_price+","+trigger_price+","+mkt_flag+","+on_stop_flag+\
             ","+io_flag+","+spread_type+","+algo_indicator+","+client_identity_flag
    output_file.write(stringi+"\n");
    
input_file.close() #closing input file
output_file.close() #closing output file
