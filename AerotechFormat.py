# -*- coding: utf-8 -*-
"""
Unified AerotechFormat for single or dual plot templates.
"""
import matplotlib.pyplot as plt
import matplotlib.image as image
import matplotlib.backends.backend_agg as agg
import os
import sys


class AerotechFormat:
    @staticmethod
    def resource_path(relative_path):
        """
        Get the absolute path to a resource file.

        This method is useful for locating resource files in both development 
        and packaged (e.g., PyInstaller) environments.

        Args:
            relative_path (str): The relative path to the resource file.

        Returns:
            str: The absolute path to the resource file.
        """
        # Determine the base path. If running as a PyInstaller bundle, use the
        # temporary _MEIPASS directory. Otherwise, use the directory of the script.
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        
        # Construct the full path to the resource and return it
        return os.path.join(base_path, relative_path)

    @staticmethod
    def makeTemplate(num_plots=1):
        """
        Create a figure template with a single or dual plot layout.

        Args:
            num_plots (int): Number of plots (1 or 2). Defaults to 1.

        Returns:
            tuple: The figure and a list of axes for the plots and text boxes.
        """
        def calculate_max_label_width(ax, fig):
            renderer = fig.canvas.get_renderer()
            label_widths = [label.get_window_extent(renderer).width for label in ax.get_yticklabels()]
            return max(label_widths) if label_widths else 0

        # Update default font size for plots
        plt.rcParams.update({"font.size": 8})

        # Create a new figure with specified size
        fig = plt.figure()
        fig.set_size_inches(11, 8.5)  # Full page size

        # Load and display the Aerotech logo
        logo_path = AerotechFormat.resource_path("AerotechLogo.png")
        if not os.path.exists(logo_path):
            raise FileNotFoundError(f"Logo file not found at {logo_path}")
        logo = image.imread(logo_path)
        ax_logo = plt.subplot2grid((12, 3), (0, 0), rowspan=1, colspan=3)
        ax_logo.imshow(logo)
        ax_logo.axis("off")  # Hide axes for the logo image

        # Initialize a list to store plot axes
        axes = []

        if num_plots == 1:
            # Single plot layout
            ax1 = plt.subplot2grid((12, 3), (2, 0), rowspan=7, colspan=3)
            ax1.spines["top"].set_visible(True)
            ax1.spines["right"].set_visible(True)
            ax1.tick_params(left=True, bottom=True, labelsize=8)
            ax1.grid(False)
            axes.append(ax1)
            
        if num_plots == 2:
            # Top plot
            ax1 = plt.subplot2grid((12, 3), (2, 0), rowspan=3, colspan=3)
            ax1.spines["top"].set_visible(True)
            ax1.spines["right"].set_visible(True)
            ax1.tick_params(left=True, bottom=True, labelsize=8)
            ax1.grid(False)
            axes.append(ax1)

            # Bottom plot
            ax2 = plt.subplot2grid((12, 3), (6, 0), rowspan=3, colspan=3)
            ax2.spines["top"].set_visible(True)
            ax2.spines["right"].set_visible(True)
            ax2.tick_params(left=True, bottom=True, labelsize=8)
            ax2.grid(False)
            axes.append(ax2)

        for ax in axes:  # Iterate over all plot axes
            max_label_width = calculate_max_label_width(ax, fig)
            shrink_factor = max_label_width / fig.dpi / fig.get_size_inches()[0]
            plot_position = ax.get_position()
            ax.set_position([plot_position.x0 + shrink_factor, plot_position.y0, 
                            plot_position.width - shrink_factor, plot_position.height])
        
        # Text Boxes
        box_width = 0.25  # Width of each text box
        margin = 0.1  # Margin from the edges of the page
        gap = (1 - 2 * margin - 3 * box_width) / 2  # Equal gap between boxes

        ax3 = plt.subplot2grid((12, 3), (10, 0), rowspan=2, colspan=1)
        ax3.set_position([margin, 0.05, box_width, 0.15])  # Left box
        axes.append(ax3)

        ax4 = plt.subplot2grid((12, 3), (10, 1), rowspan=2, colspan=1)
        ax4.set_position([margin + box_width + gap, 0.05, box_width, 0.15])  # Center box
        axes.append(ax4)

        ax5 = plt.subplot2grid((12, 3), (10, 2), rowspan=2, colspan=1)
        ax5.set_position([margin + 2 * (box_width + gap), 0.05, box_width, 0.15])  # Right box
        axes.append(ax5)

        # Ensure text boxes have proper padding
        for ax in [ax3, ax4, ax5]:
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
            for spine in ax.spines.values():
                spine.set_visible(True)

        for ax, text, color in zip(
            [ax3, ax4, ax5],
            ["Results", "System Information", "Test Conditions"],
            ["black", "black", "black"],
        ):
            ax.text(0.02, 0.9, text, color=color, weight="bold", size=9)
            ax.axes.get_xaxis().set_ticks([])
            ax.axes.get_yaxis().set_ticks([])
        # Return the figure and the list of axes
        return fig, [ax_logo] + axes