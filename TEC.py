import serial
import argparse
import datetime
import time
import pandas as pd

## consulted https://github.com/linnarsson-lab/Py_TC-720/blob/master/Py_TC720.py for much of this

#Define a function that generates a hexcode message for set functions
def make_hexcode(val, message):
    #dealing with negative numbers
    if val < 0:
        val = int(0.5 * 2**16 - val)
    #converting number into a hex form that will be put into message
    val_str = '{h:0>4}'.format(h=hex(val)[2:])
    #the next 4 elements represent the value that is given to the TEC
    message[3:7] = val_str[0], val_str[1], val_str[2], val_str[3]
    return message

#Define a function that generates the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
def make_checksum(message):
    byt_message = ''.join(message)
    checksum = hex(sum(byt_message[1:7].encode('ascii'))%256)[-2:]
    message[7:9] = checksum[0], checksum[1]

#Define a function that sends a signal to the TEC
def send_signal(ser, message, sleep_time):
    # Actually send the signal
    for i in message:
        ser.write(str.encode(i))
        time.sleep(sleep_time)
        ser.read_all()

#Define a function that sends a read signal to the TEC        
def read_signal(ser, message, sleep_time):
    for i in message:
        ser.write(str.encode(i))
        time.sleep(sleep_time)
    
    if ser.inWaiting() >= 8:
        val = ser.read_all()
    else:
        time.sleep(sleep_time)
        val = ser.read_all()
    return val

# Define a function that takes a temperature and sends it to the TEC
def set_temp(temp, tec_ser, sleep_time):
    #this is the message that will be passed to the TEC to set the temperature. The second and third elements are the command that tells the TEC
    #that the temperature is being set (1c)
    temp_message = ['*','1','c','0','0','0','0','0','0','\r']
    #for some reason we need to multiply the temperature by 100 before we convert to hex
    temp = int(temp*100)
    make_hexcode(temp, temp_message)
    make_checksum(temp_message)

    # message = ['*','1','c','f','f','6','a','f','7','\r']    ### test message

    send_signal(tec_ser, temp_message, sleep_time)

def get_temp(tec_ser, sleep_time):
    #these are the messages that will be passed to the TEC to get the temperatures
    #the second and third elements are the command that tells the TEC that we want to read the temperatures
    message1 = ['*','0','1','0','0','0','0','0','0','\r']
    #there is no value to set, unlike set_temp so the next 4 elements stay 0

    make_checksum(message1)
    temp1 = read_signal(tec_ser, message1, sleep_time)
    
    #converting the temperature readout to a number
    temp1 = int(temp1[1:5], base=16)

    if temp1 > .5 * (2**16):
        temp1 = -(2**16 - temp1)
    
    return temp1/100

#Define a function that checks if the output is enabled, and if not, turns it on
#if output is defined, then it will set the output percentage, otherwise it wil be at 100%
def set_output(temp, tec_ser, sleep_time):#, output=None):
    #these messages are what the TEC reads to determine information about the output
    #check to see whether or not the power output is on
    #the first two elements after '*' tell the machine that the we want to check if
    #the power output is enabled
    check_message = ['*','6','4','0','0','0','0','0','0','\r']
    
    #there is no value to set, because we are just reading the value so the next 4 elements stay 0
    make_checksum(check_message)
    output_message = read_signal(tec_ser, check_message, sleep_time)

    #converting the output readout to a number
    output_message = int(output_message[1:5], base=16)
    # print('output: {}'.format(output_message))

    #if the output is off, turn it on
    if output_message == 0:
        #the first two entries after '*' are to either turn the output on or off
        #the next entry: '1' tells the TEC to turn on the output
        on_message = ['*','3','0','1','0','0','0','0','0','\r']

        make_checksum(on_message)
        send_signal(tec_ser, on_message, sleep_time)
    
    # #setting the output power
    # #possible output values range from -511 (cooling) to 511 (heating) (-100% to 100%)
    # if output is not None:
    #     #if we want to speficy the output power, we have to set the control to manual
    #     #'3' and 'f' tell the machine that we are changing the control type
    #     #'1' sets the control to manual output
    #     control_message = ['*','3','f','1','0','0','0','0','0','\r']
    #     make_checksum(control_message)
    #     send_signal(tec_ser, control_message, sleep_time)

    #     #setting the output power
    #     # '4' and '0' is the command that tells the TEC to set the output power to a certain percentage
    #     power_message = ['*','4','0','0','0','0','0','0','0','\r']
        
    #     #accounting for the possibility that the sign is not entered in output correctly
    #     output = abs(output)
    #     current_temp = get_temp(tec_ser, sleep_time)
    #     if (temp < current_temp) & (output > 0):
    #         output = -1*output
    #     if output < 0:
    #         output = int(0.5 * 2**16 - output)
    
    #     make_hexcode(output, power_message)
    #     make_checksum(power_message)
    #     send_signal(tec_ser, power_message, sleep_time)

def h5store(store, df):#, i, **kwargs):

    store.append(key='tec/tec', value=df, format='table')
    store.append(key='tec/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')
    #store.get_storer('rga').attrs.metadata = kwargs


parser = argparse.ArgumentParser(description="Set the temperature of the TEC")

parser.add_argument('--channel_name',
                    help='Name of the channel to which the pressure gauge is connected',
                    type=str,
                    default='COM3') 
parser.add_argument('--file_path',
                    help="File that stores the pressure measurements",
                    type=str,
                    default='./TEC_{}.h5'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=.5)
parser.add_argument('--temp',
                    help='TEC set temperature in Celcius',
                    type=int)
parser.add_argument('--output_power',
                    help='Set the output power. Takes values from -511 (-100%) to 511 (100%)',
                    type=int,
                    default=None)

args = parser.parse_args()

# Define the TEC temperature controller's serial settings 
TEC = serial.Serial(args.channel_name, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

#start heating
tec_table = []
set_output(args.temp, TEC, args.sleep_time)#, args.output_power)
set_temp(args.temp, TEC, args.sleep_time)

tec_data = True
while tec_data:
    try:
        store = pd.HDFStore(args.file_path)
        #read the current temperature as the tec heats up
        temps = get_temp(TEC, args.sleep_time)
        print(temps)
        measure = pd.DataFrame({'Set Temp': [args.temp], 'Current Temp': [temps]})
        tec_table.append(measure)
        h5store(store, measure)
        time.sleep(.33)
        store.close()
    except serial.SerialException as e:
        store.close()
        print(e)
        tmd_data = False


#store = pd.HDFStore(args.file_path)
#temperatures = pd.DataFrame({'Set temperature': args.temp, 'Current temperature': temps})
#h5store(store, temperatures, 'test')

#store.close()