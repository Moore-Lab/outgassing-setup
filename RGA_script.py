import serial
import datetime
import time
import struct
import decimal
import numpy
import os
import argparse


# Define a function that will initialize a scan and return the analog scan file with time stamp


def RGA_Scan(rga, path_to_file):
    # Ask what the sensitivity factor is
    rga.write(str.encode('SP?\r'))
    sensitivity = rga.readlines()
    print(sensitivity)
    sensitivity = sensitivity[0]
    sensitivity = sensitivity.decode('utf-8')
    print("This is the sensitivity: " + str(sensitivity))
    print(float(sensitivity))
    # Trigger one analog scan
    rga.write(str.encode('SC*\r'))
    # Hang out until the rga's buffer fills up with a legit value.

    """ The original code was found here: https://github.com/brennmat/ruediPy/blob/master/python/classes/rgams_SRS.py
    
    N = int(self.param_IO('AP?',1)) # number of data points in the scan

    Y = [] # init empty list

		k = 0
		while ( k < N+1 ): # read data points. Note: after scanning, the RGA also measures the total pressure and returns this as an extra data point, giving N+1 data points in total. All N+1 data points need to be read in order to empty the data buffer.

			# wait for data in buffer:
			t = 0
			dt = 0.1
			doWait = 1
			while doWait > 0:
				if self.ser.inWaiting() == 0: # wait
					time.sleep(dt)
					t = t + dt
					if t > 10: # give up waiting
						doWait = -1
				else:
					doWait = 0

			# read back result:
			if doWait == -1:
				self.warning('RGA did not produce scan result (or took too long)!')
			else:
				u = self.ser.read(4)

				if k < N: # if this was not the final data point (total pressure)
					u = struct.unpack('<i',u)[0] # unpack 4-byte data value
					u = u * 1E-16 # divide by 1E-16 to convert to Amperes
					Y.append(u) # append value to list 'ans'

				# prepare for next value:
				k = k + 1

    """
    Y = []  # init empty list
    N = int(rga.write(str.encode('AP?\r')))
    N = 99*10+1
    print(N)

    k = 0
    while k < N:  # read data points. Note: after scanning, the RGA also measures the total pressure and
        #  returns this as an extra data point, giving N+1 data points in total. All N+1 data points need
        # to be read in order to empty the data buffer.

        # wait for data in buffer:
        t = 0
        dt = 0.1
        doWait = 1
        while doWait > 0:
            if rga.inWaiting() == 0:  # wait
                time.sleep(dt)
                t = t + dt
                if t > 10:  # give up waiting
                    doWait = -1
            else:
                doWait = 0

        # read back result:
        if doWait == -1:
            print('RGA did not produce scan result (or took too long)!')
        else:
            
            #time.sleep(10)
            u = rga.read()
            #time.sleep(1)
            print(u)

            if k < N-1:  # if this was not the final data point (total pressure)
                u = struct.unpack('<i', u)[0]  # unpack 4-byte data value
                u = (u * 1E-13) / float(sensitivity) # divide by 1E-16 to convert to Amperes, times 1E3 for mA to A
                Y.append(u)  # append value to list 'ans'

            # prepare for next value:
            k = k + 1

    """
    wait until the RGA has completed its scan to transmit the data into one text file,
    642 chosen because there are (10 steps per amu and we scan 65-1 amu )+ 1 pressure 
    """
    print(Y)
    # Read the serial output from the buffer and save as a text file that has the time code in the name
    # filename = datetime.datetime.now().strftime("%h_%d_%Y__%H-%M-%S_%p.txt") # use %H instead of %I for 24 hr
    # filename = os.path.join(path, filename)
    f = open(path_to_file, 'w+')
    f.write("We have to write 22 bogus metadata lines so that Ako's code can read this data \n"
            "Today's date \n "
            "Python Script \n "
            "Software Version, 3.218.004 \n"
            " Analog Scan Setup: \n "
            "Data Points in Scan, 641 \n"
            " Units, Torr \n"
            " Noise Floor, 2 \n"
            " CEM Status, OFF \n"
            " Points Per AMU, 10 \n "
            "Scan Start Mass, 1, amu \n "
            "Scan Stop Mass, 65, amu \n "
            "Focus Voltage, 90, Volts \n "
            "Ion Energy, HIGH \n "
            "Electron Energy, 70, eV \n "
            "CEM Voltage, 1000, Volts \n "
            "CEM Gain, 1.00E+006 \n "
            "Sensitivity Factor, 1.00E-004 \n "
            "Filament Current, 1.00, mAmps \n"
            "line 20 \n"
            "line 21 \n"
            "line 22 \n")
    i = 0
    mass = decimal.Decimal("1.00")
    while i < N-1:
        if str(Y[i])[0] == "-":
            f.write("  %s,  %s, \n" % (str(mass), str(numpy.format_float_scientific(Y[i], precision=2, exp_digits=3))))
        else:
            f.write("  %s,   %s, \n" % (str(mass), str(numpy.format_float_scientific(Y[i], precision=2, exp_digits=3))))
        #f.write("  %s,   %-s, \n" % (str(mass), str(numpy.format_float_scientific(Y[i], precision=2, exp_digits=3))))
        #f.write("  {0:4},   {}, \n".format(str(mass), str(numpy.format_float_scientific(Y[i], precision=2, exp_digits=3))))
        i = i+1
        mass = mass + decimal.Decimal("0.10")
    f.close()

