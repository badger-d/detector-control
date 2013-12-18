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
import numpy as np
sys.path.append("C:\Users\XAS\Desktop\element\src")
import acquis_params as a_p
import single_acquis as s_a
import pv_control as p_c
import scan_config as s_c

def doBatchScan(scanType, scanIOC, countTime, detIOCList, detector, pvLogFile, logPVs, verbose, scanPVList, outBase, timeStamp):
    for count, line in enumerate(scanPVList):
        # Loop over the variables (PVs) to scan.
        for pv2Set, val2Write in line:
            # Set the PV to the val.
            p_c.caputPV(pv2Set, val2Write, pvLogFile, logPVs, params.verbose)
            print 'Changed %s ...' %(pv2Set)
        # Do the desired scan.
        a_p.acquire(scanType, scanIOC, countTime, detIOCList, detector, pvLogFile, logPVs, verbose, count, outBase, timeStamp)
        
if __name__ == '__main__':

    """ Running the code below shows how to configure
        the input parameters for a rivers style acquisition
        and then to perform a batch scan over a paraameter
        space e.g. varying the shaping time.
    """

    #################################
    # User defined params go below. #
    #################################

    # Create an instance of the Params object.
    # The attributes of this will have to become buttons.
    params = a_p.Params()

    # Do the initialisation.
    # This only needs to be done the first time around.
    params.doInit = False
    
    # Spcify whether to write the PVs to file.
    params.logPVs = True

    # Spcify whether to store the data file.
    # The IOCs were not built under Cygwin so save data does not work.
    params.saveData = False

    # Spcify whether to print the PVs to screen.
    params.verbose = False
    
    """ Specify which detector.
        When running the scan, it can only be the EXCLUSIVE OR of the Vortex
        (detector = vortex), 10 element (detector = 'ele10') and 100 element (detector = 'ele100')
        detectors.
        More detectors can be added later.
    """
    params.detector = 'ele36'
                               
    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    params.dxpVer = '2_11'

    # Check that the user has specified only one detector and get the IOC strings.
    params.detIOCList, params.scanIOC, params.mcaIOC, params.numChans = a_p.getIOCs(params.detector, params.verbose)  

    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    params.outBase = '\\\SR12ID01IOC56\\share\\'
    
    # Specify the REAL count time in seconds.
    params.countTime = float(10.0)

    # Set the mode.
    params.trigOnScaler = False

    # Specify the scan type.
    params.scanType = 'wait-for-mcas'

    # Flag whether to initialize the DXP values.
    params.initDXPs = False

    # Initialize the appropriate parameters.
    params, pvLogFile = a_p.initialize(params)
    
    ################################################
    # Now perform a batch scan over a param space. #
    ################################################

    # Initialize an empty list to hold the dictionaries of scan vars.
    scanVarList = []

    ######################################
    # First, do the energy peaking time. #
    ######################################
    
    # Scan over energy filter peaking times.
    if params.dxpVer == '2_11':
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1.PKTIM')
    else:
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:PeakingTime')
        
    #  Define range to scan,  scan from 1 to 10.
    pvVals = [1, 2, 4, 8, 12]
    # Add the PV and its vals to the scannable list.
    scanVarList = s_c.add2List(pv2Set, pvVals, scanVarList)

    #################################
    # Next, do the energy gap time. #
    #################################

    # Scan over energy filter gap times.
    if params.dxpVer == '2_11':
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1.GAPTIM')
    else:
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:GapTime')

    # Define range to scan, scan from 0.1 to 2.0 in steps of 0.2.
    pvVals = [0.1, 0.2, 0.3, 0.5, 1.0]
    # Add the PV and its vals to the scannable list.
    scanVarList = s_c.add2List(pv2Set, pvVals, scanVarList)
    
    ########################################################
    # Next, do the energy max width for pileup inspection. #
    ########################################################

    # Scan over energy max width.
    if params.dxpVer == '2_11':
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1.MAXWIDTH')
    else:
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:MaxWidth')

    # Define range to scan, scan from 0.0 to 3.0 in steps of 0.25.
    pvVals = [0.1, 0.2, 0.5, 1.0, 2.0, 3.0]
    # Add the PV and its vals to the scannable list.
    scanVarList = s_c.add2List(pv2Set, pvVals, scanVarList)

    ########################################
    # Next, do the baseline filter length. #
    ########################################

    # Scan over baseline filter length.
    if params.dxpVer == '2_11':
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1.BASE_LEN')
    else:
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:BaselineFilterLength')

    # Define range to scan, scan from 512 to 16 in powers of 2.
    pvVals = [512, 256, 128, 64]
    pvVals.reverse()
    # Add the PV and its vals to the scannable list.
    scanVarList = s_c.add2List(pv2Set, pvVals, scanVarList)

    ####################################
    # Next, do the baseline threshold. #
    ####################################

    # Scan over energy filter peaking times.
    if params.dxpVer == '2_11':
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1.BASE_THRESH')
    else:
        pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:BaselineThreshold')

    # Define some baseline thresholds.
    pvVals = [0.2, 0.4, 0.8, 1.6]
    # Add the PV and its vals to the scannable list.
    scanVarList = s_c.add2List(pv2Set, pvVals, scanVarList)

    # Get all combinations of the parameters.
    scanVarList = s_c.product(scanVarList)

    # Now run the batch scan.
    doBatchScan(params.scanType,
                params.scanIOC,
                params.countTime,
                params.detIOCList,
                params.detector,
                pvLogFile,
                params.logPVs,
                params.verbose,
                scanVarList,
                params.outBase,
                params.timeStamp)

    # Close the PV log file, if used.
    a_p.finalize(params.logPVs, pvLogFile)

    print "Done ..."
