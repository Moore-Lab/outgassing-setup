import logging
#import matplotlib.pyplot as plt
import pyrga
import argparse
import datetime
import pandas as pd
import serial
import numpy as np

def Initialize_RGA(rga, ee, ie, fp, eec):
    rga.set_electron_energy(ee)
    print('Electron energy set to {} eV'.format(rga.get_electron_energy()))
    rga.set_ion_energy(ie)
    print('Ion energy set to {} eV'.format(rga.get_ion_energy()))
    rga.set_plate_voltage(fp)
    print('Plate voltage set to {} V'.format(rga.get_plate_voltage()))
    rga.set_emission_current(eec)
    print('Emission Current (filament) set to {} mA'.format(rga.get_emission_current()))

def h5store(store, df, i, **kwargs):
    store.append(key='rga/rga', value=df, format='table')
    store.append(key='rga/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')
    
    #store.get_storer('rga').attrs.metadata = kwargs



# turn off logging
logging.getLogger('pyrga').setLevel(logging.CRITICAL)

# if __name__ == "__main__":
parser = argparse.ArgumentParser(description="Read out the pressure of the RGA at given time intervals")
print('hello')
parser.add_argument('--channel_name',
                    help='Name of the channel to which the RGA is connected',
                    type=str,
                    default='COM6') 
parser.add_argument('--file_path',
                    help="path to file that stores RGA scans",
                    type=str,
                    default='./RGAScan_{}.h5'.format(datetime.date.today()))
parser.add_argument('--sleep_time',
                    help='Number of seconds between measurements',
                    type=float,
                    default=1)
parser.add_argument('--electron_energy', 
                    help='Electron energy. Takes values from 25-105 eV',
                    type=int,
                    default=70)
parser.add_argument('--ion_energy',
                    help='Ion energy. {8: 0, 12: 1} pyrga is weird so it has you input 8 for 0 or and 12 for 1',
                    type=int,
                    default=12)
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
                    help='Steps per amu for RGA scan. Takes values from 10 to 25',
                    type=int,
                    default=10)

args = parser.parse_args()

# initialize client with default settings
try:
    RGA = pyrga.RGAClient(args.channel_name, noise_floor=args.noise_floor)
except pyrga.driver.RGAException as e:
    #trying again to receive the buffer line if it is a timeout problem
    RGA = pyrga.RGAClient(args.channel_name, noise_floor=args.noise_floor)

#initialize RGA parameters
# Initialize_RGA(RGA, args.electron_energy, args.ion_energy, args.focus_plate, args.ee_current)

# # check filament status and turn it on if necessary
# if not RGA.get_filament_status():
#     RGA.turn_on_filament()

# print(masses)
# print(pressures)
# print(total)

cdemv = RGA.get_cdem_voltage()
sp = RGA.get_partial_sens()
metadata = {'Date': datetime.date.today(), 'Version': '3.218.004', 'Noise Floor': args.noise_floor, 'CEM': 'Off', 
            'Steps': args.steps, 'Initial Mass': args.initial_mass, 'Final Mass': args.final_mass, 
            'Focus Plate Voltage': args.focus_plate, 'Ion Energy': args.ion_energy, 'Electron Energy': args.electron_energy,
            'CDEM Voltage': cdemv, 'Partial Sensitivity': sp, 'Electron Emission Current': args.ee_current}

#starting scan
rga_table = []
scan_num = 0


rga_data = True
while rga_data:
    try:
        store = pd.HDFStore(args.file_path)
        # read analog scan of mass range from (default) 1-100 amu with max resolution of 10 steps per amu
        masses, pressures, total = RGA.read_spectrum(args.initial_mass, args.final_mass, args.steps)
        # print(pressures)
        print(masses)
        #creating a pandas dataframe and writing data to an hdf5 file
        # scan = pd.DataFrame({'Mass': masses, 'Pressure': pressures})
        # scan = pd.DataFrame({'Pressure': pressures})
        # rga_table.append(scan)
        h5store(store, pd.DataFrame(np.array(pressures)).transpose(), scan_num)#, **metadata)
        scan_num += 1
        print('number of scans: {}'.format(scan_num))
        store.close()
    except serial.SerialException as e:
        store.close()
        print(e)
        rga_data = False


RGA.turn_off_filament()