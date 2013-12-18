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
from copy import deepcopy
import read_dir_funcs as rdf

def getFWHM(histo, maxIndex):
    """
    Function: Returns the FWHM of a histogram.  
    """
    nHisto = deepcopy(histo)
    maxVal = nHisto[maxIndex]
    # Get bins of histogram that are >= half the maximum height.
    bools = nHisto >= (maxVal * 0.5)
    return list(bools).count(True)

def printList(toPrintList):
    for statement in toPrintList:
        print statement

def getPeak(histo):
    """
    Function: Returns peak index and value.  
    """
    maxVal = np.max(histo)
    return np.float64(list(histo).index(maxVal)), np.float64(maxVal) 

def getCenters(hist, pkIndex, pkVal):
    """
    Function: Returns index of bins that could be the peak center.
    """
    # Make a copy of the histo.
    tmpHist = deepcopy(hist)

    # Get the chans that are > than half the heigh of the peak.
    bools = tmpHist < (0.5 * pkVal)

    # Get an array of bin numbers.
    lowChans = np.arange(len(hist))

    # Set the bins that are < FWHM to 0.
    lowChans[bools] = 0

    # Set the bins that are higher than the peak index to 0.
    lowChans[(pkIndex + 1):] = 0

    # Get an array of bin numbers.
    highChans = np.arange(len(hist))

    # Set the bins that are > FWHM to 0.
    highChans[bools] = 0

    # Set the bins that are higher than the peak index to 0.
    highChans[:pkIndex] = 0

    # Eliminate the zero channels from the low side.
    bools = lowChans > 0
    lowChansUse = lowChans[bools]

    # Eliminate the zero channels from the high side.
    bools = highChans > 0
    highChansUse = highChans[bools]

    # Reverse the low chans so the chan closest to the cetner of the peak is firset.
    #lows = list(reversed(lowChansUse))
    lows = list(lowChansUse)
    highs = list(highChansUse)
    return lows, highs


def getBackground(hist, bgVal, pkIndex):
    """
    Function: Returns index of bins that could be the peak center.
    """
    # Make a copy of the histo.
    tmpHist = deepcopy(hist)

    # Get the chans that are > than the bg.
    bools = tmpHist > bgVal

    # Get an array of bin numbers.
    lowChans = np.arange(len(hist))

    # Set the bins that are < bg to 0.
    lowChans[bools] = 0

    # Set the bins that are higher than the peak index to 0.
    lowChans[(pkIndex + 1):] = 0

    # Get an array of bin numbers.
    highChans = np.arange(len(hist))

    # Set the bins that are > bg to 0.
    highChans[bools] = 0

    # Set the bins that are higher than the peak index to 0.
    highChans[:pkIndex] = 0

    # Eliminate the zero channels from the low side.
    bools = lowChans > 0
    lowChansUse = lowChans[bools]

    # Eliminate the zero channels from the high side.
    bools = highChans > 0
    highChansUse = highChans[bools]

    # Reverse the low chans so the chan closest to the cetner of the peak is firset.
    lowBg = lowChansUse[-1]
    highBg = highChansUse[0]
   
    return lowBg, highBg

def getGaussian(max, x, cent, sig):
    return max * np.exp(-(x - cent)**2 / (2.0 * sig**2))

def fitGaussian(spec, cent, sig):
    """
    Function: Fits Gaussian.  
    """
    x = np.arange(len(spec))
    max = np.max(spec)
    gaus = getGaussian(max, x, cent, sig)
    return gaus

def movingaverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')


