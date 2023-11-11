import glob
import json
import os
import uuid
import sys
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk


fm_export_path = ""
class CustomLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Autoscroll to the bottom
        self.text_widget.update_idletasks()  # Update the Tkinter GUI

    def flush(self):
        pass

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.display_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def display_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
        )
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def gen_html(dataframe: pd.DataFrame):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id="table", index=False)
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                paging: false,
                order: [[12, 'desc']],
                // scrollY: 400,
            }});
        }});
    </script>
    </body>
    </html>
    """
    # return the html
    return html


def weight_calc(position, category_id, position_weights: json, squad_rawdata):
    """
    This takes in a position as defined in the json
    And a category_id (IE: essential, core, secondary) and provides a consistent way of calculating a players ability
    based on given attributes and weights from the json
    We do this via the value of the attribute * the weight divided by the number of items * the weight
    """
    try:
        attributes = position_weights["positions"][position][category_id]["attributes"]
    except KeyError:
        attributes = []
    if attributes:
        try:
            weight = position_weights["positions"][position][category_id]["weight"]
        except KeyError:
            weight = 0
        # calculate the normaliser via the number of items * the weight
        normaliser = (
            len(position_weights["positions"][position][category_id]["attributes"])
            * weight
        )
        # print(
        #    f"""
        #      Debug:
        #      Position: {position}
        #      Cat: {category_id}
        #      Debug weight: {weight}
        #      normaliser: {normaliser}"""
        # )
        attribute_values = (
            sum(squad_rawdata[attribute] for attribute in attributes) * weight
        )
        if normaliser != 0:
            v = attribute_values / normaliser
            return v
        else:
            return 0
    else:
        # print(
        #    f"""
        #      Debug:
        #      Position: {position}
        #      Cat: {category_id}
        #      Debug weight: Not set (0)
        #      normaliser: Not Set (0)"""
        # )
        return 0


def main(fm_export_path, output_path):
    # finds most recent file in specified folder
    export_dir: str = fm_export_path

    list_of_files = glob.glob(os.path.join(export_dir, "*"))
    try:
        latest_file = max(list_of_files, key=os.path.getctime)
        latest_filename = os.path.basename(latest_file).replace(".html", "")
    except ValueError:
        print(f"No files found in {export_dir}")
        latest_filename = None

    # print(f"Debug Latest File: {latest_filename}")

    # Read HTML file exported by FM - in this case an example of an output from the squad page
    # This reads as a list, not a dataframe
    squad_rawdata_list: list = pd.read_html(
        latest_file, header=0, encoding="utf-8", keep_default_na=False
    )

    # transform the list into a dataframe
    squad_rawdata = squad_rawdata_list[0]

    # Calculate simple speed and workrate scores
    squad_rawdata["Spd"] = (squad_rawdata["Pac"] + squad_rawdata["Acc"]) / 2
    squad_rawdata["Work"] = (squad_rawdata["Wor"] + squad_rawdata["Sta"]) / 2
    squad_rawdata["SetP"] = (squad_rawdata["Jum"] + squad_rawdata["Bra"]) / 2

    # Keep a list of all the headers we want to use in the final view
    final_view_headers = []

    # Add all the exported view names for the final view
    allowed_view_items = [
        "Reg",
        "Inf",
        "Name",
        "Age",
        "Wage",
        "Transfer Value",
        "Nat",
        "2nd Nat",
        "Position",
        "Personality",
        "Media Handling",
        "Av Rat",
        "Left Foot",
        "Right Foot",
        "Height",
        "1v1",
        "Acc",
        "Aer",
        "Agg",
        "Agi",
        "Ant",
        "Bal",
        "Bra",
        "Cmd",
        "Cnt",
        "Cmp",
        "Cro",
        "Dec",
        "Det",
        "Dri",
        "Fin",
        "Fir",
        "Fla",
        "Han",
        "Hea",
        "Jum",
        "Kic",
        "Ldr",
        "Lon",
        "Mar",
        "OtB",
        "Pac",
        "Pas",
        "Pos",
        "Ref",
        "Spd",
        "Work",
        "Sta",
        "Str",
        "Tck",
        "Tea",
        "Tec",
        "Thr",
        "TRO",
        "Vis",
        "Wor",
        "UID",
        "Cor",
        "Club",
    ]

    # Add the views from the "views.json" to the final views list if its in the allowed list
    try:
        with open("views.json", "r") as views_json:
            core_views = json.load(views_json)
    except FileNotFoundError:
        print("Could not find the views.json file")
    for view_item in core_views["order"]:
        if view_item in allowed_view_items:
            final_view_headers.append(view_item)
        else:
            print(f"Ignoring {view_item} since it is not in the allowed views list")

    # Load position weights from JSON file
    try:
        with open("positions.json", "r") as json_file:
            position_weights = json.load(json_file)

            # Retrieve position category from JSON configuration
            position_category = list(
                position_weights["positions"].keys()
            )  # Get the key from the "positions" dictionary
            for position in position_category:
                squad_rawdata[f"{position}"] = 0
                # Now get each scoring category from the json ie: "core, essential etc"
                scoring_categories = list(
                    position_weights["positions"][position].keys()
                )
                for category in scoring_categories:
                    # Add the data back to the data frame after we have run some calculations on it
                    squad_rawdata[f"{position}"] += weight_calc(
                        position, category, position_weights, squad_rawdata
                    )
                squad_rawdata[position] = squad_rawdata[position].round(1)
                final_view_headers.append(position)
    except FileNotFoundError:
        print("Could not find the positions.json file")

    squad = squad_rawdata[final_view_headers]
    # Create the dir if it does not exist
    if not os.path.exists(f"{output_path}/fmds_fmds_generated_data/"):
        os.makedirs(f"{output_path}/fmds_generated_data/")
    # generates random file name for write-out of html file based on the file we use

    filename = str(
        f"{output_path}/fmds_generated_data/{latest_filename}-{uuid.uuid4()}.html"
    )
    # creates a sortable html export from the dataframe 'squad'
    html = gen_html(squad)
    open(filename, "w", encoding="utf-8").write(html)
    print(f"Saved file: {filename}")


