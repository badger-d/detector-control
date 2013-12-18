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
import sys
import os
import itertools as it
import time
import time_stamp as t_s
import pv_control as p_c 

def detOS():
    """ Determine if the operating system is Windows or Linux.
        The code can only deal with Linux OR Windows (not OSX), so assert this.
    """
    assert os.name == 'posix' or os.name == 'nt'
    # Test whether Linux OR Windows

    # Assume it is Linux.
    isLinux = True
    if os.name == 'nt':
        # The OS is Windows.
        isLinux = False
    return isLinux
    
def mkOutDirs(outDirStr, detIOCList, timeStamp):
    """ Create a directory and all parent folders.
    """
    # Make the desired output directory specified by the user and also a local
    # directory on each detector IOC. 
    
    # Test if the dir exists.
    if not os.path.exists(outDirStr):
        os.mkdir(outDirStr)

    for detIOC in detIOCList:
        outBase = "\\\%s\\share\\" %(detIOC)
        detDirStr = os.path.join(outBase, timeStamp)
        print "Making directory %s ..." %(detDirStr) 
        if not os.path.exists(detDirStr):
            os.mkdir(detDirStr)

def setReadBack(detIOC, dxpVer, pvLogFile, logPVs, verbose):
    """ These are the usual values for the read-back parameter PVs.
    """
    
    # Set the MCA Status rate.
    pv2Set = '%s%s%s' %(detIOC, ':', 'StatusAll.SCAN')
    val2Write = float(0.1)
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the MCA read rate.
    pv2Set = '%s%s%s' %(detIOC, ':', 'ReadAll.SCAN')
    val2Write = str('1 second')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the read rate rate of the lower level params.
    if dxpVer == '2_11':
        pv2Set = '%s%s%s' %(detIOC, ':', 'ReadDXPs.SCAN')
    elif dxpVer == '3_1':
        pv2Set = '%s%s%s' %(detIOC, ':', 'ReadLLParams.SCAN')
    val2Write = str('Passive')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the client wait params.
    pv2Set = '%s%s%s' %(detIOC, ':', 'EnableClientWait')
    val2Write = str('Disable')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
    pv2Set = '%s%s%s' %(detIOC, ':', 'ClientWait')
    val2Write = str('Done')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

