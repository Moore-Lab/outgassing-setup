import pandas as pd
import numpy as np
from datetime import datetime as dt

class DataIO:
    def __init__(self, Path):
        self.Path = Path

    def GetTimeData(self):
        timedata = pd.read_hdf(self.Path, key = '/scan/timestamp')
        self.timedata = pd.to_datetime(timedata, format='%Y%m%d%H%M%S')
    
    def GetTECData(self):
        tecdata = pd.read_hdf(self.Path, key = '/scan/tec_temp')
        self.tecdata = tecdata
        
    def GetPressureData(self):
        pressuredata = pd.read_hdf(self.Path, key = '/scan/ed_pres')    
        self.pressuredata = pressuredata
        
    def GetOmegaData(self):
        omegadata = pd.read_hdf(self.Path, key = '/scan/omega_temp')
        omegadata.columns = ['CH1', 'CH2']
        self.omegadata = omegadata
        
    def GetRGAData(self):
        rgadata = pd.read_hdf(self.Path, key = '/scan/rga')
        rgadata.columns = ['{:.2f}amu'.format(mass) for mass in np.arange(1.0, 100.1, 0.1)]
        rgadata.index = ['data run = {}'.format(i) for i in range(1, len(rgadata) + 1)]
        self.rgadata = rgadata