from datetime import datetime as dt
import os
import pandas as pd
import glob
import zipfile
import numpy as np


class DataIO:
    def __init__(self, Path):
        self.Path = Path
        self.ZipDir = self.Path+'/RGA/'
    
    def Unzip(self): 
        File = glob.glob(self.Path+'*.zip')[0]
        if os.path.exists(self.ZipDir):
            pass
        else:
            with zipfile.ZipFile(File, 'r') as zip_ref:
                zip_ref.extractall(self.Path)
        self.RGAFiles = glob.glob(self.ZipDir+'/*.txt')
    
    def RemoveUnzippedDir(self):
        for File in self.RGAFiles:
            os.remove(File)
        os.rmdir(self.ZipDir)
   

    def GetRGAData(self, Size=-1, Path=None):
        """Reads in all '.txt' files in filepath as RGA data output files and returns the data as a pandas DataFrame."""

        if Path == None:
            pass
        else: 
            self.Path = Path
            self.Unzip 

        RGAData = []
        for ii,File in enumerate(self.RGAFiles):
            RGAWaveform = pd.read_csv(File, sep=",", header=None, skiprows=22, usecols=[0,1])
            RGAWaveform.columns = ["Mass", "Pressure"]

            RGATime = np.sum(pd.read_csv(File, nrows=0).columns.values)
            RGATime = dt.strptime(RGATime, "%b %d %Y  %I:%M:%S %p")

            RGAScan = pd.DataFrame(data=[[RGATime for i in range(RGAWaveform.shape[0])], RGAWaveform['Mass']]).T
            RGAScan['Pressure'] = RGAWaveform['Pressure']
            RGAScan.columns = ['Datetime', 'Mass', 'Pressure']
            RGAData.append(RGAScan)
            
            if ii == Size:
                break

        self.RGAData = pd.concat(RGAData, ignore_index=True)

    def GetTemperatureData(self, Path=None):
        if Path == None:
            pass
        else:
            self.Path = Path

        self.TempFiles = glob.glob(self.Path+'Temperature/*.csv')
        TempData = []
        for File in self.TempFiles: 
            RawTempData = pd.read_csv(File, sep=",", header=None, skiprows=12, usecols=[1,2,4,7])
            RawTempData.columns = ['Date', 'Time', 'CH1', 'CH2']
            RawTempData['Datetime'] = [dt.strptime("%s %s" % (x,y), "%Y/%m/%d  %H:%M:%S") for x,y in zip(RawTempData['Date'], RawTempData['Time'])]
            RawTempData.drop(['Date', 'Time'], axis=1)
            RawTempData.drop(RawTempData[RawTempData['CH1'] == 'Time out'].index, inplace = True)
            RawTempData.drop(RawTempData[RawTempData['CH2'] == 'Time out'].index, inplace = True)

            TempData.append(RawTempData)
        self.TempData = pd.concat(TempData, ignore_index=True)

if __name__ == "__main__":
    Path = '/project/david_moore/aj487/Data_WL110/Outgassing_Setup/20201014/'
    IO = DataIO(Path)
    IO.Unzip()
    Data = IO.GetRGAData(Size=100)
    Temp = IO.GetTemperatureData()