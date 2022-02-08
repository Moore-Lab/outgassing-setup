import argparse
import os
import serial
import datetime
import time
import pandas as pd

os.environ['PATH']



# This function writes data indefinitely at regular time intervals until the program is exited

def read_pressure(port):
    '''Define a function that gets the current pressure and then writes it to a text file along with a timestamp
    Requires serial object
    '''

    port.write(str.encode("?GA1\r")) # Query the gauge for the current pressure
    current_pressure = port.readlines()
   
    # The gauge returns a value in the form [b' PRESSURE \r'] as the first element of a list,
    # so we need to convert this first element into a string and then make the string mutable by turning into a list
    # and then chopping off the irrelevant parts of the returned pressure and then stitching them together to be printed
    current_pressure = str(current_pressure[0])
    current_pressure = list(current_pressure)
    current_pressure = current_pressure[2:len(current_pressure)-3]
    current_pressure = "".join(current_pressure)
    return current_pressure
    

def h5store(store, df):#, i, **kwargs):
    ## copied from https://stackoverflow.com/questions/29129095/save-additional-attributes-in-pandas-dataframe
    store.append(key='ed/ed', value=df, format='table')
    store.append(key='ed/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')
    #store.get_storer('rga').attrs.metadata = kwargs


# Define arguments to be passed via command line

parser = argparse.ArgumentParser(description="Read out the pressure of the system at given time intervals")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM7') 
parser.add_argument('--file_path',
                    help="File that stores the pressure measurements",
                    type=str,
                    default='./Pressure_{}.h5'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.33)

args = parser.parse_args()


ED = serial.Serial(args.channel_name , baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE, timeout=1) # serial port that will be used for the pressure gauge

# measuring and recording the pressure
ed_table = []

ed_data = True
while ed_data:
    try:
        store = pd.HDFStore(args.file_path) # creating an h5 file to store the data
        pressures = read_pressure(ED) # read the pressure
        print(pressures)
        measure = pd.DataFrame({'Total Pressure': [pressures]}) # storing the pressures in a pandas dataframe
        ed_table.append(measure) # adding a line of new measurements to previous table of data
        h5store(store, measure)
        time.sleep(args.sleep_time)
        store.close()
    except serial.SerialException as e:
        store.close()
        print(e)
        ed_data = False