def fit(specToFit, 
        asciiDirPath,
        idx,
        numPksInRange, 
        pkRangeMin, 
        pkRangeMax, 
        bgRange, 
        numStDevs,
        savePlot,
        showPlot,
        verbose):
        
    # The index for the spectrum must be a real positive integer, so assert this.
    assert (type(idx) == int) and (idx >= 0)
    
    # Print a status update.
    if np.mod(idx, 1) == 0:
        print 'Current index is %i ...' %(idx)    
    
    # Make a copy of the input spectrum.
    y = np.asarray(deepcopy(specToFit))

    # Take a moving average to smooth the noise.
    y = movingaverage(y, 3)
    
    # The spectrum must be 1d.
    assert (len(y.shape) == 1)
    
    # Assume this is the spectral magnitudes and construct a bins axis.
    # Construct a bins axis.
    x = np.arange(len(y))
    
    # Store the total counts in the spectrum
    totCounts = np.sum(y)
    
    # Set min y-scale value to 0 counts.
    yMin = 0
    
    # Set max y-scale value.
    yMax = y.max()
        
    # Set min x-scale value to 0.
    xMin = 0
    
    # Set max x-scale value.
    xMax = len(x)
         
    # Initialize the dimensions of the subplot
    subDims = [5, 1]
    
    # Make a copy and zero everthing below the threshold.
    thresh = bgRange[0]
    yThresh = deepcopy(y)
    yThresh[:thresh] = 0

    # Cut out values outside of the peak range search.
    yThresh[:pkRangeMin] = 0
    yThresh[pkRangeMax:] = 0
    
    # Store the total counts in the threshold range of the spectrum
    totCountsThresh = np.sum(yThresh)
    
    # Get mean background.
    bg = deepcopy(y)

    # Set everything below the lower bound bg bin of the background spectrum to 0.
    bg[:thresh] = 0

    # Set everything above the upper bound bg bin of the background spectrum to 0.
    bgUpBound =  bgRange[-1]
    bg[bgUpBound:] = 0

    # Find the standard deviation of the background.
    meanBg = (bg.sum() / len(bg)) + 1.0
    maxLim = meanBg + (numStDevs * np.std(bg))

    #######################
    # Now do peak search. #
    #######################
    
    # Initialize a variable to count the number of peaks found.
    numPksFound = 0
    
    # Initialize a variable to count the number of times we go around the loop to stop infinite loops.
    loopCntr = 0
    
    # Initialize a list to store the fit parameters in.
    storeFit = []
    
    calPoints = []
    fits = []
    fwhms = []
    
    while True:

        if numPksFound == numPksInRange:
            print "Found %i peaks." %(numPksFound)
            break

        if yThresh.sum() < 50:
            # If not enough counts, don't fit.
            print "Not exough counts in spectrum."
            break
        
        if yThresh.max() < 3.0 * meanBg:
            # If not enough counts, don't fit.
            print "Not exough counts in peak."
            break
        
        if loopCntr > 6:
            # The code should not be used to find more than 6 peaks, so if the counter gets to 20, then stop.
            print "Stuck in loop, the number of peaks found is %i ..."  %(numPksFound)
            break
                
        # Get index of peak value in histo.
        pkIndex, pkVal = getPeak(y)

        # Get possible bin centers.
        lowCents, highCents = getCenters(yThresh, pkIndex, pkVal)
        
        # Get the width - take the smallest of the two in case there is a peak near by.
        width = len(highCents)
        if len(lowCents) < width:
            width = len(lowCents)

        # Add two to the width to make sure.
        width += 2

        centers = lowCents + highCents

        if len(centers) < 7 or width < 5:
            """ Because we start with the biggest peak and work to the smallest,
                if there are no centers to choose from and the peak has no width,
                end the peak search.
            """
            print "Peak width or number of centers is insufficient." 
            break

        # Get the middle of the list of centers.
        mid = int(np.floor((float(len(centers)) + 1.0) / 2.0))

        # Just keep the 7 low and high centers closest to the peak position.
        centers2Keep = centers[int(mid - 3):int(mid + 3)]
        
        # There are enough bin centers and there is enough width, so fit the peak.
        # This first fit is a rough one to determine the backgorund.
        gaus = fitGaussian(yThresh, centers[mid], width)
   
        # Get the points where the fit reaches the background.
        lowBg, highBg = getBackground(yThresh, maxLim, pkIndex)        

        # Get the line that defines the background.
        bgLine = np.linspace(yThresh[lowBg], yThresh[highBg], num = highBg - lowBg)

        # Set the background as a spectrum that can be used.
        bgSpec = np.zeros_like(yThresh)
        bgSpec[lowBg:highBg] = bgLine 

        # Get just the section of the spectrum to fit.
        spec2Fit = deepcopy(yThresh)[lowBg:highBg]

        diffFit = []
        diffVal = []
        
        for cent in centers2Keep:
            for wid in range(width - 5, width + 5):
                
                # Get the Gaussian with the desired parameters.
                gaus = fitGaussian(yThresh, cent, wid)
        
                # Add the background to the fit.
                gaus += bgSpec

                # Get just the section of the spectrum to fit.
                gaus2Fit = deepcopy(gaus)[lowBg:highBg]

                # Rescale by the area.
                gaus2Fit *=  (spec2Fit.max() / gaus2Fit.max())
                
                # Get the difference.
                diff = np.sum((spec2Fit - gaus2Fit) ** 2)
                # Append.
                diffFit.append(gaus2Fit)
                diffVal.append(diff)

        # Get the index of the best fir.
        minIndex = diffVal.index(np.min(diffVal))
        bestGaus = diffFit[minIndex]
        
        # Get centroid of best fit.
        calChan = list(bestGaus).index(bestGaus.max()) + lowBg
        
        # Get the FWHM of the peak.
        fwhms.append(np.float64(getFWHM(bestGaus, list(bestGaus).index(np.max(bestGaus)))))

        # Remove data from the existing fit so it can't be reused.
        yThresh[lowBg:highBg] = bgLine
        
        numPksFound += 1
        
        # Increment the loop counter by 1.
        loopCntr += 1

        calPoints.append(calChan)
        fits.append((lowBg + np.arange(len(bestGaus)), bestGaus))
        
        print "Peak center is %d ..." %(calChan)

    return calPoints, fits, fwhms

if __name__ == '__main__':

    print 'Done.'
