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

import sys
import os
from time import clock, time
from copy import deepcopy
import numpy as np
import pylab as plt
import acquis_params as a_p
import pv_control as p_c
import peak_fit as p_f
# Get pylib as relative path to cur work dir.  Should be up two dirs from cur work dir.
pylibPath = os.path.join(os.getcwd().split(os.path.basename(os.path.abspath('..')))[0], 'pylib', 'src')
sys.path.append(pylibPath)

def doSingleAcquis(params, pvLogFile):
    """ Do the desired scan.
        No values / objects are returned.
        There will just be the output files.
    """

    # Check assertions that need to be checked.
    a_p.checkAssertions(params.dxpVer)

    ###################################
    # Now go and do the desired scan. #
    ###################################
    
    # Also need to set the mode which depends on the IOC.
    a_p.setMode(params.trigOnScaler,
                params.detIOCList,
                params.scanIOC,
                params.mcaIOC,
                params.scanType,
                params.detector,
                params.countTime,
                params.dxpVer,
                pvLogFile,
                params.logPVs,
                params.verbose)

    # Acquire the data. 
    a_p.acquire(params.scanType,
                params.scanIOC,
                params.countTime,
                params.detIOCList,
                params.detector,
                pvLogFile,
                params.logPVs,
                params.verbose)


def getSingleSpec(mcaIOC, numChans, xMin, xMax, chan):
    # chan must go from 1 top 100, not 0 to 99.

    # Define the PV string for the spectrum.
    mcaSpecPV = '%s%s%s%d' %(mcaIOC, ':', 'mca', chan)

    # Get the spectrum
    mcaSpec = np.asarray(p_c.cagetPV(mcaSpecPV, verbose = False))
                
    return mcaSpec

def getSpectra(mcaIOC, numChans, xMin, xMax):
    # Initialize a list to store the spectra in.
    specStore = []

    # Loop over the detector channels.
    for chan in np.arange(numChans) + 1:
        # Define the PV string for the spectrum.
        mcaSpecPV = '%s%s%s%d' %(mcaIOC, ':', 'mca', chan)

        # Get the spectrum
        mcaSpec = np.asarray(p_c.cagetPV(mcaSpecPV, verbose = False))
        
        # Append the spectrum to the list.
        specStore.append(mcaSpec)

    return np.asarray(specStore)

def matchVars2Energies(pkEnergies_keV, varList):
    """ Match the variables (centroids or FWHMs) of peaks found to the energies in the list supplied.
    """

    # At this stage, there should always be at least one FWHM in the list, so assert this.
    assert len(varList) > 0

    # At this stage, there should be energies in the list supplied by the user, so assert this.
    assert len(pkEnergies_keV) > 0

    # Assume that the peaks can't be matched.
    toCal = False

    if len(varList) == len(pkEnergies_keV):
        # There are the same number of peaks as there are supplied energies.
        sigVars = [[varList[i], pkEnergies_keV[i]] for i in np.arange(len(varList))]
        toCal = True
        
    elif len(varList) > len(pkEnergies_keV):
        # Assume the most significant peaks found are the first ones, so use them.
        sigVars = [[varList[i], pkEnergies_keV[i]] for i in np.arange(len(pkEnergies_keV))]
        toCal = True
        
    elif len(varList) < len(pkEnergies_keV):
        # Not enough peaks were found, so calibrate from zero.
        sigVars = []
        #### sigVars.append([float(0.0), float(0.0)])
        #### sigVars.append([varList[0], pkEnergies_keV[0]])
        
    return sigVars, toCal

def pad(vars2Pad):
    sigVars = vars2Pad    
    if len(vars2Pad) == 1:
        # If there is only one peak energy, need to add zero as second ref point.
        sigVars = []
        sigVars.append([float(0.0), float(0.0)])    
        sigVars.append([vars2Pad[0][0], vars2Pad[0][1]])
    return sigVars

