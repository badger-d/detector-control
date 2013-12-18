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
import acquis_params as a_p

def doSingleAcquis(params):
    """ Do the desired scan.
        No values / objects are returned.
        There will just be the output files.
    """
    # Acquire the data. 
    a_p.acquire(params, pvLogFile)
    
if __name__ == '__main__':

    """ Running the code below will perform a single
        rivers style acquisition.
    """
    
    #################################
    # User defined params go below. #
    #################################
    
    # Create an instance of the Params object.
    # The attributes of this will have to become buttons.
    params = a_p.Params()
    
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
                               
    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    params.dxpVer = '3_1'

    # Check that the user has specified only one detector and get the IOC strings.
    params.detIOCList, params.scanIOC, params.mcaIOC = a_p.getIOCs(params.detector, params.verbose)  

    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    params.outBase = '\\\SR12ID01IOC55\\share\\'
    
    # Specify the count time in seconds.
    params.countTime = float(5.0)

    # Specify that the scaler will not be used for the trigger.
    params.trigOnScaler = False

    # Specify the scan type.
    params.scanType = 'wait-for-mcas'

    # Initialize the appropriate parameters.
    params, pvLogFile = a_p.initialize(params)

    #####################################
    # Now perform a single acquisition. #
    #####################################
    doSingleAcquis(params)
  
    # Close the PV log file, if used.
    a_p.finalize(params.logPVs, pvLogFile)
    
    print "Done ..."