def setWaitForMCAs(mcaList, scanIOC, mcaIOC, detIOCList, detector, pvLogFile, logPVs, verbose, dxpVer):
    """ The difference in setup depends on the different detectors as the 100ele
        detector uses a scan recod that has a weird name.  
    """

    ################################################
    # Set the Mark River's style scan in MCA mode. #
    ################################################
 
    # Set the readback to time.
    pv2Set = '%s%s%s' %(scanIOC, ':', 'scan1.R1PV')
    #val2Write = str('time')
    val2Write = str('')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the number of points in the scan to 1.
    pv2Set = '%s%s%s' %(scanIOC, ':', 'scan1.NPTS')
    val2Write = int(1)
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the positioner to read 'time'
    pv2Set = '%s%s%s' %(scanIOC, ':', 'scanH.NPTS')
    val2Write = int(2048)
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    # Set the scan1 record to trigger the scanH record.
    pv2Set = '%s%s%s' %(scanIOC, ':', 'scan1.T1PV')
    val2Write = '%s%s%s' %(scanIOC, ':', 'scanH.EXSC')
    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    """ The MCAs must be written
    """
    # First, clear them all.
    for index in np.arange(70):
        listIndex = '%02i' %(index + 1)
        pv2Set = '%s%s%s%s%s' %(scanIOC, ':', 'scanH.D', str(listIndex), 'PV')
        val2Write = ''
        p_c.caputPV(pv2Set, val2Write, pvLogFile, False, verbose)
            
    # Add the MCAs to the detectors list.
    for mcaIndex, mca in enumerate(mcaList):
        # Have to add 1 as m it starts from 0.
        listIndex = '%02i' %(mcaIndex + 1)
        pv2Set = '%s%s%s%s%s' %(scanIOC, ':', 'scanH.D', str(listIndex), 'PV')
        val2Write = '%s%s%s%s' %(mcaIOC, ':', 'mca', str(mca))
        p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

    """ The triggering of the detector readout depends on the detector.
    """
        
    # Set the scanH record to trigger from the appropriate IOC(s)
    # There are only two entries in the scanH for detector triggers, so assert this.
    assert len(detIOCList) <= 2
    for detIndex, detIOC in enumerate(detIOCList):
        pv2Set = '%s%s%s%s%s' %(scanIOC, ':', 'scanH.T', detIndex + 1, 'PV')
        val2Write = '%s%s%s' %(detIOC, ':', 'EraseStart')
        p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)


        if (dxpVer == '3_0') ^ (dxpVer == '3_1'):
            # Set the number of SCAs to 1 
            pv2Set = '%s%s%s' %(detIOC, ':', 'NumSCAs')
            val2Write = int(1)
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
            
        for mcaIndex, mca in enumerate(mcaList):
            # Set the lower MCA limit in the spectrum for the current mca.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'mca', str(mcaIndex + 1), '.R0LO')
            val2Write = int(1)
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Set the upper MCA limit in the spectrum for the current mca.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'mca', str(mcaIndex + 1), '.R0HI')
            val2Write = int(2048)
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

        
def getIOCs(detector, verbose):
    # Assert this EXCLUSIVE OR condition.
    assert (detector == 'vortex') ^ (detector == 'ele10') ^ (detector == 'ele100') ^ (detector == 'ele36')
    
                               
    #####################################
    # Assume it is the vortex detector. #
    #####################################

    """ Specify detector IOC alias list.
        For the 10 element detector, this is SR12ID01IOC55, so use
        detIOCList = [SR12ID01IOC55].        
    """
    detIOCList = ['SR12ID01IOC55']
                               
    """ Specify the alias of the IOC that the scan record is running on.
        For the Vortex detector, this is SR12ID01IOC55.
    """
    scanIOC = 'SR12ID01IOC55'
                               
    """ Specify the alias of the IOC that reads back the MCAs.
        For the Vortex detector, this is SR12ID01IOC55.
    """
    mcaIOC = 'SR12ID01IOC55'

    # Specify the number of detector channels.
    numChans = 1

    print 'Detector is %s ####################' %(detector)

    # Set the string to print to screen to 10 for 10 elements.
    detStr = 'Vortex'

    # Test if the Vortex vars should be overwritten with 10 element vars.
    if detector == 'ele10':
        """ The detector is the 10 element detector, so overwrite the values
            that were configured for the Vortex detector.
        """
        
        """ Specify detector IOC alias list.
            For the 10 element detector, detIOCList = [SR12ID01IOC55].
        """
        detIOCAliasList = ['SR12ID01IOC55']

        """ Specify the alias of the IOC that the scan record is running on.
            For the 10 element detector, this is SR12ID01IOC55.
        """
        scanIOC = 'SR12ID01IOC55'
                               
        """ Specify the alias of the IOC that reads back the MCAs.
            For the 10 element detector, the MCAs are IOC55.
        """
        mcaIOC = 'SR12ID01IOC55'

        # Set the string to print to screen to 100 for 100 elements.
        detStr = '10 element'

        # Specify the number of detector channels.
        numChans = 10

    elif detector == 'ele36':
        """ The detector is the 36 element detector, so overwrite the values
            that were configured for the Vortex detector.
        """
        
        """ Specify detector IOC alias list.
            For the 36 element detector, detIOCList = [SR12ID01IOC56].
        """
        detIOCAliasList = ['SR12ID01IOC56']
        detIOCList = ['SR12ID01IOC56']
        """ Specify the alias of the IOC that the scan record is running on.
            For the 36 element detector, this is SR12ID01IOC56.
        """
        scanIOC = 'SR12ID01IOC56'
                               
        """ Specify the alias of the IOC that reads back the MCAs.
            For the 10 element detector, the MCAs are IOC55.
        """
        mcaIOC = 'SR12ID01IOC56'

        # Set the string to print to screen to 100 for 100 elements.
        detStr = '36 element'

        # Specify the number of detector channels.
        numChans = 32

    # Test if the Vortex vars should be overwritten with 100 element vars.
    elif detector == 'ele100':
        """ The detector is the 100 element detector, so overwrite the values
            that were configured for the Vortex detector.
        """
        # Get the PV that gives the IOC config.
        pv2Get = '%s%s%s' %('SR12ID01DET01', ':', 'IOC_CONFIG_CMD')
        IOCConf100Ele = p_c.cagetPV(pv2Get, verbose)

        """ The IOC config can only be EXCLUSIVE OR of dual, IOC53 and IOC54, so assert this. 
            The PV that differentiates between these for the 100 element detector
            is SR12ID01DET01:IOC_CONFIG_CMD
        """
        # DO NOT remove this assertion or the if statements below may fail.
        assert (IOCConf100Ele == 3) ^ (IOCConf100Ele == 2) ^ (IOCConf100Ele == 1)

        # Set the appropriate vars for the config that is detected.
        """ Specify detector IOC alias list.
            For the 100 element detector, these are SR12ID01IOC53 and
            SR12ID01IOC54, or either of these. So use
            detIOCList = [SR12ID01IOC53, SR12ID01IOC54] OR,
            detIOCList = [SR12ID01IOC53] OR,
            detIOCList = [SR12ID01IOC54].
        """
        if IOCConf100Ele == 3: # 'Dual_IOC'
            detIOCList = ['SR12ID01IOC53', 'SR12ID01IOC54']
        elif IOCConf100Ele == 2: #  'IOC54':
            detIOCList = ['SR12ID01IOC54']
        else:
            # Assume only IOC53.
            detIOCList = ['SR12ID01IOC53']
        
        """ Specify the alias of the IOC that the scan record is running on.
            For the 100 element detector, this is SR12ID01IOC51.
        """
        scanIOC = 'SR12ID01IOC53'


        # Specify the number of detector channels.
        numChans = 100
                       
        """ Specify the alias of the IOC that reads back the MCAs.
            For the 100 element detector, the MCAs have been remapped to
            SR12ID01DET01 to cope with having two IOCs.
        """
        mcaIOC = 'SR12ID01DET01'

        # Set the string to print to screen to 100 for 100 elements.
        detStr = '100 element'
        
    print 'You are working with the %s detector ...' %(detStr)
    print 'The IOC(s) that control the %s detector  are:' %(detStr)
    for detIOC in detIOCList:
        print detIOC
    print '...'
    print 'The IOC that controls the scan record is %s ...' %(scanIOC)
    print 'The IOC that controls the MCA fields is %s ...' %(mcaIOC)                           
    return detIOCList, scanIOC, mcaIOC, numChans

def checkDXPVer(dxpVer):
    """ Check the version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
        Other versions can be added later.
    """
    assert (dxpVer == '2_11') ^ (dxpVer == '3_1')
    print 'The DXP version is %s ...' %(dxpVer)

def checkScanType(scanType):
    """ Check that the scan type is valid.
        When running the scan, it can only be the EXCLUSIVE OR of
        wait-for-mcas, mca-map and ......
        Other versions can be added later.
    """
    assert (scanType == 'wait-for-mcas') ^ (scanType == 'mca-map') ^ (scanType == 'mca-spec')
    print 'The scan type is %s ...' %(scanType)