def setGainParams(dxpVer, cents, detIOC, chan, verbose, logPVs, pvLogFile):
    """ Apply the new gain.
    """
    # Get the old gain.
    if (dxpVer == '3_0') or (dxpVer == '3_1'):
        pv2Get = '%s%s%s%d%s%s' %(detIOC, ':', 'dxp', chan, ':', 'PreampGain_RBV')
    else:
        pv2Get = '%s%s%s%d%s%s' %(detIOC, ':', 'dxp', chan, '.', 'PGAIN_RBV') 
    oldGain = p_c.cagetPV(pv2Get, verbose) 

    # The peak energy to calc gain from should be the middle one iff there are 3 and the last one iff there are 2.
    pkEnergy_keV = cents[1][1]

    # Calc the difference in the number of channels between the 2 peaks.
    energyDiff = cents[-1][1] -  cents[-1][0]

    # Calc the difference in the energies of the 2 peaks.
    chanDiff = cents[0][1] -  cents[0][0]

    # Calc the new gain to be written.
    newGain = (chanDiff / (pkEnergy_keV * 100.)) * oldGain * 1.0

    # Write the new gain.
    if (dxpVer == '3_0') or (dxpVer == '3_1'):
        pv2Set = '%s%s%s%d%s%s' %(detIOC, ':', 'dxp', chan, ':', 'PreampGain')
    else:
        pv2Set = '%s%s%s%d%s%s' %(detIOC, ':', 'dxp', chan, '.', 'PGAIN')
    p_c.caputPV(pv2Set, newGain, pvLogFile, logPVs, verbose) 
  
def getDetIOCChanPair(detIOCList, index):
    # Test if dual IOC
    if len(detIOCList) > 1:
        if index > 51:
            # Must be the second IOC.
            return detIOCList[1], index - 51

    # Not dual IOC, or first IOC in dual IOC system, so easy.
    return detIOCList[0], index + 1


def doCalibration(dxpVer,
                  pkEnergies_keV,
                  index,
                  centroidList,
                  detIOCList,
                  verbose,
                  logPVs,
                  pvLogFile):
    
    """ Perform the calibration of the data.
    """
    # The peak energies must be supplied as a list, so assert this.
    assert type(pkEnergies_keV) == list
    
    # Match the centroids of the peaks to the energies
    matchedCentroids, toCal = matchVars2Energies(pkEnergies_keV, centroidList)
    matchedCentroids = pad(matchedCentroids)
    matchedCentroids = (np.asarray(matchedCentroids)).T
    if toCal:
        # Get the appropriate
        detIOC, chan = getDetIOCChanPair(detIOCList, index)
        print "DETIOC", detIOC
        print "CHAN", chan
        # Get the parameters to gain adjust the bins axis. 
        setGainParams(dxpVer, matchedCentroids, detIOC, chan, verbose, logPVs, pvLogFile)

def scaleFWHMs(matchedEnergies):
    """ Scale the normalized FWHMs by the energies in keV.
    """
    return [pair[0] * pair[1] for pair in matchedEnergies]

def getScaledFWHMs(pkEnergies_keV, chanList, listOfFWHMLists):
    """ The FWHMs returned from the peak fit are normalized but must be scaled by
        the energies of the peaks.
    """
    # The peak energies must be supplied as a list, so assert this.
    assert type(pkEnergies_keV) == list

    # Declare empty list to write scaled FWHMs to.
    scaledFWHMLists = []
    
    # Loop over the list of FWHM lists for the peaks found for each channel.
    for fwhmList in listOfFWHMLists:

        # Match the number of peaks found to the energies in the list supplied.
        matchedEnergies, toCal = matchVars2Energies(pkEnergies_keV, fwhmList)

        # Now scale the normalized FWHMs by the peak energies to get FWHM in keV. 
        scaledFWHMLists.append(scaleFWHMs(matchedEnergies))
    return scaledFWHMLists

