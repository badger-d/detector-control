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

from traits.api import HasTraits, List, Button, Enum, on_trait_change, Array, Dict, Str, Instance
from traitsui.api import Item, VGroup, View, UItem, Group, HGroup
from chaco.api import Plot, ArrayPlotData, VPlotContainer, HPlotContainer, OverlayPlotContainer
from chaco.chaco_plot_editor import ChacoPlotEditor, ChacoPlotItem
from enable.api import Component, ComponentEditor
import numpy as np
import calibrate as c
import acquis_params as a_p

params = a_p.Params()

def convDetName(detStr):
    """ Convert the numan readable detector name to the
        abreviated string.
    """
    assert ((detStr == '100 element') ^ (detStr == '10 element') ^ (detStr == 'Vortex'))
    
    if detStr == '100 element':
        return 'ele100'
    elif detStr == '10 element':
        return 'ele10'
    return 'vortex'
    pass

class ImshowPlot(HasTraits):
    plot = Instance(HPlotContainer)
    
    def __init__(self):
        #The delegates views don't work unless we caller the superclass __init__
        super(ImshowPlot, self).__init__()
        
        container = HPlotContainer(padding=0, spacing=20)
        self.plot = container
        #make some 2D data for a colourmap plot
        xy_range = (-5, 5)
        x = np.linspace(xy_range[0], xy_range[1] ,100)
        y = np.linspace(xy_range[0], xy_range[1] ,100)
        X,Y = np.meshgrid(x, y)
        Z = np.sin(X)*np.arctan2(Y,X)
        
        #easiest way to get a CMapImagePlot is to use the Plot class
        ds = ArrayPlotData()
        ds.set_data('img', Z)
        
        img = Plot(ds, padding=40)
        img.img_plot("img",
                     xbounds = xy_range,
                     ybounds = xy_range)
        
        container.add(img)
        

class GUI(HasTraits):
    
    def __init__(self):
        self.detStr = '100 element'
        self.detector = 'ele100'
        
    # Define a button to initiate the calibration.
    calButton = Button()

    # Define a trait for the detector options.
    detOpts = Enum(('100 element', '10 element', 'Vortex'), 
                   cols   = 1
    )('Vortex')

    # Define a trait for the detector options.
    dxpOpts = Enum(('2_11', '3_0', '3_1'), 
                   cols   = 1
    )  

    # Define a trait for the detector options.
    trigOpts = Enum(('Yes', 'No'), 
                   cols   = 1
    )  

    # Define a trait for whether to log the PVs.
    logPVs = Enum(('Yes', 'No'), 
                  cols   = 1
    ) 
        
    # Define a trait for whether to save the calibration data.
    saveData = Enum(('Yes', 'No'),     
                    cols   = 1
    ) 
        
    # Define a trait for whether to print warnings to screen.  Default set to No.
    verbose = Enum('Yes', 'No',
                   cols   = 1
    )('No')     
   
    plot_type = Enum('line')
    xData = Array
    yData = Array
    container = Instance(HPlotContainer)

    # Default detector = 'Vortex'
    params.detector = 'vortex'
    
    def _detOpts_changed(self):
        # Check to see if the detector has been updated.
        if self.detOpts != self.detStr:
            # It has, so get the correponding abreviated name.
            params.detector = convDetName(self.detOpts)

    def _calButton_changed(self):
        # Pass the variables to the parameters object.
        params.logPVs = self.logPVs
        params.saveData = self.saveData
        params.detOpts = self.detOpts
        params.trigOnScaler = self.trigOpts

        # Now do the calibration.
        spectra = c.run(params)
        self._perform_calculations()
    
    
    def _perform_calculations(self):
        self.xData = np.linspace(-2*np.pi, 2*np.pi ,100)
        self.yData = self.xData**2
        self.intensity = np.asarray([[np.arange(3)], [np.arange(3)], [np.arange(3)]])
     
        self.container = ImshowPlot().plot
     

class Viewer():

    def __init__(self):
        
        # CheckListEditor for configuration parameters.
        self.confOptsGroup = VGroup(
                                Item( 'detOpts', style = 'simple',   label = 'Detector' ),
                                Item( 'dxpOpts', style = 'simple',   label = 'DXP version' ),
                                Item( 'trigOpts', style = 'simple',   label = 'Trigger on scaler' ),
                                label = 'Configure'
        )

        # CheckListEditor for calibration parameters.
        self.calOptsGroup = VGroup(
                               Item( 'logPVs', style = 'simple',   label = 'Log PVs' ),
                               Item( 'saveData', style = 'simple',   label = 'Save data' ),
                               Item( 'verbose', style = 'simple',   label = 'Print messages' ),
                               UItem( 'calButton', label = 'Gain match' ),
                               label = 'Calibrate'
        )    
        
        
        self.calPlotGroup = VGroup(ChacoPlotItem(
                                                 "xData", "yData",
                                                 type_trait="plot_type",

                                                 # Basic axis and label properties
                                                 show_label = False,
                                                 resizable = True,
                                                 orientation = "h",
                                                 x_label = "Index data",
                                                 y_label = "Value data",

                                                 # Plot properties
                                                 color = "green",
                                                 bgcolor = "white",

                                                 # Border, padding properties
                                                 border_visible = True,
                                                 border_width=1,
                                                 padding_bg_color = "lightgray"),                     
                                   
        )
                                   
        
        self.calImshowGroup = HGroup(Item('container',
                                        editor=ComponentEditor(),
                                        resizable=True, springy=True,
                                        show_label=False),
                                        springy=True
                                        )
        
        
        # Show the view with two tabs.
        self.view = View(
                         self.confOptsGroup,
                         self.calOptsGroup,
                         self.calPlotGroup,
                         self.calImshowGroup,
                         title = 'Detector Configurations',
                         #width=500, height=500,
                         resizable = True
        ) 
        
    





# Run if invoked from the command line.
if __name__ == '__main__':
    # Create the GUI:
    gui = GUI()
    v = Viewer()
    gui.configure_traits(view = v.view)

