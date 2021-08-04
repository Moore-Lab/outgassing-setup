import re
import time
import serial
import datetime
import csv
import threading
import matplotlib.pyplot as plt
import struct
import decimal
import numpy
import os
import matplotlib
import argparse
import binascii


#one possible version of getting temperature
def get_temp(ser, retry=2):
    ##most of this I commandeered from https://github.com/artisan-roaster-scope/artisan/blob/71e271c9ec21376d14680ef390bdd59fcc2ca026/src/artisanlib/comm.py#L1938
    #this is the command that the Amprobe reads to then give the temperatures (I think)
    command = bytes( '#0A0000NA2\r\n', 'ascii')
    r = ''
    if not ser.isOpen():
        ser.open()
        time.sleep(.2)
    if ser.isOpen():
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(command)
        r = ser.read(16)
        if (len(r) == 16) and (int(r[0]) == 62) and (int(r[1]) == 15):
            #converting temperatures from hex
            temp1 = int(r[5]*256 + r[6])/10
            temp2 = int(r[10]*256 + r[11])/10
            return [temp1, temp2]
        else:
            for i in range(4):
                if (len(r) > 12+i) and (int(r[1+i])==62) and (int(r[2+i])==15):
                        temp1 = int(r[5+i]*256 + r[6+i])/10
                        temp2 = int(r[10+i]*256 + r[11+i])/10
                        return [temp1, temp2]
            if retry:
                if retry < 2:
                    if ser.isOpen():
                        ser.close()
                        time.sleep(.2)
                    time.sleep(.05)
                temp1, temp2 = get_temp(retry=retry-1)
                return temp1, temp2
            else:
                nbytes = len(r)
                print('Error: {0} bytes received'.format(nbytes))
                return [-1, -1]
    else:
        return [-1, -1]


#another possible way to get the temperature
#might end up combining the two into one
def get_temp_other(ser, file, retry=10, response_length = 16):
    ## from https://www.home-barista.com/roasting/thermocouple-issues-in-artisan-t41350.html
    command = bytes( '#0A0000NA2\r\n', 'ascii')
    try:
        for i in range(retry):
            ser.write(command)
            data = ser.read(response_length)

            if (ord(data[0]) == 0x3e) and (ord(data[1]) == 0x0f):
                temp1 = ((ord(data[5]) << 8) | ord(data[6]))/10.0
                # << shift left by 5 bits
                temp2 = ((ord(data[10]) << 8) | ord(data[11]))/10.0
                if (i > 1):
                    print('Good data ({}, {}) found after {} retries'.format(temp1, temp2, i))
                    return [temp1, temp2]
                else:
                    print('Bad data found: ')
                    for j in range(16):
                        print('{} {}'.format(ord(data[j]),'02x'))
                    return [-1, -1]
    except serial.SerialException as e:
        print(e)
        return [-1, -1]

# if __name__ == "__main__":

parser = argparse.ArgumentParser(description="Read out the pressure of the system at given time intervals")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM3') 
parser.add_argument('--file_path',
                    help="File that stores the temperature measurements",
                    type=str,
                    default='./Thermoprobe_{}.csv'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.33)
parser.add_argument('--temp',
                    help='TEC set temperature',
                    type=int)

args = parser.parse_args()

    # Set up the Amprobe serial object


tmd = serial.Serial(args.chanel_name, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE, timeout=1, write_timeout=1, inter_byte_timeout=1)




# Define a function that returns the two's complement of a signed hex number as a signed decimal
def signed_int(value):
    # I've got to include this try case because this function is called in the temperature function
    # sometimes the temp function will pass a bunk value for whatever reason and we can't use the int function on it
    # so we need to make an exception if we get a value error
    try:
        # This line checks if the raw int value is over 1000. Because the TEC only gets to 70 celsius, the probe
        # will only ever send a signal corresponding to a high of 700, thus if we are passed a string "ffff"
        # we know it must be a negative value because its raw unsigned conversion is over 60000
        if int(value, 16) > 2000:
            # If we're inside this if statement, it means that the number should be a negative, so we need to take the
            # two's complement
            value = int(value, 16) - (2 ** 16)
        else:
            value = int(value, 16)
    except ValueError:
        value = 0
    return value


while True:
    # This is the command that tells the Amprobe to send back a message that has the temp encoded
    print("before command sent")
    #tmd.reset_input_buffer()
    #tmd.reset_output_buffer()
    TMD56_CMD = str.encode("#0A0000NA2\r\n")
    tmd.write(TMD56_CMD)
    proxytemp = tmd.readlines()
    print("After message is read:")
    print(proxytemp)
    # The message that the Amprobe sends back is a list whose first entry is the message, we want it as a string
    proxytemp = repr(proxytemp[0])
    # Split the string based on the delimiters in the message
    proxytemporary = proxytemp.split('\\x')
    print(proxytemporary)
    # Now that we've split the message, in order to search it for a substring,
    #  we need to convert it back to a string
    proxytemp = "".join(proxytemporary)
    print("After splitting and rejoining:")
    print(proxytemp)
    # Now we search the message for the substring that says "message starts" (\x10) to "message ends" (\x0b)
    print("After search:")
    print(re.findall('10(.+?)0b', proxytemp))
    result = re.findall('10(.+?)0b', proxytemp)
    time.sleep(5)