def runCal(countTime, energyList_keV, logPVs, saveData, verbose, detector, dxpVer, trigOnScaler, pkRangeMin, pkRangeMax, minBg, maxBg):

    # Create an instance of the Params object.
    # The attributes of this will have to become buttons.
    params = a_p.Params()

    # Anything attached to the params object after this point is not for general users to supply.

    # Assign the detector to the params class.
    params.detector = detector
    
    # Assign the count time for the acquisition to the params class.
    params.countTime = countTime
    
    # Assign the dxp version to the params class.
    params.dxpVer = dxpVer
    
    # Assign the trigger on scaler variable to the params class.
    params.trigOnScaler = trigOnScaler
    
    # Spcify whether to write the PVs that are set to file.
    params.logPVs = logPVs

    # Spcify whether to store the data file.
    params.saveData = saveData

    # Spcify whether to print the PVs to screen.
    params.verbose = verbose
    
    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    params.outBase = '\\\SR12ID01IOC53\\share\\'

    # Specify the scan type.
    params.scanType = 'mca-spec'

    # Specify the energies that the peaks to be fit correspond to.
    #params.pkEnergies_keV = [5.889]
    params.pkEnergies_keV = energyList_keV

    # The input energies must be specified as a list, even if there is only one.
    assert type(params.pkEnergies_keV) == list
    assert len(params.pkEnergies_keV) > 0 and len(params.pkEnergies_keV) < 3
    
    # The number of peaks in the window must equal the number of energies supplied.
    params.numPksInRange = len(params.pkEnergies_keV)

    # Specify the peak range to search.
    # This is only used if numPksInRange > 0.  
    params.pkRangeMin = pkRangeMin
    params.pkRangeMax = pkRangeMax

    # Check that the user has specified only one detector and get the IOC strings.
    # Cumulative exe time is 0.109 sec.
    params.detIOCList, params.scanIOC, params.mcaIOC, params.numChans = a_p.getIOCs(params.detector, params.verbose)  
    
    # Initialize the appropriate parameters.
    # Cumulative exe time is 0.328 sec.
    params, pvLogFile = a_p.checkConfigs(params)

    #####################################
    # Now perform a single acquisition. #
    #####################################
    # Cumulative exe time is 3.143 sec + acquis time.
    doSingleAcquis(params, pvLogFile)
  
    ##########################################
    # There are 2 ways to do the peak fit.   #
    #      - Auto detect                     #
    #      - Speicfy num of peaks in a range #
    ##########################################
        
    # Set spectral limits.
    xMin = None
    xMax = None
    yMin = None
    yMax = None

    # Acquire the spectra for the first time so they can be calibrated.
    spectra = getSpectra(params.mcaIOC, params.numChans, xMin, xMax)

    # Specify hard threshold.
    thresh = 300
    
    # Specify factor to multiply sigma to get noise.
    numStDevs = 5
    
    # Set region of the spectrum that is background.
    bgRange = range(minBg, maxBg)

    # Specify whether to save the plots.
    savePlot = True
    
    # Specify whether to show the plots.
    showPlot = False
    
    # Open the output data file to write to.
    fitDataFileName = 'TestFitData.txt'

    # outDisrStr is returned from the a_p.checkConfigs function.
    fitDataFilePath = os.path.join(params.outDirStr, fitDataFileName)

    if len(params.pkEnergies_keV) > 1:
        # Sort the list of user supplied peak energies into ascending order.
        params.pkEnergies_keV = ascend(params.pkEnergies_keV)


    # Set the run parameters for the fir.
    # Assume auto peak detection.
    autoDetect = True
    # Set the lower bound of the peak search to be channels > the max background chan.
    apdLowBound = bgRange[1]
    # Set the upper bound of the peak search to length of the array (length of the array - 1 for visual effect).
    apdUpBound = len(spectra[0]) - 1
    
    # Check whether to auto detect the numbe of peaks in the spectrum.
    if params.numPksInRange > 0:

        ###########################################################
        # It is not an autofit, so search in the specified range. #
        ###########################################################
        
        # The number of peaks is specified by the user so:
        # 1) The minimum and maximum peak range values must be real numbers.
        assert (type(params.pkRangeMin) == int) and (type(params.pkRangeMax) == int) 
        # 2) The minimum and maximum peak range values must be >= 0.
        assert (params.pkRangeMin >= 0) and (params.pkRangeMax > 0)
        # 3) The pkRangeMax must be > pkRangeMin.
        assert params.pkRangeMax > params.pkRangeMin
        # 4) The pkRangeMax must be <= length of the spectrum.
        assert params.pkRangeMax <= len(spectra[0])
       

    # Loop over the spectra that have been collected so they can be fitted.
    for specIdx, spec in enumerate(spectra):
       
        # Fit the peak
        fitData = p_f.fit(spec, 
                          params.outDirStr,
                          specIdx,
                          params.numPksInRange, 
                          params.pkRangeMin, 
                          params.pkRangeMax, 
                          bgRange, 
                          numStDevs,
                          savePlot,
                          showPlot,
                          params.verbose)

        if fitData:
            # Perform the energy calibration.
            doCalibration(params.dxpVer,
                          params.pkEnergies_keV,
                          specIdx,
                          [i[0] for i in fitData],
                          params.detIOCList,
                          params.verbose,
                          params.logPVs,
                          pvLogFile)

            
          

        # Get the FWHMs scaled to the energies of the peaks.
