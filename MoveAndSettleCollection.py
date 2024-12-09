# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 10:57:47 2022
Edited last on 6/21/2022 at 8:00 am

@author: shunn, abakhtar
"""

import automation1 as a1
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
import os
import traceback
import plotly.graph_objs as go
import plotly.io as pio
import sys
import datetime
#sys.path.append('../')

import a1data

sys.path.append(r"K:\10. Released Software\Systems Manufacturing Support\Shared")
sys.path.append(r"C:\Users\tbates\Python\shared")
from Logger import TextLogger

class move_and_settle(a1data.a1data):
    '''
    Represents a B5.64 compliant test procedure using the Automation 1 controller. When constructing an instance
    of this class, you specify the test parameters you want, then use the 'test' function to actually perform the
    move-and-settle test

    Parameters
    ----------
    axis : str
        The axis that the test will be run on.
    sample_rate : int
        Sample rate collected by the Automation 1 controller in Hz, must match up with one of the existing
        Automation 1 sample rate values.
    step_size : float
        Size of each step, units are the same as the controller parameter.
    frame : tuple
        Beginning and end points of the test in terms of an absolute coordinate system,
        units are the same as the controller parameter.
    **kwargs : Optional parameters
        direction : a1data.mode
            Specify either a unidirectional test or a bidirectional test
        num_cycles : int
            Number of times to repeat the move and settle test across the frame
        step_time: float
            Time between each step and the time of each data collection period
        speed : float
            speed of the movement in units per second
        ramp_type : automation1.RampType
            Specify the type of ramp performed by the Automatiion 1 controller
        ramp_value : float
            Specify the acceleration of the move. Units are the same as the controller parameter.
        ramp_type_arg : float
            The ramping type additional argument for accelerations. 
            This is only used when $rampTypeAccel is RampType.SCurve and represents the s-curve percentage.
        folder : str
            This is specifies the folder used to store the .csv files in self.test() and access the files in self.plot()
            and self.to_dataframe()
        units: str
            units of the automation 1 controller

    Returns
    -------
    None.

    '''

    def __init__(self, axis:str, sample_rate, step_size:float, frame:tuple, probe_axis, **kwargs):

        #Input arguments that are necessary for the test to run
        super().__init__(axis, sample_rate, probe_axis, **kwargs)
        self.step_size = step_size
        self.frame = frame
        self.probe_axis = probe_axis
        
        #Input arguments that can be defined but may not be necessary
        default_kwargs = {'direction' : a1data.mode.Bidirectional,
                          'num_cycles': 1,
                          'step_time' : 1, #second
                          'folder' : 'moveandsettlecollection'
                         }
        
        #Update defaults if they exist
        kwargs = {**default_kwargs,**kwargs}
        
        self.direction = kwargs['direction']
        self.num_cycles = kwargs['num_cycles']
        self.step_time = kwargs['step_time']
        self.folder = kwargs['folder']
        self.import_data = kwargs['import_data']
        self.text_widget = kwargs['text_widget']
        self.units = kwargs['units']
        
        
        #Non-user definable parameters
        self.data_len = -1 #Obviously fake number for error checking, defined in populate method
        self.pos_dev = [[]] #Position Deviation, 2D list
    
    def setup_error_logging(self):
        # Redirect sys.stderr to the text widget
        sys.stderr = TextLogger(self.text_widget)

    def log_exception(self, exc_type, exc_value, exc_traceback):
        """Custom exception handler to log exceptions to the Text widget."""
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(error_message)  # This will be redirected to the Text widget    
    
    def test(self, controller : a1.Controller):
        '''
        Method to perform the corresponding Automation 1 test in compliance with ASME B5.64

        Parameters
        ----------
        controller : a1.Controller.connect()
            The active Automation1 controller that should be performing the specified test

        Returns
        -------
        CSV files corresponding to each step performed in the move-and-settle test.
        These files are located in the folder, 'moveandsettlecollection', in the current directory

        '''
        #Set units
        self.n = (int)(self.sample_rate*self.step_time)
        data_config = super().test(controller)
        
        # Define the folder name and path
        self.folder_name = 'Step And Settle Test Data'
        self.folder_path = os.path.join(self.folder, self.folder_name)
        os.makedirs(self.folder_path, exist_ok=True)
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Format the current datetime
        
        # Create a new folder path with the timestamp
        self.new_folder_path = os.path.join(self.folder_path, f"{current_time}")
        
        # Create the directory if it doesn't exist
        os.makedirs(self.new_folder_path, exist_ok=True)
        
        #Move to start position of travel
        controller.runtime.commands.motion.movelinear(self.axis, [self.frame[0]], self.speed)
        
        #wait for the stage to be in position
        time.sleep(self.step_time)
        
        self.sens = 1

        #For the number of cycles that should be run
        for i in range(1, self.num_cycles + 1):
            #For the amount of steps that can fit in the given frame
            for j in range(1, (self.frame[1] - self.frame[0]) // self.step_size + 1):
                #Collect data and move
                controller.runtime.data_collection.start(a1.DataCollectionMode.Snapshot, data_config)
                
                # #Wait before move starts
                # time.sleep(1/100)
                
                controller.runtime.commands.motion.movelinear(self.axis, [self.frame[0] + j*self.step_size], self.speed)
                
                #Wait for the results to complete
                results = controller.runtime.data_collection.get_results(data_config, self.n)

                #Results as n length arrays with all of the data points collected
                self.populate(self.sens, results)

                #Write cycle to a csv
                self.write_to_csv('{}\step{}_{}.csv'.format(self.new_folder_path, j,i))

                
            #If Bidirectional move and settle requested    
            if self.direction == a1data.mode.Bidirectional:
                for j in range(1, (self.frame[1] - self.frame[0]) // self.step_size + 1):
                    #Collect data and move backward
                    #Collect data and move
                    controller.runtime.data_collection.start(a1.DataCollectionMode.Snapshot, data_config)
                   
                    # #Wait before move starts
                    # time.sleep(1/100)
                    
                    #Move backward to the next step
                    controller.runtime.commands.motion.movelinear(self.axis, [self.frame[1] - j*self.step_size], self.speed)
                   
                    #Wait for the results to complete
                    results = controller.runtime.data_collection.get_results(data_config, self.n)
                    
                    #Results as n length arrays with all of the data points collected
                    self.populate(self.sens, results)

                    
                    #Write cycle to a csv
                    self.write_to_csv('{}\stepback{}_{}.csv'.format(self.new_folder_path,j,i))
            
            #Move to start position of travel    
            else:
                controller.runtime.commands.motion.movelinear(self.axis, [self.frame[0]], self.speed)
                time.sleep(self.step_time)
                
        self.data_files = [file for file in os.listdir(self.new_folder_path) if 'csv' in file]
        self.data_len = len(self.data_files)
        
                       
                    
    def to_dataframe(self):
        '''
        Since a move and settle test requires the collection of multiple test windows at once, this method
        converts the csv files in self.folder to a list of dataframes for ease of accessing multiple data sets at 
        once

        Returns
        -------
        dataframe_list : pd.Dataframe[]
            List of every dataframe from a move-and-settle test

        '''
        dataframe_list = []
        #For number of cycles
        for i in range(1, self.num_cycles + 1):
            #For the amount of steps that can fit in the given frame
            for j in range(1, (self.frame[1] - self.frame[0]) // self.step_size + 1):
                dataframe_list.append(pd.read_csv(r'{}\step{}_{}.csv'.format(self.new_folder_path,j,i))) #Read in Move and Settle as a csv file
            if self.direction == a1data.mode.Bidirectional:
                for j in range(1, (self.frame[1] - self.frame[0]) // self.step_size + 1):
                    dataframe_list.append(pd.read_csv(r'{}\stepback{}_{}.csv'.format(self.new_folder_path,j,i))) #Read in Move and Settle as a csv file
        return dataframe_list
    
    
    def populate(self, results = None, file = None, dataframe = None, folder = None, df_list = None):
        super(move_and_settle,self).populate(results, file, dataframe)
        
        #Extending the populate function of a1data class to check if a folder was inputted
        if folder is not None: 
            data_files = [file for file in os.listdir(folder) if 'csv' in file]
            self.import_folder = folder
            
            #data is a list of dataframes
            data = [pd.read_csv(folder + '\\' +i) for i in data_files]
            self.time_array = [(file['Time (seconds)']).tolist() for file in data]
            self.pos_com = [(file[' PosCmd ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.pos_fbk = [(file[' PosFbk ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.pos_err = [(file[' PosErr ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.vel_com = [(file[' VelCmd ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.vel_fbk = [(file[' VelFbk ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.vel_err = [(file[' VelErr ({}) {}'.format(self.axis, self.units)].tolist()) for file in data]
            self.ai0 = [(file[' Ain 0 ({})'.format(self.axis)].tolist()) for file in data]
        elif df_list is not None:
            #Extending further to input a list of dataframes
            self.time_array = [(file['Time (seconds)']).tolist() for file in df_list]
            self.pos_com = [(file[' PosCmd ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.pos_fbk = [(file[' PosFbk ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.pos_err = [(file[' PosErr ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.vel_com = [(file[' VelCmd ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.vel_fbk = [(file[' VelFbk ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.vel_err = [(file[' VelErr ({}) {}'.format(self.axis, self.units)].tolist()) for file in df_list]
            self.ai0 = [(file[' Ain 0 ({})'.format(self.axis)].tolist()) for file in df_list]

    def adjust_start(self):
        '''
            Shifts the starting point of all collected signals so that the start point corresponds with the start of the step. For the time array,
            the endpoint is shifted back by the same number of points to match the length. 
        Returns
        -------
        None.

        '''
        self.time_array = []
        self.pos_com = []
        self.pos_fbk = []
        self.pos_err = []
        self.vel_com = []
        self.vel_fbk = []
        self.vel_err = []
        self.ai0 = []

        #Empty variables for determining all of the indices where there is no movement, the index groupings where there is no movement, and the total move time for each file
        no_move = []
        no_move_range =  []
        self.move_time = []
        
        if self.import_data == True:
            self.csv_path = f"{self.import_folder}/{self.df}"
            self.csv_folder = f"{self.import_folder}"
        
        else:
            self.csv_path = f"{self.new_folder_path}/{self.df}"
            self.csv_folder = f"{self.new_folder_path}"

        signal_dict = {}
        
        if self.sig == 'Average':
            for file in os.listdir(self.csv_folder):

                csv_file = os.path.join(self.csv_folder, file)
                # Read the CSV file
                data = pd.read_csv(csv_file)
                
                # Initialize a dictionary to store data for the current CSV
                file_data = {}
            
                # Attempt to extract data, with fallback to alternative column names if needed
                try:
                    file_data['time_array'] = data['Time (seconds)'].tolist()
                    file_data['pos_com'] = data[' PosCmd ({}) {}'.format(self.axis, self.units)].tolist()
                    file_data['pos_fbk'] = data[' PosFbk ({}) {}'.format(self.axis, self.units)].tolist()
                    file_data['pos_err'] = data[' PosErr ({}) {}'.format(self.axis, self.units)].tolist()
                except KeyError:
                    file_data['time_array'] = data['Time (sec)'].tolist()
                    file_data['pos_com'] = data[' PosCmd ({}) ({})'.format(self.axis, self.units)].tolist()
                    file_data['pos_fbk'] = data[' PosFbk ({}) ({})'.format(self.axis, self.units)].tolist()
                    file_data['pos_err'] = data[' PosErr ({}) ({})'.format(self.axis, self.units)].tolist()
            
                try:
                    file_data['vel_com'] = data[' VelCmd ({}) {}'.format(self.axis, self.units)].tolist()
                    file_data['vel_fbk'] = data[' VelFbk ({}) {}'.format(self.axis, self.units)].tolist()
                    file_data['vel_err'] = data[' VelErr ({}) {}'.format(self.axis, self.units)].tolist()
                except KeyError:
                    file_data['vel_com'] = data[' VelCmd ({}) ({}/sec)'.format(self.axis, self.units)].tolist()
                    file_data['vel_fbk'] = data[' VelFbk ({}) ({}/sec)'.format(self.axis, self.units)].tolist()
                    file_data['vel_err'] = data[' VelErr ({}) ({}/sec)'.format(self.axis, self.units)].tolist()
            
                try:
                    file_data['ai0'] = data[' Ain 0 ({})'.format(self.axis)].tolist()
                except KeyError:
                    file_data['ai0'] = []
            
                # Store the data for the current file in the main dictionary
                signal_dict[file] = file_data
                
                self.time_array = np.mean([file_data['time_array'] for file_data in signal_dict.values()], axis=0)
                
                self.pos_com = np.mean([file_data['pos_com'] for file_data in signal_dict.values()], axis=0)
                self.pos_fbk = np.mean([file_data['pos_fbk'] for file_data in signal_dict.values()], axis=0)
                self.pos_err = np.mean([file_data['pos_err'] for file_data in signal_dict.values()], axis=0)
                
                self.vel_com = np.mean([file_data['vel_com'] for file_data in signal_dict.values()], axis=0)
                self.vel_fbk = np.mean([file_data['vel_fbk'] for file_data in signal_dict.values()], axis=0)
                self.vel_err = np.mean([file_data['vel_err'] for file_data in signal_dict.values()], axis=0)
    
                self.ai0 = np.mean([file_data['ai0'] for file_data in signal_dict.values()], axis=0)
        else:    
            data = pd.read_csv(self.csv_path)
            
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
            try:
                self.ai0 = (data[' Ain 0 ({})'.format(self.axis)]).tolist()
            except KeyError:
                pass

        #for file in range(self.data_len): #For every file that is present
        
        #Condition that checks if the length of the current time_array is not 1-this will fail during the second iteration for a single file
        if len(self.time_array) != 1: 
            no_move = np.where(np.array(self.vel_com) == 0)[0] #finds all indices where vel_com = 0 

            start_index = 0
            for idx, val in enumerate(no_move[1:], start = 1):
                    
                #Condition for grouping no move indices: successive indices that are part of one stretch of no movement will have a difference of 1
                if ((val-no_move[idx-1] !=1) & (idx<len(no_move)-1)): 
                    no_move_range.append([no_move[start_index], no_move[idx-1]])
                    start_index = idx
                #Condition for last strectch of no movement, makes sure that the difference between successive points is equal to 1
                elif ((val-no_move[idx-1] ==1) & (idx==len(no_move)-1)): 
                    no_move_range.append([no_move[start_index], no_move[len(no_move)-1]])
                
        #Shifts the starting point of all signals to the index where the first movement occurs, shifts endpoint of time_array back by the same number of indices
        self.time_array = self.time_array[:(len(self.time_array)-no_move_range[0][1])]
        self.pos_com = self.pos_com[no_move_range[0][1]:]
        self.pos_fbk = self.pos_fbk[no_move_range[0][1]:]
        self.pos_err = self.pos_err[no_move_range[0][1]:]
        self.vel_com = self.vel_com[no_move_range[0][1]:]
        self.ai0 = self.ai0[no_move_range[0][1]:]
        
        #Calculates the total duration of the move for each step file
        
        self.move_time = (no_move_range[1][0]-no_move_range[0][1])/self.sample_rate   
                
    def moving_window(self, process_window, window_direction):
        '''
        
        
        Parameters
        ----------
        process_window : float
            Duration of the desired process window in seconds
        window_direction : a1data.mode
            Enum found in mode class of a1data module used to describe direction of process window: forward, centered, or backward

        Returns
        -------
        window_dict : dict
            Dictionary containing the following values related to the desired window:
                Process Window: float
                    Process window that was chosen
                
                Process Window Direction: string
                    Specified calculation direction of the process window 

                Window Ranges: list
                    Upper and lower index range of each process window throughout the length of the position deviation signal
                

        '''
        #Calling the adjust_start() method to make sure the starting point of the signals are where the move starts
        self.adjust_start()
        #Calculates the index length that the process window spans over 
        self.window_len = process_window*self.sample_rate
        
        window_ranges = []
        
        #Determines starting and ending points based off window and calculation direction
        #for file in range(self.data_len):
            
        #Condition that checks if the length of the current time_array is not 1-this will fail during the second iteration for a single file
        if len(self.time_array) != 1: 
            if window_direction == a1data.mode.forward_window: #forward window process
                lowerSubtract = 0.0
                upperAdd = self.window_len
                window_direction = 'Forward'
            
            elif window_direction == a1data.mode.centered_window: #centered window process
                lowerSubtract = self.window_len/2
                upperAdd = self.window_len/2
                window_direction = 'Centered'
            elif window_direction == a1data.mode.backward_window: #backward window process
                lowerSubtract = self.window_len
                upperAdd = 0.0
                window_direction = 'Backward'
                
            time_vals = self.time_array
                
            #Finding the starting and ending point of each process window throughout the length of time_array
            start_pos = [0 if round(i*self.sample_rate - lowerSubtract) <0 else round(i*self.sample_rate - lowerSubtract) for i in time_vals]
            end_pos = [len(time_vals)-1 if int(i*self.sample_rate + upperAdd) > len(time_vals) else int(i*self.sample_rate + upperAdd) for i in time_vals]
   
            #Pairing each start and end index for each process window     
            window_ranges = ([[j, k] for j,k in zip(start_pos, end_pos)])
# =============================================================================
#             print('Window Ranges: ', window_ranges)
#             print('Process Window: ', process_window)
# =============================================================================
        #Dictionary with the window ranges and the specified process window direction 
        window_dict = {'Window Ranges': window_ranges,
                       'Process Window (sec)': process_window,
                       'Process Window Direction': window_direction}
        
        return window_dict
    
    
    def data_analysis(self, error_metric, process_window, window_direction, position_tolerance, df) -> dict:
        '''
        Parameters
        ----------
        error_metric : a1data.mode
            Enum found in mode class of a1data module used to specify which ASME B5.64 error metric should be found.
        process_window : float
            Duration of the desired process window in seconds.
        window_direction : a1data.mode
            Enum found in mode class of a1data module used to describe direction of process window: forward, centered, or backward
        position_tolerance : float
            Desired position tolerance that must be met for system to be considered settled 

        Returns
        -------
        data_dict : dict
            Dictionary with the following information related to the data analysis:
                Error Metric Values: list
                    Calculated error metric values for each step based of which metric was chosen
                
                Position Deviation Windows: list
                    Index ranges of each window throughout the signal used to determine each position deviation window
                
                Move and Settle Time: list
                    Move and Settle time found for each step file that was included

        '''
        self.df = df
        #Calling the moving window function to find the each window index range throughout the entire position deviation signal             
        window_dict = self.moving_window(process_window, window_direction)
        #Extracting the window index range
        moving_window = window_dict['Window Ranges']
        
        
        
        #Creating empty list of lists for the number of files that are present
        error_metric_vals = []
        t_ms = []
        dev_window = []
        self.pos_dev = []
        self.move_end_ind = []
        
        #for file in range(self.data_len): #for the number of files that were found
            #Condition that checks if the length of the current time_array is not 1-this will fail during the second iteration for a single file
            #Condition that checks if the length of the current time_array is not 1-this will fail during the second iteration for a single file
        if len(self.time_array) != 1: 
                
            #Equation 7.3.1 for calculating the dynamic position deviation
            self.pos_dev = [abs(i - self.pos_com[-1]) for i in self.pos_fbk]
 
            #Finding each position deviation window based off the index ranges in moving_window
            dev_window = [(self.pos_dev[i[0]:i[1]]) for i in moving_window] 

            #Calculating the desired error metric (Moving Average Error, Moving Standard Deviation, or Moving Peak Error)
            if error_metric == a1data.mode.MAE: 
                error_metric_vals = [round(sum(i) / self.window_len, 4) for i in dev_window]
  
            elif error_metric == a1data.mode.MSD: 
                std_vals = [np.std(i) for i in dev_window]
                error_metric_vals = np.nan_to_num(std_vals, 0)
                      
            elif error_metric == a1data.mode.MPE: 
                error_metric_vals  = [max(list(map(abs, i))) if len(i) >=1 else 0 for i in dev_window]
                
                
            t_ind = len(error_metric_vals) - 1 #Last index of time
             
            #finds last time point where the error metric is less than position tolerance
            while abs(error_metric_vals[t_ind]) <= position_tolerance: 
                t_ms = round((self.time_array[t_ind]), 4)
                self.move_end_ind = t_ind
                t_ind-=1
                
            #Makes sure that the error metric move and settle time is not less than the move duration. 
            #This is essentially the instantly settled condition check
            if t_ms < self.move_time: t_ms = self.move_time

        #Initializing Data Dict
        data_dict = {}
     
        #Storing the error metric values in the data dictionary
        data_dict['Error Metric Values'] = error_metric_vals        
     
        #Storing window ranges used for the position deviation and the move and settle time(s) for all files present 
        data_dict['Position Deviation Windows'] = moving_window
        data_dict['Move and Settle Time'] = t_ms
        data_dict['Move and Settle Time Index'] = self.move_end_ind
     
        return data_dict
    
        
    
    
    def aero_move_and_settle(self, time_spec : float, settle_window : float, sig, df):
        '''
        Determines the aerotech move and settle time for a move and settle test.
        Creates a bar graph displaying the aerotech move and settle time for each step overlayed with the desired time specification
        
        Parameters
        ----------
        time_spec : float
            Specified time specification not to exceed in seconds.
        settle_window : float
            Specified position window for the system to settle within in self.units

        Returns
        -------
        aerosettle_dict : dict
            Dictionary containing the following information related to the Aerotech Move and Settle Time: 
                Aerotech Move and Settle Time: list
                    Contains the move and settle time of the step using Aerotech's method
                Passed Settle Time: list
                    Bool returning if the calculated move and settle time was less than the specification
                    
        fig1: figure
            Figure containing a bar plot of each step that was included, and if its move and settle time met the specified criteria 

        '''
        self.df = df
        self.sig = sig
        
        #Calling the adjust_start() method to make sure the starting point of the signals are where the move starts
        self.adjust_start()
        
        #Creating empty list of lists for the actual move and settle time of step file, and if the test passed or not
        actual_ms_time = []
        test_passed = []
        
# =============================================================================
#         data_files = [file for file in os.listdir(self.folder) if 'csv' in file]
#         self.data_len = len(data_files)
#         for file in range(self.data_len): #for every file that is present
# =============================================================================
        
        # Condition that checks if the length of the current time_array is not 1
        if len(self.time_array) != 1:

            # Temporary index of where the last position deviation that is greater than the move and settle window is located

            # Temporary index of where the last velocity command that is greater than zero is located
            temp_vel_ind = np.where(np.abs(self.vel_com) > 0)[0]
            last_vel_ind = np.max(temp_vel_ind) if len(temp_vel_ind) > 0 else -1
            
            # If length of temp_vel_ind is 0, then there was no move captured
            if last_vel_ind == -1: 
                print('No move captured')
                        
            # Adjusts index to be relative from the beginning rather than the end of the list
            self.move_end_ind = last_vel_ind + 1
            
            #Shifts the starting point of all signals to the index where the first movement occurs, shifts endpoint of time_array back by the same number of indices
            self.time_array = self.time_array[:(len(self.time_array)-len(temp_vel_ind)-1)]
            self.pos_com = self.pos_com[self.move_end_ind:]
            self.pos_fbk = self.pos_fbk[self.move_end_ind:]
            self.pos_err = self.pos_err[self.move_end_ind:]
            self.vel_com = self.vel_com[self.move_end_ind:]
            self.ai0 = self.ai0[self.move_end_ind:]
            
            temp_pos_ind = np.where(np.abs(self.pos_err) >= settle_window)[0].tolist()
            
            if len(temp_pos_ind) > 0:
                # Adjust the index to the original array orientation
                last_pos_ind = np.max(temp_pos_ind)
                self.start_plot = int(round((last_pos_ind) / 2,0))
            else:
                # If no significant deviation found, set to -1
                last_pos_ind = -1
 
            # If no indices in temp_pos_ind, store the length of the current velocity command minus 1
            if last_pos_ind == -1:
                actual_ms_time = self.move_time
                
            actual_ms_time = self.time_array[last_pos_ind]

            test_passed = (actual_ms_time <= time_spec) #Bool returning if the calculated move and settle time was less than the specification
             

         
        #Dictionary with information related to calculating Aerotech Move and Settle time
        aero_settle_dict = {'Aerotech Move and Settle Time': actual_ms_time,
                           'Time Specification': time_spec,
                           'Move and Settle Window': settle_window,
                           'Passed Move and Settle Time': test_passed}
                 
        return aero_settle_dict
    
    def aero_move_and_settle_bars(self, aero_dictionary):
        actual_ms_time = aero_dictionary['Aerotech Move and Settle Time']
        test_passed = aero_dictionary['Passed Move and Settle Time']
        settle_window = aero_dictionary['Move and Settle Window']
        time_spec = aero_dictionary['Time Specification']
        bar_width = 0.25 
        pass_color = 'green'
        fail_color = 'red'
        
        #Creating empty list of lists for the x-axis graph labels
        data_label = [[] for _ in range(self.data_len)]
        
        #for file in range(self.data_len): #for every file that is present
        if len(self.time_array) != 1:  
            #Creates data label based off the file, axis, step size, units, and specified move and settle window 
            if (self.direction == a1data.mode.Bidirectional):
                data_label = (['{0}: {1} (-{2}) {3} to +/-{4} {3}'.format(self.df, self.axis, self.step_size, self.units, settle_window)])
               
            else: 
                data_label = (['{0}: {1} ({2}) {3} to +/-{4} {3}'.format(self.df, self.axis, self.step_size, self.units, settle_window)])

        #Section that creates a txt file with info regarding the entire test, 
        #and a bar plot comparing the actual move and settle time with the time specification
        
        
        fig1, ax1 = plt.subplots(constrained_layout=True,figsize=(10,6))
        with open(os.path.join(self.folder,'Aerotech Move and Settle Time Results.dat'),'w+') as f1:
            f1.write('Test, Spec, Achieved, DidPass\n')
            
            start_ind = 0
            xtick_Vals, xtick_Labels = [[] for _ in range(2)]
            xtick_Labels = []
            bars1, bars2, this_ax_ind = [[0]*self.data_len for _ in range(3)]
           
          
            #for file in range(self.data_len):
            this_ax_ind = np.arange(actual_ms_time)*bar_width + start_ind
               
                
            if test_passed: 
                color_1 = pass_color
                hatch_1 = None
            else: 
                color_1=fail_color
                hatch_1 = '//'
                
            bars1 = ax1.bar(data_label, actual_ms_time,bar_width,color=color_1) #actual move and settle time from sec to ms
            ax1.bar_label(bars1)
            bars2 = ax1.bar(data_label, time_spec, bar_width,color='black',alpha=0.1,hatch=hatch_1) #desired move and settle time from sec to ms
            ax1.bar_label(bars2)
            f1.write('{0}, {1}, {2}, {3}\n'.format(data_label, time_spec, actual_ms_time, test_passed))
            xtick_Vals.extend(this_ax_ind)
            xtick_Labels.extend(data_label)
          
            ax1.set_xticklabels(xtick_Labels, rotation = 45, ha = 'right')
           
            plt.title('Aerotech Move and Settle Times')
            plt.ylabel('Move and Settle Time [sec]')
            plt.savefig('ResultsTEST.png',dpi=100, bbox_inches='tight')
        
        return fig1

    def GUI_plot(self, aero_settle_dict, canvas_size, **kwargs):
        '''
        
        Parameters
        ----------
        data_dict : dict
            Data dictionary that is returned from running the data_analysis function using ASME B5.64 method of evaluation
        aero_settle_dict : dict
            Data dicionary that is returned from running the aero_move_and_settle function using Aerotech method of evaluation
     
        **kwargs : Optional Parameters 
            after_move_end: bool
                User decision whether they want to view the entire plot or the portion after the move ends (True/False)
            fignum: int
                Specifies the figure number of the metric plot
            legend_loc: string
                Specifies the location of the legend on the plot
            legend_size: float
                Specifies the font size of the text in the legend, and therefore its size
            signal: list
                Specifies which data values to use. Can be right from the class object

        Returns
        -------
        metric_plot : figure
            Figure containing the error metric plotted against the position deviation. Average position deviation and all error metrics shown if multiple files are included. 

        '''
        
        
        #Default kwargs if none are specified
        default_kwargs = {'step_num': 0,
                          'after_move_end': True,
                          'fignum': 1,
                          'legend_loc': 'best', 
                          'legend_size': 20,                              
                          'signal': self.pos_err}
        #'legend_loc_x': 1.01,
        #'legend_loc_y': 1.0,
        #Updates kwargs in case some are specified 
        kwargs = {**default_kwargs,**kwargs}
        step_num = kwargs['step_num']
        after_move_end = kwargs['after_move_end']
        fignum = kwargs['fignum']
        legend_size = kwargs['legend_size']
        signal = kwargs['signal']

        #legend_loc_x = kwargs['legend_loc_x']
        #legend_loc_y = kwargs['legend_loc_y']
        index = next((i for i, char in enumerate(step_num) if char.isdigit()), None)
        if index is not None:
            step_num = int(step_num[index]) if index < len(step_num) else None
        #Creating labels for signal and move and settle times for the plot legend
        sig_label = 'Position Deviation'
        #asme_settle_label = 'ASME Move and Settle Time'
        aerotech_settle_label = 'Aerotech Move and Settle Time'
        
        #all_asme_ms_times = data_dict['Move and Settle Time']
        all_aero_ms_times = aero_settle_dict['Aerotech Move and Settle Time']
        #all_error_metric_vals = data_dict['Error Metric Values']

        #Plot creation, starts with the single/averaged specified signal
        metric_plot = plt.figure(fignum, figsize=(15, 10))    
        
        plt_signal = np.abs(signal)
        time_vals = self.time_array
        aerotech_settle_time = all_aero_ms_times


        time_spec = aero_settle_dict['Time Specification']    
        ms_times = [aerotech_settle_time, time_spec]
        
        if after_move_end == True:
            start = self.start_plot
            #start = int(np.average(self.move_end_ind))
            ms_label_locs = [i+0.015 for i in ms_times]
            end = np.where(np.array(time_vals) == time_spec)[0][0] + 50

        else: 
            start = 0
            ms_label_locs = [i/2 for i in ms_times]
            end = len(time_vals)-1
       
        plt.plot(time_vals[start:end], plt_signal[start:end], linewidth = 7, label = sig_label)

        plt.xlim(left = time_vals[start], right = time_vals[end])
        
        #Vertically stretching the graph to reduce overlap between the time annotations and the signal that is plotted
        min_val = np.min(plt_signal[start:end])
        max_val = np.max(plt_signal[start:end])

        if max_val > abs(min_val): limit = max_val
        else: limit = min_val 
         
        graph_bound = 1.5*limit    
        diff = graph_bound - limit
     
        if graph_bound >0: plt.ylim(top = graph_bound)
        else: plt.ylim(bottom = graph_bound) 
            
        
        ms_times = [aerotech_settle_time, time_spec]
        
        #Sets the colors of the move and settle times based off if the step passed or failed the time specification
        aero_color = 'green' 
        #if asme_settle_time > time_spec: asme_color = 'red'
        if aerotech_settle_time > time_spec: aero_color = 'red'
        
        #Vertical lines plotting where the time specification and the ASME and Aerotech move and settle times are located 
        plt.axvline(x = time_spec, label = 'Time Specification', color = 'k', linewidth = 4, linestyle = '-.')
        #plt.axvline(x = asme_settle_time, label = asme_settle_label, color = asme_color, linewidth = 5, linestyle = 'dashed')
        plt.axvline(x = aerotech_settle_time, label = aerotech_settle_label, color = aero_color, linewidth = 4, linestyle = 'dotted')
            
        divisors = [1.25, 1.8, 3.35] #For adjusting the spacing of the annocations
        diff_color = [aero_color, 'black'] #Colors of the annotations
          
        #Annotates where the time spec and move and settle times are from the start with respective colors 
        for j, k  in zip(ms_times, divisors):
            
            plt.annotate("", xy = (time_vals[start], (graph_bound-diff/k)), xytext=(j, graph_bound-diff/k), xycoords= "data",
                                  va="center", ha="center", size = 20, arrowprops=dict(arrowstyle="<-")) 
        
        #Separate for loop for labels, so that they are always in front of the vertical line markers
        for i, j, k, h  in zip(ms_label_locs, ms_times, divisors, diff_color):
             
            plt.annotate(str(j) + ' sec', xy=(i, graph_bound-diff/k), xycoords="data",
                                  va="center", ha="center", size = 20, color = h, bbox=dict(boxstyle="round", fc="w")) 
        
        
        #Annotation outside the graph with information related to the data analysis             
        # plt.annotate('Process Window: {} seconds ({})     Time Specification: {} sec     Settle Window: {} ({})'.format(
        #                     data_dict['Process Window (sec)'], data_dict['Process Window Direction'], 
        #                     time_spec, aero_settle_dict['Move and Settle Window'], self.units), 
        #                     xy = (0, -0.15), xycoords='axes fraction', size = 20)    
       
        #Configuring the plot. 
        #plt.title('{} with a {} second {} Process Window'.format(data_dict['Error Metric'][0], data_dict['Process Window (sec)'], data_dict['Process Window Direction']), fontsize = 20)
        
        plt.xlabel('Time (sec)', size = 12)
        plt.ylabel('Position Deviation ({})'.format(self.units), size = 12)
        plt.xticks(fontsize = 10)
        plt.yticks(fontsize = 10)
        plt.legend(loc = "upper right", fontsize = legend_size)  #bbox_to_anchor=(legend_loc_x, legend_loc_y)
        plt.tight_layout()
     
        return metric_plot
    
    def GUI_plot_plotly(self,aero_settle_dict, new_folder_path, **kwargs):
        """
        Generates a Plotly plot based on the provided data and displays it in an HTML window.
        
        Parameters
        ----------
        aero_settle_dict : dict
            Data dictionary returned from running the aero_move_and_settle function using Aerotech method of evaluation.
        canvas_size : tuple
            Canvas size to fit the plot (not directly used in Plotly but kept for consistency).
        new_folder_path : str
            Directory path to save the resulting HTML plot.
        **kwargs : dict
            Optional parameters for customization.
            
        Returns
        -------
        None
        """
        
        # Default kwargs if none are specified
        default_kwargs = {
            'step_num': 0,
            'after_move_end': True,
            'fignum': 1,
            'legend_loc': 'best',
            'legend_size': 20,
            'signal': self.pos_err
        }
        # Update kwargs with any provided options
        kwargs = {**default_kwargs,**kwargs}
        after_move_end = kwargs['after_move_end']
        legend_size = kwargs['legend_size']
        signal = kwargs['signal']
        
        # Extract relevant data and options from kwargs
        after_move_end = kwargs['after_move_end']
        signal = kwargs['signal']
        
        sig_label = 'Position Deviation'
        aerotech_settle_label = 'Aerotech Move and Settle Time'
        all_aero_ms_times = aero_settle_dict['Aerotech Move and Settle Time']

        plt_signal = np.abs(signal)
        time_vals = self.time_array
        aerotech_settle_time = all_aero_ms_times
        
        plt_signal = [abs(x) for x in signal]
        time_vals = self.time_array
        aerotech_settle_time = all_aero_ms_times

        time_spec = aero_settle_dict['Time Specification']

        if after_move_end:
            start = self.start_plot
            # Use np.isclose to find the index of the value closest to time_spec within a small tolerance
            tolerance = 1e-6  # Adjust this value as needed based on the precision of your data
            result = np.where(np.isclose(time_vals, time_spec, atol=tolerance))[0]
            
            if result.size > 0:
                end = result[0] + 50
            else:
                print(f"No matching elements close to {time_spec} found in time_vals. Using default end value.")
                end = 50  # Default handling if no match is found
        else:
            start = 0
            end = len(time_vals) - 1
    
        trace = go.Scatter(
            x=time_vals[start:end],
            y=plt_signal[start:end],
            mode='lines',
            name=sig_label,
            line=dict(width=7),
            hovertemplate='%{x:.2f} sec<br>%{y:.6f} mm<extra></extra>'
        )
    
        aero_color = 'green' if aerotech_settle_time <= time_spec else 'red'
    
        layout = go.Layout(
            title='Aerotech Move and Settle Plot',
            xaxis=dict(title='Time (sec)'),
            yaxis=dict(title='Position Deviation ({})'.format(self.units),tickformat=".6f"),
            shapes=[
                dict(
                    type="line",
                    x0=time_spec,
                    x1=time_spec,
                    y0=min(plt_signal[start:end]),
                    y1=max(plt_signal[start:end]),
                    line=dict(color="black", width=4, dash="dot"),
                    name='Time Specification'
                ),
                dict(
                    type="line",
                    x0=aerotech_settle_time,
                    x1=aerotech_settle_time,
                    y0=min(plt_signal[start:end]),
                    y1=max(plt_signal[start:end]),
                    line=dict(color=aero_color, width=4, dash="dash"),
                    name=aerotech_settle_label
                )
            ],
            annotations=[
                dict(
                    x=aerotech_settle_time,
                    y=max(plt_signal[start:end]) - (max(plt_signal[start:end]) - min(plt_signal[start:end])) / 10,
                    xref="x",
                    yref="y",
                    text=f'{aerotech_settle_time} sec',
                    showarrow=True,
                    arrowhead=2,
                    ax=100,
                    ay=-40,
                    font=dict(size=legend_size, color=aero_color)
                ),
                dict(
                    x=time_spec,
                    y=max(plt_signal[start:end]) - (max(plt_signal[start:end]) - min(plt_signal[start:end])) / 6,
                    xref="x",
                    yref="y",
                    text=f'{time_spec} sec',
                    showarrow=True,
                    arrowhead=2,
                    ax=100,
                    ay=-40,
                    font=dict(size=legend_size, color='black')
                )
            ],
            legend=dict(font=dict(size=legend_size))
        )
    
        fig = go.Figure(data=[trace], layout=layout)
    
        # Save to an HTML file
        html_file = os.path.join(new_folder_path, 'Aerotech_Move_and_Settle_Plot.html')
        pio.write_html(fig, file=html_file, auto_open=True)
    
        # Optionally, you can directly open the file in a web browser
        #webbrowser.open('file://' + os.path.realpath(html_file))
    
    def pdf_plot(self, aero_settle_dict, ax=None, **kwargs):
        """
        Parameters
        ----------
        aero_settle_dict : dict
            Data dictionary returned from running the aero_move_and_settle function.
        df : str
            Step number or 'Average' for averaging all steps.
        ax : matplotlib.axes.Axes, optional
            The axis to plot on. If None, a new figure and axis are created.
        **kwargs : Additional optional parameters.
            Optional parameters for customizing the plot (e.g., fignum, legend_loc, etc.)
        
        Returns
        -------
        ax : matplotlib.axes.Axes
            The axis containing the plot.
        """

        # Default kwargs if none are specified
        default_kwargs = {'step_num': 0,
                          'after_move_end': True,
                          'legend_loc': 'best', 
                          'legend_size': 20.0,                              
                          'signal': self.pos_err}
        kwargs = {**default_kwargs, **kwargs}
        after_move_end = kwargs['after_move_end']
        legend_size = kwargs['legend_size']
        signal = kwargs['signal']
        
        # Check if an axis is provided; if not, create a new figure and axis
        if ax is None:
            pdf_plot = plt.figure(figsize=(30, 25))    
            ax = pdf_plot.add_subplot(111)
    
        # Get the size of the axis in inches
        ax_width, ax_height = ax.get_figure().get_size_inches()
    
        # Scale plot elements based on the axis size
        line_width = max(1, ax_width / 6)
        font_size = max(8, ax_width * .50)
    
# =============================================================================
#         # Plot creation, starts with the single/averaged specified signal
#         step_num = df
#         index = next((i for i, char in enumerate(step_num) if char.isdigit()), None)
#         if index is not None:
#             step_num = int(step_num[index]) if index < len(step_num) else None
# =============================================================================
    
        # Creating labels for signal and move-and-settle times for the plot legend
        sig_label = 'Position Deviation'
        aerotech_settle_label = 'Aerotech Move and Settle Time'
        all_aero_ms_times = aero_settle_dict['Aerotech Move and Settle Time']
    
        plt_signal = np.abs(signal)
        time_vals = self.time_array
        aerotech_settle_time = all_aero_ms_times
    
        time_spec = aero_settle_dict['Time Specification']
        ms_times = [aerotech_settle_time, time_spec]
    
        if after_move_end:
            start = self.start_plot
            ms_label_locs = [i + 0.015 for i in ms_times]
            end = np.where(np.array(time_vals) == time_spec)[0][0] + 50
        else:
            start = 0
            ms_label_locs = [i / 2 for i in ms_times]
            end = len(time_vals) - 1
    
        # Adjust line width, font size, etc., based on the axis size
        ax.plot(time_vals[start:end], plt_signal[start:end], linewidth=line_width, label=sig_label)
    
        ax.set_xlim(left=time_vals[start], right=time_vals[end])
    
        #Vertically stretching the graph to reduce overlap between the time annotations and the signal that is plotted
        min_val = np.min(plt_signal[start:end])
        max_val = np.max(plt_signal[start:end])
        graph_bound = 1.5 * max(max_val, abs(min_val))
    
        if graph_bound > 0:
            ax.set_ylim(top=graph_bound)
        else:
            ax.set_ylim(bottom=graph_bound)
    
        aero_color = 'green' if aerotech_settle_time <= time_spec else 'red'
    
        ax.axvline(x=time_spec, label='Time Specification', color='k', linewidth=line_width, linestyle='-.')
        ax.axvline(x=aerotech_settle_time, label=aerotech_settle_label, color=aero_color, linewidth=line_width, linestyle='dotted')
    
        divisors = [1.25, 1.8, 3.35]
        diff_color = [aero_color, 'black']
    
        for j, k in zip(ms_times, divisors):
            ax.annotate("", xy=(time_vals[start], graph_bound - graph_bound / (k*4)), xytext=(j, graph_bound - graph_bound / (k*4)),
                        xycoords="data", va="center", ha="center", size=font_size,
                        arrowprops=dict(arrowstyle="<-"))
    
        for i, j, k, h in zip(ms_label_locs, ms_times, divisors, diff_color):
            ax.annotate(f'{j} sec', xy=(i, graph_bound - graph_bound / (k*4)), xycoords="data",
                        va="center", ha="center", size=font_size, color=h, bbox=dict(boxstyle="round", fc="w"))
    
        ax.set_xlabel('Time (sec)', size=font_size)
        ax.set_ylabel(f'Position Deviation ({self.units})', size=font_size)
        ax.tick_params(axis='both', labelsize=font_size)
        ax.legend(loc = "upper right", fontsize = legend_size)
    
        return ax