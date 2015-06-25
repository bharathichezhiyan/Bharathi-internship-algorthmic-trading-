import matplotlib.pyplot as plt

#program to extract and merge the outputs

fname=raw_input("Enter the calculated file name:")
tname=raw_input("Enter the trade file name:")
out=fname.split(".")
outname=out[0]+"_combined.csv"
#print outname
try:
    inputfile=open(fname,'r')
    inputfile2=open(tname,'r')
    outfile=open(outname,'w')
except:
    print "File cannot be opened"
    exit()
#print fname
k=[]
t=[]

for line in inputfile:
    line.strip()
    kline=line.split(" ")
    if kline[0][0]=='-' or kline[0][0]=='T':
	continue
    elif kline[2]=='trades:':
	k.append(int(kline[16]))
#print k

for line in inputfile2:
    line.strip()
    splitedline=line.split(" ")
    t.append(int(splitedline[0]))
#print t
for i in range(len(k)):
    row="{0},{1}\n".format(k[i],t[i])
    outfile.write(row)

inputfile.close()
inputfile2.close()
outfile.close()
    

