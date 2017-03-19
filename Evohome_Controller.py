# Evohome Controller v0.1
# Author: Evsdd (2017)
# Python 2.7.11
# Requires pyserial module which can be installed using 'python -m pip install pyserial'
# Prototype program to bind and sync with a single Evohome device (HR92).
# TO DO: add simple setpoint control
# TO DO: add scheduled SYNC message from controller

from __future__ import print_function
import serial                     # import the module

output_log = open("e:\\Python\\Evohome_Controller.log", "w")

ComPort = serial.Serial('COM8')   # open port COM8
ComPort.baudrate = 250000         # set Baud rate to 250000
ComPort.bytesize = 8              # Number of data bits = 8
ComPort.parity   = 'N'            # No parity
ComPort.stopbits = 1              # Number of Stop bits = 1
ComPort.timeout = 1               # Read timeout = 1sec

ControllerID = 0x55555            # Set this to any value as long as ControllerTYPE=1

Com_BIND = 0x1FC9                 # Evohome Command BIND
Com_SYNC = 0x1F09                 # Evohome Command SYNC
Com_TEMP = 0x30C9                 # Evohome Command ZONE_TEMP

# Create controller values required for message structure
ControllerTYPE = (ControllerID & 0xFC0000) >> 18;
ControllerADDR = ControllerID & 0x03FFFF;
ControllerTXT = bytearray(b'%02d:%06d' %(ControllerTYPE, ControllerADDR))

print('ControllerID=0x%06X (%s)' % (ControllerID, ControllerTXT))

while True:
 data = ComPort.readline()        # Wait and read data

 msg_type = data[4:6]             # Extract message type
 dev1 = data[11:20]               # Extract deviceID 1
 dev2 = data[21:30]               # Extract deviceID 2
 dev3 = data[41:45]               # Extract deviceID 3
 cmnd = data[41:45]               # Extract command 

 print(data)                      # print the received data

 if ((msg_type == ' I') and (dev1 != ControllerTXT) and (cmnd == '%04X' % Com_BIND)):  # Received BIND message
  send_data = bytearray(b'I --- %s --:------ %s %04X 018 012309%06X0130C9%06X011FC9%06X\r\n' % (ControllerTXT, ControllerTXT, Com_BIND, ControllerID, ControllerID, ControllerID))
  print('Send:(%s)' % send_data)
  No = ComPort.write(send_data)                
 else:
   if ((msg_type == 'RQ') and (cmnd == '%04X' % Com_SYNC)): # Received SYNC request
     send_data = bytearray(b'RP --- %s %s --:------ %04X 003 FF0BB8\r\n' % (ControllerTXT, dev1, Com_SYNC)) # 5min SYNC 0x0BB8 = 3000 (300.0sec)
     print('Send:(%s)' % send_data)
     No = ComPort.write(send_data)

ComPort.close()                   # Close the COM Port
file.close(output_log)



