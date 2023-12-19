############################## Imports ##############################

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta


############################## Configuration ##############################

# Load the chore data from the yaml file
yaml_file = "./chore-list.yaml"

# This list creates the column headers for the chart
dates = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Weekly",
    "Monthly"
]

# Set the colors for each chore frequency and the room row
room_row_color = 'DarkSeaGreen'
color_config = {
    "Daily": "Azure",
    "Weekly": "LemonChiffon",
    "Monthly": "LightPink",
    "Individual": "DarkTurquoise"
}

# Set the max number of rows per page
max_rows_per_page = 28

# Set the max number of characters per line for the chore text
text_wrap_length = 30


############################## Functions ##############################

# Function to wrap chore text into lines of a maximum length in the cell
def wrap_text(text, max_length):
    """
    A simple word-wrap function that breaks text into lines of a maximum length.
    """
    words = text.split()
    lines = []
    current_line = ''

    for word in words:
        if len(current_line + ' ' + word) <= max_length:
            current_line += ' ' + word
        else:
            lines.append(current_line.strip())
            current_line = word
    lines.append(current_line.strip())

    return '\n'.join(lines)

# Function to create a dataframe from the yaml data
def process_chores_data(chores_data):
    rows = []
    for room, frequencies in chores_data.items():
        for freq, chores in frequencies.items():
            for chore in chores:
                rows.append([room, chore, freq])
    return pd.DataFrame(rows, columns=["Room", "Chore", "Frequency"])

# Function to create subsets of chores that will fit on a single page
def create_subsets(df, max_rows_pp_func):
    # Create subsets of chores that will fit on a single page
    # Each subset will start with a new room
    # max_row_pp_func is directly controlled by the max_rows_per_page variable at the top of the script
    subsets = []
    current_subset = []
    current_room = None

    for _, row in df.iterrows():
        room = row['Room']
        # Count the number of chores for the current room
        room_chores_count = len(df[df['Room'] == room]) + 2  # Add 2 for the room label and blank row

        # Check if adding this room's chores would exceed the max rows per page
        if current_room != room:
            if current_subset and len(current_subset) + room_chores_count > max_rows_pp_func:
                # Current subset is full, start a new subset
                subsets.append(pd.DataFrame(current_subset))
                current_subset = []
        
        current_subset.append(row)
        current_room = room

        # If the current subset reaches the max rows, start a new subset
        if len(current_subset) == max_rows_pp_func:
            subsets.append(pd.DataFrame(current_subset))
            current_subset = []
            current_room = None  # Reset to allow the next set to start with the same room if needed

    # Add the remaining chores in the last subset
    if current_subset:
        subsets.append(pd.DataFrame(current_subset))

    return subsets

# Function to create a subplot for a subset of chores
def create_subplot_for_subset(subset, ax):
    # Row by row, take in one of the subset of chores and add them to the chart
    # If the room changes, add a row with the room name
    y_pos = 0
    prev_room = None
    for i, (room, chore, freq) in enumerate(subset.itertuples(index=False, name=None)):
        # Add room label only when it changes
        if room != prev_room:
            ax.add_patch(plt.Rectangle((0, y_pos - 0.5), 11, 1, color=room_row_color, zorder=0))
            ax.text(0.04, y_pos, room, ha='left', va='center', fontweight='bold', fontsize=10)
            prev_room = room
            y_pos += 1

        # Chore label
        wrapped_chore = wrap_text(chore, text_wrap_length)
        ax.text(0.1, y_pos, wrapped_chore, ha='left', va='center', fontsize=8, style='italic')

        monthly_column = dates.index("Monthly")  + 2
        weekly_column = dates.index("Weekly") + 2
        columns = list(range(2, 11))


        # Custom coloring based on chore frequency
        color_y_pos = y_pos - 0.5  # Adjust the y-position for coloring
        if freq == "Monthly":
            ax.add_patch(plt.Rectangle((monthly_column, color_y_pos), 1, 1, color=color_config[freq]))
            columns.remove(monthly_column)
            for day_idx in columns:
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color='lightgray'))
        elif freq == "Weekly":
            ax.add_patch(plt.Rectangle((weekly_column, color_y_pos), 1, 1, color=color_config[freq]))
            columns.remove(weekly_column)
            for day_idx in columns:
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color='lightgray'))
        elif freq == "Individual":
            for day_idx in range(2, 6):
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color=color_config.get(freq, 'grey')))
            for day_idx in range(6, 11):
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color='lightgray'))
        else:  # Daily chores
            columns.remove(weekly_column)
            columns.remove(monthly_column)
            for day_idx in columns:
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color=color_config.get(freq, 'grey')))
            for day_idx in [weekly_column, monthly_column]:
                ax.add_patch(plt.Rectangle((day_idx, color_y_pos), 1, 1, color='lightgray'))

        y_pos += 1

    # Add the date range to the bottom of the chart
    previous_sunday = datetime.today() - timedelta(days=(datetime.today().weekday() + 1) % 7)
    next_saturday = previous_sunday + timedelta(days=6)
    week_range = f"{previous_sunday.strftime('%m/%d/%Y')} - {next_saturday.strftime('%m/%d/%Y')}"
    ax.set_xlabel(week_range, fontsize=16, style='oblique', labelpad=10)
    
    for i in range(2, 11):  # Iterate over the columns (excluding the first two)
        middle_of_cell = i + 0.5  # Calculate the middle of the cell
        ax.axvline(x=middle_of_cell, color='darkgray', linestyle='-', linewidth=0.5)

    # Grid and axis formatting
    ax.set_xlim(0, 10.5) 
    ax.set_ylim(-0.5, y_pos - 0.5)
    ax.set_yticks(np.arange(y_pos) + 0.5)
    ax.set_yticklabels([])
    ax.set_xticks(np.arange(2, 2 + len(dates) + 1))
    ax.set_xticks(np.arange(2.5, 2 + len(dates)), minor=True)
    ax.set_xticklabels(dates, minor=True, rotation_mode='anchor', ha='right', va='center', rotation=-50)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.tick_params(axis='x', which='major', labelsize=0, length=0)
    ax.tick_params(axis='x', which='minor', length=0) 
    ax.tick_params(axis='y', length=0)
    ax.grid(True, color='black')


############################## Main ##############################

# Load the yaml data
with open(yaml_file, 'r') as file:
    chores_data = yaml.safe_load(file)

# Create a dataframe from the yaml data
chores_df = process_chores_data(chores_data)

# Create subsets of chores that will fit on a single page
subsets = create_subsets(chores_df, max_rows_per_page)

# Create a pdf with a page("subplot") for each subset of chores
with PdfPages('chore_chart.pdf') as pdf:
    for subset in subsets:
        fig, ax = plt.subplots(figsize=(11, 8.5))
        create_subplot_for_subset(subset, ax)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)
