# Evohome Controller v0.3
# Copyright (c) 2017 Evsdd 
# Python 2.7.11
# Requires pyserial module which can be installed using 'python -m pip install pyserial'
# Prototype program to provide controller functionality for Evohome HR92 devices
# 
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
import serial                     # import the modules
import time

output_log = open("e:\\Python\\Evohome_Controller.log", "w")

ComPort = serial.Serial('COM8')   # open port COM8
ComPort.baudrate = 76800          # set Baud rate to 250000
ComPort.bytesize = 8              # Number of data bits = 8
ComPort.parity   = 'N'            # No parity
ComPort.stopbits = 1              # Number of Stop bits = 1
ComPort.timeout = 1               # Read timeout = 1sec

# Set-up Controller and Zone information
ControllerID = 0x55555            # Set this to any value as long as ControllerTYPE=1

# Zone definition: deviceID placeholder (TYPE:ADRR), name, placeholder for name (Hex string), setpoint, placeholder for setpoint (Hex string), placeholder for temp (Hex string)
Zone_INFO = [
             ['','Zone1','','8.5','',''],
             ['','Zone2','','11.3','','']
             ]                    

Zone_num = 2                      # Number of zones 

Device_count = 0                  # Count of devices successfully bound

Sync_dur = 300                    # Time interval between periodic SYNC messages (sec)
SyncTXT = '{0:04X}'.format(Sync_dur * 10)
Sync_time = 0

Com_BIND = 0x1FC9                 # Evohome Command BIND
Com_SYNC = 0x1F09                 # Evohome Command SYNC
Com_NAME = 0x0004                 # Evohome Command ZONE_NAME
Com_SETP = 0x2309                 # Evohome Command ZONE_SETPOINT
Com_TEMP = 0x30C9                 # Evohome Command ZONE_TEMP
Com_UNK = 0x0100                  # Evohome Command ZONE_UNK (unknown)

# Create controller values required for message structure
ControllerTYPE = (ControllerID & 0xFC0000) >> 18;
ControllerADDR = ControllerID & 0x03FFFF;
ControllerTXT = bytearray(b'%02d:%06d' %(ControllerTYPE, ControllerADDR))

# Populate zone name Hex strings
for i in xrange(0,Zone_num):
   Hex_name = ''.join('{0:02X}'.format(ord(c)) for c in Zone_INFO[i][1])
   Hex_pad = ''.join('00' for j in xrange(len(Zone_INFO[i][1]),20))            
   Zone_INFO[i][2] = Hex_name + Hex_pad

# Populate setpoint Hex strings
for i in xrange(0,Zone_num):
   Hex_name = '{0:04X}'.format(int(float(Zone_INFO[i][3]) * 100))         
   Zone_INFO[i][4] = Hex_name
   print('Zone %d:(%s):(%s):(%s:0x%s)' % (i+1,Zone_INFO[i][0],Zone_INFO[i][1],Zone_INFO[i][3],Zone_INFO[i][4]))

print('ControllerID=0x%06X (%s)' % (ControllerID, ControllerTXT))
##### End of setup 