# Function to select export path using file dialog
def select_fm_export_path():
    global fm_export_path
    fm_export_path = filedialog.askdirectory()
    fm_export_path_label.config(text="Export Path: " + fm_export_path)


# Function to select output directory using file dialog
def select_output_dir():
    global output_dir
    output_dir = filedialog.askdirectory()
    output_dir_label.config(text="Output Directory: " + output_dir)


# Function to generate the HTML and perform other operations
def generate_html():
    try:
        main(fm_export_path, output_dir)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


# Function to save configuration settings to JSON file
def save_config_to_json():
    try:
        config_data = {
            "fm_export_path": fm_export_path,
            "output_dir": output_dir
            # Add more configuration parameters here if needed
        }
        with open("config.json", "w") as config_file:
            json.dump(config_data, config_file)
        print("Configuration saved to config.json.")
    except NameError:
        print("Please set the paths before saving!")


# Function to load configuration settings from JSON file
def load_config_from_json():
    global fm_export_path, output_dir  # Declare fm_export_path and output_dir as global variables
    try:
        with open("config.json", "r") as config_file:
            config_data = json.load(config_file)
            fm_export_path = config_data.get("fm_export_path")
            output_dir = config_data.get("output_dir")
            if fm_export_path and output_dir:
                fm_export_path_label.config(text="Export Path: " + fm_export_path)
                output_dir_label.config(text="Output Directory: " + output_dir)
                print("Configuration loaded from config.json.")
            else:
                print("Invalid configuration data in config.json.")
    except FileNotFoundError:
        print("No config.json file found.")
    return fm_export_path, output_dir  # Return the values if needed elsewhere 


root = tk.Tk()
root.iconbitmap("media/icon.ico")
root.title("FMDS")

# Create a Text widget for logging
log_text = tk.Text(root, wrap=tk.WORD, height=20, width=80)
log_text.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

# Redirect sys.stdout and sys.stderr to the custom logger
custom_logger = CustomLogger(log_text)
sys.stdout = custom_logger
sys.stderr = custom_logger


# Configure styles
style = ttk.Style()
style.configure("TButton", padding=10, font=("Arial", 12))

# Frame for export path
export_frame = ttk.Frame(root, padding=10, relief="solid", borderwidth=1)
export_frame.pack(pady=10, padx=10, fill="x")
fm_export_path_button = ttk.Button(
    export_frame, text="Select FM Exported Data Path", command=select_fm_export_path
)
fm_export_path_button.pack(side="left")
fm_export_path_label = ttk.Label(export_frame, text="Export Path: Not Selected")
fm_export_path_label.pack(side="left")
tooltip_export = ToolTip(fm_export_path_button, "Select the export path containing the exported views from Football Manager")

# Frame for output directory
output_frame = ttk.Frame(root, padding=10, relief="solid", borderwidth=1)
output_frame.pack(pady=10, padx=10, fill="x")
output_dir_button = ttk.Button(
    output_frame, text="Select Output Directory", command=select_output_dir
)
output_dir_button.pack(side="left")
output_dir_label = ttk.Label(output_frame, text="Output Directory: Not Selected")
output_dir_label.pack(side="left")
tooltip_output = ToolTip(output_dir_button, "Select the output directory, This will create a fmds_generated_data folder")

# Frame for save and load config buttons
config_frame = ttk.Frame(root, style="TFrame")
config_frame.pack(pady=10, padx=10, fill="x")

# Button to load config from JSON
load_button = ttk.Button(config_frame, text="Load Config", command=load_config_from_json, style="TButton")
load_button.pack(side="left")

# Button to save config to JSON
save_button = ttk.Button(config_frame, text="Save Config", command=save_config_to_json, style="TButton")
save_button.pack(side="left")

# Action button with an icon
action_button = ttk.Button(
    root, text="Generate", command=generate_html, compound="left", style="TButton"
)
action_button.pack(pady=10)

root.mainloop()