'''
    Manages Time Functionality
'''


import time

def ReturnCurrentTimeOnSecondEnd():
    Time = time.gmtime() #Get GMT time from computer
    while(Time.tm_sec == time.gmtime().tm_sec):
        pass
    return time.gmtime()

def GetCurrentTime():
    TimeString=[0x00,0x00,0x00,0x00,0x00,0x00]#Year, Month,Day, Hour , Minute, Second
    TimeStruct = ReturnCurrentTimeOnSecondEnd();
    TimeString = [TimeStruct.tm_year%100,TimeStruct.tm_mon,TimeStruct.tm_mday,TimeStruct.tm_hour,TimeStruct.tm_min,TimeStruct.tm_sec]
    return TimeString

