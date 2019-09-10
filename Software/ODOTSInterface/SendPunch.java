/*
  Copyright 2014 Melin Software HB
  
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
  
      http://www.apache.org/licenses/LICENSE-2.0
  
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

import java.io.*;
import java.net.Socket;
import java.util.*;

public class SendPunch {
  enum SpecialPunch {
    PunchStart(1),
    PunchFinish(2),
    PunchCheck(3);
                 
    private final short code;
    private SpecialPunch(int code) {
      this.code = (short)code;
    }
  }
  
  public static class SIPunch {
    static final byte Punch = 0;
    static final byte Card = 64;
    
    byte type = Punch;
    /** 2 byte 0-65K or the code of a SpecialPunch*/
    short codeNumber;
    /** 4 byte integer  -2GB until +2GB*/
    int SICardNo; 
    /** Obsolete, not used anymore. */
    final int codeDay = 0;
    /** Time tenths of seconds after 00:00:00 */
    int codeTime;  
    
    final byte[] serialize() {
      ByteArrayOutputStream bs = new ByteArrayOutputStream(15);
      DataOutputStream oos = null;
      try {       
        oos = new DataOutputStream(bs);
        serialize(oos);     
      } catch (IOException e) {
        return null;
      }
      return bs.toByteArray();
    }
    
    void serialize(DataOutputStream out) throws IOException { 
      out.writeByte(type);
      out.writeShort(Short.reverseBytes(codeNumber));
      out.writeInt(Integer.reverseBytes(SICardNo));
      out.writeInt(Integer.reverseBytes(codeDay));
      out.writeInt(Integer.reverseBytes(codeTime));
    }
  }
  
  public static class CardPunch {   
    int codeNumber; // SI code number
    int codeTime; // Time tenth of seconds after 00:00:00
    void serialize(DataOutputStream out) throws IOException {
      out.writeInt(Integer.reverseBytes(codeNumber));
      out.writeInt(Integer.reverseBytes(codeTime));
    }
  }
  
  public static class SICard extends SIPunch {
    ArrayList<CardPunch> punches = new ArrayList<>();
    SICard() {
      type = Card;
      codeTime = 0;
    }
    
    void addPunch(int code, int time) {
      CardPunch cp = new CardPunch();
      cp.codeNumber = code;
      cp.codeTime = time;
      punches.add(cp);
      codeNumber = (short) punches.size();
    }
    
    void serialize(DataOutputStream out) throws IOException { 
      super.serialize(out);
      for(CardPunch p : punches) {
        p.serialize(out);
      }
    }
  }
  
  public static void main(String[] args) throws Throwable {
	String Switch = args[0];
	Integer NumberPunches = Integer.parseInt(args[1]);
	
	Integer CardID = Integer.parseInt(args[2]);
	
	String[] PunchIDString = args[3].split(",");
	String[] PunchTimeString = args[4].split(",");
	
    
    SIPunch punch = null;
    
    if (Switch.equalsIgnoreCase("P")) {
      punch = new SIPunch();
      //Set Control ID
      punch.codeNumber = Short.parseShort(PunchIDString[0]);
      
      //Set CardID
      punch.SICardNo = CardID;
      
      //Set Control TImeStamp
      punch.codeTime = readTime(PunchTimeString[0]);
    }
    else {
      SICard card = new SICard();
      punch = card;
      //System.out.print("Card, enter card number:");
      punch.SICardNo = CardID;
      
      int time;
      //System.out.print("Enter start time (HH:MM:SS):");
      time = readTime(PunchTimeString[0]);
      if (time > 0)
        card.addPunch(SpecialPunch.PunchStart.code, time);
      
      int code = 1;
      int Iterator = 0;
      while (Iterator < (NumberPunches-1)) 
      {
    	//Add control code
        String codeS = PunchIDString[Iterator];
        
		code = Integer.parseInt(codeS);
		//Add time
		time = readTime(PunchTimeString[Iterator]);
		card.addPunch(code, time);
        Iterator ++;
        
      }
      //ReadFinalPunchTime
      time = readTime(PunchTimeString[(Iterator)]);
      if (time > 0)
        card.addPunch(SpecialPunch.PunchFinish.code, time);
    }

    Socket socket = new Socket("localhost", 10000);
    OutputStream socketOutputStream = socket.getOutputStream();
    
    byte[] buffer = punch.serialize();
    for(int i=0; i<buffer.length;i++)
    {
    	int Temp =buffer[i];
    	if(Temp <0)
    		Temp = Temp+255;
    	System.out.print(Temp +" ");
    }
    socketOutputStream.write(buffer, 0, buffer.length);
    socketOutputStream.close();
    socket.close();
  }

  private static int readTime(String TimeString) throws IOException {
    String[] hms = TimeString.split(":");
    int time = 0;
    for (String p:hms)
       time = 60 * time + Integer.parseInt(p);
    return time * 10;
  }
}
