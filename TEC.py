import serial
import argparse
import datetime
import time
import pandas as pd

# Define a function that takes a temperature and sends it to the TEC
def set_temp(temp, tec_ser, sleep_time):
    ## consulted https://github.com/linnarsson-lab/Py_TC-720/blob/master/Py_TC720.py for much of this
    #this is the message that will be passed to the TEC to set the temperature. The second and third elements are the command that tells the TEC
    #that the temperature is being set (1c)
    message = ['*','1','c','0','0','0','0','0','0','\r']
    #for some reason we need to multiply the temperature by 100 before we convert to hex
    temp = int(temp*100)
    if temp < 0:
        temp = int(0.5 * 2**16 - temp)
    #converting the temperature into a hex form that will be put into message
    temp_str = '{h:0>4}'.format(h=hex(temp)[2:])
    #the next 4 elements represent the temperature that is given to the TEC
    message[3:7] = temp_str[0], temp_str[1], temp_str[2], temp_str[3]
    
    # generate the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
    byt_message = ''.join(message)
    checksum = hex(sum(byt_message[1:7].encode('ascii'))%256)[-2:]
    message[7:9] = checksum[0], checksum[1]
    print(message)

    # message = ['*','1','c','f','f','6','a','f','7','\r']    ### test message

    # Actually send the signal
    for i in message:
        tec_ser.write(str.encode(i))
        time.sleep(sleep_time)
        tec_ser.read_all()

def get_temp(tec_ser, sleep_time):
    ## consulted https://github.com/linnarsson-lab/Py_TC-720/blob/master/Py_TC720.py for much of this
    #these are the messages that will be passed to the TEC to get the temperatures
    #the second and third elements are the command that tells the TEC that we want to read the temperatures
    message1 = ['*','0','1','0','0','0','0','0','0','\r']
    #there is no value to set, unlike set_temp so the next 4 elements stay 0
    #generate the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
    byt_message1 = ''.join(message1)
    checksum1 = hex(sum(byt_message1[1:7].encode('ascii'))%256)[-2:]
    message1[7:9] = checksum1[0], checksum1[1]
    print(message1)

    # Actually send the signal
    for i in message1:
        tec_ser.write(str.encode(i))
        time.sleep(sleep_time)
    
    if tec_ser.inWaiting() >= 8:
        temp1 = tec_ser.read_all()
    else:
        time.sleep(sleep_time)
        temp1 = tec_ser.read_all()

    #converting the temperature readout to a number
    temp1 = int(temp1[1:5], base=16)

    if temp1 > .5 * (2**16):
        temp1 = -(2**16 - temp1)
    
    return temp1/100

#Define a function that checks if the output is enabled, and if not, turns it on
#if output is defined, then it will set the output percentage, otherwise it wil be at 100%
def set_output(temp, tec_ser, sleep_time, output=None):
    #these messages are what the TEC reads to determine information about the output
    #check to see whether or not the power output is on
    #the first two elements after '*' tell the machine that the we want to check if
    #the power output is enabled
    check_message = ['*','6','4','0','0','0','0','0','0','\r']
    
    #there is no value to set, because we are just reading the value so the next 4 elements stay 0
    #generate the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
    byt_check_message = ''.join(check_message)
    read_checksum = hex(sum(byt_check_message[1:7].encode('ascii'))%256)[-2:]
    check_message[7:9] = read_checksum[0], read_checksum[1]
    print(check_message)

    # # Actually send the signal
    for i in check_message:
        tec_ser.write(str.encode(i))
        time.sleep(sleep_time)
    
    if tec_ser.inWaiting() >= 8:
        output_message = tec_ser.read_all()
    else:
        time.sleep(sleep_time)
        output_message = tec_ser.read_all()

    #converting the output readout to a number
    output_message = int(output_message[1:5], base=16)
    print('output: {}'.format(output_message))

    #if the output is off, turn it on
    if output_message == 0:
        #the first two entries after '*' are to either turn the output on or off
        #the next entry: '1' tells the TEC to turn on the output
        output_message = ['*','3','0','1','0','0','0','0','0','\r']

        # generate the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
        byt_message = ''.join(output_message)
        checksum = hex(sum(byt_message[1:7].encode('ascii'))%256)[-2:]
        output_message[7:9] = checksum[0], checksum[1]
        print(output_message)

        # Actually send the signal
        for i in output_message:
            tec_ser.write(str.encode(i))
            time.sleep(sleep_time)
            tec_ser.read_all()

    #setting the output power
    if output is not None:
        # '4' and '0' is the command that tells the TEC to set the output power to a certain percentage
        message = ['*','4','0','0','0','0','0','0','0','\r']
        
        #accounting for the possibility that the sign is not entered in output correctly
        output = abs(output)
        current_temp = get_temp(tec_ser, sleep_time)
        if (temp < current_temp) & (output > 0):
            output = -1*output
        if output < 0:
            output = int(0.5 * 2**16 - output)
        #converting the output into a hex form that will be put into message
        #possible output values range from -511 (cooling) to 511 (heating) (-100% to 100%)
        output_str = '{h:0>4}'.format(h=hex(output)[2:])
        #the next 4 elements represent the temperature that is given to the TEC
        message[3:7] = output_str[0], output_str[1], output_str[2], output_str[3]

        # generate the check sum, which are 2 ASCII hex characters that compose the last 2 elements of message before '\r'
        byt_message = ''.join(message)
        checksum = hex(sum(byt_message[1:7].encode('ascii'))%256)[-2:]
        message[7:9] = checksum[0], checksum[1]
        print(message)

         # Actually send the signal
        for i in message:
            tec_ser.write(str.encode(i))
            time.sleep(sleep_time)
            tec_ser.read_all()

def h5store(store, df, i, **kwargs):
    ## copied from https://stackoverflow.com/questions/29129095/save-additional-attributes-in-pandas-dataframe
    store.put('tec{}'.format(i), df)
    #store.get_storer('rga').attrs.metadata = kwargs

# if __name__ == "__main__":

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
                    default=1)
parser.add_argument('--temp',
                    help='TEC set temperature in Celcius',
                    type=int)
parser.add_argument('--output_percent',
                    help='Set the output power. Takes values from -511 (-100%) to 511 (100%)',
                    type=int)

args = parser.parse_args()

# Define the TEC temperature controller's serial settings 
TEC = serial.Serial(args.channel_name, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

set_output(args.temp, TEC, args.sleep_time, args.output_percent)

set_temp(args.temp, TEC, args.sleep_time)
#print(set_temp(args.temp, TEC, args.sleep_time))
# print('output: {}' .format(output_on))

temps = get_temp(TEC, args.sleep_time)
print('temperature: {}'.format(temps))

#store = pd.HDFStore(args.file_path)
#temp = pd.DataFrame({'Temperature 1': temps[0], 'Temperature 2': temps[1]})
#h5store(store, temp, 'test')

#store.close()