import time
import serial
import datetime
import argparse
import pandas as pd


#one possible version of getting temperature
def get_temp(ser, retry=2):
    ##most of this I commandeered from https://github.com/artisan-roaster-scope/artisan/blob/71e271c9ec21376d14680ef390bdd59fcc2ca026/src/artisanlib/comm.py#L1938
    #this is the command that the Amprobe reads to then give the temperatures
    command = bytes( '#0A0000NA2\r\n', 'ascii')
    r = ''
    if not ser.isOpen():
        ser.open()
        time.sleep(.5)
    if ser.isOpen():
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(.5)
        ser.write(command)
        time.sleep(.5)
        r = ser.readline()
        #r = ser.read(16)
        ser.close()
        time.sleep(.5)
        if (len(r) == 16) and (int(r[0]) == 62) and (int(r[1]) == 15):
            # print(r)
            #converting temperatures from hex
            temp1 = int(r[5]*256 + r[6])/10
            temp2 = int(r[10]*256 + r[11])/10
            return [temp1, temp2]
        else:
            print('missing bits: ' + str(r))
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
                    time.sleep(args.sleep_time)
                temp1, temp2 = get_temp(ser, retry=retry-1)
                return temp1, temp2
            else:
                nbytes = len(r)
                print('Error: {0} bytes received'.format(nbytes))
                return [-1, -1]
    else:
        return [-1, -1]

def h5store(store, df):#, i, **kwargs):
    store.append(key='tmd/tmd', value=df, format='table')
    store.append(key='tmd/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')
    #store.get_storer('rga').attrs.metadata = kwargs


# #another possible way to get the temperature
# #might end up combining the two into one
# def get_temp_other(ser, file, retry=10, response_length = 16):
#     ## from https://www.home-barista.com/roasting/thermocouple-issues-in-artisan-t41350.html
#     command = bytes( '#0A0000NA2\r\n', 'ascii')
#     try:
#         for i in range(retry):
#             ser.write(command)
#             data = ser.read(response_length)

#             if (ord(data[0]) == 0x3e) and (ord(data[1]) == 0x0f):
#                 temp1 = ((ord(data[5]) << 8) | ord(data[6]))/10.0
#                 # << shift left by 5 bits
#                 temp2 = ((ord(data[10]) << 8) | ord(data[11]))/10.0
#                 if (i > 1):
#                     print('Good data ({}, {}) found after {} retries'.format(temp1, temp2, i))
#                     return [temp1, temp2]
#                 else:
#                     print('Bad data found: ')
#                     for j in range(16):
#                         print('{} {}'.format(ord(data[j]),'02x'))
#                     return [-1, -1]
#     except serial.SerialException as e:
#         print(e)
#         return [-1, -1]


parser = argparse.ArgumentParser(description="Read out the pressure of the system at given time intervals")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM5') 
parser.add_argument('--file_path',
                    help="File that stores the temperature measurements",
                    type=str,
                    default='./Thermoprobe_{}.h5'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.33)

args = parser.parse_args()

# Set up the Amprobe serial object
TMD = serial.Serial(args.channel_name, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE, timeout=1, write_timeout=1, inter_byte_timeout=1)

#starting measurements
tmd_table = []

tmd_data = True
while tmd_data:
    try:
        store = pd.HDFStore(args.file_path)
        #read the temperatures from the thermocouples
        temperatures = get_temp(TMD)
        print(temperatures)
        measure = pd.DataFrame({'Temp 1': [temperatures[0]], 'Temp 2': [temperatures[1]]})
        tmd_table.append(measure)
        h5store(store, measure)
        time.sleep(args.sleep_time)
        store.close()
    except serial.SerialException as e:
        store.close()
        print(e)
        tmd_data = False
