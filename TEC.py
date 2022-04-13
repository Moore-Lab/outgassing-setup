import serial
import argparse
import datetime
import time
import pandas as pd

## consulted https://github.com/linnarsson-lab/Py_TC-720/blob/master/Py_TC720.py for much of this

def make_hexcode(val, message):
    '''Generates a hexcode message for set functions to talk with the TEC
    Requires the value being sent to the TEC and message format: ['*','x','x','0','0','0','0','0','0','\r']
    '''

    #dealing with negative numbers
    if val < 0:
        val = int(0.5 * 2**16 - val)
    val_str = '{h:0>4}'.format(h=hex(val)[2:]) # converting number into a hex form that will be put into message
    message[3:7] = val_str[0], val_str[1], val_str[2], val_str[3] # the 4 elements after the third element represent the value that is given to the TEC
    return message

def make_checksum(message):
    '''Generates the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
    '''

    byt_message = ''.join(message)
    checksum = hex(sum(byt_message[1:7].encode('ascii'))%256)[-2:]
    message[7:9] = checksum[0], checksum[1]

def send_signal(ser, message, sleep_time):
    ''' Sends a signal to the TEC
    Requires serial obect, full message, and time between sending message elements (default 0.5s)
    '''

    for i in message:
        ser.write(str.encode(i))
        time.sleep(sleep_time)
        ser.read_all()
      
def read_signal(ser, message, sleep_time):
    '''Sends a signal to the TEC to read a value from it
    Requires serial obect, full message, and time between sending message elements (default 0.5s)
    '''

    for i in message:
        ser.write(str.encode(i))
        time.sleep(sleep_time)
    
    if ser.inWaiting() >= 8:
        val = ser.read_all()
    else:
        time.sleep(sleep_time)
        val = ser.read_all()
    return val

def set_temp(temp, tec_ser, sleep_time):
    ''' Takes a temperature and sends it to the TEC
    Starts with a message that will be passed to the TEC to set the temperature.
    Requires set temperature, serial object, and time between sending message elements (default 0.5s)
    '''

    temp_message = ['*','1','c','0','0','0','0','0','0','\r'] # The second and third elements are the command that tells the TEC that the temperature is being set (1c)
    temp = int(temp*100) # need to multiply the temperature by 100 before we convert to hex
    make_hexcode(temp, temp_message) # conerting the temperature into a hexcode
    make_checksum(temp_message) # making the checksum that goes at the end of the message
    send_signal(tec_ser, temp_message, sleep_time) # sending a signal to set the temperature of the TEC

def get_temp(tec_ser, sleep_time):
    '''Reading the current temperature that the TEC is set to
    Starts with a message that will be passed to the TEC to get the temperatures
    Requires serial object and time between sending message elements (default 0.5s)
    '''

    message1 = ['*','0','6','0','0','0','0','0','0','\r'] # the second and third elements are the command that tells the TEC that we want to read the temperatures
                                                          # there is no value to set, unlike set_temp so the next 4 elements stay 0
    make_checksum(message1) # making the checksum that goes at the end of the message
    temp1 = read_signal(tec_ser, message1, sleep_time)
    temp1 = int(temp1[1:5], base=16) # converting the temperature readout to a number

    if temp1 > .5 * (2**16):
        temp1 = -(2**16 - temp1)
    
    return temp1/100

def set_output(tec_ser, sleep_time):#, output=None):
    '''Checks if the output is enabled, and if not, turns it on
    If output is defined, then it will set the output percentage, otherwise it will keep the standard power output
    Starts with a message that the TEC reads to determine information about the output
    and ensures the power output is on
    Requires serial object and time between sending message elements (default 0.5s)
    '''

    check_message = ['*','6','4','0','0','0','0','0','0','\r'] # the first two elements after '*' tell the machine that the we want to check if the power output is enabled
    # there is no value to set, because we are just reading the value so the next 4 elements stay 0
    make_checksum(check_message) # making the checksum that goes at the end of the message
    output_message = read_signal(tec_ser, check_message, sleep_time).decode('UTF-8') # reads the status of the output
    output_message = int(output_message[1]) # converting the output readout to a number

    # if the output is off, turn it on
    if output_message == 0:
        on_message = ['*','3','0','1','0','0','0','0','0','\r'] # the first two entries after '*' are to either turn the output on or off, the next entry: '1' tells the TEC to turn on the output
        make_checksum(on_message) # making the checksum that goes at the end of the message
        send_signal(tec_ser, on_message, sleep_time) # sending the signal the the TEC telling it to turn on the power output

    
    # #setting the output power (does not work yet, but saving the code in case we need to change the output power percentage)
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

def turn_off_output(tec_ser, sleep_time):
    '''Turns off the output on the tec'''

    check_message = ['*','6','4','0','0','0','0','0','0','\r'] # the first two elements after '*' tell the machine that the we want to check if the power output is enabled
    # there is no value to set, because we are just reading the value so the next 4 elements stay 0
    make_checksum(check_message) # making the checksum that goes at the end of the message
    output_message = read_signal(tec_ser, check_message, sleep_time).decode('UTF-8') # reads the status of the output
    output_message = int(output_message[1]) # converting the output readout to a number

    # if output is on, turn it off
    if output_message == 1:
        off_message = ['*','3','0','0','0','0','0','0','0','\r'] # the first two entries after '*' are to either turn the output on or off, the next entry: '0' tells the TEC to turn off the output
        make_checksum(off_message) # making the checksum that goes at the end of the message
        send_signal(tec_ser, off_message, sleep_time) # sending the signal the the TEC telling it to turn off the power output

def h5store(store, df):

    store.append(key='tec/tec', value=df, format='table')
    store.append(key='tec/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')

def run_tec(tec, temp, sleep_time):
    '''Initializing TEC and setting heater temperature'''
    # initializing TEC
    TEC = serial.Serial(tec, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) # TEC temperature controller's serial settings 
    print('Opening connection to TEC')
    # TEC.close()
    # TEC.open()
    # print(TEC.is_open)

    # setting temperture
    set_output(TEC, sleep_time)#, args.output_power)
    print('Sending output signal')
    set_temp(temp, TEC, sleep_time) # set the temperature to value inputted in the command line
    print('Sending temperature signal')
    print(TEC.is_open)

    return TEC

if __name__ == '__main__':
    # Define arguments to be passed via command line

    parser = argparse.ArgumentParser(description="Set the temperature of the TEC")

    parser.add_argument('--channel_name',
                        help='Name of the channel to which the tec is connected',
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


    # start heating

    TEC = run_tec(args.channel_name, args.temp, args.sleep_time)

    tec_data = True
    while tec_data:
        try:
            store = pd.HDFStore(args.file_path) # creating an h5 file to store the data
            temps = get_temp(TEC, args.sleep_time)  # read the current temperature as the tec heats up
            print(temps)
            measure = pd.DataFrame({'Set Temp': [args.temp]}) # storing the temperatures in a pandas dataframe
            h5store(store, measure)
            time.sleep(1)
            store.close()
        except serial.SerialException as e:
            store.close()
            print(e)
            tmd_data = False