def getMCAList(detector, numChans):
    # Specigy the MCA list.
    if detector == 'vortex':
        mcaList = [1]
    elif detector == 'ele10':
        mcaList = np.asarray([1, numChans])
    elif detector == 'ele36':
        mcaList = np.asarray([1, numChans])
    elif detector == 'ele100':
        # Must be 100 elemet detector.
        # Add the MCAs to the detectors list.
        # The MCSs are spread across both IOCs to ensure even data collection.
        m = np.arange(20) + 1
        n = np.arange(15) + 38
        o = np.arange(20) + 53
        p = np.arange(15) + 86
        mcas = [list(m), list(n), list(o), list(p)]
        mcaList = list(it.chain(*mcas))
    return mcaList

def getPollTime(countTime):
    # Return the time between each poll of the PV
    # If scan time < 1.0 s, poll time == scan time.
    if countTime:

        if countTime < 1.0:
            return countTime
        # Poll time <= 1.0 s, to poll time = 0.5 s
        return 0.5
    else:
        return 1.0

def wait(waitTime):
    # Get the python code to wait for a specified period of time.
    # The time should be in seconds.
    time.sleep(waitTime)

def pollPV(pv2Get, pollTime):
    # The second while statement checks to see if the scan has stopped.
    while True:
        if int(p_c.cagetPV(pv2Get, verbose = False)) == 0:
            # Break the poll cycle.
            break
        else:
            # Wait fixed time prior to polling again.
            wait(pollTime)
            
def checkScanStatus(scanType,
                    countTime,
                    scanIOC,
                    detIOCList):
    assert (scanType == 'wait-for-mcas') ^ (scanType == 'mca-map') ^ (scanType == 'mca-spec')

    pollTime = getPollTime(countTime)
    pv2Get = None

    if (scanType == 'wait-for-mcas') ^ (scanType == 'mca-spec'):
        # Assume that the scan1.EXSC PV has to reset to 0 for the scan to finish.
        pv2Get = '%s%s%s' %(scanIOC, ':', 'scan1.EXSC')
        assert pv2Get != None
        
        pollPV(pv2Get, pollTime)
    
    elif scanType == 'mca-map':
        for detIOC in detIOCList:
            # Assume that the Acquiring PV has to reset to 0 for the scan to finish.
            pv2Get = '%s%s%s' %(detIOC, ':', 'Acquiring')
            assert pv2Get != None
            pollPV(pv2Get, pollTime)  
            
def configPreamps(detIOC, dxpVer, detector, pvLogFile, logPVs, verbose):
    """ Configure the preamplifier parameters.
        This is only currently for the Vortex.
        Other versions can be added later.
    """
    # Number of channels to set the preamp vals for.
    chans = int(1)
    # Pre-amp gain in mV as a list for the number of chans.
    gainList_mVperkeV = [float(1.7)]
    # Pre-amp polarity.
    pol = str('Pos')
    # Pre-amp delay in micro sec.
    """ Is actually 1 us, but for XMAPs older than RevD,
        this should be set to 10.0.  As we have a mix, set to 10 to
        be safe.
    """
    if detector == 'vortex':
        delay_us = float(1.0)
    else:
        delay_us = float(10.0)
    # Decay time in micro sec.
    """ Not used as we have reset preamps, so set to 10 as default.
    """
    decay_us = float(50.0)
    # Maximum energy of scale in keV. 
    maxEn_keV = float(20.0)
    # ADC percent - recommended val is 6% 
    adcPerc = float(6.0)

    # Now set the values.
    for chan in np.arange(chans) + 1:
        # Pre-amp gain in mV as a listfor the number of chans.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'PreampGain')
        p_c.caputPV(pv2Set, gainList_mVperkeV[chan-1], pvLogFile, logPVs, verbose)
        # Pre-amp polarity.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'DetectorPolarity')
        p_c.caputPV(pv2Set, pol, pvLogFile, logPVs, verbose)
        # Pre-amp delay in micro sec.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'ResetDelay')
        p_c.caputPV(pv2Set, delay_us, pvLogFile, logPVs, verbose)
        # Decay time in micro sec.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'DecayTime')
        p_c.caputPV(pv2Set, decay_us, pvLogFile, logPVs, verbose)
        # Maximum energy of scale in keV. 
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'MaxEnergy')
        p_c.caputPV(pv2Set, maxEn_keV, pvLogFile, logPVs, verbose)
        # ADC percent - recommended val is 6% 
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'ADCPercentRule')
        p_c.caputPV(pv2Set, adcPerc, pvLogFile, logPVs, verbose)

