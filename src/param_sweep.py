"""
    Copyright (C) 2013 Matthew Dimmock, Australian Synchrotron.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import pylab as plt
import os
import sys
import read_dir_funcs as rdf
import peak_fit as pkf

def getWrittenPVChunks(pvBeforeStart, pvFilePath, startAcquisPV, detIOC):
    """ Get a list of the PVs that were written.
    """
    """ The last thing that is done prior to starting the scan is to
        set the scan number to 0 with the command
        'SR12ID01IOC55:saveData_scanNumber, 0' .
        So find that line.
    """
    
    # Print some sanity checks for the user.
    print 'Only PVs after the line %s will be considered as being part of the parameter sweep ...' %(pvBeforeStart)
    print 'Lines containing the string %s will be stripped from the list of PVs in the parameter sweep ...' %(startAcquisPV)
    
    # Initialize an empty list to fill with PV chunks.
    pvList = []
    
    # Initialize an empty list to fill with lists of PV chunks.
    pvListOfLists = []
    
    # Assume the the 'pvBeforeStart' is not found in the file.
    startLineReached = False
    
    # Loop over data in file.
    for parts, line in rdf.readData(pvFilePath, True, ' '):
    
        # Test to see if this is the line before the scan params start to be written.
        #'SR12ID01IOC55:saveData_scanNumber, 0' .
        pvName = parts[0].strip(',')
      
        if pvName == pvBeforeStart:
        
            # The 'lineBeforeStart' string has been found in the file.
            startLineReached = True
    
        # Test to make sure that this is a PV in the sweep.        
        if startLineReached:
            
            # Test to make sure that this is not the PV that starts the acquisition.
            if ((pvName != startAcquisPV) and (pvName != pvBeforeStart)):
            
                if len (parts) == 2:
                
                    # Strip off the detector IOC name and the colon from the PV name.
                    pvName.strip(detIOC).strip(':')
                
                    # Add the tuple of the PV name and the PV value 
                    pvList.append((pvName, float(parts[1])))
            else:
                pvListOfLists.append(pvList)
                
                # This is the PV that starts the acquisition, so clear the list ready for the next chunk.
                pvList = []
    
    # The 'lineBeforeStart' string must be found otherwise something is wrong, so assert this.
    assert startLineReached == True
    
    # Strip off the top line as this is the line before the scan params start to be written.
    pvListOfLists = pvListOfLists[1:]
    return pvListOfLists
 
def getIdxFromString(filePath, splitChar, fileExt):
    """ Get the acquisition index as the number attached to the filename.
    """
    # Get the basename, i.e. the filename part of the path string.
    fileName = os.path.basename(filePath)
    # Assume that the index is wedged between a split character (i.e. underscore) and the file extension.
    idx = fileName.strip(fileExt).split(splitChar)[-1]
    return int(idx)

class Params():
    # An empty parameter container object.
    pass

def fitAllData(params, dirPath, fileList, fitDataFilePath, bgRange, numPksInRange, pkRangeMin_chan, pkRangeMax_chan, numStDevs, savePlot, showPlot, verbose):
    # Open the output data file to write to.
    fitDataFile = open(fitDataFilePath, 'w')
    
    # Loop over the filenames that will be processed.
    for npyFilePath in fileList[:-1]:
        
        # Get the acquisition index as the number attached to the filename.
        acquisIdx = getIdxFromString(npyFilePath, splitChar = '_', fileExt = '.npy')
 
        # Initialize an empty list to dump the data into.
        dataList = []
        
        # Load the spectral data.  
        spec = np.load(npyFilePath)
                
        # Fit the peak
        calPoints, fits, fwhms = pkf.fit(spec,
                                         dirPath,
                                         acquisIdx,
                                         numPksInRange, 
                                         pkRangeMin_chan, 
                                         pkRangeMax_chan, 
                                         bgRange, 
                                         numStDevs,
                                         savePlot,
                                         showPlot,
                                         verbose)

        
        if len(fits) > 0:
            # Save the figure that has been plotted.
            headStr = '# %i \n' %(acquisIdx)
            fitDataFile.write(headStr)
       
            # For each peak the fit data has the form, [fitPeakIndex, fitPeakVal, fwhm, fwhm / fitPeakIndex, totCounts]
            print acquisIdx, calPoints[0], fwhms[0]
            fitStr = 'acquisIdx=%i, fitPeakIndex=%i, fwhmNorm=%f \n' %(acquisIdx, calPoints[0], fwhms[0])
            fitDataFile.write(fitStr)
            
    # Close the file.
    fitDataFile.close()
  
def unfoldData(data):
    # Loop over the data.
    labels = []
    vals = []
    # Loop over the data fileds in the line of the file.
    for datum in data:
        # Split the data string at the '='.
        splitStr = str(datum).strip().split("=")
        
        # Pull out the data label and its value from the split string.
        labels.append(splitStr[0])
        
        # Assumes that all values magnitudes are floating point.
        vals.append(float(splitStr[1].strip(',')))
    
    # Zip the entries and their vals into a dictionary.
    dataDict = dict(zip(labels, vals))
    return dataDict

def readBackFitData(fitDataFilePath, toStrip):
    # Open the file that contains the plot data for reading.
    
    # Declare empty list to store the dicts of peak data in.
    dictsForSpecPks = []

    # Declare empty master dict to store all spectra in.
    masterDict = {}

    # Define an aquisNum that is not real as a starting point.
    acquisNum = -1

    # Loop over data in file.
    for parts, line in rdf.readData(fitDataFilePath, toStrip, ' '):
        # Get the data, returns "None" for "isData" if header line.
        isData, data = rdf.getValid(parts, True, ["#", "##"])
        if isData:
            # This is data:
            dataDict = unfoldData(data)
            
            # Append the data dictionary to a list
            dictsForSpecPks.append(dataDict)
            
        else:
            # Append the list to 
            if dictsForSpecPks:
                # There are entries in the list, so append it to the master dict with the key that is the scan number.
                masterDict[acquisNum] = dictsForSpecPks
                
            # Empty the list for the next spectrum.
            dictsForSpecPks = []
        
            # This is a header line so get the scan number.
            acquisNum = int(data[-1])
    if dictsForSpecPks:
        masterDict[acquisNum] = dictsForSpecPks
    
    return  masterDict

def getDictAtt(attKey, attDict):
    return attDict[attKey]
        

def processFitData(masterDict, energy_keV):
    acquisNumList = []
    fwhmList = []
    totCountsList = []
     
    for key in masterDict:
        acquisList = masterDict[key]
        primPeakDict = acquisList[0]
        acquisNumList.append(key)
        fwhmList.append(getDictAtt('fwhmNorm', primPeakDict) * energy_keV)
        
    return acquisNumList, fwhmList
        
if __name__ == '__main__':

    # Set plotting parameters.
    params = {'axes.labelsize': 12,
         'axes.formatter.limits': [-3,3],
         'text.fontsize': 22,
         'legend.fontsize': 12,
         'xtick.labelsize': 11,
         'ytick.labelsize': 11}
    plt.rcParams.update(params)

    # Specify the directory where the output files are located.
    dirPath = '/home/dimmockm/Private/data/param-sweep-36element/2013-12-11_12.40.48.547000'
    
    # Specify the name of the detector IOC name.
    detIOC = 'SR12ID01IOC56'
    
    ####################################################
    # First, load the file with the list of PVs in it. #
    ####################################################
    
    # Specify the string on which to filter the files in the directory.
    pvFiltStr = "pvList.txt"
    
    # Filter the contents of dirPath based on the required file extension.
    pvFileList = rdf.listDirCont(dirPath, keepPath = True)
    pvFileList = rdf.filterDirCont(pvFileList, pvFiltStr, sort = True)
     
    # There should be one and only one PV list file, so assert this.
    assert len(pvFileList) == 1
    
    """ The last thing that is done prior to starting the scan is
        'SR12ID01IOC56:ClientWait' 
        So find that line.
    """
    pvBeforeStart = '%s:ClientWait' %(detIOC)
    
    """ A scan is composed of many acquisitions.
        Each acquisition is the process of setting the PVs to sweep over and then 
        starting the acquisition.  The PV that starts each acquisition is included in the log file
        and must be removed from the list as we don't want to plot this parameter.
    """ 
    # Specify the name of the PV that starts each acquisition and that is to be stripped from the PV list.
    startAcquisPV =   '%s:scan1.EXSC' %(detIOC)
    
    # Get the list of PVs that were set during the parameter sweep.
    pvListOfLists = getWrittenPVChunks(pvBeforeStart, pvFileList[0], startAcquisPV, detIOC)
    
    # Specify the string on which to filter the files in the directory.
    mdaFiltStr = '.npy'
    
    # Filter the contents of dirPath based on the required file extension.
    fileList = rdf.listDirCont(dirPath, keepPath = True)
    fileList = rdf.filterDirCont(fileList, mdaFiltStr, sort = True)
    
    # Declare the path of file to write the output data to.
    fitDataFileName = 'FitData.txt'
    fitDataFilePath = os.path.join(dirPath, fitDataFileName)
    
    # Now do the fit.
    
    # Specify the background range to search.
    # If there are not sufficient counts in this region, the peaks will not align correctly.
    minBg_chan = 250
    maxBg_chan = minBg_chan + 50
    
    # Specify hard threshold.
    thresh = 600
    
    # Specify factor to multiply sigma to get noise.
    numStDevs = 5
    
    # Spcify whether to print the PVs to screen.
    showPlot = False
    
    # Spcify whether to print the PVs to screen.
    savePlot = True
    
    # Spcify whether to print the PVs to screen.
    verbose = False
    
    # Set region of the spectrum that is background.
    bgRange = range(minBg_chan, maxBg_chan)
    
    # Specify the number of peaks in the range.
    energyList_keV = [5.889]
    numPksInRange = len(energyList_keV)
    
    # Specify the peak range to search.
    pkRangeMin_chan = 601
    pkRangeMax_chan = 2040
    
    # Now fit all the data. 
    #fitAllData(params, dirPath, fileList, fitDataFilePath, bgRange, numPksInRange, pkRangeMin_chan, pkRangeMax_chan, numStDevs, savePlot, showPlot, verbose)
    
    # Now plot the result.
    masterDict = readBackFitData(fitDataFilePath, True)
      
    # Now the data is imported into a dict of lists of dicts of peak info, process it.
    acquisNumList, fwhmList = processFitData(masterDict, energyList_keV[0])
    
    # Plot the results.
    plt.figure()
    plt.scatter(acquisNumList, fwhmList)
    plt.xlabel('Acquisition Number')
    plt.ylabel('FWHM (keV)')
    plt.xlim([0, 2400])
    plt.xlabel('Parameter combination')
    plt.ylabel('FWHM / [keV]')
    saveStr = os.path.join(dirPath, 'FWHM_Sweep.png')
    plt.savefig(saveStr)
    
    plt.figure()
    s1 = np.load(os.path.join(dirPath, 'spec_1150.npy'))
    s2 = np.load(os.path.join(dirPath, 'spec_200.npy'))
    s3 = np.load(os.path.join(dirPath, 'spec_240.npy'))
    s4 = np.load(os.path.join(dirPath, 'spec_987.npy'))
    
    plt.plot(s1, label = '1150')
    plt.plot(s2, label = '200')
    plt.plot(s3, label = '240')
    plt.plot(s4, label = '987')
    plt.yscale('log')
    plt.xlabel('Channel')
    plt.ylabel('Counts')
    plt.legend()
    saveStr = os.path.join(dirPath, 'Example_Spectra.png')
    plt.savefig(saveStr)
    
    for i in pvListOfLists[521]:
        print i
    
    for i in np.arange(len(pvListOfLists[521])):
        print pvListOfLists[1150][i]
        print pvListOfLists[1300][i]
                       
    
    plt.show()
    print 'Done.'
    
  