##        listOfFWHMLists = getScaledFWHMs(params.pkEnergies_keV, chanList, listOfFWHMLists)
##
##            # Get the FWHM for the primary (zeroth) peak for each channel.
##            primFWHMs = np.asarray([fwhmList[0] for fwhmList in listOfFWHMLists])
##
##            # Plot the FWHM for the primary peak for each channel.
##
##            # Initialize a figure.
##            fig = plt.figure()
##            
##            # Adjust the size of the figure.
##            fig.set_size_inches(10,8)
##            
##            # Get the first handle for the sub figure axis.
##            subHandle = plf.initSub(fig, [1,1])
##
##            # Specify ranges.
##            xMin = 0
##            xMax = params.numChans + 1
##            yMin = 0
##            yMax = np.max(primFWHMs) + 0.2
##        
##            # Plot the raw spectrum on the first subplot.
##            plf.hanPlot1D(subHandle, chanList, primFWHMs, "Primary FWHM", "Channel Number", "FWHM (keV)", 1.0, "g", "steps", 1.0, [xMin, xMax], [yMin, yMax])            
##
##            if params.saveData:
##                saveStr = os.path.join(params.outDirStr, 'FWHM_%s.png' %(params.detector))
##                plt.savefig(saveStr)
##       
    
    # Close the PV log file, if used.
##    a_p.finalize(params.logPVs, pvLogFile)

##   if showPlot:
##        plt.show()

def ascend(inpList):
    """ Sort list into ascending order.
    """
    # Input must be a list, so assert this.
    assert type(inpList) == list

    # Make a copy of the list.
    nInpList = deepcopy(inpList)

    # Sort the values into ascending order.
    nInpList.sort()

    return nInpList 

if __name__ == '__main__':

    """ Running the code below will perform a calibration
        of the 100 element detector.
    """
    # Start a counter to calculate how long the code takes to execute.
    startTime = time()

    #################################
    # User defined params go below. #
    #################################
    
    # Specify the count time in seconds.
    countTime = float(10.0)

    # Specify the energies of the peaks to search for.
    # Energies must be supplied as a list, i.e. energyList_keV = [4.9, 5.7]
    # Only properly tested for single energy in the list.
    ## if E>20keV, halve keV value (if high energy settings file!)
    ## if E<20keV, give full keV value (if low energy settings file!)
    energyList_keV = [4.02]

    # Specify the peak range to search.
    pkRangeMin_chan = 360
    pkRangeMax_chan = 420

    # Specify the background range to search.
    # If there are not sufficient counts in this region, the peaks will not align correctly.
    minBg_chan = 250
    maxBg_chan = minBg_chan + 50

    # Spcify whether to write the PVs that are set to file.
    logPVs = True

    # Spcify whether to store the data file.
    saveData = True

    # Spcify whether to print the PVs to screen.
    verbose = False
    
    """ Specify which detector.
        When running the scan, it can only be the EXCLUSIVE OR of the Vortex
        (detector = vortex), 10 element (detector = 'ele10') and 100 element (detector = 'ele100')
        detectors.
        More detectors can be added later.
    """
    detector = 'ele100'
    #params.detector = 'vortex'
    
    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    dxpVer = '2_11'
    #dxpVer = '3_1'

    # Specify that the scaler will not be used for the trigger.
    trigOnScaler = True
    
    # Do the calibration
    runCal(countTime, energyList_keV, logPVs, saveData, verbose, detector, dxpVer, trigOnScaler, pkRangeMin_chan, pkRangeMax_chan, minBg_chan, maxBg_chan)
    
    # Stop the timer that calculates how long the code takes to run.
    stopTime = time()
    
    print "Time to run is %f seconds ..." %((stopTime - startTime))
    print "Done ..."