# Define arguments to be passed via command line

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Read out the pressure of the RGA at given time intervals")
    print('hello')
    parser.add_argument('--channel_name',
                        help='Name of the channel to which the RGA is connected',
                        type=str,
                        default='COM6') 
    parser.add_argument('--file_path',
                        help="path to file that stores RGA scans",
                        type=str,
                        default='./RGAScan_{}.csv'.format(datetime.date.today()))
    parser.add_argument('--sleep_time',
                        help='Number of seconds between measurements',
                        type=float,
                        default=1)
    parser.add_argument('--electron_energy', 
                        help='Electron energy. Takes values from 25-105 eV',
                        type=int,
                        default=70)
    parser.add_argument('--ion_energy',
                        help='Ion energy. Takes values 0 or 1 for high or low energy',
                        type=int,
                        default=1)
    parser.add_argument('--focus_plate',
                        help = 'voltage. Takes values from 0-150 V',
                        type=int,
                        default=90)
    parser.add_argument('--ee_current',
                        help='Electron emission current. Takes values from 0-3.5 mA',
                        type=float,
                        default=1.0)
    parser.add_argument('--initial_mass',
                        help='Starting mass for RGA scan. Takes values from 1 to 100 amu',
                        type=int,
                        default=1)
    parser.add_argument('--final_mass',
                        help='Ending mass for RGA scan. Takes values from 1 to 100 amu',
                        type=int,
                        default=100)
    parser.add_argument('--noise_floor',
                        help='Noise floor. Takes values from 0 to 7',
                        type=int,
                        default=2)
    parser.add_argument('--steps',
                        help='Steps per amu forRGA scan. Takes values from 10 to 25',
                        type=int,
                        default=10)

    args = parser.parse_args()
    print('hello')


rga = serial.Serial(args.channel_name, baudrate=28800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, rtscts=True)

"""
The version of this code that I based this off of uses a stopbit of 2, while the RGA instruction manual uses a stopbit 
of 1; I am not sure if this is intentional due to the use of an USB to serial connection, so if the code does not
work, check here!
"""
"""
Also, it is possible that pyserial does not want to send the ASCII as is,
so if this code does not compile then I will need to convert all my strings using str.encode()
"""
# Initialize the hardware
# ----------------------
# Set electron energy
rga.write(str.encode('EE{}\r'.format(args.electron_energy)))
# query it to make sure it was set properly
rga.write(str.encode('EE?\r'))
print(rga.readlines())
# Set ion energy
rga.write(str.encode('IE{}\r'.format(args.ion_energy)))
# Query it to ensure proper setting
rga.write(str.encode('IE?\r'))
print(rga.readlines())
# Set the focus plate voltage
rga.write(str.encode('VF{}\r'.format(args.focus_plate)))
# Query it to make sure that it was set correctly
rga.write(str.encode('VF?\r'))
print(rga.readlines())
# Switch on the filament and set the electron emission current
rga.write(str.encode('FL{}\r'.format(args.ee_current)))
# Query it so that it is set correctly
rga.write(str.encode('FL?\r'))
print(rga.readlines())
# Reset the zero of the detector.
rga.write(str.encode('CA\r'))
# Set the CDEM voltage to 0, enabling Faraday cup operation.
#rga.write(str.encode('HV0\r'))

# Set the initial mass for the scan to 1 amu
rga.write(str.encode('MI{}\r'.format(args.initial_mass)))
# Query it to ensure it is set up correctly
rga.write(str.encode('MI?\r'))
print(rga.readlines())
# Set the final mass for the scan
rga.write(str.encode('MF{}\r'.format(args.final_mass)))
# Query it
rga.write(str.encode('MF?\r'))
print(rga.readlines())
# Take maximum averaging (slowest scan rate)
rga.write(str.encode('NF{}\r'.format(args.noise_floor)))
# Query
rga.write(str.encode('NF?\r'))
print(rga.readlines())
# Set steps per amu
rga.write(str.encode('SA{}\r'.format(args.steps)))
# Query
rga.write(str.encode('SA?\r'))
print(rga.readlines())
# Ask how many points we're gonna receive
rga.write(str.encode('AP?\r'))
print(rga.readlines())


# Hang out for a second so the RGA can fill up the buffer then clear serial buffer after this initialization.
serial.time.sleep(args.sleep_time)
rga.readlines()

print('hello')

while True:
    RGA_Scan(rga, args.file_path)
