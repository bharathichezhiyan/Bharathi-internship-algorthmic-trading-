import time
from time import strptime
from datetime import datetime
time_adjust=(datetime(1980,1,1,0,0,0)-\
             datetime(1970,1,1,0,0,0)).total_seconds()

fname=raw_input('Enter the file name: ')# getting file name from user
cond=raw_input('Enter the cond: ')
dotpos=fname.find('.') # seperating name by '.' delimiter to create output file name
host=fname[0:dotpos]
ofname=host+"_"+cond+".csv"
try:
    input_file=open(fname,'r') #opening the input file
    output_file=open(ofname,'w') #opening the output file
except:
    print "file cannot be opened" # exception handling
    exit()
for line in input_file: # reading line by line
    line=line.rstrip() 
    line=line.split(',')
    #print line[5]
    if((line[5]=='B')and(line[13]=='Y')and(line[16]=='1')):
	outstring=line[4]+","+line[12]+","+line[11]+","+line[10]+","+line[9]
	output_file.write(outstring+"\n");
	#print "%s"%outstring
input_file.close() #closing input file
output_file.close() #closing output file
