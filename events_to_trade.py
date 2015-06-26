#events to trade

while True:
    try:
	fname=raw_input("Enter the file name : ")
	fname_split=fname.split(".")
	outname=fname_split[0]+"_trade.csv"
	infile=open(fname,'r')
	outfile=open(outname,'w')
    except:
	print "files cannot be opened"
	exit()
    for line in infile:
	line.strip()
	linek=line.split(",")
        #print linek[0]
	if linek[5]=='trade':
	    outfile.write(line.strip())
    infile.close()
    outfile.close()
    exitk=raw_input("Exit: y/n \n")
    if exitk=='y':
	exit()
      

