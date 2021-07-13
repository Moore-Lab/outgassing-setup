import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


class Dataset:
    def __init__(self, run_label, gases):
        self.data_path = '/gpfs/loomis/project/fas/david_moore/aj487/Data_WL110/Outgassing_Setup/'
        self.run_label = run_label
        self.filename = self.data_path + '{}/{}.h5'.format(self.run_label,self.run_label)
        self.gases = gases
    
    def GetData(self):
        self.data = {}
        for i,gas in enumerate(self.gases):
            self.data[gas] = pd.read_hdf(self.filename, key=gas)

    def FindPeaks(self): 
        self.peak_indices = {}
        for i,gas in enumerate(self.gases):
            self.peak_indices[gas], _  = find_peaks(np.array(self.data[gas]['pressure']), width=20, distance=100)
    
    def GetRanges(self):
        self.range = {}
        for i,gas in enumerate(self.gases):
            self.range[gas] = []
            for j,peak in enumerate(self.peak_indices[gas]):
                if j == len(self.peak_indices[gas])-1:
                    self.range[gas].append([peak-100,-1])
                else:
                    self.range[gas].append([peak-100,self.peak_indices[gas][j+1]-200])
    
    def fitfunction(self,tT,a,b,c):
        factor = np.exp(-1.0*b/tT[1])
        return a * factor * np.exp(-1.0*c*tT[0]*factor)



    def PlotSingleGas(self, gas):
        plt.figure()
        plt.xlabel('Time since start [s]')
        plt.ylabel('Partial pressure [Torr]')
        plt.yscale('log')
        plt.plot(self.data[gas]['exp_time'], self.data[gas]['pressure'])