def configDXPFilters(detIOC, dxpVer, detector, pvLogFile, logPVs, verbose):
    """ Configure the fast trigger, energy and baseline parameters.
        This is only currently for the Vortex.
        Other versions can be added later.
    """
    # Number of channels to set the preamp vals for.
    chans = 1
    # Fast (trigger) filter peaking time in micro sec.
    fastPkTime_us = float(0.16)
    # Fast (trigger) filter gap time in micro sec.
    # Generally set to 0.
    fastGapTime_us = float(0.0)
    # Fast (trigger) filter level.
    fastTrigLevel_keV = float(1.0)
    # Energy filter peaking time in micro sec.
    energyPkTime_us = float(1.0)
    # Energy filter gap time in micro sec.
    # Should reflect the rise of the preamp.
    energyGapTime_us = float(0.24)
    # Energy threshold level.
    # Should be set to 0.
    energyThresh_keV = float(0.0)
    # Maximum peak width for pile-up inspection in micro sec.
    energyMaxWidth_us = float(1.0)
    # Length of the baseline filter in samples (powers of 2).
    baseFiltLen = int(256)
    # Threshold in keV of baseline filter.
    baseThresh_keV = float(1.25)
    # Baseline cut enable, always NO for XMAP.
    baseCutEn = str('No')
    # Baseline cut percent, always 0.0 for XMAP as is not enabled.
    baseCutPerc = float(0.0)
    
    # Now set the values.
    for chan in np.arange(chans) + 1:
        # Fast (trigger) filter peaking time in micro sec.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'TriggerPeakingTime')
        p_c.caputPV(pv2Set, fastPkTime_us, pvLogFile, logPVs, verbose)
        # Fast (trigger) filter gap time in micro sec.
        # Generally set to 0.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'TriggerGapTime')
        p_c.caputPV(pv2Set, fastGapTime_us, pvLogFile, logPVs, verbose)
        # Fast (trigger) filter level.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'TriggerThreshold')
        p_c.caputPV(pv2Set, fastTrigLevel_keV, pvLogFile, logPVs, verbose)
        # Energy filter peaking time in micro sec.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'PeakingTime')
        p_c.caputPV(pv2Set, energyPkTime_us, pvLogFile, logPVs, verbose)
        # Energy filter gap time in micro sec.
        # Should reflect the rise of the preamp.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'GapTime')
        p_c.caputPV(pv2Set, energyGapTime_us, pvLogFile, logPVs, verbose)
        # Energy threshold level.
        # Should be set to 0.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'EnergyThreshold')
        p_c.caputPV(pv2Set, energyThresh_keV, pvLogFile, logPVs, verbose)
        # Maximum peak width for pile-up inspection in micro sec.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'MaxWidth')
        p_c.caputPV(pv2Set, energyMaxWidth_us, pvLogFile, logPVs, verbose)
        # Length of the baseline filter in samples (powers of 2).
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'BaselineFilterLength')
        p_c.caputPV(pv2Set, baseFiltLen, pvLogFile, logPVs, verbose)
        # Threshold in keV of baseline filter.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'BaselineThreshold')
        p_c.caputPV(pv2Set, baseThresh_keV, pvLogFile, logPVs, verbose)
        # Baseline cut enable, always NO for XMAP.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'BaselineCutEnable')
        p_c.caputPV(pv2Set, baseCutEn, pvLogFile, logPVs, verbose)
        # Baseline cut percent, always 0.0 for XMAP as is not enabled.
        pv2Set = '%s%s%s%s%s%s' %(detIOC, ':', 'dxp', str(chan), ':', 'BaselineCutPercent')
        p_c.caputPV(pv2Set, baseCutPerc, pvLogFile, logPVs, verbose)


def setPixPerBuffer(detIOC, pixPerBuff, pixBufUpdat, pixPerRun,  pvLogFile, logPVs, verbose):
    """ This is a separate function as there is a strange bug to do with
        ordering in the XMAP software.
    """
    print "Setting the number of pixels per buffer ..."
    for i in np.arange(2):
        # Set the number of pixels per run.  If == 1, the system will just continue forever.
        pv2Set = '%s%s%s' %(detIOC, ':', 'PixelsPerBuffer')
        p_c.caputPV(pv2Set, pixPerBuff, pvLogFile, logPVs, verbose)
        # Set the pixel-buffer update to auto.
        pv2Set = '%s%s%s' %(detIOC, ':', 'AutoPixelsPerBuffer')
        p_c.caputPV(pv2Set, pixBufUpdat, pvLogFile, logPVs, verbose)

     
    # Update the number of captures.
    pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'NumCapture')
    # Determine the number of captures from the pixels per run / pixels per buffer.
    numCap = np.floor(float(pixPerRun) / float(pixPerBuff))
    if int(np.mod(float(pixPerRun), float(pixPerBuff))) != 0:
        numCap += 1    
    # Update the PV.
    p_c.caputPV(pv2Set, numCap, pvLogFile, logPVs, verbose)


    
