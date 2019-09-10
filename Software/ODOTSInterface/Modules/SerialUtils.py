from serial import *
import serial.tools.list_ports as SerialFind
import time
import TimeUtils #(FOR SETTINGS)
import os
class ODOTS_Serial_Interface():
    
    
    def __init__(self,FileWritePath="",CurrentWorkingDirectory=os.getcwd(),ConfigObject=None,Verbose = False):
        self.FileWritePath = FileWritePath;
        self.Verbose = Verbose
        self.ActivePort=Serial()
        self.activePortName=""
        self.CurrentWorkingDirectory = CurrentWorkingDirectory
        self.OSComPortPrefix = "COM"#note this only works for windows devices
        self.PortDetailList = []
        self.LeonardoVIDPID = [[0x2341,0x0036],[0x2341,0x8036],[0x2A03,0x0036],[0x2A03,0x8036]] #nabbed from the Arduino drivers
        self.UNOVIDPID = [[0x2341,0x0043],[0x2341,0x0001],[0x2A03,0x0043],[0x2341,0x0243]]
        
    def ListAvailablePorts(self):
        PortList = SerialFind.comports()
        self.PortDetailList = []
        i = 0
        for Port in PortList:
            #append port list info to list
            self.PortDetailList.append([PortList[i].device, \
                                   PortList[i].manufacturer, PortList[i].product, \
                                   PortList[i].vid,PortList[i].pid])
            i = i+1 #iterate iterator...
        self.PortDetailList=self.NeatenPortList(PortList = self.PortDetailList)
        
        return self.PortDetailList
        
    def SelectPort(self,Port):
        #at the moment this assumes ther is only one available port and selects it.
        if len(self.PortDetailList) ==1:
            #a quick and dirty solution to make the test environment easier (when I can pretty much guarantee there will only be one com port
            self.ActivePortName=self.PortDetailList[0][0]
        else:
            self.ActivePortName = self.PortDetailList[Port][0]
        return self.ActivePortName
    def OpenPort(self,ConfigObject=None):
        
        #opens serial port selected by Acive Port
        if self.ActivePort.is_open:
            self.ActivePort.close() #close the active port if it is open
        if(ConfigObject==None):
            self.ActivePort = Serial(self.ActivePortName,baudrate = 9600,timeout = 1)
        else:
            self.ActivePort= Serial(self.ActivePortName,ConfigObject.baudrate,\
                                 ConfigObject.bytesize,ConfigObject.parity,\
                                 ConfigObject.stopbits,ConfigObject.timeout,\
                                 ConfigObject.xonxoff,ConfigObject.rtscts,\
                                 ConfigObject.write_timeout,ConfigObject.dsrdtr,\
                                 ConfigObject.inter_byte_timeout)

    def ClosePort(self):
        self.ActivePort.close()
    
    def ReadTime(self):
        if(self.InitialiseCommand('G')):
            TimeString = self.ActivePort.read(6)
            TimeStringInt = []
            for Byte in TimeString:
                TimeStringInt.append(int(Byte))
            return TimeStringInt
        else:
            return []
    def ReadSystemTime(self):
        return TimeUtils.GetCurrentTime()
    
    def WriteTime(self):
        if(self.InitialiseCommand('E')):
            #get the time
            TimeString = TimeUtils.GetCurrentTime();
            #Time String structure [Year, Mont, Day,hour, minue,second]
            #Spam the time
            TimeString = bytes(TimeString)
            #for i in range(0,len(TimeString)):
            self.ActivePort.write(TimeString) #for structure not necessarily required, but it does ensure the output order is clear!
            return True
        
            #no further communication in this exchange, loss rate is low enough that we may assume they don't happen!
        else:
            return False

        
    def ReadDeviceID(self):
        return self.WriteDeviceID(None) #who says we can't use style! takes advantage of the fact that a lower level this is exacatle the same as writing an ID!

    def WriteDeviceID(self, NewID=None): #new ID must be of form 'byte' 'byte' or any other 16bit structure
        if(self.InitialiseCommand('A')):
            DeviceID = self.ActivePort.read(2)
            if(NewID==None):
                self.ActivePort.write(DeviceID) #write back the device ID
            else:
                self.ActivePort.write(NewID) #write back a new ID   
            return DeviceID
        else:
            return bytes(b'')

        
    def ReadDeviceMode(self):
        

        return self.SetDeviceMode(None, None) # returns [DownloadEnabled,ClearEnabled] or [none, none]

    def SetDeviceMode(self,DownloadEnabled,ClearEnabled):
        
        if(self.InitialiseCommand('B')):
           Flags = self.ActivePort.read(1)
           if(DownloadEnabled==None):
               self.ActivePort.write(Flags)
           else:
               
               #WriteFlags = (1&DownloadEnabled) + (2&ClearEnabled)+128
               #A dodgy soluton that is going to have to work for the time being....
               if DownloadEnabled:
                   if ClearEnabled:
                       WriteFlags = 3 #0b0011
                   else:
                       
                       WriteFlags = 1 #0b0001
               else:
                   if ClearEnabled:
                       
                       WriteFlags = 2 #0b0010
                       
                   else:
                       WriteFlags = 0 #0b0000    
               self.ActivePort.write(WriteFlags.to_bytes(1,'big'))
           return [(int(Flags[0])&0b00000001),(int(Flags[0])&0b00000010)]#returns, download flag then clear flag
        else:
            return [None,None]

    def ReadFirmwareVersion(self):
        if(self.InitialiseCommand('C')):
            return self.ActivePort.read(1)
        else:
            return False
            
        
    def ReadHardwareVersion(self):
        if(self.InitialiseCommand('D')):
            return self.ActivePort.read(1)
        else:
            return False

    def InterceptDownloadMessage(self,intercept):
        if self.Verbose:
            print("DEBUG: "+str(intercept))
        if(intercept == bytes('Y','u8')):
            
            return self.InterpretDownloadandWritetoFile()
        else:
            return False

    def InterpretDownloadandWritetoFile(self):
        if self.Verbose:
            print("DEBUG:SerialInterface:InterpretDownloadandWritetoFile: Card Read Begun")
        UIDLine = self.ActivePort.read_until(size=30) #read first data dump line, UID line
        UIDLine = self.ActivePort.read_until(size=30) #read first data dump line, UID line
        UIDLine = UIDLine.decode("utf-8")
        UID = ((UIDLine.split(":")[1]).strip()).split(" ") #WHOOOOOPS - strips out nont UID info and puts byte representations in an array with only byte representations
        UIDValue=0
        for i in range(0,len(UID)):
            UIDValue = (UIDValue*256)+int(('0x'+str(UID[len(UID)-i-1])),16)
        Time = TimeUtils.GetCurrentTime()
        WriteFileFileName = str(Time[0])+"-"+str(Time[1])+"-"+str(Time[2])+"-"+str(Time[3])+"_"+str(UIDValue)+".ODOTSRAW" #name of the file (without directory attached)
        WriteFileName= self.CurrentWorkingDirectory+"\\"+self.FileWritePath+"\\"+WriteFileFileName
        WriteFile=open(WriteFileName,'w')
        WriteFile.write(UIDLine[0:len(UIDLine)-2]+'\n')
        BreakBoolean = True
        i = 0
        while BreakBoolean:
            try:
                SerialInputLine = self.ActivePort.readline()
                #print(SerialInputLine[0])
                #if self.Verbose():
                #    print(str(SerialInputLine))
                if ((SerialInputLine == bytes("Z",'u8')) or(SerialInputLine[0] == 13)):#Reach the end of the download
                    WriteFile.close()
                    if self.Verbose:
                        print("DEBUG:SerialInterface:InterpretDownloadandWritetoFile: Card Read Successfully")
                    BreakBoolean = False
                    break
                elif (i>2):
                    if (self.CheckIfHex(SerialInputLine[0])): # or self.CheckIfHex(SerialInputLine[4])): #read an error (generally because the card was removed too quickly
                        #'''self.CheckIfHex(SerialInputLine[4]) and '''
                        WriteFile.write(SerialInputLine.decode('utf-8')[0:len(SerialInputLine)-2]+'\n')
                    else:
                        WriteFile.close()
                        os.remove(WriteFileName)
                        if self.Verbose:
                            print("DEBUG:SerialInterface:InterpretDownloadandWritetoFile: Card Read Error Detected")
                            print("DEBUG:"+str(SerialInputLine))
                        BreakBoolean = False
                        return False
                        break
                else:
                    WriteFile.write(SerialInputLine.decode('utf-8')[0:len(SerialInputLine)-2]+'\n')
            except:
                if self.Verbose:
                    print("DEBUG:SerialInterface:InterpretDownloadandWritetoFile: Caught Error")
                    print("DEBUG:"+str(SerialInputLine))
                return False
                #print("DEBUG:"+str(SerialInputLine))
        
                
            i=i+1 #iterate file counter (used to detect if an 'error' is actually just the download header...
        #Generate File Name
        ''' UID: PROVIDED|Int
            PICCTYPE: PROVIDED|Code
            BlockNo Block Data
            ...     ...
            ...     ...
            '''
        return WriteFileFileName

    
    def CheckIfHex(self, TestChar):
        # an ugly hex digit checker
        TestChar = chr(TestChar)
        if TestChar[0].isdigit():
            return True
        elif TestChar =='A':
            return True
        elif TestChar =='B':
            return True
        elif TestChar =='C':
            return True
        elif TestChar =='D':
            return True
        elif TestChar =='E':
            return True
        else:
            return False
			
			
    def InitialiseCommand(self, CommandChar):
        #flush the input buffer (arduino has a habit of sending ("INVALID COMMAND RECIEVED")
        self.ActivePort.reset_input_buffer()
        #send a command char and look for the reply (with in built data dump interception
        self.ActivePort.write(bytes(CommandChar,'u8'))
        ReplyByte = self.ActivePort.read(1)
        if(ReplyByte != bytes(CommandChar.lower(),'u8')):
            if(ReplyByte == bytes('>','u8')):
                if self.Verbose:
                    print("DEBUG: SerialInterface: InitialiseCommand: Status Message From PCD: "+str(self.ActivePort.readline()))
            else:
                if not(self.InterceptDownloadMessage(ReplyByte)):
                    if self.Verbose:
                        print('DEBUG: SerialInterface: InitialiseCommand: Odd command reply recieved:'+ReplyByte.hex()+"||"+str(ReplyByte))
                else:
                    if self.Verbose:
                        print("DEBUG: SerialInterface: InitialiseCommand: Download Itercepted")
                    
                
            return False
        else:
            return True

    def NeatenPortList(self, PortList):
        i = 0
        # neaten up device info to make it more readable by a user...
        for Port in PortList:
            if self.LeonardoVIDPID.count([Port[3],Port[4]]):
                PortList[i][3] = "Arduino"
                PortList[i][4] = "Leonardo"
            elif self.UNOVIDPID.count([Port[3],Port[4]]):
                PortList[i][3] = "Arduino"
                PortList[i][4] = "UNO"
            i = i+1
                
        #will add interpretation of PID and VID values
        return PortList
		
		
    def PollInputPortforDownload(self):
        #poll input port and handle downloads
        TestByte=self.ActivePort.read(1)
        try:
			FileName = self.InterceptDownloadMessage(TestByte)
			#self.ActivePort.reset_input_buffer() #good for getting rid of any extras
			return FileName
		except:
			False
if __name__=='__main__':
        
    S=ODOTS_Serial_Interface(Verbose=True)
    print(S.ListAvailablePorts())
    print(S.SelectPort(0))
    S.OpenPort()

    print("-------------------------")
    print(S.ReadTime())
    print("-------------------------")
    while 1:
        a=S.ActivePort.read(1)
        print(str(a))
        S.InterceptDownloadMessage(a)
        #S.ActivePort.reset_input_buffer()
    #print(S.WriteTime())'''
    '''print("-------------------------")
    print(S.ReadTime())
    print("-------------------------")
    print(S.ReadDeviceMode())#''''''
    S.ClosePort()'''

