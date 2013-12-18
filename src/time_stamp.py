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
import datetime as dt
import threading as th

class TimeStamp(object):
    def __init__(self):
        self.lock = th.Lock()
        self.prev = None
        self.count = 0
        self.prevStr = None
        
    def getTimeStamp(self):
        with self.lock:
            ts = str(dt.datetime.now())
            if ts == self.prev:
                ts +='.%04d' % self.count
                self.count += 1
            else:
                self.prev = ts
                self.prevStr = self.makeAsString()
                self.count = 1
            return self.prevStr

    def makeAsString(self):
        splitTS = self.prev.split()
        strTS = ''.join([splitTS[0], '_', splitTS[1]])
        strTS = strTS.replace(':', '.')
        return strTS
    
if __name__ == '__main__':
    print "Getting time stamp ..."
    ts = TimeStamp()
    print "Timestamp string is %s." %ts.getTimeStamp()
