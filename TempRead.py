import serial
import argparse
import datetime
import logging
import pymodbus
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import pandas as pd
import time 


## https://pymodbus.readthedocs.io/en/latest/source/example/synchronous_client.html

# # gives info about howthe omega is responding
# FORMAT = ('%(asctime)-15s %(threadName)-15s '
#           '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)

UNIT= 1

def read_temp(om_ser):
    ''' Connecting to the Omega device to read the temperature from the two thermoprobes
    Requires serial port name (default 'COM8')
    '''

    client = ModbusClient(method='rtu', port=om_ser, stopbits=2, parity='N', baudrate=57600, bytesize=8) # connecting to the Omega device through serial interface
    client.connect()
    print("socket:")
    print(client.is_socket_open())

    temp = client.read_input_registers(0x1000,12,unit=UNIT) # reading the temperatures: 0x1000 hex code for the temperatures
    temp_list = temp.registers
    client.close()

    temps = [temp_list[0]/10, temp_list[2]/10] # converting temperatures into C and getting rid of extraneous values (we only need elements 0 and 2)
    return temps

def h5store(store, df):
    
    store.append(key='omega/omega', value=df, format='table')
    store.append(key='omega/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')


# Define arguments to be passed via command line

parser = argparse.ArgumentParser(description="Read the current temperatures from the thermoprobes")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM8') 
parser.add_argument('--file_path',
                    help="File that stores the pressure measurements",
                    type=str,
                    default='./Temps_{}.h5'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.5)

args = parser.parse_args()

# measuring and recording the temperatures
om_table = []

om_data = True
while om_data:
    try:
        store = pd.HDFStore(args.file_path) # creating an h5 file to store the data
        temperatures = read_temp(args.channel_name) # read the temperatures from the thermocouples
        print(temperatures)
        measure = pd.DataFrame({'Temp 1': [temperatures[0]], 'Temp 2': [temperatures[1]]}) # storing temperatures in a pandas dataframe
        om_table.append(measure) # adding a line of new measurements to previous table of data
        h5store(store, measure) 
        time.sleep(args.sleep_time)
        store.close()
    # if something is wrong with the connection just try to reconnect again by doing another iteration
    except pymodbus.exceptions.ConnectionException as ce:
        print('Bad connection. Trying to connect to Modbus client again')
        continue
    except serial.SerialException as se:
        store.close()
        print(se)
        tmd_data = False


read_temp(args.channel_name)