# Program to convert the FAO Trade .dat file to comma seperated file
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
    trade_date=line[12:14]+"/"+line[10:12]+"/"+line[6:10] 
   #trade_date=line[6:14]
    
    transcation_time_f=int(line[22:36])/65536.0+time_adjust
    #transcation_time_f=((((float(line[22:36])/65535)/60)/60)/24)
    #transcation_time=str(transcation_time_f)
    transcation_time=datetime.strftime(datetime.utcfromtimestamp(transcation_time_f),'%H:%M:%S.%f')
    
    symbol=line[36:46]
    instrument=line[46:52]
    #expiry_date=line[54:63]
    mon=str(strptime(line[54:57],'%b').tm_mon)
     
    expiry_date=mon+"/"+line[52:54]+"/"+line[57:61]

    strike_price=line[61:67]+"."+line[67:69]
    option_type=line[69:71]

    trade_price=line[71:77]+"."+line[77:79]
    trade_quantity=line[79:87]
    buy_order_number=line[87:103]
    buy_algo_indicator=line[103]
    buy_client_identity_flag=line[104]
    sell_order_number=line[105:121]
    sell_algo_indicator=line[121]
    sell_client_identity_flag=line[122]



    #creating a string of variable seperated by comma","
    stringi=record_indicator+","+segment+","+trade_number+","+trade_date+","+transcation_time+\
             ","+symbol+","+instrument+","+expiry_date+\
             ","+strike_price+","+option_type+","+trade_price+\
             ","+trade_quantity+","+buy_order_number+","+buy_algo_indicator+","+buy_client_identity_flag+\
             ","+sell_order_number+","+sell_algo_indicator+","+sell_client_identity_flag
    output_file.write(stringi+"\n");
    
input_file.close() #closing input file
output_file.close() #closing output file
