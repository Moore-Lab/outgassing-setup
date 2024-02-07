import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

class Dataset:
    def __init__(self, run_label, gases, data_path='/gpfs/gibbs/project/david_moore/bfz2/Data_Analysis/outgassing-setup/h5data_postkey/'):
        self.data_path = data_path
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
    
    def fitfunction(self,tT,a,b,c):
        factor = np.exp(-1.0*b/tT[1])
        return a * factor * np.exp(-1.0*c*tT[0]*factor)

    def logfitfunction(self,tT,a,b,c):
        return a - b/tT[1] - c*tT[0]*np.exp(-b/tT[1])

    def logfitfunction2(self,tT,a,b,c):
        return np.log(a) - b/tT[1] - c*tT[0] #*np.exp(-b/tT[1])
    
    def fitfunction_short(self,tT,a,b,c,d):
        return a*(np.exp(- b/tT[1])/(tT[0]+c))**d

    def fitfunction_short_temp_offset(self,tT,a,b,c,d1,e,f):
        return a*(np.exp(- b/(tT[1]*e + f))/(tT[0]+c))**g

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