##### Main message processing loop (infinite)
while True:
 if ((time.time() - Sync_time) <  Sync_dur):
 
  data = ComPort.readline()        # Wait and read data

  if data:                         # Only proceed if line read before timeout 

      msg_type = data[4:6]             # Extract message type
      dev1 = data[11:20]               # Extract deviceID 1
      dev2 = data[21:30]               # Extract deviceID 2
      dev3 = data[31:40]               # Extract deviceID 3
      cmnd = data[41:45]               # Extract command 

      print(data)                      # print the received data

      ##### Check if device has already been defined
      i = 0
      while (i < Device_count and Zone_INFO[i][0] != dev1):
        i += 1
       
      ##### Received BIND message
      if ((msg_type == ' I') and (dev1 != ControllerTXT) and (cmnd == '%04X' % Com_BIND)):  
      
       send_data = bytearray(b'I --- %s --:------ %s %04X 018 %02d2309%06X%02d30C9%06X%02d1FC9%06X\r\n' % (ControllerTXT, ControllerTXT, Com_BIND, i, ControllerID, i, ControllerID, i,ControllerID))
       print('Send:(%s)' % send_data)
       No = ComPort.write(send_data)
       if (Zone_INFO[i][0] != dev1):  # New Device
         Zone_INFO[i][0] = dev1
         # TO DO: wait and check for confirmation of successful binding - W BIND message from device
         print('Binding complete for Zone %d:(%s):(%s)' % (Device_count+1,Zone_INFO[Device_count][0],Zone_INFO[Device_count][1]))
         Device_count += 1
       for j in xrange(0,Device_count):
         print('Zone_INFO:%d:(%s):(%s):(%s)' % (j+1,Zone_INFO[j][0],Zone_INFO[j][1],Zone_INFO[j][4]))
      else:
        if (Device_count > 0 and i < Device_count and Zone_INFO[i][0] == dev1):          # Only process messages further if message is from a device defined in Zone_INFO
            
        ##### Received BIND confirmation, respond with ZONE_NAME, SYNC and ZONE_SETPOINT
         if ((msg_type == ' W') and (cmnd == '%04X' % Com_BIND)):
           send_data = bytearray(b'I --- %s --:------ %s %04X 022 %02d00%s\r\n' % (ControllerTXT, ControllerTXT, Com_NAME, i, Zone_INFO[i][2])) 
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
           send_data = bytearray(b'W --- %s --:------ %s %04X 003 FF0BB8\r\n' % (ControllerTXT, ControllerTXT, Com_SYNC)) # 5min SYNC 0x0BB8 = 3000 (300.0sec)
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
           send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4])) 
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
         else:
          ##### Received SYNC request, respond with SYNC, ZONE_SETPOINT and ZONE_TEMP
          if ((msg_type == 'RQ') and (cmnd == '%04X' % Com_SYNC)): 
           send_data = bytearray(b'RP --- %s %s --:------ %04X 003 FF0BB8\r\n' % (ControllerTXT, dev1, Com_SYNC)) # 5min SYNC 0x0BB8 = 3000 (300.0sec)
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
           send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4])) 
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
           send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_TEMP, i, Zone_INFO[i][5])) 
           print('Send:(%s)' % send_data)
           No = ComPort.write(send_data)
          else:

           ##### Received NAME request
           if ((msg_type == 'RQ') and (cmnd == '%04X' % Com_NAME)):      
            send_data = bytearray(b'RP --- %s %s --:------ %04X 022 %02d00%s\r\n' % (ControllerTXT, dev1, Com_NAME, i, Zone_INFO[i][2])) 
            print('Send:(%s)' % send_data)
            No = ComPort.write(send_data)
           else:

            ##### Received TEMP message, send echo response from controller
            if ((msg_type == ' I') and (cmnd == '%04X' % Com_TEMP)):
             Zone_INFO[i][5] = data[52:56]  # store TEMP in Zone_INFO
             send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_TEMP, i, Zone_INFO[i][5])) 
             print('Send:(%s)' % send_data)
             No = ComPort.write(send_data)
            else: 

             ##### Received SETP message, send echo response from controller
             if ((msg_type == ' I') and (cmnd == '%04X' % Com_SETP)): 
              send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4])) 
              print('Send:(%s)' % send_data)
              No = ComPort.write(send_data)
             else:

              ##### Received UNK request
              if ((msg_type == 'RQ') and (cmnd == '%04X' % Com_UNK)): 
               send_data = bytearray(b'RP --- %s %s --:------ %04X %s\r\n' % (ControllerTXT, dev1, Com_UNK, data[46:60])) 
               print('Send:(%s)' % send_data)
               No = ComPort.write(send_data) 

 else:
  if (Device_count > 0):
   ##### Send periodic SYNC message followed by ZONE_SETPOINT and ZONE_TEMP for all zones
       Sync_time = time.time()
       send_data = bytearray(b'I --- %s --:------ %s %04X 003 FF%s\r\n' % (ControllerTXT, ControllerTXT, Com_SYNC, SyncTXT)) 
       print('Send:(%s)' % send_data)
       No = ComPort.write(send_data)
       SendTXT = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][4]) for j in xrange(0, Device_count))
       Send_len = len(SendTXT) / 2
       send_data = bytearray(b'I --- %s --:------ %s %04X %03d %s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, Send_len, SendTXT))
       print('Send:(%s)' % send_data)
       No = ComPort.write(send_data)
       SendTXT = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][5]) for j in xrange(0, Device_count))
       send_data = bytearray(b'I --- %s --:------ %s %04X %03d %s\r\n' % (ControllerTXT, ControllerTXT, Com_TEMP, Send_len, SendTXT)) 
       print('Send:(%s)' % send_data)
       No = ComPort.write(send_data)
       
# TODO: This section is redundant at the moment
ComPort.close()                   # Close the COM Port (
file.close(output_log)