def configDXPMapCont(detIOCList,
                     dxpVer,
                     detector,
                     countTime,
                     scanType,
                     scanIOC,
                     saveData,
                     timeStamp,
                     pvLogFile,
                     logPVs,
                     verbose):
    """ Configure the mapping mode controls.
    """

    print "Configuring the XMAP controls ..."
    
    # Mapping mode is only available in version greater > '2_11', so assert this.
    assert (dxpVer == '3_0') ^ (dxpVer == '3_1')
    
    #######################
    # Specify the values. #
    #######################
    
    # Assume that 'MCA mapping' is the default.
    collMode = 'MCA mapping'
    """ List mode variant is only set if collMode == 'List mapping', so leave as
        default 'E & Gate'.
    """
    listMode = 'E & Gate'
    # Set the pixel advance mode.
    pixAdv = 'Gate'
    # Value that divides the sync clock, just set to 1.
    syncCnt = 1
    # We want to respond to the gate pulse so set ignore gate low.
    ignGate = 'No'
    # Set input logic polarity to inverted due to our strange gate pulse.
    inpLogPol = 'Inverted'
    # Set the number of pixels per run.  If == 1, the system will just continue forever.
    pixPerRun = int(256)
    # Set the pixel-buffer update to auto.
    pixBufUpdat = 'Manual'
    # As the pixel-buffer update is auto, no need to set a value, just leave at 64.
    pixPerBuff = int(64)

    #########################
    # Now write the values. #
    #########################

    for detIOC in detIOCList:
        # Assume that 'MCA mapping' is the default.
        pv2Set = '%s%s%s' %(detIOC, ':', 'CollectMode')
        p_c.caputPV(pv2Set, collMode, pvLogFile, logPVs, verbose)
        """ List mode variant is only set if collMode == 'List mapping', so leave as
            default 'E & Gate'.
        """
        pv2Set = '%s%s%s' %(detIOC, ':', 'ListMode')
        p_c.caputPV(pv2Set, listMode, pvLogFile, logPVs, verbose)
        # Set the pixel advance mode.
        pv2Set = '%s%s%s' %(detIOC, ':', 'PixelAdvanceMode')
        p_c.caputPV(pv2Set, pixAdv, pvLogFile, logPVs, verbose)
        # Value that divides the sync clock, just set to 1.
        pv2Set = '%s%s%s' %(detIOC, ':', 'SyncCount')
        p_c.caputPV(pv2Set, syncCnt, pvLogFile, logPVs, verbose)
        # We want to respond to the gate pulse so set ignore gate low.
        pv2Set = '%s%s%s' %(detIOC, ':', 'IgnoreGate')
        p_c.caputPV(pv2Set, ignGate, pvLogFile, logPVs, verbose)
        # Set input logic polarity to inverted due to our strange gate pulse.
        pv2Set = '%s%s%s' %(detIOC, ':', 'InputLogicPolarity')
        p_c.caputPV(pv2Set, inpLogPol, pvLogFile, logPVs, verbose)
        # Set the number of pixels per run.  If == 1, the system will just continue forever.
        pv2Set = '%s%s%s' %(detIOC, ':', 'PixelsPerRun')
        p_c.caputPV(pv2Set, pixPerRun, pvLogFile, logPVs, verbose)

        # This is a separate function as there is a strange bug to do with ordering in the XMAP software.
        setPixPerBuffer(detIOC, pixPerBuff, pixBufUpdat, pixPerRun, pvLogFile, logPVs, verbose)
 
        #####################################
        # Now configure the saving options. #
        #####################################

        # Check that the user wants to save the data.
        if saveData:

            #######################
            # Specify the values. #
            #######################
    
            # Make sure the array port is configured correctly.
            aryPort = str('DXP1')
            # Enable callbacks.
            enCallBac = int(1)
            # Now set up the save data params.
            dirPath = '%s%s' %('C:\\share\\', timeStamp)
            # Set up the file name.
            fileName = '%s' %(detIOC)
            # Reset the scan number.
            scanNum = int(1)
            # Set auto increment to yes.
            autoInc = str('Yes')
            # Set the file name format.
            fileFormat = str('%s%s_%d.nc')
            # Set the auto save to yes.
            autoSave = str('Yes')
            # Set the file write mode to single.
            writeMode = str('Stream')
            # The number of captures is automatically updated in the function 'setPixPerBuffer', so don't need to do it here.

        
            #########################
            # Now write the values. #
            #########################
    
            # Make sure the array port is configured correctly.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'NDArrayPort')
            p_c.caputPV(pv2Set, aryPort, pvLogFile, logPVs, verbose)
            # Enable callbacks.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'EnableCallbacks')
            p_c.caputPV(pv2Set, enCallBac, pvLogFile, logPVs, verbose)
            # Now set up the save data params.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'FilePath')
            """ Assumes that the local folder 'C:\\share' corresponds to the
                global '\\\SR12ID02IOC53\\share\\' folder.
            """
            p_c.caputPV(pv2Set, dirPath, pvLogFile, logPVs, verbose)
            # Set up the file name.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'FileName')
            p_c.caputPV(pv2Set, fileName, pvLogFile, logPVs, verbose)
            # Reset the scan number.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'FileNumber')
            p_c.caputPV(pv2Set, scanNum, pvLogFile, logPVs, verbose)
            # Set auto increment to yes.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'AutoIncrement')
            p_c.caputPV(pv2Set, autoInc, pvLogFile, logPVs, verbose)
            # Set the file name format.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'FileTemplate')
            p_c.caputPV(pv2Set, fileFormat, pvLogFile, logPVs, verbose)
            # Set the auto save to yes.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'AutoSave')
            p_c.caputPV(pv2Set, autoSave, pvLogFile, logPVs, verbose)
            # Set the file write mode to single.
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'FileWriteMode')
            p_c.caputPV(pv2Set, writeMode, pvLogFile, logPVs, verbose)

    # Do dummy run to train the software about the number of buffers to write.
    dummyMapRun(detIOCList, countTime, scanType, scanIOC, pvLogFile, logPVs, verbose)

def dummyMapRun(detIOCList, countTime, scanType, scanIOC, pvLogFile, logPVs, verbose):
    """ Do dummy run to train the software about the number of buffers
        to write.
    """
    print 'Starting dummy mapping mode run to configure buffeer write ...'
    print 'The input scaler or pulse generator should either be diconnected or not running at this moment ...'

    # If you're in this function, it's always the dummy setup run.
    isDummyRun = True
    wait(1.0)
    startCapture(isDummyRun, countTime, scanType, scanIOC, detIOCList, pvLogFile, logPVs, verbose)

    print 'Now ready to start the input scaler or pulse generator ....'
    
def startCapture(isDummyRun, countTime, scanType, scanIOC, detIOCList, pvLogFile, logPVs, verbose):
    """ Start the mapping mode capture.
    """
    waitTime = 1.0
    if isDummyRun:
        waitTime = 2.0

    for detIOC in detIOCList:
        # Start the file capture.
        pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'Capture')
        val2write = int(1)
        p_c.caputPV(pv2Set, val2write, pvLogFile, logPVs, verbose)

    wait(waitTime)

    for detIOC in detIOCList:
        # Trigger EraseSart.
        pv2Set = '%s%s%s' %(detIOC, ':', 'EraseStart')
        val2write = int(1)
        p_c.caputPV(pv2Set, val2write, pvLogFile, logPVs, verbose)

    wait(waitTime)

    # Test if this is a dummy run.  If so, do the pixeladvance.
    if isDummyRun:
        for detIOC in detIOCList:
            # Trigger the pixel advance three times.
            for i in np.arange(3):
                pv2Set = '%s%s%s' %(detIOC, ':', 'NextPixel')
                val2write = int(1)
                p_c.caputPV(pv2Set, val2write, pvLogFile, logPVs, verbose)
        print "Finished dummy scan ..."
    wait(waitTime)
    
    for detIOC in detIOCList:
        # Stop the acquisition.
        pv2Set = '%s%s%s' %(detIOC, ':', 'StopAll')
        val2write = int(1)
        p_c.caputPV(pv2Set, val2write, pvLogFile, logPVs, verbose)

        # Make sure that the file capture has stopped.
        pv2Get = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'Capture')
        retVal = bool(p_c.cagetPV(pv2Get, verbose))

    checkScanStatus(scanType,
                    countTime,
                    scanIOC,
                    detIOCList)
    
    pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'Capture')
    val2write = int(0)
    p_c.caputPV(pv2Set, val2write, pvLogFile, logPVs, verbose)
    
