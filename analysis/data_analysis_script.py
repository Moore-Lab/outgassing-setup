import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

class Dataset:
    def __init__(self, run_label, gases, data_path):
        self.data_path = '/gpfs/gibbs/project/david_moore/aj487/Data_WL110/Outgassing_Setup/'
        self.data_path = self.data_path+data_path
        self.run_label = run_label
        self.filename = self.data_path + '{}.h5'.format(self.run_label)
        self.gases = gases
    
    def GetData(self):
        self.data = {}
        for i,gas in enumerate(self.gases):
            self.data[gas] = pd.read_hdf(self.filename, key=gas)

    def FindPeaks(self): 
        self.peak_indices = {}
        for i,gas in enumerate(self.gases):
            self.peak_indices[gas], _  = find_peaks(np.array(self.data[gas]['Partial_pressure']), width=20, distance=100)
    
    def GetRanges(self):
        self.range = {}
        for i,gas in enumerate(self.gases):
            self.range[gas] = []
            for j,peak in enumerate(self.peak_indices[gas]):
                if j == len(self.peak_indices[gas])-1:
                    self.range[gas].append([peak-180,-1])
                else:
                    self.range[gas].append([peak-120,self.peak_indices[gas][j+1]-300])
    
    def fitfunction(self,tT,a,b,c, tau):
        
        dt = tT[0][1] - tT[0][0]  # Assuming t is evenly spaced
        decay_t = np.arange(0, len(tT[0])) * dt  # Define time for the decay function
        decay = np.exp(-decay_t/tau) * (decay_t >= 0)
        Normdecay = decay/np.sum(decay) #Normalize decay function
        padded_data = np.pad(tT[1], (len(decay)-1, 0), mode='edge')  # Pad data with values similar to edge to resolve boundary issues
        smooth_step = np.convolve(padded_data, Normdecay, mode='valid') #Convolve two functions
        
        factor = np.exp(-1.0*b/(smooth_step))
        pi = 3.141592653589793
        function = 0
        d = .01
       
        
        for n in [0, 1, 2, 3, 4, 5]:
            function += np.exp(-1.0*((((2*n+1)*(pi))/d)**2)*tT[0]*c*factor)
            
        return  ((4*a)/d)*(c) * factor * function
    
    # a = C0 ~ 200
    # b = E/k ~ 6100 [K]
    # c = D0 ~ .003 [m^2/s]
    # d = d ~ [.01 meters]
    
    def fitfunction_offset(self,tT,a,b,c,e,tau):
        
        dt = tT[0][1] - tT[0][0]  # Assuming t is evenly spaced
        decay_t = np.arange(0, len(tT[0])) * dt  # Define time for the decay function
        decay = np.exp(-decay_t/tau) * (decay_t >= 0)
        Normdecay = decay/np.sum(decay) #Normalize decay function
        padded_data = np.pad(tT[1], (len(decay)-1, 0), mode='edge')  # Pad data with values similar to edge to resolve boundary issues
        smooth_step = np.convolve(padded_data, Normdecay, mode='valid') #Convolve two functions
        
        factor = np.exp(-1.0*b/(smooth_step)) 
        return a * e * factor * np.exp(-1.0*c*e*(tT[0])*factor) 

    def logfitfunction(self,tT,a,b,c):
        return a - b/tT[1] - c*tT[0]*np.exp(-b/tT[1])

    def logfitfunction2(self,tT,a,b,c):
        return np.log(a) - b/tT[1] - c*tT[0] #*np.exp(-b/tT[1])
    
    def fitfunction_short(self,tT,a,b,c,d):
        return a*((np.exp(- b/tT[1]))/(tT[0]+c))**(0.5)

    
    
  

    

        
    def fitfunction_short_temp_offset(self, tT, a, b, c, tau):
        
        dt = tT[0][1] - tT[0][0]  # Assuming t is evenly spaced

        decay_t = np.arange(0, len(tT[0])) * dt  # Define time for the decay function
        
        decay = np.exp(-decay_t/tau) * (decay_t >= 0)
        Normdecay = decay/np.sum(decay) #Normalize decay function
        padded_data = np.pad(tT[1], (len(decay)-1, 0), mode='edge')  # Pad data with values similar to edge to resolve boundary issues
        smooth_step = np.convolve(padded_data, Normdecay, mode='valid') #Convolve two functions

        return a*(np.exp((-b)/(smooth_step))/(tT[0]+c))**(0.5) #+ np.exp((-1.0*e*tT[0]))


    
    
    def PlotSingleGas(self, gas, plim=[], tlim=[]):
        plt.figure(figsize=(6,8))
        plt.subplot(2,1,1)
        plt.xlabel('Time since start [s]')
        plt.ylabel('Partial pressure [Torr]')
        plt.yscale('log')
        plt.plot(self.data[gas]['Exposure_time'], self.data[gas]['Partial_pressure'])
        if(plim):
            plt.ylim(plim[0], plim[1])
        plt.subplot(2,1,2)
        plt.xlabel('Time since start [s]')
        plt.ylabel('Mean temperature [K]')
        plt.plot(self.data[gas]['Exposure_time'], self.data[gas]['Mean_temp'])
        if(tlim):
            plt.ylim(tlim[0], tlim[1])