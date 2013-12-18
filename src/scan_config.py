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
import itertools as it
from copy import deepcopy
import acquis_params as acp

def getPV2ScanList(pvName, vals2Scan):
    """ Return a list of N lists, each with the PV and its value.
    """
    # The params should be a list, so assert this.
    assert type(vals2Scan) == list
    # Return a list of N lists, each with the PV and its value.
    listOfLists = [[pvName, val] for val in vals2Scan] 
    return listOfLists 

def add2List(pv2Set, pvVals, scanVarList):
    # Make a copy of the list before appending to it.
    nScanVarList = deepcopy(scanVarList)
    # Get a scannable object.
    pv2ScanList = getPV2ScanList(pv2Set, pvVals)
    # Add the scannable object to the list.
    nScanVarList.append(pv2ScanList)
    return nScanVarList

def unfoldList(listOfLists):
    """ Unfold the list of lists of PVs.
    """
    flatList = list(it.chain(*listOfLists))
    return flatList

def product(listOfLists):
    """ Generate all permutations of the list.
    """
    prodList = list(it.product(*listOfLists))
    return prodList

if __name__ == '__main__':

    """ Running the code below shows how to configure
        a scan over input parameters for a wait-for-mcas style acquisition.
    """
    #################################
    # User defined params go below. #
    #################################
    
    # Create an instance of the Params object.
    # The attributes of this will have to become buttons.
    params = acp.Params()
    
    # Spcify whether to write the PVs to file.
    params.logPVs = True

    # Spcify whether to store the data file.
    params.saveData = True

    # Spcify whether to print the PVs to screen.
    params.verbose = False
    
    """ Specify which detector.
        When running the scan, it can only be the EXCLUSIVE OR of the Vortex
        (detector = vortex), 10 element (detector = 'ele10') and 100 element (detector = 'ele100')
        detectors.
        More detectors can be added later.
    """
    params.detector = 'vortex'
                               
    # Check that the user has specified only one detector and get the IOC strings.
    params.detIOCList, params.scanIOC, params.mcaIOC = acp.getIOCs(params.detector, params.verbose)

    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    params.dxpVer = '3_1'

    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    #params.outBase = '%s%s%s%s' %('\\', '\\', params.detIOCList[0], '\\share\\')
    params.outBase = '\\\SR12ID01IOC55\\share\\'
 
    # Specify the count time in seconds.
    params.countTime = float(10.0)

    # Specify that the scaler will not be used for the trigger.
    params.trigOnScaler = False
    
    # Specify the scan type.
    params.scanType = 'wait-for-mcas'

    # Initialize the appropriate parameters.
    params, pvLogFile = acp.initialize(params)

    ################################################
    # Now perform a batch scan over a param space. #
    ################################################

    # Initialize an empty list to hold the dictionaries of scan vars.
    scanVarList = []

    ######################################
    # First, do the energy peaking time. #
    ######################################
    
    # Scan over energy filter peaking times.
    pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:PeakingTime')
    #  Define range to scan,  scan from 1 to 10.
    pvVals = list(np.arange(9) + 1)
    # Add the PV and its vals to the scannable list.
    scanVarList = add2List(pv2Set, pvVals, scanVarList)

    #################################
    # Next, do the energy gap time. #
    #################################

    # Scan over energy filter peaking times.
    pv2Set = '%s%s%s' %(params.detIOCList[0], ':', 'dxp1:GapTime')
    # Define range to scan, scan from 0.1 to 2.0 in steps of 0.2.
    pvVals = list(np.linspace(0,2,9))
    # Add the PV and its vals to the scannable list.
    scanVarList = add2List(pv2Set, pvVals, scanVarList)
    
    ###################################################
    # Now, generate a scan list for the combinations. #
    ###################################################

    # Get all combinations of the parameters.
    scanVarList = product(scanVarList)
    
    # Close the PV log file, if used.
    acp.finalize(params.logPVs, pvLogFile)

    print "Done ..."
