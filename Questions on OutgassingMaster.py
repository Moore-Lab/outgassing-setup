import argparse
import datetime
import logging
import msvcrt
import time

import keyboard
import numpy as np
import pandas as pd
import serial

import PressureRead
import RGAScan
import TEC
import TempRead

# from threading import Thread

def h5store(store, rga_df, om_df, ed_df, tec_df):#, i, **kwargs):
    '''Creating an h5 file to store the data'''
    store.append(key='scan/rga', value=rga_df, format='table')
    store.append(key='scan/omega_temp', value=om_df, format='table')
    store.append(key='scan/ed_pres', value=ed_df, format='table')
    store.append(key='scan/tec_temp', value=tec_df, format='table')
    store.append(key='scan/timestamp', value=pd.Series(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), format='table')
    # copied from https://stackoverflow.com/questions/29129095/save-additional-attributes-in-pandas-dataframe
    # may be an option to add metadata

def run_outgassing(rga, mass1, mass2, steps, edwards, omega, tec_channel, sleep):
    '''Measuring rga, pressure, and sample temperature'''
    tec = serial.Serial(tec_channel, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) # TEC temperature controller's serial settings 
    masses, pps, totals = RGAScan.run_rga(rga, mass1, mass2, steps)
    pressures = PressureRead.read_pressure(edwards)
    temps = TempRead.read_temp(omega)
    tec_temps = TEC.get_temp(tec, sleep)
    return masses, pps, totals, pressures, temps, tec_temps

def set_temperature(temps, int_time, tec, sleep, open_chamber):
    '''Takes a list of temperatures and sets the tec to each temperature after a given time interval'''
    if open_chamber:
        time.sleep(43200) # if chamber was opened, wait 12h until heating to pump off initial outgassing
    print('heater turning on')
    for t in temps:
        TEC.run_tec(tec, t, sleep)
        print('Set heater to {} C'.format(t))
        time.sleep(int_time)

        # # type 'q' in the terminal in order to stop the script and disconnect from instruments
        # if keyboard.is_pressed('q'):
        #     break
        # else:
        #     pass



