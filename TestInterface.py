# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:03:56 2024

@author: tbates
"""

import os
import sys as syst
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import shutil
import plotly.graph_objs as go
import plotly.io as pio
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import tempfile
from datetime import datetime
import re
import socket
import copy
import gc
import json

# Assuming these are custom imports
import automation1 as a1
from Logger import TextLogger
from MoveAndSettleCollection import move_and_settle
from InPositionJitterCollection import jitter
from MinimumIncrementalMotionCollection import incremental_step
import a1data
from AerotechFormat import AerotechFormat

# Global State Class
class GlobalState:
    def __init__(self):
        self.ms = None
        self.ipj = None
        self.ins = None
        self.fig = None
        self.Comments = "No comments provided"
        self.clientsocket = None
        self.xforwarddata = []
        self.xreversedata = []
        self.yforwarddata = []
        self.yreversedata = []

    def reset(self):
        self.ms = None
        self.ipj = None
        self.ins = None
        self.fig = None
        self.Comments = "No comments provided"
        self.clientsocket = None
        self.xforwarddata = []
        self.xreversedata = []
        self.yforwarddata = []
        self.yreversedata = []


# Initialize Global State
global_state = GlobalState()

# Function to initialize or reset global variables
def initialize_globals():
    global_state.reset()

# JSON file path to store user inputs
USER_DATA_FILE = os.path.join(os.getcwd(), "user_data.json")

def save_user_inputs(data):
    """Save user inputs to a JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_user_inputs():
    """Load user inputs from a JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def controller_def():
    ver = tk.Toplevel()
    ver.title('Connection Type')
    ver.configure(bg='white')

    custom_font = font.Font(family="Times New Roman", size=12, weight="bold")

    label = tk.Label(ver, text="Are you trying to connect via USB?", bg='white', font=custom_font)
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=5)

    def on_yes():
        ver.result = 'yes'
        ver.destroy()

    def on_no():
        ver.result = 'no'
        ver.destroy()

    button_ok = tk.Button(ver, text="Yes", width=10, height=2, command=on_yes)
    button_ok.grid(row=4, column=0, padx=10, pady=10)

    button_cancel = tk.Button(ver, text="No", width=10, height=2, command=on_no)
    button_cancel.grid(row=4, column=1, padx=10, pady=10)

    ver.resizable(False, False)
    ver.update_idletasks()  # Ensure that the window sizes correctly

    screen_width = ver.winfo_screenwidth()
    screen_height = ver.winfo_screenheight()

    ver_width = ver.winfo_reqwidth()
    ver_height = ver.winfo_reqheight()

    x_cordinate = int((screen_width / 2) - (ver_width / 2))
    y_cordinate = int((screen_height / 2) - (ver_height / 2))

    ver.geometry(f"{ver_width}x{ver_height}+{x_cordinate}+{y_cordinate}")
    ver.focus_set()
    ver.result = None
    ver.wait_window()

    return ver.result

def get_clientsocket():
    if global_state.clientsocket is None:
        global_state.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        global_state.clientsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return global_state.clientsocket

def UI():
    initialize_globals()  # Initialize global variables

    global ani, window
    
    # Load stored user inputs
    stored_data = load_user_inputs()
    
    # Initialize Tkinter window
    window = tk.Tk()
    window.title("Min Step - Jitter - Step and Settle")
    window.resizable(True, False)

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    window_height = 900
    window_width = 1900

    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))

    window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
    
    # Create a style object
    style = ttk.Style()

    # Modify the appearance of the tabs only
    style.configure("TNotebook.Tab", 
                    font=('Arial', '12', 'bold'),  # Font style
                    padding=[10, 4],  # Padding around the text
                    background="lightgray",  # Background color of the tab
                    foreground="black",  # Text color
                    )

    # Change the appearance when the tab is selected
    style.map("TNotebook.Tab", 
              background=[("selected", "lightblue")],  # Background color when selected
              foreground=[("selected", "black")],  # Text color when selected
              expand=[("selected", [1, 1, 1, 0])]  # Makes selected tab appear slightly larger
              )
    
    
    interface = ttk.Notebook(window)
    interface.pack(fill='both', expand=True)
    
    # Create frames for each tab
    tab1 = ttk.Frame(interface, width=window_width, height=window_height)
    tab2 = ttk.Frame(interface, width=window_width, height=window_height)
    tab3 = ttk.Frame(interface, width=window_width, height=window_height)
    
    # Add tabs to the notebook
    interface.add(tab1, text='Step and Settle')
    interface.add(tab2, text='In-Position Jitter')
    interface.add(tab3, text='Min Incremental Motion')

    #for tab in (tab1, tab2, tab3):
    # Configure columns and rows
    tab1.columnconfigure([0, 1, 2, 3, 4, 5, 6], weight=1, minsize=700 / 4, uniform='column')
    tab1.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], weight=1, minsize=1)

    # Define row indices
    tab1.h0_row = 0
    tab1.h1_row = 1
    tab1.tt_row = 2
    tab1.h2_row = 3
    tab1.axis_row = 4
    tab1.start_row = 5
    tab1.end_row = 6
    tab1.step_row = 7
    tab1.iter_row = 8
    tab1.speed_row = 9
    tab1.ramp_v_row = 10
    tab1.dwell_row = 11
    tab1.h3_row = 12
    tab1.sys_row = 13
    tab1.st_row = 14
    tab1.op_row = 15
    tab1.temp_row = 16
    tab1.com_row = 17
    tab1.folder_row = 18
    tab1.h4_row = 19
    tab1.run_row = 20
    tab1.out_row = 21

    window.rowconfigure(tab1.out_row, minsize=4)

    # Create horizontal separators
    ttk.Separator(master=tab1, orient='horizontal').grid(row=tab1.h1_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab1, orient='horizontal').grid(row=tab1.h2_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab1, orient='horizontal').grid(row=tab1.h3_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab1, orient='horizontal').grid(row=tab1.h4_row, column=0, columnspan=4, sticky='ew')

    # Adjust column weights so the vertical separator aligns correctly
    tab1.columnconfigure(3, weight=1)
    tab1.columnconfigure(4, weight=1)
    
    # Add the vertical separator to the frame
    ttk.Separator(master=tab1, orient='vertical').grid(row=tab1.h1_row, column=4, rowspan=21, sticky='nsw', pady=(4, 0))
    
    # Load stored data or set defaults
    ms_axis_value = stored_data.get("axis_name", "X")
    ms_start_value = stored_data.get("start_position", 10)
    ms_end_value = stored_data.get("end_position", 30)
    ms_step_value = stored_data.get("step_size", 15)
    ms_iter_value = stored_data.get("iterations", 1)
    ms_speed_value = stored_data.get("speed", 5)
    ms_ramp_v_value = stored_data.get("ramp_rate", 1000)
    ms_dwell_value = stored_data.get("dwell", 1)
    ms_unit_value = stored_data.get("units", 'mm')
    ms_err_unit_value = stored_data.get("error_units", 'mm')
    ms_sample_value = stored_data.get("sample_rate", "1 kHz")
    ms_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ms_st_value = stored_data.get("part_number", '"Part Number"')
    ms_opName_value = stored_data.get("operator", '"Your Initials"')
    ms_temp_value = stored_data.get("temp", 20)
    ms_comm_value = stored_data.get("comments", "")

    def start_moveandsettletest():
        global_state.reset()
        ms_btn_run_rot.config(state=tk.DISABLED)
        threading.Thread(target=run_moveandsettletest).start()
        #threading.Thread(target=moveandsettle_live_plot).start()

    def run_moveandsettletest():
        # Save user inputs before closing
        user_data = {
            "axis_name": ms_axis.get(),
            "start_position": ms_start.get(),
            "end_position": ms_end.get(),
            "step_size": ms_step.get(),
            "iterations": ms_iter.get(),
            "speed": ms_speed.get(),
            "ramp_rate": ms_ramp_v.get(),
            "dwell": ms_dwell.get(),
            "units": ms_unit.get(),
            "error_units": ms_err_unit.get(),
            "sample_rate": ms_sample.get(),
            "system_serial_number": ms_sys.get(),
            "part_number": ms_st.get(),
            "operator": ms_opName.get(),
            "temp": ms_temp.get(),
            "comments": ms_comm.get()
        }
        save_user_inputs(user_data)
        try:
            moveandsettletest()
            ms_data_filtering()            
            ms_process_data(folder)
        finally:
            gc.collect()  
            if global_state.clientsocket:
                global_state.clientsocket.close()
            window.after(0, ms_btn_run_rot.config, {'state': tk.NORMAL})
            
    def moveandsettletest():
        syst.stdout = logger1
        global folder
        folder = filedialog.askdirectory(title="Select Data File Location")
        axis = str(ms_axis.get())
        sample_rate = ms_get_sample_rate_value()
        step_size = int(ms_step.get())
        start_pos = int(ms_start.get())
        end_pos = int(ms_end.get())
        probe_axis = 'None'
        speed = int(ms_speed.get())
        num_cycles = int(ms_iter.get())
        dwell = int(ms_dwell.get())
        ramp_value = int(ms_ramp_v.get())
        units = str(ms_unit.get())
        error_units = str(ms_err_unit.get())
        
        try:
            controller = a1.Controller.connect()
            controller.start()
        except:
            connection_type = controller_def()
            if connection_type == 'yes':
                try:
                    controller = a1.Controller.connect_usb()
                    controller.start()
                except:
                    messagebox.showerror('Connection Error', 'Check connections and try again')
            else:
                messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
        connected_axes = {}
        non_virtual_axes = []

        number_of_axes = controller.runtime.parameters.axes.count

        if number_of_axes <= 12:
            for axis_index in range(0,11):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index

            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')    
        else:
            for axis_index in range(0,32):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
            
            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')

            global_state.ms = move_and_settle(axis, sample_rate, step_size, [start_pos, end_pos], probe_axis, 
                                              direction=direction, 
                                              speed=speed, 
                                              num_cycles=num_cycles, 
                                              dwell=dwell, 
                                              ramp_value=ramp_value,
                                              ramp_type = a1.RampType.SCurve,
                                              units=units,
                                              error_units=error_units,
                                              folder=folder
                                            )
            global_state.ms.test(controller)
    def get_latest_timestamped_folder(base_folder):
        # Regular expression pattern to match your folder naming format
        pattern = re.compile(r"Step And Settle Test Data-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")

        # List all directories in the base folder
        all_folders = [os.path.join(base_folder, d) for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
        
        # Filter out folders that match the timestamp pattern
        time_stamped_folders = []
        for folder in all_folders:
            match = pattern.search(folder)
            if match:
                time_stamped_folders.append(folder)
    
        if not time_stamped_folders:
            raise ValueError("No folders found with the expected timestamp format.")

        # Sort folders by their timestamp
        latest_folder = max(time_stamped_folders, key=lambda folder: datetime.strptime(pattern.search(folder).group(1), "%Y-%m-%d_%H-%M-%S"))
        
        return latest_folder
    def ms_data_filtering():
        def apply_button_click():
            butter_func()
            filter_window.destroy()
        def reset_func():
            pos_fbk_copy = copy.deepcopy(global_state.ms.pos_fbk)
            global_state.ms.pos_fbk = pos_fbk_copy
            global_state.Comments = ms_comm.get()
            messagebox.showinfo("Filters Reset", "Filters have been reset.")
    
        def butter_func():
            omega_c = omega.get()
            order = order_.get()
            type_ = type_dropdown.get()
            type_var = filter_type_map[type_]
            global_state.ms.butter(a1data.mode.pos_fbk, omega_c, order, type_var)
            global_state.Comments = f'\n{type_var} pass butterworth filter \nwith a {omega_c} Hz cut-off frequency \napplied'
            messagebox.showinfo("Butterworth Filter Applied", "Butterworth Filter Applied")
        
        # Create a new Toplevel window instead of a new Tk window
        filter_window = tk.Toplevel()
        filter_window.title("Data Filtering")
        filter_window.grab_set()

        custom_title_font = ("Bold", 16)
        custom_header1_font = ("Bold", 14)
        custom_header2_font = ("Bold", 12)
        

        # Labels
        label = tk.Label(filter_window, text="Data Filtering:", font=custom_title_font)
        label.grid(row=0, column=0, padx=10, pady=10)

        # Butterworth Filter Parameters
        filter_label = tk.Label(filter_window, text="Butterworth Filter Parameters:", font=custom_header1_font)
        filter_label.grid(row=1, column=0, padx=10, pady=10)

        omega_c_label = tk.Label(filter_window, text="Cut-off Frequency (Hz):", font=custom_header2_font)
        omega_c_label.grid(row=2, column=0, padx=10, pady=5)
        omega = tk.DoubleVar(value=250)
        omega_c_entry = tk.Entry(filter_window, textvariable=omega)
        omega_c_entry.grid(row=3, column=0, padx=10, pady=2)

        order_label = tk.Label(filter_window, text="Order:", font=custom_header2_font)
        order_label.grid(row=4, column=0, padx=10, pady=5)
        order_ = tk.IntVar(value=2)
        order_entry = tk.Entry(filter_window, textvariable=order_)
        order_entry.grid(row=5, column=0, padx=10, pady=2)

        type_label = tk.Label(filter_window, text="Type:", font=custom_header2_font)
        type_label.grid(row=6, column=0, padx=10, pady=5)
        
        type_ = tk.StringVar(value='low')
        type_dropdown = ttk.Combobox(filter_window, textvariable=type_)
        type_dropdown['values'] = ("High Pass", "Low Pass")
        type_dropdown.current(1)  # Default to "Low Pass"
        type_dropdown.grid(row=7, column=0, padx=10, pady=2)
        
        # Mapping of the dropdown values to the filter types
        filter_type_map = {
            "High Pass": "high",
            "Low Pass": "low"
        }

        reset_button = tk.Button(filter_window, text="Reset Filters Applied", command=reset_func)
        reset_button.grid(row=8, column=0, padx=10, pady=10)

        apply_button = tk.Button(filter_window, text="Apply Filter", command=apply_button_click)
        apply_button.grid(row=9, column=0, padx=10, pady=10)
        
        # Ensure the window is fully initialized before calculating geometry
        filter_window.update_idletasks()
    
        # Get the width and height of the window
        window_width = filter_window.winfo_width()
        window_height = filter_window.winfo_height()
        
        # Calculate the screen's width and height
        screen_width = filter_window.winfo_screenwidth()
        screen_height = filter_window.winfo_screenheight()
    
        # Calculate the x and y coordinates to center the window
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
    
        # Set the geometry of the window to center it on the screen
        filter_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        filter_window.wait_window()
        
    def ms_process_data(folder):
        global desired_time,pos_tolerance
        def average_button():
            global avg
            if checkbox_var.get() == 1:  # Checkbox is checked
                avg = 'Average'
                df["state"] = tk.DISABLED
            else:  # Checkbox is unchecked
                avg = None
                df["state"] = tk.NORMAL
        
        def process_button_click():
            process_results()
        
        def next_function():
            process_window.destroy()
            ms_PDF(latest_folder)
        
        # Create a new Toplevel window instead of a new Tk window
        process_window = tk.Toplevel()
        process_window.title("Data Processing")
        
        process_window.lift()
        
        custom_font = ("Bold", 16)
        
        # Labels
        label = tk.Label(process_window, text="Post Processing:", font=custom_font)
        label.grid(row=0, column=0, padx=10, pady=10)
        
        # Add widgets for data processing and plotting
        lbl_analysis = tk.Label(process_window, text="Plotting and Data Analysis:", font=("Bold", 12), fg="black")
        lbl_analysis.grid(row=1, column=0, pady=10)
        
        position_tolerance = tk.DoubleVar(value=0.00005)
        pos_tolerance_entry = tk.Entry(process_window, textvariable=position_tolerance)
        pos_tolerance_entry.grid(row=2, column=0, pady=10)
        pos_tolerance = position_tolerance.get()
        
        label_plot = tk.Label(process_window, text="Select 'Average' to average signals")
        label_plot.grid(row=3, column=0, pady=10)
        
        # Add a Tkinter variable to track the state of the checkbox
        checkbox_var = tk.IntVar()
        
        ent_plot = tk.Checkbutton(process_window, text='Average', variable=checkbox_var, command=average_button)
        ent_plot.grid(row=4, column=0, pady=2)
        
        base_folder = folder
        latest_folder = get_latest_timestamped_folder(base_folder)

        data_files = [file for file in os.listdir(latest_folder) if 'csv' in file]

        # Dropdown for selecting DataFrame index
        df_options = data_files  # Example options, replace with actual data

        df = ttk.Combobox(process_window, values=df_options)
        df.current(0)  # Set default selection to the first DataFrame
        df.grid(row=5, column=0, pady=10)
                
        desired_time = tk.DoubleVar(value=0.5)
        desired_time_entry = tk.Entry(process_window, textvariable=desired_time)
        desired_time_entry.grid(row=6, column=0, pady=10)
        desired_time = desired_time.get()
        
        def get_canvas_size_in_inches(canvas_frame, dpi=100):
            """Get the size of the canvas in inches."""
            width_in_pixels = canvas_frame.winfo_width()
            height_in_pixels = canvas_frame.winfo_height()
            
            width_in_inches = width_in_pixels / dpi
            height_in_inches = height_in_pixels / dpi
            
            return width_in_inches, height_in_inches
        
        def embed_plot_in_canvas(plot, canvas_frame):
        
            plot.set_size_inches(20, 10)
            
            # Embed the plot in the Tkinter canvas
            canvas = FigureCanvasTkAgg(plot, master=canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
        def process_results():
            # Example processing and plotting function
            global data_dict, aero_dict
            
            plt.clf()
            
            #data_dict = global_state.ms.data_analysis(error_metric, process_window_size.get(), calc_direction, position_tolerance.get(), df=df.get())
            aero_dict = global_state.ms.aero_move_and_settle(desired_time, pos_tolerance,sig=avg,df=df.get())
            
            # Embed the metric plot in the Tkinter GUI
            plot_frame = tk.Frame(master=tab1)
            plot_frame.grid(row=tab1.h2_row, column=4, rowspan=16, columnspan=3, padx=(3,0), pady=(5, 0), sticky='nsew')
            
            canvas_size = get_canvas_size_in_inches(plot_frame)
            
            # Plot the metric plot using your existing function
            plt.rcParams.update({'font.size': 10})
            aero_plot = global_state.ms.GUI_plot(aero_dict, canvas_size, figNum=3, legend_size=7,step_num=df.get()) 
            
            embed_plot_in_canvas(aero_plot,plot_frame)
            
            #print('The ASME Move and Settle time for {} is {} seconds'.format(error_metric_w.get(), data_dict['Move and Settle Time']))
            print('The Aerotech Move and Settle Time is {} seconds'.format(aero_dict['Aerotech Move and Settle Time']))
        
        btn_process_data = tk.Button(process_window, text="Process Data", command=process_button_click)
        btn_process_data.grid(row=7, column=0, pady=10)
        
        btn_process_data = tk.Button(process_window, text="Next", command=next_function)
        btn_process_data.grid(row=8, column=0, pady=10)
        
        # Ensure the window is fully initialized before calculating geometry
        process_window.update_idletasks()
    
        # Get the width and height of the window
        window_width = process_window.winfo_width()
        window_height = process_window.winfo_height()
        
        # Calculate the screen's width and height
        screen_width = process_window.winfo_screenwidth()
        screen_height = process_window.winfo_screenheight()
    
        # Calculate the x and y coordinates to center the window
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
    
        # Set the geometry of the window to center it on the screen
        process_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        process_window.wait_window()

    def ms_PDF(folder):
        def pdf_button_click():
            gen_PDF()
            
        def end_test():
            pdf_window.destroy()
            
        # Create a new Toplevel window instead of a new Tk window
        pdf_window = tk.Toplevel()
        pdf_window.title("Generate PDF and CSV")
    
        title_font = ("Bold", 16)
        header_font = ("Bold", 12)
        # Labels
        label = tk.Label(pdf_window, text="Create PDF and CSV:", font=title_font)
        label.grid(row=0, column=0, padx=10, pady=10)
        
        # Entry for output file name
        output_file_label = tk.Label(pdf_window, text="File Name:", font=header_font)
        output_file_label.grid(row=1, column=0, pady=10)
        output_file_entry = tk.Entry(pdf_window)
        output_file_entry.insert(0, "moveandsettle.pdf")
        output_file_entry.grid(row=2, column=0, pady=2)
        
        def gen_PDF():
            # Collect input values
            axis = str(ms_axis.get())
            step_size = int(ms_step.get())
            speed = int(ms_speed.get())
            units = str(ms_unit.get())
            sys_serial = str(ms_sys.get())
            st_serial = str(ms_st.get())
            comments = str(ms_comm.get())
            oper = str(ms_opName.get())
            temp = float(ms_temp.get())
            t = global_state.ms.time_array
        
            # Create the figure and axes using the Aerotech format template
            fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
        
            # Set appropriate figsize to fit the PDF layout
            fig.set_size_inches(11, 8.5)  # Full page size
            
            # Get the current position of ax1
            pos1 = ax1.get_position()  # Returns a Bbox object with [left, bottom, width, height]
            
            # Define scaling factors
            scale_width = 0.9  # Scale ax1 width to 80% of its current size
            scale_height = 1  # Scale ax1 height to 80% of its current size
            
            # Calculate new dimensions for ax1
            new_width = pos1.width * scale_width
            new_height = pos1.height * scale_height
            
            # Calculate new position to keep ax1 centered horizontally and vertically
            new_left = pos1.x0 + (pos1.width - new_width) / 2
            new_bottom = pos1.y0 + (pos1.height - new_height) / 2
        
            # Set the new position and size for ax1
            ax1.set_position([new_left, new_bottom, new_width, new_height])
            
            # Get the size of each axis in inches
            ax2_width, ax2_height = ax2.get_position().size
            ax3_width, ax3_height = ax3.get_position().size
            ax4_width, ax4_height = ax4.get_position().size
        
            # Scale the font size based on the axis size
            font_size_ax2 = max(7, ax2_height * 40)
            font_size_ax3 = max(7, ax3_height * 40)
            font_size_ax4 = max(7, ax4_height * 40)

            # Plot directly on ax1 (instead of saving and reloading an image)
            global_state.ms.pdf_plot(aero_dict, ax=ax1, legend_size=10)
        
            # Results Text Box (ax2)
            ax2.text(0.02, .7, 'Aerotech \nmove-and-settle time: {:.3f} sec'.format(aero_dict['Aerotech Move and Settle Time']),
                     color='black', size=font_size_ax2)
        
            # Comments Text Box (ax3)
            ax3.text(.02, .8, 'Serial Number: {}'.format(sys_serial), color='black', size=font_size_ax3)
            ax3.text(.02, .725, 'Model Number: {}'.format(st_serial), color='black', size=font_size_ax3)
            ax3.text(.02, .65, 'Operator: {}'.format(oper), color='black', size=font_size_ax3)
            ax3.text(.02, .575, 'Comments: {}'.format(comments), color='black', size=font_size_ax3, verticalalignment='top')
        
            # Test Conditions Text Box (ax4)
            degree_sign = u'\N{DEGREE SIGN}'
            ax4.text(.02, .8, 'Temperature: {} {}C'.format(temp, degree_sign), color='black', size=font_size_ax4)
            ax4.text(.02, .725, 'Direction: {}'.format("direction"), color='black', size=font_size_ax4)
            ax4.text(.02, .65, 'Axis Bounds: [{} {}, {} {}]'.format(global_state.ms.frame[0], units, global_state.ms.frame[1], units), color='black', size=font_size_ax4)
            ax4.text(.02, .575, 'Speed: {} {}/s'.format(speed, units), color='black', size=font_size_ax4)
            ax4.text(.02, .5, 'Sample Rate: {} Hz'.format(1/t[1]), color='black', size=font_size_ax4)
            ax4.text(.02, .425, 'Sample Time: {} seconds'.format(np.max(t) + t[1]), color='black', size=font_size_ax4)
            ax4.text(.02, .350, 'Axis: {}'.format(axis), color='black', size=font_size_ax4)
            ax4.text(.02, .275, 'Commanded Step: {:.3e} {}'.format(step_size, units), color='black', size=font_size_ax4)
            ax4.text(.02, .200, 'Position Tolerance: {} {}'.format("position_tolerance", units), color='black', size=font_size_ax4)
        
            # Save the figure as a PDF
            start_path = ('O:/')
            sys_serial = str(ms_sys.get())
            folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
            pdf_file_path = folder_path + '/Customer Files/Plots'
            folder_name = 'Step And Settle Plots'
            new_file_path = os.path.join(pdf_file_path,folder_name)
            os.makedirs(new_file_path,exist_ok=True)
            
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            new_folder_path = os.path.join(new_file_path, f"{current_time}")
            os.makedirs(new_folder_path, exist_ok=True)
            output_file = str(sys_serial + '-' + str(ms_axis.get()) + "_Step and Settle.pdf")
            save_file = new_folder_path + '/' + output_file
        
            # Save the figure with tight bounding box
            fig.savefig(save_file, bbox_inches='tight')
            print('PDF saved')
            
            global_state.ms.GUI_plot_plotly(aero_dict, new_folder_path, ax=ax1, legend_size=20)
            
        # Button to generate PDF
        gen_pdf_button = tk.Button(pdf_window, text="Generate PDF", command=gen_PDF)
        gen_pdf_button.grid(row=3, column=0, pady=5)
    
        # Entry for CSV file name
        csv_file_label = tk.Label(pdf_window, text="CSV Name:", font=header_font)
        csv_file_label.grid(row=4, column=0, pady=10)
        csv_file_entry = tk.Entry(pdf_window)
        csv_file_entry.insert(0, "ms.csv")
        csv_file_entry.grid(row=5, column=0, pady=2)
    

        # Function to save CSV
        def save_CSV():
            def get_latest_timestamped_folder(base_folder):
                # Regular expression pattern to match your folder naming format
                pattern = re.compile(r"Step And Settle Test Data-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})")

                # List all directories in the base folder
                all_folders = [os.path.join(base_folder, d) for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]

                # Filter out folders that match the timestamp pattern
                time_stamped_folders = []
                for folder in all_folders:
                    match = pattern.search(folder)
                    if match:
                        time_stamped_folders.append(folder)
            
                if not time_stamped_folders:
                    raise ValueError("No folders found with the expected timestamp format.")

                # Sort folders by their timestamp
                latest_folder = max(time_stamped_folders, key=lambda folder: datetime.strptime(pattern.search(folder).group(1), "%Y-%m-%d_%H-%M-%S"))
                
                return latest_folder
            start_path = 'O:/'
            sys_serial = str(ms_sys.get())
            
            # Find the correct folder path
            folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
            csv_file_path = os.path.join(folder_path, 'TestData')
            
            # Define the folder name and create the directory with timestamp
            folder_name = 'Step And Settle Data'
            csv_folder_path = os.path.join(csv_file_path,folder_name)
            os.makedirs(csv_folder_path, exist_ok=True)
            
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  
            new_folder_path = os.path.join(csv_folder_path, f"{current_time}")
            os.makedirs(new_folder_path)
            
            
            # Construct the destination file path
            base_folder = folder
            latest_folder = base_folder
            
            # Move the file from the source location to the new folder
            for item in os.listdir(latest_folder):
                source_item = os.path.join(latest_folder, item)
                destination_item = os.path.join(new_folder_path, item)
                
                # Check if it's a file or directory
                if os.path.isdir(source_item):
                    shutil.move(source_item, destination_item)
                else:
                    shutil.move(source_item, destination_item)
            
            print(f'All contents moved to {new_folder_path}')
     
        # Button to save CSV
        save_csv_button = tk.Button(pdf_window, text="Save CSV", command=save_CSV)
        save_csv_button.grid(row=8, column=0, pady=10)

        # Button to save CSV
        save_csv_button = tk.Button(pdf_window, text="Finish Test", command=end_test)
        save_csv_button.grid(row=9, column=0, pady=10)
        
        # Center the window on the screen
        pdf_window.update_idletasks()
        window_width = pdf_window.winfo_width()
        window_height = pdf_window.winfo_height()
        screen_width = pdf_window.winfo_screenwidth()
        screen_height = pdf_window.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        pdf_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")        
        
        pdf_window.wait_window()
    def ms_test_type_def():
        global direction
        if ms_direction.get() == "uni":
            direction = a1data.mode.Unidirectional
        elif ms_direction.get() == "bi":
            direction = a1data.mode.Bidirectional
        else:
            direction = 'None'
    
    # Function to get the selected sample rate value
    def ms_get_sample_rate_value():
        selected_text = ms_sample.get()  # Get the selected display text, e.g., '1 kHz'
        # Find the actual numeric value corresponding to the selected text
        for option in ms_sample_options:
            if option[0] == selected_text:
                return option[1]
        return None  # If not found, return None or handle it as needed
    
    def open_rotary_Plot():
        axis = ms_axis.get()
        sys_serial = ms_sys.get()

        start_path = ('O:/')
        folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
        pdf_file_path = folder_path + '/Customer Files/Plots'

        if os.path.exists(pdf_file_path):
            try:
                output_file = str(sys_serial + '-' + axis + "_Accuracy.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
            try:
                output_file = str(sys_serial + '-' + axis + "_Verification.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
        else:
            print(f"File '{pdf_file_path}' does not exist.")
    
    # Load stored data or set defaults
    ms_axis_value = stored_data.get("axis_name", "X")
    ms_start_value = stored_data.get("start_position", 10)
    ms_end_value = stored_data.get("end_position", 30)
    ms_step_value = stored_data.get("step_size", 15)
    ms_iter_value = stored_data.get("iterations", 1)
    ms_speed_value = stored_data.get("speed", 5)
    ms_ramp_v_value = stored_data.get("ramp_rate", 1000)
    ms_dwell_value = stored_data.get("dwell", 1)
    ms_unit_value = stored_data.get("units", 'mm')
    ms_err_unit_value = stored_data.get("error_units", 'mm')
    ms_sample_value = stored_data.get("sample_rate", "1 kHz")
    ms_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ms_st_value = stored_data.get("part_number", '"Part Number"')
    ms_opName_value = stored_data.get("operator", '"Your Initials"')
    ms_temp_value = stored_data.get("temp", 20)
    ms_comm_value = stored_data.get("comments", "")
    
    # Create the UI elements and assign the stored values
    ms_lbl_test = tk.Label(master=tab1, text="Select Test Type:")
    ms_lbl_test.grid(row=tab1.tt_row, column=0, padx=5, pady=5)

    ms_direction = tk.StringVar(value=0)
    ms_uni_dir = tk.Radiobutton(master=tab1, text="Unidirectional", variable=ms_direction, value="uni", command=ms_test_type_def)
    ms_uni_dir.grid(row=tab1.tt_row, column=1, padx=5, pady=5)

    ms_bi_dir = tk.Radiobutton(master=tab1, text="Bidirectional", variable=ms_direction, value="bi", command=ms_test_type_def)
    ms_bi_dir.grid(row=tab1.tt_row, column=2, padx=5, pady=5)
    
    ms_lbl_axis = tk.Label(master=tab1, text="Axis Name", width=25, height=1)
    ms_lbl_axis.grid(row=tab1.axis_row, column=0, padx=5, pady=5)

    ms_axis = tk.StringVar(value=ms_axis_value)
    ms_ent_axis = tk.Entry(master=tab1, textvariable=ms_axis, width=25)
    ms_ent_axis.grid(row=tab1.axis_row, column=1, padx=5, pady=5)

    ms_lbl_st = tk.Label(master=tab1, text="Start Position", width=25, height=1)
    ms_lbl_st.grid(row=tab1.start_row, column=0, padx=5, pady=5)

    ms_start = tk.DoubleVar(value=ms_start_value)
    ms_ent_start_pos = tk.Entry(master=tab1, textvariable=ms_start, width=25)
    ms_ent_start_pos.grid(row=tab1.start_row, column=1, padx=5, pady=5)

    ms_lbl_end_pos = tk.Label(master=tab1, text="End Position", width=25, height=1)
    ms_lbl_end_pos.grid(row=tab1.end_row, column=0, padx=5, pady=5)

    ms_end = tk.DoubleVar(value=ms_end_value)
    ms_ent_end_pos = tk.Entry(master=tab1, textvariable=ms_end, width=25)
    ms_ent_end_pos.grid(row=tab1.end_row, column=1, padx=5, pady=5)

    ms_lbl_step_size = tk.Label(master=tab1, text="Step Size", width=25, height=1)
    ms_lbl_step_size.grid(row=tab1.step_row, column=0, padx=5, pady=5)

    ms_step = tk.DoubleVar(value=ms_step_value)
    ms_ent_step_size = tk.Entry(master=tab1, textvariable=ms_step, width=25)
    ms_ent_step_size.grid(row=tab1.step_row, column=1, padx=5, pady=5)

    ms_lbl_iter = tk.Label(master=tab1, text="Iterations")
    ms_lbl_iter.grid(row=tab1.iter_row, column=0, padx=5, pady=5)

    ms_iter = tk.DoubleVar(value=ms_iter_value)
    ms_ent_iter = tk.Entry(master=tab1, textvariable=ms_iter, width=25)
    ms_ent_iter.grid(row=tab1.iter_row, column=1, padx=5, pady=5)

    ms_lbl_speed = tk.Label(master=tab1, text="Velocity", width=25, height=1)
    ms_lbl_speed.grid(row=tab1.speed_row, column=0, padx=5, pady=5)

    ms_speed = tk.StringVar(value=ms_speed_value)
    ms_ent_speed = tk.Entry(master=tab1, textvariable=ms_speed, width=25)
    ms_ent_speed.grid(row=tab1.speed_row, column=1, padx=5, pady=5)

    ms_lbl_ramp_rate = tk.Label(master=tab1, text="Ramp Rate")
    ms_lbl_ramp_rate.grid(row=tab1.ramp_v_row, column=0, padx=5, pady=5)

    ms_ramp_v = tk.StringVar(value=ms_ramp_v_value)
    ms_ent_ramp_rate = tk.Entry(master=tab1, textvariable=ms_ramp_v, width=25)
    ms_ent_ramp_rate.grid(row=tab1.ramp_v_row, column=1, padx=5, pady=5)
    
    ms_lbl_dwell = tk.Label(master=tab1, text="Dwell")
    ms_lbl_dwell.grid(row=tab1.dwell_row, column=0, padx=5, pady=5)

    ms_dwell = tk.StringVar(value=ms_dwell_value)
    ms_ent_dwell = tk.Entry(master=tab1, textvariable=ms_dwell, width=25)
    ms_ent_dwell.grid(row=tab1.dwell_row, column=1, padx=5, pady=5)
    
    ms_lbl_units = tk.Label(master=tab1, text="Units:", width=25, height=1)
    ms_lbl_units.grid(row=tab1.axis_row, column=2, padx=5, pady=5)
    
    ms_unit_options = ['mm', 'um', 'nm', 'deg']
    ms_unit = tk.StringVar(value=ms_unit_value)
    ms_unit_menu = tk.OptionMenu(tab1, ms_unit, *ms_unit_options)
    ms_unit_menu.grid(row=tab1.start_row, column=2, padx=5, pady=5)
    
    ms_lbl_err_units = tk.Label(master=tab1, text="Error Units:", width=25, height=1)
    ms_lbl_err_units.grid(row=tab1.axis_row, column=3, padx=5, pady=5)
    
    ms_err_unit_options = ['mm', 'um', 'nm', 'arcsec', 'deg']
    ms_err_unit = tk.StringVar(value=ms_err_unit_value)
    ms_err_unit_menu = tk.OptionMenu(tab1, ms_err_unit, *ms_err_unit_options)
    ms_err_unit_menu.grid(row=tab1.start_row, column=3, padx=5, pady=5)
    
    ms_lbl_sample = tk.Label(master=tab1, text="Sample Rate:", width=25, height=1)
    ms_lbl_sample.grid(row=tab1.iter_row, column=2, padx=5, pady=5)
    
    ms_sample_options = [('1 kHz', 1000), ('10 kHz', 10000), ('20 kHz', 20000), ('100 kHz', 100000), ('200 kHz', 200000)]
    ms_sample = tk.StringVar(value=ms_sample_value)
    ms_sample_menu = tk.OptionMenu(tab1, ms_sample, *[option[0] for option in ms_sample_options])
    ms_sample_menu.grid(row=tab1.speed_row, column=2, padx=5, pady=5)

    ms_lbl_serial = tk.Label(master=tab1, text="System Serial Number", width=25, height=1)
    ms_lbl_serial.grid(row=tab1.sys_row, column=0, padx=5, pady=5)

    ms_sys = tk.StringVar(value=ms_sys_value)
    ms_ent_serial = tk.Entry(master=tab1, textvariable=ms_sys, width=25)
    ms_ent_serial.grid(row=tab1.sys_row, column=1, columnspan=3, padx=5, pady=5)

    ms_lbl_st_model = tk.Label(master=tab1, text="Part Number", width=25, height=1)
    ms_lbl_st_model.grid(row=tab1.st_row, column=0, padx=5, pady=5)

    ms_st = tk.StringVar(value=ms_st_value)
    ms_ent_st_model = tk.Entry(master=tab1, textvariable=ms_st, width=25)
    ms_ent_st_model.grid(row=tab1.st_row, column=1, columnspan=3, padx=5, pady=5)

    ms_lbl_op = tk.Label(master=tab1, text="Operator", width=25, height=1)
    ms_lbl_op.grid(row=tab1.op_row, column=0, padx=5, pady=5)

    ms_opName = tk.StringVar(value=ms_opName_value)
    ms_ent_op = tk.Entry(master=tab1, textvariable=ms_opName, width=25)
    ms_ent_op.grid(row=tab1.op_row, column=1, columnspan=3, padx=5, pady=5)

    ms_lbl_temp = tk.Label(master=tab1, text="Temp", width=25, height=1)
    ms_lbl_temp.grid(row=tab1.temp_row, column=0, padx=5, pady=5)

    ms_temp = tk.DoubleVar(value=ms_temp_value)
    ms_ent_temp = tk.Entry(master=tab1, textvariable=ms_temp, width=25)
    ms_ent_temp.grid(row=tab1.temp_row, column=1, columnspan=3, padx=5, pady=5)

    ms_lbl_comments = tk.Label(master=tab1, text="Comments", width=25, height=1)
    ms_lbl_comments.grid(row=tab1.com_row, column=0, padx=5, pady=5)

    ms_comm = tk.StringVar(value=ms_comm_value)
    ms_ent_comments = tk.Entry(master=tab1, textvariable=ms_comm, width=25)
    ms_ent_comments.grid(row=tab1.com_row, column=1, columnspan=3, padx=5, pady=5)

    #btn_import_rot = tk.Button(master=tab1, text="Import Data", width=30, height=1, command=import_data_rotary)
    #btn_import_rot.grid(row=tab1.run_row, column=1, padx=5, pady=5)

    ms_lbl_import_rot = tk.Label(master=tab1, text='', anchor='w')
    ms_lbl_import_rot.grid(row=tab1.run_row, column=1, padx=5, pady=5, columnspan=3)

    ms_btn_run_rot = tk.Button(master=tab1, text="Run", width=25, height=1, command=start_moveandsettletest)
    ms_btn_run_rot.grid(row=tab1.run_row, column=0, padx=5, pady=5)

    ms_btn_open_rot = tk.Button(master=tab1, text="Open Plot", width=25, height=1, command=open_rotary_Plot)
    ms_btn_open_rot.grid(row=tab1.run_row, column=2, padx=5, pady=5)

    frame = tk.Frame(master=tab1)

    txt_outStr = tk.Text(master=frame, state=tk.DISABLED, height=10, fg='white', bg='black')
    outStr_scroll = tk.Scrollbar(master=frame, orient=tk.VERTICAL)

    txt_outStr.configure(yscrollcommand=outStr_scroll.set)
    outStr_scroll.config(command=txt_outStr.yview)

    txt_outStr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outStr_scroll.pack(side=tk.LEFT, fill=tk.Y)

    frame.grid(row=tab1.out_row, column=0, columnspan=7, padx=5, pady=5, sticky='nsew')

    logger1 = TextLogger(txt_outStr)
    
    tab1.grid_rowconfigure(tab1.out_row, weight=1)
    tab1.grid_columnconfigure(0, weight=1)
    
    def ms_on_closing():
        # Save user inputs before closing
        user_data = {
            "axis_name": ms_axis.get(),
            "start_position": ms_start.get(),
            "end_position": ms_end.get(),
            "step_size": ms_step.get(),
            "iterations": ms_iter.get(),
            "speed": ms_speed.get(),
            "ramp_rate": ms_ramp_v.get(),
            "dwell": ms_dwell.get(),
            "units": ms_unit.get(),
            "error_units": ms_err_unit.get(),
            "sample_rate": ms_sample.get(),
            "system_serial_number": ms_sys.get(),
            "part_number": ms_st.get(),
            "operator": ms_opName.get(),
            "temp": ms_temp.get(),
            "comments": ms_comm.get()
        }
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", ms_on_closing)
    
# =============================================================================
# 
# Tab 2:
#
#
# Jitter Test    
# 
# 
# 
# =============================================================================
    # Configure columns and rows
    tab2.columnconfigure([0, 1, 2, 3, 4, 5, 6], weight=1, minsize=700 / 4, uniform='column')
    tab2.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], weight=1, minsize=1)

    # Define row indices
    tab2.h1_row = 0
    tab2.axis_row = 1
    tab2.sig_row = 2
    tab2.units_row = 3
    tab2.err_row = 4
    tab2.samp_row = 5
    tab2.dwell_row = 6
    tab2.dir_row = 7
    tab2.h2_row = 8
    tab2.sys_row = 9
    tab2.st_row = 10
    tab2.op_row = 11
    tab2.temp_row = 12
    tab2.com_row = 13
    tab2.h3_row = 14
    tab2.run_row = 15
    tab2.out_row = 16

    window.rowconfigure(tab2.out_row, minsize=4)

    # Create horizontal separators
    ttk.Separator(master=tab2, orient='horizontal').grid(row=tab2.h1_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab2, orient='horizontal').grid(row=tab2.h2_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab2, orient='horizontal').grid(row=tab2.h3_row, column=0, columnspan=4, sticky='ew')

    # Adjust column weights so the vertical separator aligns correctly
    tab2.columnconfigure(3, weight=1)
    tab2.columnconfigure(4, weight=1)
    
    # Add the vertical separator to the frame
    ttk.Separator(master=tab2, orient='vertical').grid(row=tab2.h1_row, column=4, rowspan=21, sticky='nsw', pady=(7, 0))    
    
    
    # Load stored data or set defaults
    ipj_axis_value = stored_data.get("axis_name", "X")
    ipj_signal_value = stored_data.get("signal", 0)
    ipj_probe_value = stored_data.get("probe_axis", 'X')
    ipj_sens_value = stored_data.get("scale factor (user units)", '0.0025')
    ipj_unit_value = stored_data.get("units", 'mm')
    ipj_err_unit_value = stored_data.get("error_units", 'mm')
    ipj_sample_value = stored_data.get("sample_rate", "1 kHz")
    ipj_dwell_value = stored_data.get("duration", 1)
    ipj_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ipj_st_value = stored_data.get("part_number", '"Part Number"')
    ipj_opName_value = stored_data.get("operator", '"Your Initials"')
    ipj_temp_value = stored_data.get("temp", 20)
    ipj_comm_value = stored_data.get("comments", "")
    ipj_direction_value = stored_data.get("direction", 'pos')
    

    def start_jittertest():
        global_state.reset()
        ipj_btn_run_rot.config(state=tk.DISABLED)
        threading.Thread(target=run_jittertest).start()
        #threading.Thread(target=moveandsettle_live_plot).start()

    def run_jittertest():
        # Save user inputs before closing
        user_data = {
            "axis_name": ipj_axis.get(),  # Entry widget
            "signal": ipj_signal_var.get(),  # OptionMenu
            "probe_axis": ipj_probe.get(),  # Entry widget
            "scale factor (user units)": ipj_sens.get(),  # Entry widget
            "units": ipj_unit.get(),  # OptionMenu
            "error_units": ipj_err_unit.get(),  # OptionMenu
            "sample_rate": ipj_samp.get(),  # OptionMenu
            "duration": ipj_dwell.get(),  # Entry widget
            "system_serial_number": ipj_sys.get(),  # Entry widget
            "part_number": ipj_st.get(),  # Entry widget
            "operator": ipj_opName.get(),  # Entry widget
            "temp": ipj_temp.get(),  # Entry widget
            "comments": ipj_comm.get(),  # Entry widget
            "direction": ipj_direction_var.get()  # Radiobutton selection
        }
        save_user_inputs(user_data)
        try:
            jittertest()
            ipj_data_filtering() 
            ipj_process_data()
            
        finally:
            gc.collect()  
            if global_state.clientsocket:
                global_state.clientsocket.close()
            window.after(0, ipj_btn_run_rot.config, {'state': tk.NORMAL})
            
    def jittertest():
        syst.stdout = logger2
        global folder
        Axis = str(ipj_axis.get())
        SamplingRate = ipj_get_sample_rate_value()
        TestTime = int(ipj_dwell.get())
        Direction = str(ipj_direction_var.get())
        Sensitivity = float(ipj_sens.get())
        ProbeAxis = str(ipj_probe.get())

        try:
            controller = a1.Controller.connect()
            controller.start()
        except:
            connection_type = controller_def()
            if connection_type == 'yes':
                try:
                    controller = a1.Controller.connect_usb()
                    controller.start()
                except:
                    messagebox.showerror('Connection Error', 'Check connections and try again')
            else:
                messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
        connected_axes = {}
        non_virtual_axes = []

        number_of_axes = controller.runtime.parameters.axes.count

        if number_of_axes <= 12:
            for axis_index in range(0,11):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index

            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')    
        else:
            for axis_index in range(0,32):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
            
            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')

            global_state.ipj = jitter(Axis, SamplingRate, TestTime, Direction, 
                                      Sensitivity, ProbeAxis, units = ipj_unit.get(),
                                      error_units = ipj_err_unit.get()
                                            )
            global_state.ipj.test(controller)
            
    def ipj_data_filtering():
        def apply_button_click():
            butter_func()
            filter_window.destroy()

        def reset_func():
            pos_fbk_copy = copy.deepcopy(global_state.ipj.pos_fbk)
            global_state.ipj.pos_fbk = pos_fbk_copy
            global_state.Comments = ipj_comm.get()
            print("Filters have been reset.")
    
        def remove_offset_func():
            global_state.ipj.remove_offset(mode)
            global_state.Comments += "\nDC offset removed"
            print("DC offset removed")
    
        def end_norm_func():
            global_state.ipj.endpoint_linear_norm(mode)
            global_state.Comments += "\nEndpoint Linear Normalization"
            print("Endpoint Linear Normalization applied")
    
        def square_norm_func():
            global_state.ipj.least_squares_linear_norm(mode)
            global_state.Comments += "\nLeast Squares Linear Normalization"
            print("Least Squares Linear Normalization applied")
    
        def butter_func():
            pos_fbk_copy = copy.deepcopy(global_state.ipj.pos_fbk)
            ai0_copy = copy.deepcopy(global_state.ipj.ai0)
            global_state.ipj.butter(mode, omega.get(), order_.get(), type_var.get())
            global_state.Comments += '\n{} pass Butterworth filter with a {} Hz cut-off frequency applied'.format(
                type_var.get(), omega.get()
            )
            print("Butterworth Filter Applied")
            
        def mode_def(*args):
            global mode
            if mode_var.get() == 'Position Feedback':
                mode = a1data.mode.pos_fbk
            elif mode_var.get() == 'Analog Input':
                mode = a1data.mode.ai0

        # Create a new Toplevel window
        filter_window = tk.Toplevel()
        filter_window.title("Data Filtering")
        filter_window.grab_set()
    
        custom_title_font = ("Bold", 16)
        custom_header1_font = ("Bold", 14)
        custom_header2_font = ("Bold", 12)
    
        # Labels
        label = tk.Label(filter_window, text="Data Filtering:", font=custom_title_font)
        label.grid(row=0, column=0, padx=10, pady=10)
    
        # Data Signal
        mode_var = tk.StringVar()
        mode_var.trace_add('write', mode_def)
        mode_label = tk.Label(filter_window, text="Data Signal:", font=custom_header2_font)
        mode_label.grid(row=1, column=0, padx=10, pady=5)
        mode_dropdown = ttk.Combobox(filter_window, textvariable=mode_var)
        mode_dropdown['values'] = ["Position Feedback", "Analog Input"]
        mode_dropdown.grid(row=2, column=0, padx=10, pady=2)
    
        # Filter Buttons
        remove_offset_button = tk.Button(filter_window, text="Remove DC Offset", command=remove_offset_func)
        remove_offset_button.grid(row=3, column=0, padx=10, pady=10)
    
        end_norm_button = tk.Button(filter_window, text="Endpoint Linear Normalization", command=end_norm_func)
        end_norm_button.grid(row=4, column=0, padx=10, pady=10)
    
        square_norm_button = tk.Button(filter_window, text="Least-Squares Linear Normalization", command=square_norm_func)
        square_norm_button.grid(row=5, column=0, padx=10, pady=10)
    
        # Butterworth Filter Parameters
        filter_label = tk.Label(filter_window, text="Butterworth Filter Parameters:", font=custom_header1_font)
        filter_label.grid(row=6, column=0, padx=10, pady=10)
    
        omega_c_label = tk.Label(filter_window, text="Cut-off Frequency (Hz):", font=custom_header2_font)
        omega_c_label.grid(row=7, column=0, padx=10, pady=5)
        omega = tk.DoubleVar(value=250)
        omega_c_entry = tk.Entry(filter_window, textvariable=omega)
        omega_c_entry.grid(row=8, column=0, padx=10, pady=2)
    
        order_label = tk.Label(filter_window, text="Order:", font=custom_header2_font)
        order_label.grid(row=9, column=0, padx=10, pady=5)
        order_ = tk.IntVar(value=2)
        order_entry = tk.Entry(filter_window, textvariable=order_)
        order_entry.grid(row=10, column=0, padx=10, pady=2)
    
        type_label = tk.Label(filter_window, text="Type:", font=custom_header2_font)
        type_label.grid(row=11, column=0, padx=10, pady=5)
        
        type_var = tk.StringVar(value='low')
        type_dropdown = ttk.Combobox(filter_window, textvariable=type_var)
        type_dropdown['values'] = ["High Pass", "Low Pass"]
        type_dropdown.grid(row=12, column=0, padx=10, pady=2)
    
        # Reset and Apply Buttons
        reset_button = tk.Button(filter_window, text="Reset Filters Applied", command=reset_func)
        reset_button.grid(row=13, column=0, padx=10, pady=10)
    
        apply_button = tk.Button(filter_window, text="Apply Filter", command=apply_button_click)
        apply_button.grid(row=14, column=0, padx=10, pady=10)
    
        # Ensure the window is fully initialized before calculating geometry
        filter_window.update_idletasks()
    
        # Get the width and height of the window
        window_width = filter_window.winfo_width()
        window_height = filter_window.winfo_height()
    
        # Calculate the screen's width and height
        screen_width = filter_window.winfo_screenwidth()
        screen_height = filter_window.winfo_screenheight()
    
        # Calculate the x and y coordinates to center the window
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
    
        # Set the geometry of the window to center it on the screen
        filter_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        filter_window.wait_window()        
        
    def ipj_process_data():
        global crms_freq, high_bound, low_bound
        def plot_data_func():
            plot_results()
    
        def next_function():
            process_window.destroy()
            ipj_PDF()
            # Replace PDF function with your implementation
            #PDF(latest_folder, step_num)
    
        # Create a new Toplevel window
        process_window = tk.Toplevel()
        process_window.title("Data Analysis")
    
        custom_font = ("Bold", 16)
    
        # Labels
        label = tk.Label(process_window, text="Plotting and Data Analysis:", font=custom_font)
        label.grid(row=0, column=0, padx=10, pady=10)
        
        low_bound_lbl = tk.Label(process_window, text="Low Bound:")
        low_bound_lbl.grid(row=1,column=0,pady=10)
        
        # Low bound for the plot time window
        low_bound = tk.DoubleVar(value=0)
        low_bound_entry = tk.Entry(process_window, textvariable=low_bound)
        low_bound_entry.grid(row=2, column=0, pady=2)
        
        high_bound_lbl = tk.Label(process_window, text="High Bound:")
        high_bound_lbl.grid(row=3,column=0,pady=10)
        
        # High bound for the plot time window
        high_bound = tk.DoubleVar(value=1)
        high_bound_entry = tk.Entry(process_window, textvariable=high_bound)
        high_bound_entry.grid(row=4, column=0, pady=2)
        
        CRMS_label = tk.Label(process_window, text='Max Frequency for CRMS Plot:')
        CRMS_label.grid(row=5, column=0,pady=10)
        
        # Max Frequency for the CRMS plot
        crms_freq = tk.DoubleVar(value=200)
        crms_freq_entry = tk.Entry(process_window, textvariable=crms_freq)
        crms_freq_entry.grid(row=6, column=0, pady=2)
    
        def plot_results():
            # Clear the current figure
            plt.clf()
        
            # Assuming ipj is part of your global state or passed in as a parameter
            data_dict = global_state.ipj.data_analysis(mode, [low_bound.get(), high_bound.get()])
        
            # Plotting the jitter data
            fig1 = plt.figure(figsize=(10, 5))
            ax1 = fig1.add_subplot(111)
            ax1.plot(data_dict['t_window'], data_dict['d_window'], '-r')
            ax1.set_xlabel('Time (seconds)', size=12)
            ax1.set_ylabel('Jitter ({})'.format(ipj_err_unit.get()), size=12)
            ax1.tick_params(axis='both', labelsize=10)
        
            print(f'The sample standard deviation is {data_dict["stdev"]:.3e}')
            print(f'The peak-to-peak in-position jitter is {data_dict["peak"]:.3e}')
        
            # Plotting the CRMS data
            fig2 = plt.figure(figsize=(10, 5))
            ax2 = fig2.add_subplot(111)
            ax2.plot(data_dict['freq'], data_dict['CRMS'])
            ax2.set_xlabel('Frequency Hz', size=12)
            ax2.set_ylabel('Cumulative RMS ({})'.format(ipj_err_unit.get()), size=12)
            ax2.tick_params(axis='both', labelsize=10)
            ax2.set_xlim(0, crms_freq.get())
        
            # Embed the first plot in the GUI
            plot_frame1 = tk.Frame(master=tab2)
            plot_frame1.grid(row=tab2.h1_row, column=4, rowspan=7, columnspan=3, padx=(3, 0), pady=(8, 0), sticky='nsew')
            canvas1 = FigureCanvasTkAgg(fig1, master=plot_frame1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
            # Embed the second plot in the GUI
            plot_frame2 = tk.Frame(master=tab2)
            plot_frame2.grid(row=tab2.h2_row, column=4, rowspan=6, columnspan=3, padx=(3, 0), pady=(0, 0), sticky='nsew')
            canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
        btn_plot_data = tk.Button(process_window, text="Plot Data", command=plot_data_func)
        btn_plot_data.grid(row=7, column=0, pady=10)
    
        btn_next = tk.Button(process_window, text="Next", command=next_function)
        btn_next.grid(row=8, column=0, pady=10)
    
        # Ensure the window is fully initialized before calculating geometry
        process_window.update_idletasks()
    
        # Get the width and height of the window
        window_width = process_window.winfo_width()
        window_height = process_window.winfo_height()
    
        # Calculate the screen's width and height
        screen_width = process_window.winfo_screenwidth()
        screen_height = process_window.winfo_screenheight()
    
        # Calculate the x and y coordinates to center the window
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
    
        # Set the geometry of the window to center it on the screen
        process_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
    
        process_window.wait_window()

    def ipj_PDF():
        def finish_test():
            pdf_window.destroy()
            
        # This function sets up the PDF generation interface and logic in a Tkinter GUI
        def generate_pdf():
            
            def plot_results_plotly(new_folder_path):
                # Assuming `ipj` is part of your global state or passed in as a parameter
                data_dict = global_state.ipj.data_analysis(mode, [low_bound.get(), high_bound.get()])
                
                # Create the first figure for Jitter data
                jitter_trace = go.Scatter(
                    x=data_dict['t_window'],
                    y=data_dict['d_window'],
                    mode='lines',
                    name='Jitter',
                    line=dict(color='red')
                )
            
                jitter_layout = go.Layout(
                    title='In-Position Stability vs Time',
                    xaxis=dict(title='Time (seconds)'),
                    yaxis=dict(title=f'Position ({ipj_err_unit.get()})'),
                    autosize=True,
                    margin=dict(l=50, r=50, t=50, b=50),
                )
            
                jitter_fig = go.Figure(data=[jitter_trace], layout=jitter_layout)
            
                # Create the second figure for CRMS data
                crms_trace = go.Scatter(
                    x=data_dict['freq'],
                    y=data_dict['CRMS'],
                    mode='lines',
                    name='CRMS',
                    line=dict(color='blue')
                )
            
                crms_layout = go.Layout(
                    title='Cumulative RMS',
                    xaxis=dict(title='Frequency (Hz)'),
                    yaxis=dict(title=f'Cumulative RMS ({ipj_unit.get()})'),
                    xaxis_range=[0, crms_freq.get()],
                    autosize=True,
                    margin=dict(l=50, r=50, t=50, b=50),
                )
            
                crms_fig = go.Figure(data=[crms_trace], layout=crms_layout)
            
                # Ensure the folder path exists
                os.makedirs(new_folder_path, exist_ok=True)
                
                # Generate the HTML filename
                html_file = str(sys_serial + '-' + str(ipj_axis.get()) + "_In_Position_Jitter.html")
                html_save = os.path.join(new_folder_path, html_file)
                
                # Write both figures to the HTML file
                with open(html_save, 'w') as f:
                    f.write(pio.to_html(jitter_fig, full_html=False, include_plotlyjs='cdn'))
                    f.write(pio.to_html(crms_fig, full_html=False, include_plotlyjs='cdn'))
                
                # Open the saved HTML file in the default web browser
                webbrowser.open('file://' + os.path.realpath(html_save))
                
            global fig
            plt.rcParams.update({'font.size': 6})
            fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
    
            # Assuming `ipj` is part of your global state or passed in as a parameter
            data_dict = global_state.ipj.data_analysis(mode, [low_bound.get(), high_bound.get()])        
    
            # Upper Jitter Plot
            ax1_up = plt.subplot2grid((14, 3), (2, 0), rowspan=3, colspan=3)
            ax1_up.plot(data_dict['t_window'], data_dict['d_window'], '-r')
            plt.title('In-Position Stability vs Time')
            plt.ylabel('Position ({})'.format(ipj_err_unit.get()))
            plt.xlabel('Time (seconds)')
    
            # Lower Jitter Plot
            ax1_down = plt.subplot2grid((14, 3), (6, 0), rowspan=3, colspan=3)
            ax1_down.plot(data_dict['freq'], data_dict['CRMS'], '-b')
            plt.xlabel('Frequency Hz')
            plt.ylabel('Cumulative RMS ({})'.format(ipj_unit.get()))
            plt.title('Cumulative RMS')
            plt.xlim(0, crms_freq.get())
            
            # Get the size of each axis in inches
            ax2_width, ax2_height = ax2.get_position().size
            ax3_width, ax3_height = ax3.get_position().size
            ax4_width, ax4_height = ax4.get_position().size
        
            # Scale the font size based on the axis size
            font_size_ax2 = max(7, ax2_height * 40)
            font_size_ax3 = max(7, ax3_height * 40)
            font_size_ax4 = max(7, ax4_height * 40)
            
            # Results Text Box
            ax2.text(0.02, .8, 'Standard Deviation: {:.3e} {}'.format(data_dict['stdev'], ipj_err_unit.get()), color='black', size=font_size_ax2)
            ax2.text(0.02, .7, 'Peak-to-Peak Value: {:.3e} {}'.format(data_dict['peak'], ipj_err_unit.get()), color='black', size=font_size_ax2)
    
            # Comments Text Box
            ax3.text(.02, .8, 'Serial Number: {}'.format(ipj_sys.get()), color='black', size=font_size_ax3)
            ax3.text(.02, .7, 'Model Number: {}'.format(ipj_st.get()), color='black', size=font_size_ax3)
            ax3.text(.02, .6, 'Axis: {}'.format(ipj_axis.get()), color='black', size=font_size_ax3)
            #ax3.text(.02, .575, 'System Location: {}'.format(system_location_var.get()), color='black', size=9)
            ax3.text(.02, .5, 'Signal: {}'.format(ipj_signal_var.get()), color='black', size=font_size_ax3)
            ax3.text(.02, .4, 'Comments: {}'.format(ipj_comm.get()), color='black', size=7, verticalalignment='top')
    
            # Test Conditions Text Box
            degree_sign = u'\N{DEGREE SIGN}'
            ax4.text(.02, .8, 'Temperature: {}  {}C'.format(ipj_temp.get(), degree_sign), color='black', size=font_size_ax4)
            ax4.text(.02, .7, 'Sample Rate: {} Hz'.format(1/global_state.ipj.time_array[1]), color='black', size=font_size_ax4)
            ax4.text(.02, .6, 'Sample Time: {} seconds'.format(np.max(global_state.ipj.time_array) + global_state.ipj.time_array[1]), color='black', size=font_size_ax4)
            print('PDF generated')
    
            # Save the figure as a PDF
            start_path = ('O:/')
            sys_serial = str(ipj_sys.get())
            folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
            pdf_file_path = folder_path + '/Customer Files/Plots'
            folder_name = 'In Position Jitter Plots'
            jitter_folder_path = os.path.join(pdf_file_path, folder_name)
            os.makedirs(jitter_folder_path, exist_ok=True)
            
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            new_folder_path = os.path.join(jitter_folder_path, f"{current_time}")
            os.makedirs(new_folder_path, exist_ok=True)
            output_file = str(sys_serial + '-' + str(ipj_axis.get()) + "_In_Position_Jitter.pdf")
            save_file = new_folder_path + '/' + output_file
        
            # Save the figure with tight bounding box
            fig.savefig(save_file, bbox_inches='tight')
            print('PDF saved')
            
            plot_results_plotly(new_folder_path)
            
        def save_csv():
            global_state.ipj.write_to_csv(csv_file_entry.get(),ipj_sys.get(),ipj_axis.get())
            print('CSV saved')
        
        pdf_title_font = ('Bold', 16)    
        
        # Create the window
        pdf_window = tk.Toplevel()
        pdf_window.title("Generate PDF and CSV")
        
        pdf_label = tk.Label(pdf_window, text='Generate PDF and CSV', font=pdf_title_font)
        pdf_label.grid(row=0, column=0, pady=10)
    
        # Save PDF Section
        output_file_label = tk.Label(pdf_window, text="File Name:")
        output_file_label.grid(row=1, column=0, padx=10, pady=5)
        output_file_entry = tk.Entry(pdf_window)
        output_file_entry.insert(0, "jitter_report.pdf")
        output_file_entry.grid(row=2, column=0, padx=10, pady=5)
        
        # Generate PDF Button
        gen_pdf_button = tk.Button(pdf_window, text="Generate PDF", command=generate_pdf)
        gen_pdf_button.grid(row=3, column=0, padx=10, pady=10)
    
        # Save CSV Section
        csv_file_label = tk.Label(pdf_window, text="CSV Name:")
        csv_file_label.grid(row=4, column=0, padx=10, pady=5)
        csv_file_entry = tk.Entry(pdf_window)
        csv_file_entry.insert(0, "ipj.csv")
        csv_file_entry.grid(row=5, column=0, padx=10, pady=5)
    
        export_csv_button = tk.Button(pdf_window, text="Save CSV", command=save_csv)
        export_csv_button.grid(row=6, column=0, padx=10, pady=10)
        
        finish_button = tk.Button(pdf_window, text='Finish Test', command=finish_test)
        finish_button.grid(row=7, column=0, padx=10, pady=10)
        
        # Center the window on the screen
        pdf_window.update_idletasks()
        window_width = pdf_window.winfo_width()
        window_height = pdf_window.winfo_height()
        screen_width = pdf_window.winfo_screenwidth()
        screen_height = pdf_window.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        pdf_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
    def ipj_direction_def():
        global direction
        if direction.get() == "Positive":
            direction = 'pos'
        elif direction.get() == "Negative":
            direction = 'neg'
        else:
            direction = 'None'
            
    def ipj_signal_def(*args):
        global ipj_signal
        if ipj_signal_var.get() == "Encoder":
            ipj_signal = a1data.mode.pos_fbk
            ipj_ent_probe["state"] = tk.DISABLED
            ipj_lbl_probe["state"] = tk.DISABLED
            ipj_ent_sens["state"] = tk.DISABLED
            ipj_lbl_sample["state"] = tk.DISABLED
            ipj_sample_menu["state"] = tk.DISABLED
            ipj_lbl_sens["state"] = tk.DISABLED
            ipj_lbl_dir["state"] = tk.DISABLED
            ipj_pos_dir["state"] = tk.DISABLED
            ipj_neg_dir["state"] = tk.DISABLED
        elif ipj_signal_var.get() == "Capacitance Probe":
            ipj_signal = a1data.mode.ai0
            ipj_ent_probe["state"] = tk.NORMAL
            ipj_lbl_probe["state"] = tk.NORMAL
            ipj_lbl_sample["state"] = tk.NORMAL
            ipj_sample_menu["state"] = tk.NORMAL
            ipj_ent_sens["state"] = tk.NORMAL
            ipj_lbl_sens["state"] = tk.NORMAL
            ipj_lbl_dir["state"] = tk.NORMAL
            ipj_pos_dir["state"] = tk.NORMAL
            ipj_neg_dir["state"] = tk.NORMAL
        else:
            ipj_signal = 'None'
    
    def ipj_get_sample_rate_value():
        selected_text = ipj_samp.get()  # Get the selected display text, e.g., '1 kHz
        # Find the actual numeric value corresponding to the selected text
        for option in ipj_sample_options:
            if option[0] == selected_text:
                return option[1]
        return None  # If not found, return None or handle it as needed
    
    def open_rotary_Plot():
        axis = ipj_axis.get()
        sys_serial = ipj_sys.get()

        start_path = ('O:/')
        folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
        pdf_file_path = folder_path + '/Customer Files/Plots'

        if os.path.exists(pdf_file_path):
            try:
                output_file = str(sys_serial + '-' + axis + "_Accuracy.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
            try:
                output_file = str(sys_serial + '-' + axis + "_Verification.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
        else:
            print(f"File '{pdf_file_path}' does not exist.")
    
    # Load stored data or set defaults
    ipj_axis_value = stored_data.get("axis_name", "X")
    ipj_signal_value = stored_data.get("signal", 0)
    ipj_probe_value = stored_data.get("probe_axis", 'X')
    ipj_sens_value = stored_data.get("scale factor (user units)", '0.0025')
    ipj_unit_value = stored_data.get("units", 'mm')
    ipj_err_unit_value = stored_data.get("error_units", 'mm')
    ipj_sample_value = stored_data.get("sample_rate", "1 kHz")
    ipj_dwell_value = stored_data.get("duration", 1)
    ipj_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ipj_st_value = stored_data.get("part_number", '"Part Number"')
    ipj_opName_value = stored_data.get("operator", '"Your Initials"')
    ipj_temp_value = stored_data.get("temp", 20)
    ipj_comm_value = stored_data.get("comments", "")
    ipj_direction_value = stored_data.get("direction", 'pos')
    
    
    ipj_lbl_axis = tk.Label(master=tab2, text="Axis Name", width=25, height=1)
    ipj_lbl_axis.grid(row=tab2.axis_row, column=0, padx=5, pady=5)

    ipj_axis = tk.StringVar(value=ipj_axis_value)
    ipj_ent_axis = tk.Entry(master=tab2, textvariable=ipj_axis, width=25)
    ipj_ent_axis.grid(row=tab2.axis_row, column=1, padx=5, pady=5)

    ipj_lbl_sig = tk.Label(master=tab2, text="Signal", width=25, height=1)
    ipj_lbl_sig.grid(row=tab2.sig_row, column=0, padx=5, pady=5)
    
    ipj_signal_var = tk.StringVar(value=ipj_signal_value)
    ipj_signal_var.trace_add('write', ipj_signal_def)
    ipj_signal_options = ['Encoder', 'Capacitance Probe']
    ipj_signal_menu = tk.OptionMenu(tab2, ipj_signal_var, *ipj_signal_options)
    ipj_signal_menu.grid(row=tab2.sig_row, column=1, padx=5, pady=5)

    ipj_lbl_probe = tk.Label(master=tab2, text="Probe Axis Name:", width=25, height=1,state=tk.DISABLED)
    ipj_lbl_probe.grid(row=tab2.sig_row, column=2, padx=5, pady=5)

    ipj_probe = tk.StringVar(value=ipj_probe_value)
    ipj_ent_probe = tk.Entry(master=tab2, textvariable=ipj_probe, width=25,state=tk.DISABLED)
    ipj_ent_probe.grid(row=tab2.units_row, column=2, padx=5, pady=5)
    
    ipj_lbl_sens = tk.Label(master=tab2, text="Scale Factor (User Units)", width=25, height=1,state=tk.DISABLED)
    ipj_lbl_sens.grid(row=tab2.sig_row, column=3, padx=5, pady=5)

    ipj_sens = tk.StringVar(value=ipj_sens_value)
    ipj_ent_sens = tk.Entry(master=tab2, textvariable=ipj_sens, width=25,state=tk.DISABLED)
    ipj_ent_sens.grid(row=tab2.units_row, column=3, padx=5, pady=5)
    
    ipj_lbl_units = tk.Label(master=tab2, text="Units:", width=25, height=1)
    ipj_lbl_units.grid(row=tab2.units_row, column=0, padx=5, pady=5)
    
    ipj_unit_options = ['mm', 'um', 'nm', 'deg']
    ipj_unit = tk.StringVar(value=ipj_unit_value)
    ipj_unit_menu = tk.OptionMenu(tab2, ipj_unit, *ipj_unit_options)
    ipj_unit_menu.grid(row=tab2.units_row, column=1, padx=5, pady=5)

    ipj_lbl_err_units = tk.Label(master=tab2, text="Error Units:", width=25, height=1)
    ipj_lbl_err_units.grid(row=tab2.err_row, column=0, padx=5, pady=5)
    
    ipj_err_unit_options = ['mm', 'um', 'nm', 'arcsec', 'deg']
    ipj_err_unit = tk.StringVar(value=ipj_err_unit_value)
    ipj_err_unit_menu = tk.OptionMenu(tab2, ipj_err_unit, *ipj_err_unit_options)
    ipj_err_unit_menu.grid(row=tab2.err_row, column=1, padx=5, pady=5)
    
    ipj_lbl_sample = tk.Label(master=tab2, text="Sample Rate:", width=25, height=1)
    ipj_lbl_sample.grid(row=tab2.samp_row, column=0, padx=5, pady=5)
    
    ipj_sample_options = [('1 kHz', 1000), ('10 kHz', 10000), ('20 kHz', 20000), ('100 kHz', 100000), ('200 kHz', 200000)]
    ipj_samp = tk.StringVar(value=ipj_sample_value)
    ipj_sample_menu = tk.OptionMenu(tab2, ipj_samp, *[option[0] for option in ipj_sample_options])
    ipj_sample_menu.configure(state=tk.DISABLED)
    ipj_sample_menu.grid(row=tab2.samp_row, column=1, padx=5, pady=5)
    
    ipj_lbl_dwell = tk.Label(master=tab2, text="Duration")
    ipj_lbl_dwell.grid(row=tab2.dwell_row, column=0, padx=5, pady=5)

    ipj_dwell = tk.StringVar(value=ipj_dwell_value)
    ipj_ent_dwell = tk.Entry(master=tab2, textvariable=ipj_dwell, width=25)
    ipj_ent_dwell.grid(row=tab2.dwell_row, column=1, padx=5, pady=5)    
    
    # Create the UI elements and assign the stored values
    ipj_lbl_dir = tk.Label(master=tab2, text="Direction To Sensor:",state=tk.DISABLED)
    ipj_lbl_dir.grid(row=tab2.dir_row, column=0, padx=5, pady=5)

    ipj_direction_var = tk.StringVar(value=ipj_direction_value)
    ipj_pos_dir = tk.Radiobutton(master=tab2, text="Positive", variable=ipj_direction_var, value="pos",state=tk.DISABLED, command=ipj_direction_def)
    ipj_pos_dir.grid(row=tab2.dir_row, column=1, padx=5, pady=5)

    ipj_neg_dir = tk.Radiobutton(master=tab2, text="Negative", variable=ipj_direction_var, value="neg",state=tk.DISABLED, command=ipj_direction_def)
    ipj_neg_dir.grid(row=tab2.dir_row, column=2, padx=5, pady=5)

    ipj_lbl_serial = tk.Label(master=tab2, text="System Serial Number", width=25, height=1)
    ipj_lbl_serial.grid(row=tab2.sys_row, column=0, padx=5, pady=5)

    ipj_sys = tk.StringVar(value=ipj_sys_value)
    ipj_ent_serial = tk.Entry(master=tab2, textvariable=ipj_sys, width=25)
    ipj_ent_serial.grid(row=tab2.sys_row, column=1, columnspan=3, padx=5, pady=5)

    ipj_lbl_st_model = tk.Label(master=tab2, text="Part Number", width=25, height=1)
    ipj_lbl_st_model.grid(row=tab2.st_row, column=0, padx=5, pady=5)

    ipj_st = tk.StringVar(value=ipj_st_value)
    ipj_ent_st_model = tk.Entry(master=tab2, textvariable=ipj_st, width=25)
    ipj_ent_st_model.grid(row=tab2.st_row, column=1, columnspan=3, padx=5, pady=5)

    ipj_lbl_op = tk.Label(master=tab2, text="Operator", width=25, height=1)
    ipj_lbl_op.grid(row=tab2.op_row, column=0, padx=5, pady=5)

    ipj_opName = tk.StringVar(value=ipj_opName_value)
    ipj_ent_op = tk.Entry(master=tab2, textvariable=ipj_opName, width=25)
    ipj_ent_op.grid(row=tab2.op_row, column=1, columnspan=3, padx=5, pady=5)

    ipj_lbl_temp = tk.Label(master=tab2, text="Temp", width=25, height=1)
    ipj_lbl_temp.grid(row=tab2.temp_row, column=0, padx=5, pady=5)

    ipj_temp = tk.DoubleVar(value=ipj_temp_value)
    ipj_ent_temp = tk.Entry(master=tab2, textvariable=ipj_temp, width=25)
    ipj_ent_temp.grid(row=tab2.temp_row, column=1, columnspan=3, padx=5, pady=5)

    ipj_lbl_comments = tk.Label(master=tab2, text="Comments", width=25, height=1)
    ipj_lbl_comments.grid(row=tab2.com_row, column=0, padx=5, pady=5)

    ipj_comm = tk.StringVar(value=ipj_comm_value)
    ipj_ent_comments = tk.Entry(master=tab2, textvariable=ipj_comm, width=25)
    ipj_ent_comments.grid(row=tab2.com_row, column=1, columnspan=3, padx=5, pady=5)

    #btn_import_rot = tk.Button(master=tab1, text="Import Data", width=30, height=1, command=import_data_rotary)
    #btn_import_rot.grid(row=run_row, column=1, padx=5, pady=5)

    ipj_lbl_import_rot = tk.Label(master=tab2, text='', anchor='w')
    ipj_lbl_import_rot.grid(row=tab2.run_row, column=1, padx=5, pady=5, columnspan=3)

    ipj_btn_run_rot = tk.Button(master=tab2, text="Run", width=25, height=1, command=start_jittertest)
    ipj_btn_run_rot.grid(row=tab2.run_row, column=0, padx=5, pady=5)

    ipj_btn_open_rot = tk.Button(master=tab2, text="Open Plot", width=25, height=1, command=open_rotary_Plot)
    ipj_btn_open_rot.grid(row=tab2.run_row, column=2, padx=5, pady=5)

    # Create a Frame to hold the Text widget and the Scrollbar
    frame1 = tk.Frame(tab2)

    # Create the Text widget
    txt_outStr1 = tk.Text(master=frame1, state=tk.DISABLED, height=10, fg='white', bg='black')

    # Create the Scrollbar widget
    outStr_scroll1 = tk.Scrollbar(master=frame1, orient=tk.VERTICAL)

    # Link the Scrollbar to the Text widget
    txt_outStr1.configure(yscrollcommand=outStr_scroll1.set)
    outStr_scroll1.config(command=txt_outStr1.yview)

    # Pack the Text widget and the Scrollbar inside the Frame
    txt_outStr1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outStr_scroll1.pack(side=tk.LEFT, fill=tk.Y)

    # Grid the Frame containing the Text widget and the Scrollbar
    frame1.grid(row=tab2.out_row, column=0, columnspan=7, padx=5, pady=5, sticky='nsew')

    # Create the logger object
    logger2 = TextLogger(txt_outStr1)
    
    # Configure the grid to expand the Frame
    tab2.grid_rowconfigure(tab2.out_row, weight=1)
    tab2.grid_columnconfigure(0, weight=1)
    
    def ipj_on_closing():
        # Save user inputs before closing
        user_data = {
            "axis_name": ipj_axis.get(),  # Entry widget
            "signal": ipj_signal_var.get(),  # OptionMenu
            "probe_axis": ipj_probe.get(),  # Entry widget
            "scale factor (user units)": ipj_sens.get(),  # Entry widget
            "units": ipj_unit.get(),  # OptionMenu
            "error_units": ipj_err_unit.get(),  # OptionMenu
            "sample_rate": ipj_samp.get(),  # OptionMenu
            "duration": ipj_dwell.get(),  # Entry widget
            "system_serial_number": ipj_sys.get(),  # Entry widget
            "part_number": ipj_st.get(),  # Entry widget
            "operator": ipj_opName.get(),  # Entry widget
            "temp": ipj_temp.get(),  # Entry widget
            "comments": ipj_comm.get(),  # Entry widget
            "direction": ipj_direction_var.get()  # Radiobutton selection
            }
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", ipj_on_closing)    

# =============================================================================
# Tab 3
# 
# 
# Min Step
# 
# 
# 
# 
# 
# 
# 
# =============================================================================
    
    #for tab in (tab1, tab2, tab3):
    # Configure columns and rows
    tab3.columnconfigure([0, 1, 2, 3, 4, 5, 6], weight=1, minsize=700 / 4, uniform='column')
    tab3.rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21], weight=1, minsize=1)

    # Define row indices
    tab3.h0_row = 0
    tab3.h1_row = 1
    tab3.tt_row = 2
    tab3.h2_row = 3
    tab3.axis_row = 4
    tab3.start_row = 5
    tab3.step_row = 6
    tab3.num_step_row = 7
    tab3.speed_row = 8
    tab3.ramp_v_row = 9
    tab3.dwell_row = 10
    tab3.ipj_row = 11
    tab3.h3_row = 12
    tab3.sys_row = 13
    tab3.st_row = 14
    tab3.op_row = 15
    tab3.temp_row = 16
    tab3.com_row = 17
    tab3.sens_row = 18
    tab3.h4_row = 19
    tab3.run_row = 20
    tab3.out_row = 21

    window.rowconfigure(tab3.out_row, minsize=4)

    # Create horizontal separators
    ttk.Separator(master=tab3, orient='horizontal').grid(row=tab3.h1_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab3, orient='horizontal').grid(row=tab3.h2_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab3, orient='horizontal').grid(row=tab3.h3_row, column=0, columnspan=4, sticky='ew')
    ttk.Separator(master=tab3, orient='horizontal').grid(row=tab3.h4_row, column=0, columnspan=4, sticky='ew')

    # Adjust column weights so the vertical separator aligns correctly
    tab3.columnconfigure(3, weight=1)
    tab3.columnconfigure(4, weight=1)
    
    # Add the vertical separator to the frame
    ttk.Separator(master=tab3, orient='vertical').grid(row=tab3.h1_row, column=4, rowspan=21, sticky='nsw', pady=(4, 0))
    
    # Load stored data or set defaults
    ins_axis_value = stored_data.get("axis_name", "X")
    ins_start_value = stored_data.get("start_position", 10)
    ins_step_value = stored_data.get("step_size", 30)
    ins_num_step_value = stored_data.get("num_step", 1)
    ins_signal_value = stored_data.get("signal", 0)
    ins_probe_value = stored_data.get("probe_axis", 'None')
    ins_sens_value = stored_data.get("scale factor (user units)", '0.0025')
    ins_speed_value = stored_data.get("speed", 5)
    ins_ramp_v_value = stored_data.get("ramp_rate", 1000)
    ins_dwell_value = stored_data.get("dwell", 1)
    ins_ipj_value = stored_data.get("jitter",'')
    ins_settle_value = stored_data.get("settle",'')
    ins_unit_value = stored_data.get("units", 'mm')
    ins_err_unit_value = stored_data.get("error_units", 'mm')
    ins_sample_value = stored_data.get("sample_rate", "1 kHz")
    ins_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ins_st_value = stored_data.get("part_number", '"Part Number"')
    ins_opName_value = stored_data.get("operator", '"Your Initials"')
    ins_temp_value = stored_data.get("temp", 20)
    ins_comm_value = stored_data.get("comments", "")

    def start_incrementalsteptest():
        global_state.reset()
        ins_btn_run_rot.config(state=tk.DISABLED)
        threading.Thread(target=run_incrementalsteptest).start()
        #threading.Thread(target=moveandsettle_live_plot).start()

    def run_incrementalsteptest():
        # Save user inputs before closing
        user_data = {
            "axis_name": ins_axis.get(),
            "start_position": ins_start.get(),
            "step_size": ins_step.get(),
            "num_step": ins_num_step.get(),
            "signal": ins_signal_var.get(),
            "probe_axis": ins_probe.get(),
            "scale factor (user units)": ins_sens.get(),
            "speed": ins_speed_.get(),
            "ramp_rate": ins_ramp_v.get(),
            "dwell": ins_dwell.get(),
            "jitter": ins_ipj.get(),
            "settle": ins_settle.get(),
            "units": ins_unit.get(),
            "error_units": ins_err_unit.get(),
            "sample_rate": ins_samp.get(),
            "system_serial_number": ins_sys.get(),
            "part_number": ins_st.get(),
            "operator": ins_opName.get(),
            "temp": ins_temp.get(),
            "comments": ins_comm.get()
        }
        save_user_inputs(user_data)
        try:
            incrementalsteptest()
            ins_data_filtering()
            ins_process_data()

        finally:
            gc.collect()  
            if global_state.clientsocket:
                global_state.clientsocket.close()
            window.after(0, ins_btn_run_rot.config, {'state': tk.NORMAL})
            
    def incrementalsteptest():
        syst.stdout = logger3
        global folder
        axis = str(ins_axis.get())
        sample_rate = ins_get_sample_rate_value()
        step_size = float(ins_step.get())
        s = float(ins_ipj.get())
        t_ms = float(ins_settle.get())
        sensitivity = float(ins_sens.get())
        probe_axis = str(ins_probe.get())
        num_steps = int(ins_num_step.get())
        units = str(ins_unit.get())
        error_units = str(ins_err_unit.get())
        t_ave = int(ins_dwell.get())
        start_pos = int(ins_start.get())
        speed = int(ins_speed_.get())
        ramp_value = int(ins_ramp_v.get())
        
        try:
            controller = a1.Controller.connect()
            controller.start()
        except:
            connection_type = controller_def()
            if connection_type == 'yes':
                try:
                    controller = a1.Controller.connect_usb()
                    controller.start()
                except:
                    messagebox.showerror('Connection Error', 'Check connections and try again')
            else:
                messagebox.showerror('Update Software', 'Update Hyperwire firmware and try again')
        connected_axes = {}
        non_virtual_axes = []

        number_of_axes = controller.runtime.parameters.axes.count

        if number_of_axes <= 12:
            for axis_index in range(0,11):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index

            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')    
        else:
            for axis_index in range(0,32):
                status_item_configuration = a1.StatusItemConfiguration()
                status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
                
                result = controller.runtime.status.get_status_items(status_item_configuration)
                axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
                
                if (axis_status & 1 << 13) > 0:
                    connected_axes[controller.runtime.parameters.axes[axis_index].identification.axisname.value] = axis_index
            
            for key, value in connected_axes.items():
                non_virtual_axes.append(key)
                
            if len(non_virtual_axes) == 0:
                try:
                    controller = a1.Controller.connect_usb()
                except:
                    messagebox.showerror('No Device', 'No Devices Present. Check Connections.')

            global_state.ins = incremental_step(axis, sample_rate, step_size, s, t_ms, sensitivity, probe_axis, num_steps,
                                              units=units,
                                              error_units=error_units,
                                              direction=direction, 
                                              t_ave=t_ave,
                                              start_pos=start_pos,
                                              speed=speed, 
                                              ramp_value=ramp_value,
                                              )
            global_state.ins.test(controller)
            
    def ins_data_filtering():
        def apply_button_click():
            butter_func()
            filter_window.destroy()
        def reset_func():
            pos_fbk_copy = copy.deepcopy(global_state.ins.pos_fbk)
            global_state.ins.pos_fbk = pos_fbk_copy
            global_state.Comments = ins_comm.get()
            messagebox.showinfo("Filters Reset", "Filters have been reset.")
    
        def butter_func():
            omega_c = omega.get()
            order = order_.get()
            type_ = type_dropdown.get()
            type_var = filter_type_map[type_]
            if ins_probe.get() == 'None':
                global_state.ins.butter(a1data.mode.pos_fbk, omega_c, order, type_var)
            else:
                global_state.ins.butter(a1data.mode.ai0, omega_c, order, type_var)
            global_state.Comments = f'\n{type_var} pass butterworth filter \nwith a {omega_c} Hz cut-off frequency \napplied'
            messagebox.showinfo("Butterworth Filter Applied", "Butterworth Filter Applied")
        
        # Create a new Toplevel window instead of a new Tk window
        filter_window = tk.Toplevel()
        filter_window.title("Data Filtering")
        filter_window.grab_set()

        custom_title_font = ("Bold", 16)
        custom_header1_font = ("Bold", 14)
        custom_header2_font = ("Bold", 12)
        

        # Labels
        label = tk.Label(filter_window, text="Data Filtering:", font=custom_title_font)
        label.grid(row=0, column=0, padx=10, pady=10)

        # Butterworth Filter Parameters
        filter_label = tk.Label(filter_window, text="Butterworth Filter Parameters:", font=custom_header1_font)
        filter_label.grid(row=1, column=0, padx=10, pady=10)

        omega_c_label = tk.Label(filter_window, text="Cut-off Frequency (Hz):", font=custom_header2_font)
        omega_c_label.grid(row=2, column=0, padx=10, pady=5)
        omega = tk.DoubleVar(value=250)
        omega_c_entry = tk.Entry(filter_window, textvariable=omega)
        omega_c_entry.grid(row=3, column=0, padx=10, pady=2)

        order_label = tk.Label(filter_window, text="Order:", font=custom_header2_font)
        order_label.grid(row=4, column=0, padx=10, pady=5)
        order_ = tk.IntVar(value=2)
        order_entry = tk.Entry(filter_window, textvariable=order_)
        order_entry.grid(row=5, column=0, padx=10, pady=2)

        type_label = tk.Label(filter_window, text="Type:", font=custom_header2_font)
        type_label.grid(row=6, column=0, padx=10, pady=5)
        
        type_ = tk.StringVar(value='low')
        type_dropdown = ttk.Combobox(filter_window, textvariable=type_)
        type_dropdown['values'] = ("High Pass", "Low Pass")
        type_dropdown.current(1)  # Default to "Low Pass"
        type_dropdown.grid(row=7, column=0, padx=10, pady=2)
        
        # Mapping of the dropdown values to the filter types
        filter_type_map = {
            "High Pass": "high",
            "Low Pass": "low"
        }

        reset_button = tk.Button(filter_window, text="Reset Filters Applied", command=reset_func)
        reset_button.grid(row=8, column=0, padx=10, pady=10)

        apply_button = tk.Button(filter_window, text="Apply Filter", command=apply_button_click)
        apply_button.grid(row=9, column=0, padx=10, pady=10)
        
        # Ensure the window is fully initialized before calculating geometry
        filter_window.update_idletasks()
    
        # Get the width and height of the window
        window_width = filter_window.winfo_width()
        window_height = filter_window.winfo_height()
        
        # Calculate the screen's width and height
        screen_width = filter_window.winfo_screenwidth()
        screen_height = filter_window.winfo_screenheight()
    
        # Calculate the x and y coordinates to center the window
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
    
        # Set the geometry of the window to center it on the screen
        filter_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        filter_window.wait_window()
    
    def ins_process_data():
        global html_file_path
        def next_function():
            ins_PDF()
            criteria()
            analyze_window.destroy()
        # Create a new Toplevel window
        analyze_window = tk.Toplevel()
        analyze_window.title("Data Analysis")
        
        # Define custom fonts
        custom_font = ("Bold", 16)
        header_font = ("Bold", 12)
                
        # Labels
        label = tk.Label(analyze_window, text="Data Analysis", font=custom_font)
        label.grid(row=0, column=0, padx=10, pady=10)
        
        step_num = tk.Label(analyze_window, text='Step To Plot')
        step_num.grid(row=1, column=0, padx=10, pady=10)
    
        step_num_var = tk.IntVar(value=0)
        step_num_entry = tk.Entry(analyze_window, textvariable=step_num_var)
        step_num_entry.grid(row=2, column=0, pady=2)
        
        def extra_signals(*args):
            global extra_signal
            analyze_window.lift()
            if extra_signal_var.get() == 'None':
                extra_signal = 'None'
            elif extra_signal_var.get() == 'Position Error':
                extra_signal = a1data.mode.pos_err
            elif extra_signal_var.get() == 'Position Command':
                extra_signal = a1data.mode.pos_com
            elif extra_signal_var.get() == 'Position Feedback':
                extra_signal = a1data.mode.pos_fbk
        
        lbl_extra_signal = tk.Label(analyze_window, text='Additional Signals To Plot')
        lbl_extra_signal.grid(row=3, column=0, padx=10, pady=10)
        
        extra_signal_var = tk.StringVar()
        extra_signal_var.trace_add('write', extra_signals)
        extra_signal_options = ['None', 'Position Command', 'Position Feedback']
        extra_signal_menu = tk.OptionMenu(analyze_window, extra_signal_var, *extra_signal_options)
        extra_signal_menu.grid(row=4, column=0, padx=10, pady=2)
        
        # Function to handle analysis logic
        def analyze_func():
            global data, ins, data_table, criteria_table, B, criteria
            
            data = global_state.ins.data_analysis()
    
            def plot_results():
                global html_file_path
                # Clear any existing plots
                plt.clf()
                
                # Configure the figure size
                fig = plt.figure(figsize=(15, 3))  # Adjusted size to fit both plots vertically
                plt.rcParams.update({'font.size': 11})
            
                # Plotting the Staircase Plot
                if ins_probe.get() == 'None':
                    plt.ylabel('Position {}'.format(ins_err_unit.get()))
                else:
                    plt.ylabel('Analog Input {}'.format(ins_err_unit.get()))
            
                # Using parent plot method
                if extra_signal_var.get() == 'None':
                    if ins_probe.get() == 'None':
                        stair_plt = super(incremental_step, global_state.ins).plot(a1data.mode.pos_fbk)
                    else:
                        stair_plt = super(incremental_step, global_state.ins).plot(a1data.mode.ai0)
                else:
                    if ins_probe.get() == 'None':
                        stair_plt = super(incremental_step, global_state.ins).plot(a1data.mode.pos_fbk)
                        stair_plt = super(incremental_step, global_state.ins).plot(extra_signal)
                    else:
                        stair_plt = super(incremental_step, global_state.ins).plot(a1data.mode.ai0)
                        stair_plt = super(incremental_step, global_state.ins).plot(extra_signal)
                
                # Check if stair_plt is None and create a default figure if necessary
                if stair_plt is None:
                    stair_plt = plt.gcf()  # Get the current figure
                
                # Using child plot method for the second plot
                step_plt = global_state.ins.plot(legend_loc='upper right', step_num=step_num_var.get(), fig_size=(8, 4))
                
                # Check if step_plt is None and create a default figure if necessary
                if step_plt is None:
                    step_plt = plt.figure(figsize=(10, 5))
                
                # Create frames for each plot
                stair_plot_frame = tk.Frame(master=tab3)
                stair_plot_frame.grid(row=tab3.h0_row, rowspan=9, column=4, columnspan=3, padx=(3,0), pady=(15,0), sticky='nsew')
            
                step_plot_frame = tk.Frame(master=tab3)
                step_plot_frame.grid(row=tab3.ramp_v_row, rowspan=12, column=4, columnspan=3, padx=(3,0), pady=(0,0), sticky='nsew')
            
                # Make frames responsive
                tab3.grid_rowconfigure(tab3.h0_row, weight=1)
                tab3.grid_rowconfigure(tab3.num_step_row, weight=1)
                tab3.grid_columnconfigure(4, weight=1)
            
                # Embed the plots in Tkinter canvas
                embed_plot_in_canvas(stair_plt, step_plt, stair_plot_frame, step_plot_frame)
                
                global_state.ins.plot_to_plotly(step_num=step_num_var.get(), legend_loc='upper right', legend_size=7)
                
            def embed_plot_in_canvas(stair_plot, step_plot, stair_canvas_frame, step_canvas_frame):
                # Clear any existing plots in the frames
                for widget in stair_canvas_frame.winfo_children():
                    widget.destroy()
                for widget in step_canvas_frame.winfo_children():
                    widget.destroy()
            
                # Embed the first plot in the Tkinter canvas
                stair_canvas = FigureCanvasTkAgg(stair_plot, master=stair_canvas_frame)
                stair_canvas.draw()
                stair_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
                # Embed the second plot in the Tkinter canvas
                step_canvas = FigureCanvasTkAgg(step_plot, master=step_canvas_frame)
                step_canvas.draw()
                step_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
                # Make the plots responsive
                stair_canvas_frame.bind('<Configure>', lambda event: resize_plot(event, stair_plot, stair_canvas))
                step_canvas_frame.bind('<Configure>', lambda event: resize_plot(event, step_plot, step_canvas))
            
            def resize_plot(event, plot, canvas):
                # Adjust the plot size dynamically based on the frame size
                width = event.width / 100  # Convert from pixels to inches
                height = event.height / 100
                plot.set_size_inches(width, height)
                canvas.draw()
                
            plot_results()
        
        def criteria():
            criteria = [
                global_state.ins.A1(),
                global_state.ins.A2(data, a1data.mode.positive_direction),
                global_state.ins.A3(data, a1data.mode.positive_direction),
                global_state.ins.unidirectional_criteria(data, a1data.mode.positive_direction),
                global_state.ins.A1(),
                global_state.ins.A2(data, a1data.mode.negative_direction),
                global_state.ins.A3(data, a1data.mode.negative_direction),
                global_state.ins.unidirectional_criteria(data, a1data.mode.negative_direction),
                global_state.ins.B1(),
                global_state.ins.B2(data),
                global_state.ins.B3(data),
                global_state.ins.bidirectional_criteria(data)
            ]
            
            # Table Data
            criteria_table = """<table>
            <tr>
                <th colspan = "2"></th>
                <th colspan = "3">Criteria</th>
                <th colspan = "3"></th>
                <th colspan = "3">Criteria</th>
                <th colspan = "2"></th>
            </tr>
            <tr>
                <th colspan = "2">Direction of Motion</th>
                <th>A1</th>
                <th>A2</th>
                <th>A3</th>
                <th colspan = "2">Criteria Satisfied?</th>
                <td></td>
                <th>B1</th>
                <th>B2</th>
                <th>B3</th>
                <th colspan = "2">Criteria Satisfied?</th>
            </tr>
            <tr>
                <th colspan = "2">Forward</th>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td colspan = "2">{}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td colspan = "2"></td>
            </tr>
            <tr>
                <th colspan = "2">Reverse</th>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td colspan = "2">{}</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
                <td colspan = "2"></td>
            </tr>
            <tr>
                <th colspan = "2">Combined</th>
                <td></td>
                <td></td>
                <td></td>
                <td colspan = "2"></td>
                <td></td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td colspan = "2">{}</td>
            </tr>
            </table>
            """.format(*['Yes' if val else 'No' for val in criteria])
            
            # Data Table Display
            data_table = """<table>
            <tr>
                <th colspan = "3"></th>
                <th colspan = "3">Direction of Motion</th>
            </tr>
            <tr>
                <th colspan = "3"></th>
                <th>Forward</th>
                <th>Reverse</th>
                <th>Combined</th>
            </tr>
            <tr>
                <th colspan = "3">Sample Mean, X<sub>inc</sub> {}</th>
                <td>{:.3e}</td>
                <td>{:.3e}</td>
                <td>{:.3e}</td>
            </tr>
            <tr>
                <th colspan = "3">Sample Standard Deviation, s<sub>inc</sub> {}</th>
                <td>{:.3e}</td>
                <td>{:.3e}</td>
                <td>{:.3e}</td>
            </tr>
            <table>
            """.format(global_state.ins.units, data['Forward Sample Mean'], data['Reverse Sample Mean'], data['Combined Sample Mean'],
                       global_state.ins.units, data['Forward Sample Standard Deviation'], data['Reverse Sample Standard Deviation'],
                       data['Combined Sample Standard Deviation'])
    
            # Combine both tables in one HTML content
            full_html_content = f"""
            <html>
            <head>
                <title>Data Analysis Display</title>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ padding: 8px; text-align: center; }}
                </style>
            </head>
            <body>
                <h1>ASME Criteria Table</h1>
                {criteria_table}
                <h1>Data Table</h1>
                {data_table}
            </body>
            </html>
            """
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                html_file_path = tmp_file.name
                tmp_file.write(full_html_content.encode("utf-8"))
            
            def open_criteria():
                criteria = tk.Toplevel()
                criteria.title('Open Criteria Results')
                
                # Make the window modal and bring it to the front
                criteria.grab_set()
                criteria.focus_set()
                criteria.attributes('-topmost', True)
                
                lbl_criteria = tk.Label(criteria, text='Would you like to view the ASME criteria results?')
                lbl_criteria.grid(row=0,column=0,padx=10,pady=10)
                
                def on_yes():
                    # Open the HTML file in the default web browser
                    webbrowser.open(f"file://{os.path.realpath(html_file_path)}")
                    
                    # Make the window modal and bring it to the front
                    analyze_window.grab_set()
                    analyze_window.focus_set()
                    analyze_window.attributes('-topmost', True)
                    
                    criteria.destroy()
                    
                def on_no():
                    # Make the window modal and bring it to the front
                    analyze_window.grab_set()
                    analyze_window.focus_set()
                    analyze_window.attributes('-topmost', True)
                    
                    criteria.destroy()
                    return
                
                # Frame to hold the buttons
                button_frame = tk.Frame(criteria)
                button_frame.grid(row=1, column=0, pady=10)
                
                yes_button = tk.Button(button_frame, text='Yes', command=on_yes)
                yes_button.pack(side=tk.LEFT, padx=(0,5))
                
                no_button = tk.Button(button_frame, text='No', command=on_no)
                no_button.pack(side=tk.LEFT,padx=(5,0))
                
                # Center the window on the screen
                criteria.update_idletasks()
                window_width = criteria.winfo_width()
                window_height = criteria.winfo_height()
                screen_width = criteria.winfo_screenwidth()
                screen_height = criteria.winfo_screenheight()
            
                x_cordinate = int((screen_width / 2) - (window_width / 2))
                y_cordinate = int((screen_height / 2) - (window_height / 2))
                criteria.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
            
                criteria.wait_window()
                
            open_criteria()
            
        # Analyze Button
        analyze_button = tk.Button(analyze_window, text="Data Analysis", command=analyze_func)
        analyze_button.grid(row=5, column=0, pady=10)
        
        next_button = tk.Button(analyze_window, text='Next', command=next_function)
        next_button.grid(row=6,column=0,pady=10)
        
        # Finalize window geometry
        analyze_window.update_idletasks()
        window_width = analyze_window.winfo_width()
        window_height = analyze_window.winfo_height()
        screen_width = analyze_window.winfo_screenwidth()
        screen_height = analyze_window.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        analyze_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        analyze_window.wait_window()
    def ins_PDF():
        def pdf_button_click():
            gen_PDF()
            
        def end_test():
            pdf_window.destroy()
            
        def finish_test():
            pdf_window.destroy()
            
        # Create a new Toplevel window instead of a new Tk window
        pdf_window = tk.Toplevel()
        pdf_window.title("Generate PDF and CSV")
    
        title_font = ("Bold", 16)
        header_font = ("Bold", 12)
        
        # Labels
        label = tk.Label(pdf_window, text="Create PDF and CSV:", font=title_font)
        label.grid(row=0, column=0, padx=10, pady=10)
        
        step_num = tk.Label(pdf_window, text='Step To Plot')
        step_num.grid(row=1, column=0, padx=10, pady=10)
    
        step_num_var = tk.IntVar(value=0)
        step_num_entry = tk.Entry(pdf_window, textvariable=step_num_var)
        step_num_entry.grid(row=2, column=0, pady=2)
        
        # Entry for output file name
        output_file_label = tk.Label(pdf_window, text="File Name:", font=header_font)
        output_file_label.grid(row=3, column=0, pady=10)
        output_file_entry = tk.Entry(pdf_window)
        output_file_entry.insert(0, "minimumstep.pdf")
        output_file_entry.grid(row=4, column=0, pady=2)
        
        def gen_PDF():
            global fig
        
            plt.rcParams.update({'font.size': 6})
            fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
            
            # Get the size of each axis in inches
            ax2_width, ax2_height = ax2.get_position().size
            ax3_width, ax3_height = ax3.get_position().size
            ax4_width, ax4_height = ax4.get_position().size
        
            # Scale the font size based on the axis size
            font_size_ax2 = max(7, ax2_height * 40)
            font_size_ax3 = max(7, ax3_height * 40)
            font_size_ax4 = max(7, ax4_height * 40)
            
            if ins_probe.get() == 'None':
                if extra_signal == 'Position Command':
                    # Upper Step Plot
                    ax1_up = plt.subplot2grid((14, 3), (2, 0), rowspan=3, colspan=3)
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.pos_fbk, '-r', label='Position Feedback')
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.pos_com, '-b', label='Position Command')
                    plt.title('Incremental Step Test')
                    plt.ylabel('Position ({})'.format(global_state.ins.error_units))
                    plt.xlabel('Time (seconds)')
                    plt.legend(loc='upper right')
                else:
                    ax1_up = plt.subplot2grid((14, 3), (2, 0), rowspan=3, colspan=3)
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.pos_fbk, '-r')
                    plt.title('Incremental Step Test')
                    plt.ylabel('Position ({})'.format(global_state.ins.error_units))
                    plt.xlabel('Time (seconds)')
        
            else:
                if extra_signal == 'Position Command':
                    #Upper Step Plot
                    ax1_up = plt.subplot2grid((14, 3),(2,0), rowspan = 3, colspan = 3)
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.ai0, '-r', label='Analog Input')
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.pos_com, '-b', label='Position Command')
                    plt.title('Incremental Step Test')
                    plt.ylabel('Position ({})'.format(global_state.ins.error_units))
                    plt.xlabel('Time (seconds)')
                    plt.legend(loc='upper right')
                elif extra_signal == 'Position Feedback':
                    #Upper Step Plot
                    ax1_up = plt.subplot2grid((14,3),(2,0), rowspan = 2, colspan = 3)
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.ai0, '-r', label='Analog Input')
                    plt.title('Incremental Step Test')
                    plt.ylabel('Position ({})'.format(global_state.ins.error_units))
                    plt.legend(loc='upper right')
                    ax1_mid = plt.subplot2grid((14,3),(4,0), rowspan = 2, colspan = 3)            
                    ax1_mid.plot(global_state.ins.time_array, global_state.ins.pos_fbk, '-b', label='Position Feedback')
                    plt.ylabel('Position Error ({})'.format(global_state.ins.error_units))
                    plt.xlabel('Time (seconds)')
                    plt.legend(loc='upper right')
                else:
                    ax1_up = plt.subplot2grid((14, 3),(2,0), rowspan = 3, colspan = 3)
                    ax1_up.plot(global_state.ins.time_array, global_state.ins.ai0, '-r')
                    plt.title('Incremental Step Test')
                    plt.ylabel('Position ({})'.format(global_state.ins.error_units))
                    plt.xlabel('Time (seconds)')
            
            # Lower Step Plot
            ax1_down = plt.subplot2grid((14, 5), (6, 0), rowspan=4, colspan=5)
    
            # Directly plot onto the ax1_down axis
            global_state.ins.plot(ax=ax1_down, legend_loc='upper right', step_num=step_num_var.get(), fig_size=(8, 4))
        
            #Results Text Box
            ax2.text(0.02,.8, 'Forward Mean: {:.3e} {}'.format(data['Forward Sample Mean'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax2.text(0.02,.725, 'Reverse Mean: {:.3e} {}'.format(data['Reverse Sample Mean'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax2.text(0.02,.65, 'Combined Mean: {:.3e} {}'.format(data['Combined Sample Mean'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax2.text(0.02,.575, 'Forward StDev: {:.3e} {}'.format(data['Forward Sample Standard Deviation'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax2.text(0.02,.5, 'Reverse StDev: {:.3e} {}'.format(data['Reverse Sample Standard Deviation'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax2.text(0.02,.425, 'Combined StDev: {:.3e} {}'.format(data['Combined Sample Standard Deviation'], global_state.ins.error_units), color = 'black', size = font_size_ax2)
            #ax2.text(0.02,.35, 'Forward Unidirectional Criteria: {}'.format(criteria[3]), color = 'black', size = 8.5)
            #ax2.text(0.02,.275, 'Reverse Unidirectional Criteria: {}'.format(criteria[7]), color = 'black', size = 8.5)
            #ax2.text(0.02,.2, 'Bidirectional Criteria: {}'.format(criteria[11]), color = 'black', size = 8.5)
                        
            #Comments Text Box
            ax3.text(.02, .8, 'Serial Number: {}'.format(ins_sys.get()), color = 'black', size = font_size_ax2)
            ax3.text(.02, .725, 'Model Number: {}'.format(ins_st.get()), color = 'black', size = font_size_ax2)
            ax3.text(.02, .65, 'Axis: {}'.format(ins_axis.get()), color = 'black', size = font_size_ax2)
            ax3.text(.02, .575, 'Feedback: {}'.format(ins_signal_var.get()), color = 'black', size = font_size_ax2)
            ax3.text(.02, .5, 'Comments: {}'.format(ins_comm.get()), color = 'black', size = font_size_ax2, verticalalignment = 'top')
        
            if ins_err_unit.get() == 'nm':
                StepSize = round(ins_step.get() * 1000,2)
            elif ins_err_unit.get() == 'um':
                StepSize = round(ins_step.get() * 1000,2)
            elif ins_err_unit.get() == 'arcsec':
                StepSize = round(ins_step.get() * 3600,2)
            else:
                StepSize = ins_step.get()
            #Test Conditions Text Box
            degree_sign = u'\N{DEGREE SIGN}'
            ax4.text(.02, .8, 'Temperature: {}  {}C'.format(ins_temp.get(), degree_sign), color = 'black', size = font_size_ax2)
            #ax4.text(.02, .725, 'IPS StDev: {} {}'.format(ins.s, ins.units), color = 'black', size = 9)
            ax4.text(.02, .725, 'Move-and-Settle time: {} seconds'.format(global_state.ins.t_ms), color = 'black', size = font_size_ax2)
            ax4.text(.02, .65, 'Average Time: {} seconds'.format(global_state.ins.t_ave), color = 'black', size = font_size_ax2)
            ax4.text(.02, .575, 'Sample Rate: {} Hz'.format(1/global_state.ins.time_array[1]), color = 'black', size = font_size_ax2)
            ax4.text(.02, .500, 'Sample Time: {:.3f} seconds'.format(np.max(global_state.ins.time_array) + global_state.ins.time_array[1]), color = 'black', size = font_size_ax2)
            ax4.text(.02, .425, 'Step Size: {} {}'.format(StepSize,global_state.ins.error_units), color = 'black', size = font_size_ax2)
            ax4.text(.02, .350, 'Start Position: {} {}'.format(global_state.ins.start_pos, global_state.ins.units), color = 'black', size = font_size_ax2)
            ax4.text(.02, .275, 'Number of Steps: {}'.format(global_state.ins.num_steps), color = 'black', size = font_size_ax2)
            #ax4.text(.02, .350, 'Axis: {}'.format(Axis.value), color = 'black', size = 9)
            
            # Save the figure as a PDF
            start_path = ('O:/')
            sys_serial = str(ms_sys.get())
            folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
            pdf_file_path = folder_path + '/Customer Files/Plots'
            folder_name = 'Minimum Step Plots'
            new_file_path = os.path.join(pdf_file_path,folder_name)
            os.makedirs(new_file_path,exist_ok=True)
            
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            new_folder_path = os.path.join(new_file_path, f"{current_time}")
            os.makedirs(new_folder_path, exist_ok=True)
            output_file = str(sys_serial + '-' + str(ms_axis.get()) + "_MinStep.pdf")
            save_file = new_folder_path + '/' + output_file
        
            # Save the figure with tight bounding box
            fig.savefig(save_file, bbox_inches='tight')
            print('PDF saved')
            
            #global_state.ms.GUI_plot_plotly(aero_dict, new_folder_path, ax=ax1, legend_size=20)
            
        # Button to generate PDF
        gen_pdf_button = tk.Button(pdf_window, text="Generate PDF", command=gen_PDF)
        gen_pdf_button.grid(row=5, column=0, pady=5)
    
        # Entry for CSV file name
        csv_file_label = tk.Label(pdf_window, text="CSV Name:", font=header_font)
        csv_file_label.grid(row=6, column=0, pady=10)
        csv_file_entry = tk.Entry(pdf_window)
        csv_file_entry.insert(0, "ms.csv")
        csv_file_entry.grid(row=7, column=0, pady=2)
        
        def save_csv():
            global_state.ins.write_to_csv(csv_file_entry.get(),ipj_sys.get(),ipj_axis.get())
            print('CSV saved')
    
        export_csv_button = tk.Button(pdf_window, text="Save CSV", command=save_csv)
        export_csv_button.grid(row=8, column=0, padx=10, pady=10)
        
        finish_button = tk.Button(pdf_window, text='Finish Test', command=finish_test)
        finish_button.grid(row=9, column=0, padx=10, pady=10)
        
        # Center the window on the screen
        pdf_window.update_idletasks()
        window_width = pdf_window.winfo_width()
        window_height = pdf_window.winfo_height()
        screen_width = pdf_window.winfo_screenwidth()
        screen_height = pdf_window.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        pdf_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
    def ins_test_type_def():
        global direction
        if ins_direction.get() == "uni":
            direction = a1data.mode.Unidirectional
        elif ins_direction.get() == "bi":
            direction = a1data.mode.Bidirectional
        else:
            direction = 'None'
            
    def ins_signal_def(*args):
        global signal
        if ins_signal_var.get() == "Encoder":
            ins_signal = a1data.mode.pos_fbk
            ins_ent_probe["state"] = tk.DISABLED
            ins_lbl_probe["state"] = tk.DISABLED
            ins_ent_sens["state"] = tk.DISABLED
            ins_lbl_sens["state"] = tk.DISABLED
            ins_lbl_sample["state"] = tk.DISABLED
            ins_sample_menu["state"] = tk.DISABLED
        elif ins_signal_var.get() == "Capacitance Probe":
            ins_signal = a1data.mode.ai0
            ins_ent_probe["state"] = tk.NORMAL
            ins_lbl_probe["state"] = tk.NORMAL
            ins_ent_sens["state"] = tk.NORMAL
            ins_lbl_sens["state"] = tk.NORMAL
            ins_lbl_sample["state"] = tk.NORMAL
            ins_sample_menu["state"] = tk.NORMAL

            
    # Function to get the selected sample rate value
    def ins_get_sample_rate_value():
        selected_text = ins_samp.get()  # Get the selected display text, e.g., '1 kHz
        # Find the actual numeric value corresponding to the selected text
        for option in ins_sample_options:
            if option[0] == selected_text:
                return option[1]
        return None  # If not found, return None or handle it as needed
    
    def open_rotary_Plot():


        axis = ins_axis.get()
        sys_serial = ins_sys.get()

        start_path = ('O:/')
        folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)
        pdf_file_path = folder_path + '/Customer Files/Plots'

        if os.path.exists(pdf_file_path):
            try:
                output_file = str(sys_serial + '-' + axis + "_Accuracy.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
            try:
                output_file = str(sys_serial + '-' + axis + "_Verification.pdf")
                pdf = pdf_file_path + '/' + output_file
                os.startfile(pdf)
            except:
                pass
        else:
            print(f"File '{pdf_file_path}' does not exist.")
    
    # Load stored data or set defaults
    ins_axis_value = stored_data.get("axis_name", "X")
    ins_start_value = stored_data.get("start_position", 10)
    ins_step_value = stored_data.get("step_size", 30)
    ins_num_step_value = stored_data.get("num_step", 1)
    ins_signal_value = stored_data.get("signal", 'Encoder')
    ins_probe_value = stored_data.get("probe_axis", 'None')
    ins_sens_value = stored_data.get("scale factor (user units)", '0.0025')
    ins_speed_value = stored_data.get("speed", 5)
    ins_ramp_v_value = stored_data.get("ramp_rate", 1000)
    ins_dwell_value = stored_data.get("dwell", 1)
    ins_ipj_value = stored_data.get("jitter",'')
    ins_settle_value = stored_data.get("settle",'')
    ins_unit_value = stored_data.get("units", 'mm')
    ins_err_unit_value = stored_data.get("error_units", 'mm')
    ins_sample_value = stored_data.get("sample_rate", "1 kHz")
    ins_sys_value = stored_data.get("system_serial_number", '"System Serial Number"')
    ins_st_value = stored_data.get("part_number", '"Part Number"')
    ins_opName_value = stored_data.get("operator", '"Your Initials"')
    ins_temp_value = stored_data.get("temp", 20)
    ins_comm_value = stored_data.get("comments", "")
    
    # Create the UI elements and assign the stored values
    ins_lbl_test = tk.Label(master=tab3, text="Select Test Type:")
    ins_lbl_test.grid(row=tab3.tt_row, column=0, padx=5, pady=5)

    ins_direction = tk.StringVar(value=0)
    ins_uni_dir = tk.Radiobutton(master=tab3, text="Unidirectional", variable=ins_direction, value="uni", command=ins_test_type_def)
    ins_uni_dir.grid(row=tab3.tt_row, column=1, padx=5, pady=5)

    ins_bi_dir = tk.Radiobutton(master=tab3, text="Bidirectional", variable=ins_direction, value="bi", command=ins_test_type_def)
    ins_bi_dir.grid(row=tab3.tt_row, column=2, padx=5, pady=5)
    
    ins_lbl_axis = tk.Label(master=tab3, text="Axis Name", width=25, height=1)
    ins_lbl_axis.grid(row=tab3.axis_row, column=0, padx=5, pady=5)

    ins_axis = tk.StringVar(value=ins_axis_value)
    ins_ent_axis = tk.Entry(master=tab3, textvariable=ins_axis, width=25)
    ins_ent_axis.grid(row=tab3.axis_row, column=1, padx=5, pady=5)

    ins_lbl_st = tk.Label(master=tab3, text="Start Position", width=25, height=1)
    ins_lbl_st.grid(row=tab3.start_row, column=0, padx=5, pady=5)

    ins_start = tk.DoubleVar(value=ins_start_value)
    ins_ent_start_pos = tk.Entry(master=tab3, textvariable=ins_start, width=25)
    ins_ent_start_pos.grid(row=tab3.start_row, column=1, padx=5, pady=5)
    
    ins_lbl_step_size = tk.Label(master=tab3, text="Step Size", width=25, height=1)
    ins_lbl_step_size.grid(row=tab3.step_row, column=0, padx=5, pady=5)

    ins_step = tk.DoubleVar(value=ins_step_value)
    ins_ent_step_size = tk.Entry(master=tab3, textvariable=ins_step, width=25)
    ins_ent_step_size.grid(row=tab3.step_row, column=1, padx=5, pady=5)
    
    ins_lbl_num_step = tk.Label(master=tab3, text="Number of Steps", width=25, height=1)
    ins_lbl_num_step.grid(row=tab3.num_step_row, column=0, padx=5, pady=5)

    ins_num_step = tk.DoubleVar(value=ins_num_step_value)
    ins_ent_num_step = tk.Entry(master=tab3, textvariable=ins_num_step, width=25)
    ins_ent_num_step.grid(row=tab3.num_step_row, column=1, padx=5, pady=5)

    ins_lbl_speed = tk.Label(master=tab3, text="Velocity", width=25, height=1)
    ins_lbl_speed.grid(row=tab3.speed_row, column=0, padx=5, pady=5)

    ins_speed_ = tk.StringVar(value=ins_speed_value)
    ins_ent_speed = tk.Entry(master=tab3, textvariable=ins_speed_, width=25)
    ins_ent_speed.grid(row=tab3.speed_row, column=1, padx=5, pady=5)

    ins_lbl_ramp_rate = tk.Label(master=tab3, text="Ramp Rate")
    ins_lbl_ramp_rate.grid(row=tab3.ramp_v_row, column=0, padx=5, pady=5)

    ins_ramp_v = tk.StringVar(value=ins_ramp_v_value)
    ins_ent_ramp_rate = tk.Entry(master=tab3, textvariable=ins_ramp_v, width=25)
    ins_ent_ramp_rate.grid(row=tab3.ramp_v_row, column=1, padx=5, pady=5)
    
    ins_lbl_dwell = tk.Label(master=tab3, text="Dwell")
    ins_lbl_dwell.grid(row=tab3.dwell_row, column=0, padx=5, pady=5)

    ins_dwell = tk.StringVar(value=ins_dwell_value)
    ins_ent_dwell = tk.Entry(master=tab3, textvariable=ins_dwell, width=25)
    ins_ent_dwell.grid(row=tab3.dwell_row, column=1, padx=5, pady=5)

    ins_lbl_jitter = tk.Label(master=tab3, text="Jitter")
    ins_lbl_jitter.grid(row=tab3.ipj_row, column=0, padx=5, pady=5)

    ins_ipj = tk.DoubleVar(value=ins_ipj_value)
    ins_ent_jitter = tk.Entry(master=tab3, textvariable=ins_ipj, width=25)
    ins_ent_jitter.grid(row=tab3.ipj_row, column=1, padx=5, pady=5)
    
    ins_lbl_sig = tk.Label(master=tab3, text="Signal", width=25, height=1)
    ins_lbl_sig.grid(row=tab3.axis_row, column=2, padx=5, pady=5)
    
    ins_signal_var = tk.StringVar(value=ins_signal_value)
    ins_signal_var.trace_add('write', ins_signal_def)
    ins_signal_options = ['Encoder', 'Capacitance Probe']
    ins_signal_menu = tk.OptionMenu(tab3, ins_signal_var, *ins_signal_options)
    ins_signal_menu.grid(row=tab3.start_row, column=2, padx=5, pady=5)
    
    ins_lbl_probe = tk.Label(master=tab3, text="Probe Axis", width=25, height=1,state=tk.DISABLED)
    ins_lbl_probe.grid(row=tab3.axis_row, column=3, padx=5, pady=5)

    ins_probe = tk.StringVar(value=ins_probe_value)
    ins_ent_probe = tk.Entry(master=tab3, textvariable=ins_probe, width=25,state=tk.DISABLED)
    ins_ent_probe.grid(row=tab3.start_row, column=3, padx=5, pady=5)
    
    ins_lbl_sens = tk.Label(master=tab3, text="Scale Factor (User Units)", width=25, height=1,state=tk.DISABLED)
    ins_lbl_sens.grid(row=tab3.step_row, column=3, padx=5, pady=5)

    ins_sens = tk.StringVar(value=ins_sens_value)
    ins_ent_sens = tk.Entry(master=tab3, textvariable=ins_sens, width=25,state=tk.DISABLED)
    ins_ent_sens.grid(row=tab3.num_step_row, column=3, padx=5, pady=5)
    
    ins_lbl_sample = tk.Label(master=tab3, text="Sample Rate:", width=25, height=1,state=tk.DISABLED)
    ins_lbl_sample.grid(row=tab3.speed_row, column=3, padx=5, pady=5)
    
    ins_sample_options = [('1 kHz', 1000), ('10 kHz', 10000), ('20 kHz', 20000), ('100 kHz', 100000), ('200 kHz', 200000)]
    ins_samp = tk.StringVar(value=ins_sample_value)
    ins_sample_menu = tk.OptionMenu(tab3, ins_samp, *[option[0] for option in ins_sample_options])
    ins_sample_menu.configure(state=tk.DISABLED)
    ins_sample_menu.grid(row=tab3.ramp_v_row, column=3, padx=5, pady=5)
    
    ins_lbl_units = tk.Label(master=tab3, text="Units:", width=25, height=1)
    ins_lbl_units.grid(row=tab3.step_row, column=2, padx=5, pady=5)
    
    ins_unit_options = ['mm', 'um', 'nm', 'deg']
    ins_unit = tk.StringVar(value=ins_unit_value)
    ins_unit_menu = tk.OptionMenu(tab3, ins_unit, *ins_unit_options)
    ins_unit_menu.grid(row=tab3.num_step_row, column=2, padx=5, pady=5)
    
    ins_lbl_err_units = tk.Label(master=tab3, text="Error Units:", width=25, height=1)
    ins_lbl_err_units.grid(row=tab3.speed_row, column=2, padx=5, pady=5)
    
    ins_err_unit_options = ['mm', 'um', 'nm', 'arcsec', 'deg']
    ins_err_unit = tk.StringVar(value=ins_err_unit_value)
    ins_err_unit_menu = tk.OptionMenu(tab3, ins_err_unit, *ins_err_unit_options)
    ins_err_unit_menu.grid(row=tab3.ramp_v_row, column=2, padx=5, pady=5)
    
    ins_lbl_settle = tk.Label(master=tab3, text="Settle Time")
    ins_lbl_settle.grid(row=tab3.ipj_row, column=2, padx=5, pady=5)

    ins_settle = tk.DoubleVar(value=ins_settle_value)
    ins_ent_settle = tk.Entry(master=tab3, textvariable=ins_settle, width=25)
    ins_ent_settle.grid(row=tab3.ipj_row, column=3, padx=5, pady=5)

    ins_lbl_serial = tk.Label(master=tab3, text="System Serial Number", width=25, height=1)
    ins_lbl_serial.grid(row=tab3.sys_row, column=0, padx=5, pady=5)

    ins_sys = tk.StringVar(value=ins_sys_value)
    ins_ent_serial = tk.Entry(master=tab3, textvariable=ins_sys, width=25)
    ins_ent_serial.grid(row=tab3.sys_row, column=1, columnspan=3, padx=5, pady=5)

    ins_lbl_st_model = tk.Label(master=tab3, text="Part Number", width=25, height=1)
    ins_lbl_st_model.grid(row=tab3.st_row, column=0, padx=5, pady=5)

    ins_st = tk.StringVar(value=ins_st_value)
    ins_ent_st_model = tk.Entry(master=tab3, textvariable=ins_st, width=25)
    ins_ent_st_model.grid(row=tab3.st_row, column=1, columnspan=3, padx=5, pady=5)

    ins_lbl_op = tk.Label(master=tab3, text="Operator", width=25, height=1)
    ins_lbl_op.grid(row=tab3.op_row, column=0, padx=5, pady=5)

    ins_opName = tk.StringVar(value=ins_opName_value)
    ins_ent_op = tk.Entry(master=tab3, textvariable=ins_opName, width=25)
    ins_ent_op.grid(row=tab3.op_row, column=1, columnspan=3, padx=5, pady=5)

    ins_lbl_temp = tk.Label(master=tab3, text="Temp", width=25, height=1)
    ins_lbl_temp.grid(row=tab3.temp_row, column=0, padx=5, pady=5)

    ins_temp = tk.DoubleVar(value=ins_temp_value)
    ins_ent_temp = tk.Entry(master=tab3, textvariable=ins_temp, width=25)
    ins_ent_temp.grid(row=tab3.temp_row, column=1, columnspan=3, padx=5, pady=5)

    ins_lbl_comments = tk.Label(master=tab3, text="Comments", width=25, height=1)
    ins_lbl_comments.grid(row=tab3.com_row, column=0, padx=5, pady=5)

    ins_comm = tk.StringVar(value=ins_comm_value)
    ins_ent_comments = tk.Entry(master=tab3, textvariable=ins_comm, width=25)
    ins_ent_comments.grid(row=tab3.com_row, column=1, columnspan=3, padx=5, pady=5)

    #btn_import_rot = tk.Button(master=tab1, text="Import Data", width=30, height=1, command=import_data_rotary)
    #btn_import_rot.grid(row=tab1.run_row, column=1, padx=5, pady=5)

    ins_lbl_import_rot = tk.Label(master=tab3, text='', anchor='w')
    ins_lbl_import_rot.grid(row=tab3.run_row, column=1, padx=5, pady=5, columnspan=3)

    ins_btn_run_rot = tk.Button(master=tab3, text="Run", width=25, height=1, command=start_incrementalsteptest)
    ins_btn_run_rot.grid(row=tab3.run_row, column=0, padx=5, pady=5)

    ins_btn_open_rot = tk.Button(master=tab3, text="Open Plot", width=25, height=1, command=open_rotary_Plot)
    ins_btn_open_rot.grid(row=tab3.run_row, column=2, padx=5, pady=5)

    frame2 = tk.Frame(master=tab3)

    txt_outStr2 = tk.Text(master=frame2, state=tk.DISABLED, height=10, fg='white', bg='black')
    outStr_scroll2 = tk.Scrollbar(master=frame2, orient=tk.VERTICAL)

    txt_outStr2.configure(yscrollcommand=outStr_scroll2.set)
    outStr_scroll2.config(command=txt_outStr2.yview)

    txt_outStr2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    outStr_scroll2.pack(side=tk.LEFT, fill=tk.Y)

    frame2.grid(row=tab3.out_row, column=0, columnspan=7, padx=5, pady=5, sticky='nsew')

    logger3 = TextLogger(txt_outStr2)
    
    tab3.grid_rowconfigure(tab3.out_row, weight=1)
    tab3.grid_columnconfigure(0, weight=1)
    
    def ins_on_closing():
        # Save user inputs before closing
        user_data = {
            "axis_name": ins_axis.get(),
            "start_position": ins_start.get(),
            "step_size": ins_step.get(),
            "num_step": ins_num_step.get(),
            "signal": ins_signal_var.get(),
            "probe_axis": ins_probe.get(),
            "scale factor (user units)": ins_sens.get(),
            "speed": ins_speed_.get(),
            "ramp_rate": ins_ramp_v.get(),
            "dwell": ins_dwell.get(),
            "jitter": ins_ipj.get(),
            "settle": ins_settle.get(),
            "units": ins_unit.get(),
            "error_units": ins_err_unit.get(),
            "sample_rate": ins_samp.get(),
            "system_serial_number": ins_sys.get(),
            "part_number": ins_st.get(),
            "operator": ins_opName.get(),
            "temp": ins_temp.get(),
            "comments": ins_comm.get()
        }
        save_user_inputs(user_data)
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", ins_on_closing)
    
    window.mainloop()

if __name__ == "__main__":
    UI()