def disableAutoApply(detIOCList,
                     dxpVer,
                     pvLogFile,
                     logPVs,
                     verbose):
    """ Disable auto apply if possible.
    """
    # If the DXP version is > '2_11', we can cheat and save time by setting the autoapply.
    if (dxpVer == '3_0') ^ (dxpVer == '3_1'):
        for detIOC in detIOCList:
            
            pv2Get = '%s%s%s' %(detIOC, ':', 'AutoApply')
            storAutAppl = p_c.cagetPV(pv2Get, verbose)

            # Test if auto apply is set to yes.
            if storAutAppl == 1:
                # It is, so set it to no.
                pv2Set = '%s%s%s' %(detIOC, ':', 'AutoApply')
                val2Write = int(0)
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

def enableAutoApply(detIOCList,
                    dxpVer,
                    pvLogFile,
                    logPVs,
                    verbose):
    """ Enable autoapply and read the parameters into the xmap.
    """
    
    # If the DXP version is > '2_11', we must re-enable the auto apply.
    if (dxpVer == '3_0') ^ (dxpVer == '3_1'):
        # It is, so set it to yes.

        for detIOC in detIOCList:

            pv2Get = '%s%s%s' %(detIOC, ':', 'AutoApply')
            storAutAppl = p_c.cagetPV(pv2Get, verbose)
            # Auto apply must have already been set to 0, otherwise there is not point in re-setting it.
            if storAutAppl == 0:
    
                # First poke the apply button.
                pv2Set = '%s%s%s' %(detIOC, ':', 'Apply')
                val2Write = int(1)
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

                # Now set auto apply to yes.
                pv2Set = '%s%s%s' %(detIOC, ':', 'AutoApply')
                val2Write = int(1)
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)


def checkAssertions(dxpVer):
    """ Check fundamental assertions for the system.
    """
    assert (dxpVer == '2_11') ^ (dxpVer == '3_0') ^ (dxpVer == '3_1')


def stopIOCs(detIOCList, pvLogFile, logPVs, verbose):
    """ Make sure that the IOCs are stopped before the scan starts.
    """
    for detIOC in detIOCList:
        pv2Set = '%s%s%s' %(detIOC, ':', 'StopAll')
        val2Write = int(1)
        p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

def checkConfigs(params):
    """ Check the configuration.
    """
    # Check the scan type.
    checkScanType(params.scanType)

    # Check the DXP version.
    checkDXPVer(params.dxpVer)

    # Print to screen that the scan is starting.
    print "Starting the scan ..."

    # Initialize the PV log file assuming therre is NOT one.
    pvLogFile = None
    
    # Print base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    print 'Timestamped data dir will be written to %s ...' %(params.outBase)

    # Specify timestamp for file that stores list of of PVs. 
    # Also, add the time stamp to the parameters object.
    params.timeStamp = t_s.TimeStamp().getTimeStamp()
                    
    # Join the base and timestamp to form the dir path.
    # Also, add the output directory string to the parameters object.
    params.outDirStr = os.path.join(params.outBase, params.timeStamp)
                    
    # Make a time stamp directory to write the data to
    mkOutDirs(params.outDirStr, params.detIOCList, params.timeStamp)

    # Generate the string for the file that logs the PVs written.
    # Also, add the string to the parameters object.
    params.pvLogStr = os.path.join(params.outDirStr, 'pvList.txt')

    if params.logPVs:
        # Open the output file to log the PVs to
        pvLogFile = p_c.setFile(params.pvLogStr)

    return params, pvLogFile
     
def initialize(params):
    """ Initialize the acquisition parameters.
    """

    params, pvLogFile = checkConfigs(params)
    
    #################################
    # Set up the basic parameters.. #
    #################################

    # Print to screen that the PVs are being set.
    print "Setting PVs for scan ..."


    # Set the read back PVs to their usual values.
    # These are the same for all scans.
    for detIOC in params.detIOCList:
        setReadBack(detIOC, params.dxpVer, pvLogFile, params.logPVs, params.verbose)
    

    if params.initDXPs:

        # Disable auto apply.
        disableAutoApply(params.detIOCList,
                         params.dxpVer,
                         pvLogFile,
                         params.logPVs,
                         params.verbose)

        # Config preamplifier parameters.
        for detIOC in params.detIOCList:
            configPreamps(detIOC, params.dxpVer, params.detector, pvLogFile, params.logPVs, params.verbose)

        # Configure energy, trigger and baseline parameters.
        for detIOC in params.detIOCList:
            configDXPFilters(detIOC, params.dxpVer, params.detector, pvLogFile, params.logPVs, params.verbose)
                
    # Check assertions that need to be checked.
    checkAssertions(params.dxpVer)

    ###################################
    # Now go and do the desired scan. #
    ###################################

    # Also need to set the mode which depends on the IOC.
    assert params.doInit != None

    if params.doInit ==True:
        setMode(params.trigOnScaler,
                params.detIOCList,
                params.scanIOC,
                params.mcaIOC,
                params.scanType,
                params.detector,
                params.countTime,
                params.dxpVer,
                pvLogFile,
                params.logPVs,
                params.verbose,
                params.numChans)

    # Enable auto apply and set the PVs.
    enableAutoApply(params.detIOCList,
                    params.dxpVer,
                    pvLogFile,
                    params.logPVs,
                    params.verbose)
        
    if params.scanType == 'wait-for-mcas':
        # Do the wait-for-mcas style scan.
        waitForMCAsAcquis(params, pvLogFile)
    elif params.scanType == 'mca-map':
        # Do the mca-map style scan.
        mcaMapAcquis(params, pvLogFile)
    
    return params, pvLogFile