if __name__ == '__main__':
    # turn off logging
    logging.getLogger('pyrga').setLevel(logging.CRITICAL)


    # Define arguments to be passed via command line

    parser = argparse.ArgumentParser(description="Run outgasing measurements")
    print('hello')
    parser.add_argument('--temps',
                        nargs='+',
                        help='List of temperatures to measure at',
                        type=float)
    parser.add_argument('--time_interval',
                        help='The amount of time before changing the temperature in hours',
                        type=float)
    parser.add_argument('--close_chamber',
                        action='store_false',
                        help='Indicates whether or not the chamber has been opened since last run, if it has not, include close_chamber in command line',
                        default=True)
    parser.add_argument('--rga_channel',
                        help='Name of the channel to which the RGA is connected',
                        type=str,
                        default='COM4')
    parser.add_argument('--ed_channel',
                        help='Name of the channel to which the pressure gauge is connected',
                        type=str,
                        default='COM7')
    parser.add_argument('--om_channel',
                        help='Name of the channel to which the temperature reader is connected',
                        type=str,
                        default='COM8')
    parser.add_argument('--tec_channel',
                        help='Name of the channel to which the tec is connected',
                        type=str,
                        default='COM3')  
    parser.add_argument('--file_path',
                        help="path to file that stores RGA scans",
                        type=str,
                        default='./OutgassingData_{}.h5'.format(datetime.date.today()))
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

    arg = parser.parse_args()

    RGA = RGAScan.Initialize_RGA(arg.rga_channel, arg.electron_energy, arg.ion_energy, arg.focus_plate, arg.ee_current, arg.noise_floor)

    scan_num = 0
    print('starting measurements')
    start_heater = False
    temp_list = arg.temps
    temp_index = 0 
    start_time = datetime.datetime.now()

    while True:
        masses, p_pressures, totals, pressures, temperatures, tec_temperatures = run_outgassing(RGA, arg.initial_mass, arg.final_mass, arg.steps, arg.ed_channel, arg.om_channel, arg.tec_channel, arg.sleep_time)
        store = pd.HDFStore(arg.file_path)
        rga_press = pd.DataFrame(np.array(p_pressures)).transpose()
        ed_press = pd.DataFrame({'Total Pressure': [pressures]})
        om_ts = pd.DataFrame({'Temp 1': [temperatures[0]], 'Temp 2': [temperatures[1]]})
        tec_ts = pd.DataFrame({'Set Temp': [tec_temperatures]})

        if ((arg.close_chamber == True) & (start_heater == False)): # waiting 12 h to start heater if the chamber has been opened ; ##if chamber was NOT closed and heater NOT started 
            test_time = datetime.datetime.now() #We would use this test time to "test" whether the time difference b/n current time and start time is 12 hours (this is when it is checking the time; the code is doing this check continuously)
            #QUESTION: both start_time and test_time are defined in the same way. Wouldn't that make their difference zero, or has time elapsed when we go from start_time line to test_time line?
            if (test_time - start_time)/datetime.timedelta(hours=1) >= 12: #converting the time difference to hours and checking if that's greater than 12
                TEC.run_tec(arg.tec_channel, temp_list[0], arg.sleep_time) #Argument 1: tec specification (signal settings); Argument 2: the temperature at which the tec will run; 
                #Argument 3: the time between measurements)
                print('starting TEC after waiting period') # waiting period will be 43200 seconds)
                print('turning heater to {} C'.format(temp_list[0])) # after the waiting period, the TEC turns to the first item in the temp_list: 30 in the step-function temp rise 
                start_heater = True #now that the heater starts, the code leaves the main if branch and goes to the else downstairs
                #QUESTION: does that mean the two lines below are mis-placed as they will be ignored? Nope, it's just that the loop won't be re-run
                temp_index += 1 #increase the temperature from the first item in temp_list to the second item: 40 in the step-function temp rise 
                start_time = test_time #resetting start time to test time when raising TEC temp
            else:
                tec_ts = pd.DataFrame({'Set Temp': [0.0]}) #if time difference is less than 12 hours, then the temp is just set to "0, 0"
        else: #in the event that the chamber has been closed or the heater had been started; when the heating happens right away
            test_time = datetime.datetime.now()
            if temp_index == 0: #in the event that the heater brought the temp to 30: we can run 
                TEC.run_tec(arg.tec_channel, temp_list[0], arg.sleep_time) 
                print('starting TEC') #QUESTION: I thought this conditional loop was already starting from the assumption that TEC has started (unless chamber 
                #being closed was the reason the code ran)
                print('turning heater to {} C'.format(temp_list[0])) 
                start_heater = True #QUESTION (similar): I thought this conditional loop was already starting from the assumption that heater has started (unless chamber 
                #being closed was the reason the code ran)
                temp_index +=1 
                start_time = test_time
            elif (temp_index < len(temp_list)): #in the event that the TEC was at a temperature greater than the lowest index in the list (but less than the maximum index)
                if (test_time - start_time)/datetime.timedelta(hours=1) >= arg.time_interval: #has it been 12 hours since the test time, which is now the start time 
                    TEC.run_tec(arg.tec_channel, temp_list[temp_index], arg.sleep_time) #Argument 2: not 30 (or whenever the list starts) but rather the first temp of the TEC
                    print('turning heater to {} C'.format(temp_list[temp_index])) #converting the time difference to hours and checking if that's greater than THE AMOUNT OF TIME 
                    #BEFORE CHANGING THE TEMPERATURE IN HOURS
                    temp_index += 1
                    start_time = test_time


        h5store(store, rga_press, om_ts, ed_press, tec_ts)#, **metadata)
        scan_num += 1
        print('number of scans: {}'.format(scan_num))

        # stopping measurements after the last temperature change
        if (temp_index == len(temp_list)):
            end_time = datetime.datetime.now()
            if (end_time - start_time)/datetime.timedelta(hours=1) >= arg.time_interval: 
                print('End of data taking period. Stopping measurements')
                store.close()
                break
        
        # type 'q' in the terminal in order to stop the script and disconnect from instruments
        # only works on Windows
        if msvcrt.kbhit():
            if msvcrt.getwche() == 'q':
                print(' \n Stopping measurements')
                store.close()
                break




    RGA.turn_off_filament()
    print('turning off the RGA filament')

    tec = serial.Serial(arg.tec_channel, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
    TEC.turn_off_output(tec, 1)
    print('turning off heater')
