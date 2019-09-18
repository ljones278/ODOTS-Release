#Glue code to go from file -socket...
#The socket does not take sub second precision - thereofre this class truncates the time info, luckily if we do not delete the
#data dump files after parsing them we can re process them to generate more precise results to split really fine results.
import subprocess
import os



class FileParserTCPWriter():

    def __init__(self, FileReadPath=None, TCPSocket = '10000',TCPHost='localhost',DeleteFileAfterUse=False):
        self.FileReadPath = os.getcwd() +FileReadPath
        self.OutputString = ""
        #note these next two are useless
        self.TCPSocket = TCPSocket
        self.TCPHost = TCPHost
        self.DeleteFileAfterUse = DeleteFileAfterUse

    def ProcessRecord(self,filename, DeleteFileAfterUse = None):
        if DeleteFileAfterUse ==None:
            DeleteFileAfterUse = self.DeleteFileAfterUse
        #read card info dump file
        ProcessString = self.ParseFile(filename, DeleteFileAfterUse)
        print("THIS IS NICE" +str(ProcessString))#send the info to the TCP socketprint("THIS IS NICE" +str(ProcessString))
        self.SendToSocket(ProcessString)

    def ParseFile(self,filename,DeleteFileAfterUse = None):
        if DeleteFileAfterUse ==None:
            DeleteFileAfterUse = self.DeleteFileAfterUse
        self.ReadFile = open(self.FileReadPath+'\\'+filename,'r')
        #lets read the name line
        NameLine = self.ReadFile.readline()
        #lets read the extra info lines (info not used)
        DumpInfo = self.ReadFile.readline()
        DumpInfo = self.ReadFile.readline()
        PunchRecords = self.ReadPunches()
        #now to create the argument string for the Java program inputs
        self.ReadFile.close()
        
        CardID = self.CalculateCardID(NameLine)
        
        NumberOfPunches = len(PunchRecords)-1 #-1 for the finish Punch which is actually tacked on the end!
        
        PunchCodes = ""
        PunchTimes = ""

        for Entry in PunchRecords:
            #note that the records are actually stored backwards in time (most recent ones are going to have lower indecies than earlier ones)
            #this is due to how the card is read out
            PunchCodes = Entry[0]+","+PunchCodes
            PunchTimes = Entry[1]+","+PunchTimes
        #remove the sneaky extra comma
        PunchCodes=PunchCodes[:-1]
        PunchTimes=PunchTimes[:-1]
        #construct string to be passed to java as arguments
        ReturnString = "C "+str(NumberOfPunches)+" "+str(CardID)+" "+PunchCodes+" "+PunchTimes

        
        return ReturnString
        
    def CalculateCardID(self, ReadString):
        #calculates Card ID number from uid (which is in hex) this is taken directly from serial utils script)
        UID = ((ReadString.split(":")[1]).strip()).split(" ") #WHOOOOOPS - strips out nont UID info and puts byte representations in an array with only byte representations
        UIDValue=0
        for i in range(0,len(UID)):
            UIDValue = (UIDValue*256)+int(('0x'+str(UID[len(UID)-i-1])),16)
        return UIDValue

    
    def ReadPunches(self,file = None):
        if file == None:
            file = self.ReadFile
        #handles the parsing of the data section
        FirstHalfPunches = []
        SecondHalfPunches= []
        while 1:
            LineFromFile = file.readline()
            if (LineFromFile != ""):
                #data encountered, time for parsing
                PunchRecords = self.ReadTimeLine(LineFromFile)
                #concatonate punch reocrd (dumping empty ones!
                if (PunchRecords[0] != [None,None]):
                    FirstHalfPunches.append(PunchRecords[0])
                if (PunchRecords[1] != [None,None]):
                    SecondHalfPunches.append(PunchRecords[1])

            else:
                #concatonate second and first half punches (all second halves will have occured after first halves!
                for PunchRecord in SecondHalfPunches:
                    FirstHalfPunches.append(PunchRecord)
                return FirstHalfPunches
        
    def ReadTimeLine(self,LineFromFile):
        #takes line from data file and returns 
        SplitLine = (LineFromFile.split('\t')) #take out block indicator
        if int(SplitLine[0]) < 4: #this allows us to skip the last block, where all the config info is held (this spits out really weirds punch records!
            return [[None,None],[None,None]]
        else:
            DataArray = (SplitLine[1].strip(' ')).split(' ') #Turns line string into array of strings representing the bytes
            FirstEntry = self.InterpretEntry(DataArray[0:8])
            SecondEntry = self.InterpretEntry(DataArray[8:16])
            return [FirstEntry,SecondEntry]

    def InterpretEntry(self, VisitRecordEntry):
        #Visit Record Entry is a string of two digit hex characters (each two digits representing a byte)
        #returns the code and time string if a valid record is contained, otherwise returns [none,none]
        #read a byte string
        IntegerArray = []
        
        for Byte in VisitRecordEntry:
            #this converts the random sting characters into a nicer integer array
            IntegerArray.append(int(('0x'+Byte),16)) #explicit hex conversion with addition of 0x before for good measure!

        if IntegerArray[2] == 0:#how to detect an empty slot!
            return [None,None]
        else:
            ControlCode = str((IntegerArray[0]<<8)+IntegerArray[1]) #generate control code string
            TimeCode = str(IntegerArray[3])+":"+str(IntegerArray[4])+":"+str(IntegerArray[5])#generate time String
            return [ControlCode, TimeCode] 

    def SendToSocket(self, String=None):
        if String == None:
            String = self.OutputString
        FinalString = "java SendPunch " + String
        Result = subprocess.run(FinalString,capture_output=True) #calls JAVA program that actually handles sending the info over a TCP link to MEoS
        #this next bit is to ensure that 
        if Result.stderr != b'':
            print(Result.stderr)
            return False
        else:
            return True
        '''
Parser = FileParserTCPWriter()

Parser.ProcessRecord(filename = "19-8-30-23_792323713.ODOTSRAW")'''
