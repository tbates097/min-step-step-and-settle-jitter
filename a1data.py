# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 13:38:45 2022
Edited last on 6/21/2022 at 8:00 am

@author: shunn
#Modified by JStarr 12/28/23
#Modified by TB 01/12/2024
#Modified the ai0 data collection to allow selecting which axis the external sensor feedback comes in on
"""
from abc import ABC, abstractmethod
import csv
import sys
import traceback
import enum
import automation1 as a1
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal

from Logger import TextLogger

class mode(enum.Enum):
    
    #Specify a direction for the test
    Unidirectional = 1
    Bidirectional = 2
    
    #Specify the direction
    positive_direction = 3
    negative_direction = 4
    
    #specify process window for move and settle
    forward_window = 5
    centered_window = 6
    backward_window = 7
    
    #speciify array to be modified for filtering
    pos_com = 8
    pos_fbk = 9
    pos_err = 10
    vel_com = 11
    vel_fbk = 12
    vel_err = 13
    ai0 = 14
    
    #specify error metric to use for move and settle
    MAE = 15
    MSD  = 16
    MPE = 17
    
class a1data(ABC):
    '''
    Abstract base class designed to be the starting point for every ASME B5.64 related test
    Use as a general structure for all of the tests prescribed in B5.64
    '''
    
    
    #Axis and sample rate are required parameters for an a1data subclass instance
    @abstractmethod
    def __init__(self, axis, sample_rate, probe_axis, probe_dist, **kwargs):
        self.axis = axis
        self.sample_rate = sample_rate
        self.probe_axis = probe_axis
        self.probe_dist = probe_dist
        
        #These values should not be adjusted by the user, results of the test method
        self.n = 0 #number of data points
        self.time_array = []
        self.pos_com = []
        self.pos_fbk = []
        self.pos_err = []
        self.vel_com = []
        self.vel_fbk = []
        self.vel_err = []
        self.ai0 = []
        
        default_kwargs = {'units' : 'mm', 
                          'speed' : 5, #units/second 
                          'ramp_type' : a1.RampType.Linear,
                          'ramp_value' : 100, #units/second/second
                          'ramp_type_arg' : 100, #Percent for an a1.RampType.SCurve
                          }
        
        #Update defaults if they exist
        kwargs = {**default_kwargs,**kwargs}
        
        self.units = kwargs['units']
        self.error_units = kwargs['error_units']
        self.speed = kwargs['speed']
        self.ramp_type = kwargs['ramp_type']
        self.ramp_value = kwargs['ramp_value']
        self.ramp_type_arg = kwargs['ramp_type_arg']
        self.import_data = kwargs['import_data']
        self.text_widget = kwargs['text_widget']
    
    def setup_error_logging(self):
        # Redirect sys.stderr to the text widget
        sys.stderr = TextLogger(self.text_widget)

    def log_exception(self, exc_type, exc_value, exc_traceback):
        """Custom exception handler to log exceptions to the Text widget."""
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(error_message)  # This will be redirected to the Text widget

    #Basic Data Set up to be used for every proper B5.64 test, Function needs to generate arrays for time/position/analog data
    @abstractmethod
    def test(self, controller : a1.Controller):
        '''
        Method to perform the corresponding Automation 1 test in compliance with ASME B5.64
        
        *** Make sure to initialize self.n before calling this function ***

        Parameters
        ----------
        controller : a1.Controller.connect()
            The active Automation1 controller that should be performing the specified test

        Returns
        -------
        data_config : a1.DataCollectionConfiguration
            The data configuration for the automation 1 data collection

        '''
        
        #update a1data units based on controller
        self.units = controller.runtime.parameters.axes[self.axis].units.unitsname.value 
        
        #Set up speed
        controller.runtime.commands.motion_setup.setupcoordinatedspeed(self.speed,) 
        
        #Make sample_rate the correct class type for automation 1
        if self.sample_rate == 1000:
            self.__freq = a1.DataCollectionFrequency.Frequency1kHz
        elif self.sample_rate == 10000:
           self.__freq = a1.DataCollectionFrequency.Frequency10kHz
        elif self.sample_rate == 20000:
            self.__freq = a1.DataCollectionFrequency.Frequency20kHz
        elif self.sample_rate == 100000:
            self.__freq = a1.DataCollectionFrequency.Frequency100kHz
        elif self.sample_rate == 200000:
            self.__freq = a1.DataCollectionFrequency.Frequency200kHz
        else:
            raise ValueError('Frequency is invalid. Choose from available Automation 1 Options')
        #Make sure there are enough points in each sample    
        if self.n < 100:
            raise ValueError('Minimum threshold of 100 data points not met')
            
        #Set up motion parameters
        controller.runtime.commands.motion_setup.setuptasktargetmode(a1.TargetMode.Absolute) 
        controller.runtime.commands.motion_setup.setupcoordinatedramptype(self.ramp_type, self.ramp_type_arg,
                                                                             self.ramp_type, self.ramp_type_arg)
        
        controller.runtime.commands.motion_setup.setupcoordinatedrampvalue(a1.RampMode.Rate, self.ramp_value, 
                                                                              a1.RampMode.Rate, self.ramp_value)
        controller.runtime.commands.motion.enable(self.axis,1)
      # controller.runtime.commands.motion.home(self.axis, 1) #commented out so it does not home and crash probe

        #Data configurations. These are how to configure data collection parameters
        if self.probe_axis == 'None':
            data_config = a1.DataCollectionConfiguration(self.n, self.__freq)  #Freq should be 20x the max frequency required by end process
            data_config.system.add(a1.SystemDataSignal.DataCollectionSampleTime)
            data_config.axis.add(a1.AxisDataSignal.PositionCommand, self.axis)
            data_config.axis.add(a1.AxisDataSignal.PositionFeedback, self.axis)
            data_config.axis.add(a1.AxisDataSignal.PositionError, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityCommand, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityFeedback, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityError, self.axis)
            data_config.axis.add(a1.AxisDataSignal.AnalogInput0, self.axis)
        else:
            data_config = a1.DataCollectionConfiguration(self.n, self.__freq)  #Freq should be 20x the max frequency required by end process
            data_config.system.add(a1.SystemDataSignal.DataCollectionSampleTime)
            data_config.axis.add(a1.AxisDataSignal.PositionCommand, self.axis)
            data_config.axis.add(a1.AxisDataSignal.PositionFeedback, self.axis)
            data_config.axis.add(a1.AxisDataSignal.PositionError, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityCommand, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityFeedback, self.axis)
            data_config.axis.add(a1.AxisDataSignal.VelocityError, self.axis)
            
            if self.units == 'deg':
                for axis in self.probe_axis:
                    data_config.axis.add(a1.AxisDataSignal.AnalogInput0, self.axis)
                    data_config.axis.add(a1.AxisDataSignal.AnalogInput0, self.axis)
            else:
                data_config.axis.add(a1.AxisDataSignal.AnalogInput0, self.probe_axis)
        ###########TB
        
        return data_config


    def to_dataframe(self):
        '''
        Uses internal properties to generate a dataframe of automation 1 data from a B5.64 test

        Returns
        -------
        dat : pd.DataFrame
            Dataframe consisting of all of the information collected from automation 1

        '''
        d = { 'Time (seconds)': self.time_array, 
             ' PosCmd ({}) {}'.format(self.axis, self.units) : self.pos_com, 
             ' PosFbk ({}) {}'.format(self.axis, self.units) : self.pos_fbk,
             ' PosErr ({}) {}'.format(self.axis, self.units) : self.pos_err,
             ' VelCmd ({}) {}'.format(self.axis, self.units) : self.vel_com,
             ' VelFbk ({}) {}'.format(self.axis, self.units) : self.vel_fbk,
             ' VelErr ({}) {}'.format(self.axis, self.units) : self.vel_err,
             ' Ain 0 ({})'.format(self.axis) : self.ai0,
             ' Ain 0 ({})'.format(self.probe_axis) : self.ai0} 
        dat = pd.DataFrame(data = d)
        return dat
    
    def calculate_angular_step(self, sens, results):
        print(results)
        # Retrieve the lists of data points from the probes
        probe_1 = results.axis.get(a1.AxisDataSignal.AnalogInput0, self.probe_axis[0]).points
        probe_2 = results.axis.get(a1.AxisDataSignal.AnalogInput0, self.probe_axis[1]).points
        
        probe_1 = [i * sens for i in probe_1]
        probe_2 = [i * sens for i in probe_2]
        
        # Initialize a list to store the calculated angular steps
        angular_steps = []
        
        # Iterate through the data points of probe_1 and probe_2
        for i, e in zip(probe_1, probe_2):
            # Calculate the opposite side of the triangle
            opp = abs(i - e)
            
            # Adjacent side of the triangle is the distance between the probes
            adj = self.probe_dist
            
            # Calculate the angle in radians
            theta_rad = math.atan(opp / adj) if adj != 0 else 0  # Avoid division by zero
            
            if self.error_units == 'arcsec':
                # Convert the angle to degrees
                theta_deg = math.degrees(theta_rad)
                theta_arcsec = theta_deg * 3600
                # Store the calculated angle in degrees
                angular_steps.append(theta_arcsec)
                
            else:
                theta_urad = theta_rad * 1e6
                # Store the calculated angle in radians
                angular_steps.append(theta_urad) 
                
        return angular_steps
    
    def populate(self, sens, results = None, file = None, dataframe = None):
        if self.import_data == True:
            results = None
        if results is not None:
            #self.time_array = np.linspace(0, self.step_time, self.n, endpoint = False)
            self.time_array = np.array(results.system.get(a1.SystemDataSignal.DataCollectionSampleTime).points)
            self.time_array -= self.time_array[0]
            self.time_array *= .001 #msec to sec
            self.time_array = self.time_array.tolist()
            for i, time in enumerate(self.time_array):
                self.time_array[i] = i/self.sample_rate
            if self.probe_axis == 'None':
                self.pos_com = results.axis.get(a1.AxisDataSignal.PositionCommand, self.axis).points
                self.pos_fbk = results.axis.get(a1.AxisDataSignal.PositionFeedback, self.axis).points
                self.pos_err = results.axis.get(a1.AxisDataSignal.PositionError, self.axis).points
                self.vel_com = results.axis.get(a1.AxisDataSignal.VelocityCommand, self.axis).points
                self.vel_fbk = results.axis.get(a1.AxisDataSignal.VelocityFeedback, self.axis).points
                self.vel_err = results.axis.get(a1.AxisDataSignal.VelocityError, self.axis).points
                self.ai0 = results.axis.get(a1.AxisDataSignal.AnalogInput0, self.axis).points
            else:
                self.pos_com = results.axis.get(a1.AxisDataSignal.PositionCommand, self.axis).points
                self.pos_fbk = results.axis.get(a1.AxisDataSignal.PositionFeedback, self.axis).points
                self.pos_err = results.axis.get(a1.AxisDataSignal.PositionError, self.axis).points
                self.vel_com = results.axis.get(a1.AxisDataSignal.VelocityCommand, self.axis).points
                self.vel_fbk = results.axis.get(a1.AxisDataSignal.VelocityFeedback, self.axis).points
                self.vel_err = results.axis.get(a1.AxisDataSignal.VelocityError, self.axis).points
                if self.units == 'deg':
                    self.ai0 = self.calculate_angular_step(results, sens)
                else:
                    self.ai0 = results.axis.get(a1.AxisDataSignal.AnalogInput0, self.probe_axis).points
            ##########TB
            conversion_factors = {
                # Length units
                ('mm', 'nm'): 1_000_000,
                ('mm', 'um'): 1_000,
                ('um', 'nm'): 1_000,
                ('um', 'um'): 1,
                
                # Angular units
                ('deg', 'arcsec'): 3_600,
                ('arcsec', 'deg'): 1/3_600,
                ('deg', 'μrad'): 17_453.29252,
                ('μrad', 'deg'): 1/17_453.29252,
                ('arcsec', 'μrad'): 4.848136811,
                ('μrad', 'arcsec'): 1/4.848136811,
                ('μrad', 'μrad'): 1,
                ('deg', 'deg'): 1,
                ('arcsec', 'arcsec'): 1,
            }
            
            conversion_factor = conversion_factors.get((self.units, self.error_units))
            
            if conversion_factor:
                self.pos_com = [e * conversion_factor for e in self.pos_com]
                self.pos_fbk = [e * conversion_factor for e in self.pos_fbk]
                self.ai0 = [e * conversion_factor for e in self.ai0]
                    
        #populates object from a data file
        elif file is not None:
            data = pd.read_csv(file)
            if self.probe_axis == 'None':
                try:
                    self.time_array = data['Time (seconds)'].tolist()
                    self.pos_com = (data['PosCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data['PosFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data['PosErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.time_array = data['Time (sec)'].tolist()
                    self.pos_com = (data[' PosCmd ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data[' PosFbk ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data[' PosErr ({}) ({})'.format(self.axis, self.units)]).tolist()
                try:
                    self.vel_com = (data['VelCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data['VelFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data['VelErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.vel_com = (data[' VelCmd ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data[' VelFbk ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data[' VelErr ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
            else:
                try:
                    self.time_array = data['Time (seconds)'].tolist()
                    self.pos_com = (data['PosCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data['PosFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data['PosErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.time_array = data['Time (sec)'].tolist()
                    self.pos_com = (data[' PosCmd ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data[' PosFbk ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data[' PosErr ({}) ({})'.format(self.axis, self.units)]).tolist()
                try:
                    self.vel_com = (data['VelCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data['VelFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data['VelErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.vel_com = (data[' VelCmd ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data[' VelFbk ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data[' VelErr ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                self.ai0 = (data['Ain 0 ({})'.format(self.probe_axis)]).tolist()
            
            self.pos_fbk = [e - self.pos_com[0] for e in self.pos_fbk]
            self.pos_com = [e - self.pos_com[0] for e in self.pos_com]
            
        #Populates from a data frame
        elif dataframe is not None:
            data = dataframe
            if self.probe_axis == 'None':
                try:
                    self.time_array = data['Time (seconds)'].tolist()
                    self.pos_com = (data['PosCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data['PosFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data['PosErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.time_array = data['Time (sec)'].tolist()
                    self.pos_com = (data[' PosCmd ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data[' PosFbk ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data[' PosErr ({}) ({})'.format(self.axis, self.units)]).tolist()
                try:
                    self.vel_com = (data['VelCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data['VelFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data['VelErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.vel_com = (data[' VelCmd ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data[' VelFbk ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data[' VelErr ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
            else:
                try:
                    self.time_array = data['Time (seconds)'].tolist()
                    self.pos_com = (data[' PosCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data[' PosFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data[' PosErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.time_array = data['Time (sec)'].tolist()
                    self.pos_com = (data[' PosCmd ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_fbk = (data[' PosFbk ({}) ({})'.format(self.axis, self.units)]).tolist()
                    self.pos_err = (data[' PosErr ({}) ({})'.format(self.axis, self.units)]).tolist()
                try:
                    self.vel_com = (data[' VelCmd ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data[' VelFbk ({}) {}'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data[' VelErr ({}) {}'.format(self.axis, self.units)]).tolist()
                except KeyError:
                    self.vel_com = (data[' VelCmd ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_fbk = (data[' VelFbk ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                    self.vel_err = (data[' VelErr ({}) ({}/sec)'.format(self.axis, self.units)]).tolist()
                self.ai0 = (data['Ain 0 ({})'.format(self.probe_axis)]).tolist()
            
            self.pos_fbk = [e - self.pos_com[0] for e in self.pos_fbk]
            self.pos_com = [e - self.pos_com[0] for e in self.pos_com]

    def plot(self, *args : mode):
        #plot anything vs time
        for arg in args:
            d = self.choose_array(arg)
            plt.plot(self.time_array, d)
        plt.xlabel('Time (seconds)')

    def write_to_csv(self, filename : str):
        '''
        Creates a .csv file and writes the data to it

        Parameters
        ----------
        filename : str
            Name of the .csv to export the last run of data to

        Returns
        -------
        None

        '''
        if self.probe_axis == 'None':
            header = ['Time (seconds)', 
                      ' PosCmd ({}) {}'.format(self.axis, self.units),  
                      ' PosFbk ({}) {}'.format(self.axis, self.units), 
                      ' PosErr ({}) {}'.format(self.axis, self.units),
                      ' VelCmd ({}) {}'.format(self.axis, self.units),  
                      ' VelFbk ({}) {}'.format(self.axis, self.units), 
                      ' VelErr ({}) {}'.format(self.axis, self.units),
                      ' Ain 0 ({})'.format(self.axis)
                      ] #header with name of data signal
        else:
            header = ['Time (seconds)', 
                      ' PosCmd ({}) {}'.format(self.axis, self.units),  
                      ' PosFbk ({}) {}'.format(self.axis, self.units), 
                      ' PosErr ({}) {}'.format(self.axis, self.units),
                      ' VelCmd ({}) {}'.format(self.axis, self.units),  
                      ' VelFbk ({}) {}'.format(self.axis, self.units), 
                      ' VelErr ({}) {}'.format(self.axis, self.units),
                      ' Ain 0 ({})'.format(self.probe_axis)
                      ] #header with name of data signal
        
        with open(filename, 'w', encoding = 'UTF8', newline = '') as filename: #writes data to a csv file
            writer = csv.writer(filename)
            writer.writerow(header)
            writer.writerows(map(lambda a, b, c, d, e, f, g, h: [a, b, c, d, e, f, g, h], 
                                  self.time_array, 
                                  self.pos_com, 
                                  self.pos_fbk,
                                  self.pos_err,
                                  self.vel_com,
                                  self.vel_fbk,
                                  self.vel_err,
                                  self.ai0)) #based off desired signals
            
    def data_analysis(self):
        pass #will be overridden in each child class    
        
        
        
    #Filtering Functions Go Here
    def choose_array(self, data : mode):
        '''
        

        Parameters
        ----------
        data : a1data.mode
            The specified data signal to be filtered

        Returns
        -------
        d : list
            A reference to the specified data signal

        '''
        #Determine which array to perform the filtering on
        if data == mode.pos_com:
            return self.pos_com
        elif data == mode.pos_fbk:
            return self.pos_fbk
        elif data == mode.pos_err:
            return self.pos_err
        elif data == mode.vel_com:
            return self.vel_com
        elif data == mode.vel_fbk:
            return self.vel_fbk
        elif data == mode.vel_err:
            return self.vel_err
        elif data == mode.ai0:
            return self.ai0
        else:
            raise ValueError('Invalid data array specified')
        
    
    
    
    def butter(self,data:mode,omega_c : float ,order : int, var : str):
        '''
        Applies a butterworth filter to the specified data signal

        Parameters
        ----------
        data : a1data.mode
            The specified data signal to be filtered
        omega_c : float
            Cut-off frequency in Hz
        order : int
            The order filter to be applied
        var : str
            'high' or 'low'

        Returns
        -------
        None.

        '''
        #High or low pass butterworth filter
        d = self.choose_array(data)
        
        nyq = .5 * self.sample_rate #Setting the nyquist frequency
        normal_cutoff = omega_c/nyq
        b, a = signal.butter(order, normal_cutoff, btype = var, analog = False)
        d_copy = signal.filtfilt(b,a, d)
        
        #Need to structure code this way to actually alter the intended array rather than a copy of the array
        for i,e in enumerate(d_copy):
            d[i] = e
            
          
  
            
        
        
        

            
            

    
  

            
    
    