def acquire(scanType,
            scanIOC,
            countTime,
            detIOCList,
            detector,
            pvLogFile,
            logPVs,
            verbose,
            count,
            outBase,
            timeStamp):
    """ Start the acquisition.
    """

    
    if (scanType == 'wait-for-mcas') ^ (scanType == 'mca-spec'):
        # Trigger the scan1 record.
        if detector == 'ele100':
            scanIOC = 'SR12ID01HU02IOC01'
            
        pv2Set = '%s%s%s' %(scanIOC, ':', 'scan1.EXSC')

        val2Write = int(1)
        p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
        
    elif scanType == 'mca-map':
        # Trigger the Erase/Start for each IOC.
        val2Write = int(1)
        
        for detIOC in detIOCList:
            pv2Set = '%s%s%s%s%s' %(detIOC, ':', 'netCDF1', ':', 'Capture')
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
            pv2Set = '%s%s%s' %(detIOC, ':', 'EraseStart')
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
            
    print 'Acquiring ...'
   
    # Check that the scan is complete.
    checkScanStatus(scanType, countTime, scanIOC, detIOCList)

    # Save the spectrum
    pv2Get = '%s%s%s' %(scanIOC, ':', 'mca1')
    spec = p_c.cagetPV(pv2Get, verbose)
    fileName = 'spec_%d.npy' %(count)
    filePath = os.path.join(outBase, timeStamp, fileName)
    np.save(filePath, spec)
    print 'Saving spectrum %s ...' %(filePath)

def finalize(logPVs, pvLogFile):
    """ Close the PV log file.
    """
    if logPVs:
        p_c.closeFile(pvLogFile)

def setMode(trigOnScaler,
            detIOCList,
            scanIOC,
            mcaIOC,
            scanType,
            detector,
            countTime,
            dxpVer,
            pvLogFile,
            logPVs,
            verbose,
            numChans):

    """ The system can either trigger on a scaler (pulse generator) or not.
    """

    # Check if the scaler is being used.
    if trigOnScaler:

        print "Trigger mode is to trigger on scaler ..."
        
        # It is, so set the real and live times appropriately.

        """ If the 100 element detector is being used, the strange
             name for the scan IOC that controls the scaler must be set. 
        """
        
        if detector == 'ele100':

            # Set number of points to scan to 1.
            pv2Set = '%s' %('SR12ID01HU02IOC01:scan1.NPTS')
            val2Write = int(1)
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Clear out the existing configuration of Scan1.DNNPV.
            for i in np.arange(12) + 1:
                # Need to set the scaler time.
                if i <= 4:
                    val2Write = ''
                    pv2Set = '%s%01d%s' %('SR12ID01HU02IOC01:scan1.R', i, 'PV')
                    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
                    pv2Set = '%s%01d%s' %('SR12ID01HU02IOC01:scan1.P', i, 'PV')
                    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
                    pv2Set = '%s%01d%s' %('SR12ID01HU02IOC01:scan1.T', i, 'PV')
                    p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
                    
                pv2Set = '%s%02d%s' %('SR12ID01HU02IOC01:scan1.D', i, 'PV')
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Need to set the PV trigger.
            pv2Set = '%s' %('SR12ID01HU02IOC01:scan1.T1PV')
            val2Write = str('SR12ID01DET01:GateAcquireTrigger.PROC')
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
                
            # Need to set the scaler time.
            pv2Set = '%s' %('SR12ID01HU02IOC01:scaler1.TP')
            # The time to write is the count time.
            val2Write = countTime
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Also need to make sure that the scaler mode is oneshot.
            pv2Set = '%s' %('SR12ID01HU02IOC01:scaler1.CONT')
            # The time to write is the count time.
            val2Write = int(0)
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

        # Loop over the detector IOC(s).
        for detIOC in detIOCList:

            # The parameter does not exist so do not write it.
            if (dxpVer == '3_0') ^ (dxpVer == '3_1'):
                # Set mode to 'No preset'.
                pv2Set = '%s%s%s' %(detIOC, ':', 'PresetMode')
                # The count time will be determined by the scaler, so real time is 0.0.
                val2Write = 'No preset'
                # Now we have the value, write the PV.
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Set the real time to 0.0.
            pv2Set = '%s%s%s' %(detIOC, ':', 'PresetReal')
            # The count time will be determined by the scaler, so real time is 0.0.
            val2Write = 0.0
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # The live time should also be 0.0.
            pv2Set = '%s%s%s' %(detIOC, ':', 'PresetLive')
            # The count time will be determined by the scaler, so real time is 0.0.
            val2Write = 0.0
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
            
    else:

        """ It is an acquisition that waits for the call back, so
            PresetReal = countTime.
        """

        print "Trigger mode is to wait for call-back ..."
        
        
        if detector == 'ele100':
           
            """ Need to set the scaler autocount time to be very large so it
                doesn't interfere with the measurement.
                If the detector is a different one, the scaler card is ot connected and
                so the two values set below are ignored anyway.
            """
            pv2Set = '%s' %('SR12ID01HU02IOC01:scaler1.TP1')
            # The time to write is the count time.
            val2Write = float(1000.0)
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # Also need to make sure that the scaler mode is autocount.
            pv2Set = '%s' %('SR12ID01HU02IOC01:scaler1.CONT')
            # The time to write is the count time.
            val2Write = int(1)
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

        # Now set the other PVs that are not dependent on the scaler.

        # Set up the MCA params.
        mcaList = getMCAList(detector, numChans)
        print 'The mcas that will be used as detectors in the scan record are:'
        for mca in mcaList:
            print '          %s' %(mca)
        print '...'
    
        # Set the parameters to scan in the wait-for-mcas style using the scan record directly.
        setWaitForMCAs(mcaList,
                       scanIOC,
                       mcaIOC,
                       detIOCList,
                       detector,
                       pvLogFile,
                       logPVs,
                       verbose,
                       dxpVer)

        for detIOC in detIOCList:
            # The live time should also be 0.0.
            pv2Set = '%s%s%s' %(detIOC, ':', 'PresetLive')
            # The count time will be determined by the scaler, so real time is 0.0.
            val2Write = 0.0
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            # At this point, we are not triggering off the scaler for a fixed time and then waiting for the call back.
     
            # Set the real time to countTime.
            pv2Set = '%s%s%s' %(detIOC, ':', 'PresetReal')
            # The count time will be determined by the scaler, so real time is 0.0.
            val2Write = countTime
            # Now we have the value, write the PV.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

            if (dxpVer == '3_0') or (dxpVer == '3_1'):
                # Set collection mode to 'MCA Spectra'.
                pv2Set = '%s%s%s' %(detIOC, ':', 'CollectMode')
                # The count time will be determined by the scaler, so real time is 0.0.
                val2Write = int(0)
                # Now we have the value, write the PV.
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)

                # Set mode to 'Real time'.
                pv2Set = '%s%s%s' %(detIOC, ':', 'PresetMode')
                # The count time will be determined by the scaler, so real time is 0.0.
                val2Write = 'Real time'
                # Now we have the value, write the PV.
                p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
    


          
