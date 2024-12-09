# -*- coding: utf-8 -*-
"""
Created on Thu May 26 15:08:17 2022

@author: shunn
"""
import matplotlib.pyplot as plt
import matplotlib.image as image
import os

class AerotechFormat():
    
    #Inputs: Nothing
    #Outputs: fig = Complete Figure
    # ax1 = Main Plot
    # ax2 = Text Box 1
    # ax3 = Text Box 2
    # ax4 = Text Box 3
    
    def makeTemplate():
        plt.rcParams.update({'font.size': 6})
        fig = plt.figure()
        fig.set_size_inches(11, 8.5)  # Full page size
        
        # Aerotech Logo Header
        # Get the current working directory
        current_dir = os.getcwd()
        
        # Construct the absolute path to the file
        logo_path = os.path.join(current_dir, 'AERO_LogoNoTagline-RGB.png')
        logo = image.imread(logo_path, format='png')
        ax0 = plt.subplot2grid((7, 3), (0, 0), rowspan=1, colspan=3)
        ax0.imshow(logo)
        ax0.axis('off')
        
        # Main Plot (ax1) spans the top portion
        ax1 = plt.subplot2grid((7, 3), (1, 0), rowspan=4, colspan=3)
        ax1.spines['top'].set_visible(True)
        ax1.spines['right'].set_visible(True)
        
        # Create the text boxes with specific positions
        ax2 = plt.subplot2grid((7, 3), (5, 0), rowspan=2, colspan=1)
        ax3 = plt.subplot2grid((7, 3), (5, 1), rowspan=2, colspan=1)
        ax4 = plt.subplot2grid((7, 3), (5, 2), rowspan=2, colspan=1)
        
        # Set custom positions for ax2, ax3, and ax4
        ax2.set_position([0.1, 0.1, 0.25, 0.15])  # [left, bottom, width, height]
        ax3.set_position([0.375, 0.1, 0.25, 0.15])  # Center the middle text box
        ax4.set_position([0.65, 0.1, 0.25, 0.15])  # Align the right text box
        
        # Customize each text box
        ax2.text(0.01, 0.9, 'Results', color='black', weight='bold', size=9)
        ax2.text(0.02, 0.20, 'Aerotech Inc.,', color='red', weight='bold', size=7)
        ax2.text(0.02, 0.05, 'Proprietary and Confidential', color='red', weight='bold', size=7)
        ax2.axes.get_xaxis().set_ticks([])
        ax2.axes.get_yaxis().set_ticks([])
      
        ax3.text(0.01, 0.90, 'System Information', color='black', weight='bold', size=9)
        ax3.axes.get_xaxis().set_ticks([])
        ax3.axes.get_yaxis().set_ticks([])
    
        ax4.text(0.01, 0.9, 'Test Conditions', color='black', weight='bold', size=9)
        ax4.axes.get_xaxis().set_ticks([])
        ax4.axes.get_yaxis().set_ticks([])
        
        return fig, ax1, ax2, ax3, ax4

if __name__ == '__main__':
    AerotechFormat.makeTemplate()
    
    