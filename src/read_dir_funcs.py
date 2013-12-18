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

import os
import numpy as np
import itertools as it

def listDirCont(dirPath, keepPath = False):
    # Return a lis of files in dirPath.
    if not keepPath:
        return os.listdir(dirPath)
    return [dirPath + "/" + fileName for fileName in os.listdir(dirPath)]

def listDirs(dirPath):
    return [os.path.join(dirPath,name) for name in os.listdir(dirPath) if os.path.isdir(os.path.join(dirPath, name))]

def mkNewDir(dirPath, extStr):
    """ Make a directory to dump the ascii files made from the mda files.
    """
    # Get the parent dir of the dir that contains the mda files.
    parDir = dirPath.split(os.path.basename(dirPath))[0]
    
    # Get the base name of the dir that contains the mda files.
    base = os.path.basename(dirPath)
    
    # Make a new directory path with the extension '_ASCII'
    if extStr:
        baseExt = '%s%s' %(base, extStr)
    else:
        baseExt = base
    newDirPath = os.path.join(parDir, baseExt)
    
    # CHeck if the directory already exists.
    if os.path.exists(newDirPath):
        # The dir does exist so don't it.
        print 'The directory %s already exists ...' %(newDirPath)
        return newDirPath
    
    # The dir does not exist so make it. 
    os.makedirs(newDirPath)
    print 'Wrote directory %s ...' %(newDirPath)
    return newDirPath


def getData(dataLine):
    # Returns line of data.
    return np.float(list(dataLine).split())   

def getVarLines(headType, header):
    # Return the lines that have variable names in them.
    toKeep = []
    inRange = False
    if headType == "mda": 
        for line in header:
            if len(line) >= 5:
                if line[4][-1] == "]":
                    toKeep.append(getVars(headType, line))
    return toKeep

def getValid(dataLine, header, testArgs):
    if testArgs:
        assert type(testArgs) == list
        if (header):
            # Test if any null args are in the data.
            for arg in testArgs:
                if arg in dataLine:
                    return None, dataLine
    # Valid data.
    return True, dataLine   

def filterDirCont(fileList, filtStr, sort = False):
    # Filter fileList according to filtStr.
    if sort:
        return sorted([fileName for fileName in fileList if filtStr in fileName])
    else:
        return [fileName for fileName in fileList if filtStr in fileName]

def getVars(headType, line):
    if headType == "mda":
        if line[4] == "]":
            return line[3]
        else: 
            name = line[5].split(":")[1:][0][:-1]
            return name
      
def readData(fileName, toStrip, splitOn):
    # Run function as iterator.
    # Pass file descriptor.
    with open(fileName, 'rt') as fd:
        # Loop over lines in file.
        for line in fd:
            # Strip out white space.
            if toStrip:
                line = line.strip().strip()    
            parts = line.split(splitOn)
            yield parts, line
        