def waitForMCAsAcquis(params, pvLogFile):
    
    # Assume that 'MCA spectra' is the default.
    collMode = 'MCA spectra'
    """ List mode variant is only set if collMode == 'List mapping', so leave as
        default 'E & Gate'.
    """
    
    #########################
    # Now write the values. #
    #########################

    if (params.dxpVer == '3_0') ^ (params.dxpVer == '3_1'):
    
        for detIOC in params.detIOCList:
            # Assume that 'MCA mapping' is the default.
            pv2Set = '%s%s%s' %(detIOC, ':', 'CollectMode')
            p_c.caputPV(pv2Set, collMode, pvLogFile, params.logPVs, params.verbose)
            
    # Set up to save the output data.
    if params.saveData:

        # Need to get check that the Cygwin version is being run.
        pv2Get = '%s%s%s' %(params.scanIOC, ':', 'saveData_status')
        retVal = p_c.cagetPV(pv2Get, params.verbose)      
        if retVal == 0:
            raise ValueError('You need to run the Cygwin .bat file for this ...')

        # Now set up the save data params.
        pv2Set = '%s%s%s' %(params.scanIOC, ':', 'saveData_fileSystem')
        """ Assumes that the local folder 'C:\\share' corresponds to the
            global '\\\SR12ID02IOC53\\share\\' folder.
        """
        val2Write = '%s%s' %('C:\\share\\', params.timeStamp)
        p_c.caputPV(pv2Set, val2Write, pvLogFile, params.logPVs, params.verbose)      

        # Reset the scan number.
        pv2Set = '%s%s%s' %(params.scanIOC, ':', 'saveData_scanNumber')
        val2Write = int(0)
        p_c.caputPV(pv2Set, val2Write, pvLogFile, params.logPVs, params.verbose)      


def mcaMapAcquis(params, pvLogFile):
    # Configure PVs that will NOT be iterated over.
     
    #############################
    # Set the MCA mapping mode. #
    #############################

    # Configure mapping mode parameters.
    print "Configuring mapping mode parameters ..."
    configDXPMapCont(params.detIOCList,
                     params.dxpVer,
                     params.detector,
                     params.countTime,
                     params.scanType,
                     params.scanIOC,
                     params.saveData,
                     params.timeStamp,
                     pvLogFile,
                     params.logPVs,
                     params.verbose)

    # Get the MCA list for the detector.
    


class Params:
    pass

if __name__ == '__main__':

    """ Running the code below shows how to configure
        the input parameters for a wait-for-mcas style acquisition.
        It will not perform the acquisition.
    """
    
    #################################
    # User defined params go below. #
    #################################
    
    # Create an instance of the Params object.
    # The attributes of this will have to become buttons.
    params = Params()
    
    # Spcify whether to write the PVs to file.
    params.logPVs = True

    # Spcify whether to store the data file.
    params.saveData = False

    # Spcify whether to print the PVs to screen.
    params.verbose = False
    
    """ Specify which detector.
        When running the scan, it can only be the EXCLUSIVE OR of the Vortex
        (detector = vortex), 10 element (detector = 'ele10') and 100 element (detector = 'ele100')
        detectors.
        More detectors can be added later.
    """
    params.detector = 'vortex'
                               
    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    params.dxpVer = '3_1'

    # Check that the user has specified only one detector and get the IOC strings.
    params.detIOCList, params.scanIOC, params.mcaIOC, params.numChans = getIOCs(params.detector, params.verbose)  

    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    params.outBase = '\\\SR12ID01IOC55\\share\\'

    print "Done ..."
