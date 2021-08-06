import sys
import argparse
import os
os.environ['PATH']
import serial
import datetime
import csv
import time
import threading
from numpy import genfromtxt
import numpy as np


# Define a function that gets the current pressure and then writes it to a text file along with a timestamp
# This function writes data indefinitely at regular time intervals until the program is exited

def pressure(port, sleeptime, file):
    while True:
        # Query the gauge for the current pressure
        port.write(str.encode("?GA1\r"))
        # Save the response along with a timestamp to a text file
        f = open(file, 'a+')
        nower = datetime.datetime.now()
        timestamp = nower.strftime("%m-%d %H:%M:%S")
        writer = csv.writer(f, lineterminator='\n')
        current_pressure = port.readlines()
        """
        The gauge returns a value in the form [b' PRESSURE \r'] as the first element of a list,
        so we need to convert this first element into a string and then make the string mutable by turning into a list
        and then chopping off the irrelevant parts of the returned pressure and then stitching them together to be printed
        """
        current_pressure = str(current_pressure[0])
        current_pressure = list(current_pressure)
        current_pressure = current_pressure[2:len(current_pressure)-3]
        current_pressure = "".join(current_pressure)
        print(current_pressure)
        # Put the time elapsed since start (in sec), timestamp, and current pressure on a row in a csv file
        row = [timestamp, current_pressure]
        writer.writerow(row)
        f.close()
        time.sleep(sleeptime)


# Define arguments to be passed via command line

#if __name__ == "__main__":

parser = argparse.ArgumentParser(description="Read out the pressure of the system at given time intervals")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM12') 
parser.add_argument('--file_path',
                    help="File that stores the pressure measurements",
                    type=str,
                    default='./Pressure_{}.csv'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.33)

args = parser.parse_args()


# Define the serial port that will be used for the pressure gauge
ed = serial.Serial(args.channel_name , baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE, timeout=1)


# Measure the pressure by executing the pressure function
thread_pressure = threading.Thread(target=pressure, args=(ed, args.sleep_time, args.file_path))
thread_pressure.start()


#hello
