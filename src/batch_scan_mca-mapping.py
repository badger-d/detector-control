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

def doBatchScan(scanType, scanIOC, countTime, detIOCList, detector, pvLogFile, logPVs, verbose, pix2Run):
    # Set the number of pixels for the run.
    for detIOC in detIOCList:
        pv2Set = '%s%s%s' %(detIOC, ':', 'PixelsPerRun')
        # Set the PV to the val.
        p_c.caputPV(pv2Set, pix2Run, pvLogFile, params.logPVs, params.verbose)
    # Do the desired scan.
    a_p.acquire(scanType, scanIOC, countTime, detIOCList, detector, pvLogFile, logPVs, verbose)
        
if __name__ == '__main__':

    """ Running the code below shows how to configure
        the input parameters for a mapping mode style
        acquisition.
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
    #params.detector = 'vortex'
    params.detector = 'ele100'
                               
    """ Specify which version of the DXP software.
        When running the scan, it can only be the EXCLUSIVE OR of
        DXP version 2_11 and 3_1.
    """
    params.dxpVer = '3_1'

    # Check that the user has specified only one detector and get the IOC strings.
    params.detIOCList, params.scanIOC, params.mcaIOC, params.numChans = a_p.getIOCs(params.detector, params.verbose)  

    # Specify base name of dir (WITH the trailing slash) to store list of of PVs.
    # For Windows, you must specify double slash i.e. 'C:\\epics\\test'
    params.outBase = '\\\SR12ID01IOC53\\share\\'
    
    # Specify the REAL count time in seconds.
    params.countTime = float(1.0)

    # Set the mode.
    params.trigOnScaler = True

    # Specify the scan type.
    params.scanType = 'mca-map'

    # Flag whether to initialize the DXP values.
    params.initDXPs = False

    # Set the number of pixels to run.
    params.pix2Run = int(256)

    # Initialize the appropriate parameters.
    params, pvLogFile = a_p.initialize(params)

    ################################################
    # Now perform a batch scan over a param space. #
    ################################################

    # Initialize an empty list to hold the dictionaries of scan vars.
    scanVarList = []

    # Now run the batch scan.
    doBatchScan(params.scanType,
                params.scanIOC,
                params.countTime,
                params.detIOCList,
                params.detector,
                pvLogFile,
                params.logPVs,
                params.verbose,
                params.pix2Run)

    # Close the PV log file, if used.
    a_p.finalize(params.logPVs, pvLogFile)

    print "Done ..."
    #import netCDF4
    #from netCDF4 import Dataset
    #fPath = 'F:\\workspace\\element\\2012-10-01_15.33.56.187000\\SR12ID01IOC55_1.nc'
    #rootgrp = Dataset(fPath, 'r', format='NETCDF4')
    #rootgrp.file_format
    
