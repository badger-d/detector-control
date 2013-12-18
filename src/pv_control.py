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
import os
import subprocess as sb
import numpy as np
import time
import epics as ep

def setFile(fName):
    pvLogFile = open(fName, "w")
    pvLogFile.write("PV, Value \n")
    return pvLogFile

def closeFile(pvLogFile):
    # Close the PV log file.
    pvLogFile.close()

def writePV2File(outFile, pv2Set, pvVal):
    # Write the PV to file.
    outFile.write("%s, %s \n" %(pv2Set, pvVal))

def caputPV(pv2Set, pvVal, pvLogFile, log, verbose):
    """ Use the pyepics lib to write the PVs.
    """
    ep.caput(pv2Set, pvVal)
    # Test if val is to be logged to file.
    if log:
        writePV2File(pvLogFile, pv2Set, pvVal)
    # Test if val is to be printed to screen.
    if verbose:
        print "pv = %s, value = %s" %(pv2Set, pvVal)
    return pvVal

def cagetPV(pv2Get, verbose = True):
    """ Use the pyepics lib to write the PVs.
    """
    pvVal = ep.caget(pv2Get)
    # Test if val is to be printed to screen.
    if verbose:
        print "pv = %s, value = %s" %(pv2Get, pvVal)
    return pvVal

if __name__ == '__main__':
    """ Running the code below will test the
        setting and getting of PVs.
    """
    
    #################################
    # User defined params go below. #
    #################################
    
    # Spcify whether to write the PVs to file.
    logPVs = False

    # Spcify whether to print the PVs to screen.
    verbose = False
    
    # Specify the file to log PVs to.  For this test it is None.
    pvLogFile = None
    
    # Test setting of PVs
    detIOC = 'SR12ID01IOC55'
    pv2Set = '%s%s%s' %(detIOC, ':', 'ReadAll.SCAN')
    val2Write = str('Passive')
    caputPV(pv2Set, val2Write, pvLogFile, logPVs, verbose)
    
    # Test getting PV function.
    pv2Get = '%s%s%s' %(detIOC, ':', 'ReadAll.SCAN')
    cagetPV(pv2Get, verbose)
