import glob
import json
import os
import uuid
import pandas as pd


def generate_html(dataframe: pd.DataFrame):
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


def weight_calc(position, category_id):
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
        print(
            f"""
              Debug:
              Position: {position}
              Cat: {category_id}
              Debug weight: {weight}
              normaliser: {normaliser}"""
        )
        attribute_values = (
            sum(squad_rawdata[attribute] for attribute in attributes) * weight
        )
        if normaliser != 0:
            v = attribute_values / normaliser
            return v
        else:
            return 0
    else:
        print(
            f"""
              Debug:
              Position: {position}
              Cat: {category_id}
              Debug weight: Not set (0)
              normaliser: Not Set (0)"""
        )
        return 0


# finds most recent file in specified folder
export_dir: str = "E:\git\personal\FMDS\exports"
list_of_files = glob.glob(os.path.join(export_dir, "*"))
try:
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_filename = os.path.basename(latest_file).replace('.html', '')
except ValueError:
    print(f"No files found in {export_dir}")
    latest_filename = None

print(f"Debug Latest File: {latest_filename}")

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
with open("views.json", "r") as views_json:
    core_views = json.load(views_json)
for view_item in core_views["order"]:
    if view_item in allowed_view_items:
        final_view_headers.append(view_item)
    else:
        print(f"Ignoring {view_item} since it is not in the allowed views list")

# Load position weights from JSON file
with open("positions.json", "r") as json_file:
    position_weights = json.load(json_file)

    # Retrieve position category from JSON configuration
    position_category = list(
        position_weights["positions"].keys()
    )  # Get the key from the "positions" dictionary
    for position in position_category:
        squad_rawdata[f"{position}"] = 0
        # Now get each scoring category from the json ie: "core, essential etc"
        scoring_categories = list(position_weights["positions"][position].keys())
        for category in scoring_categories:
            # Add the data back to the data frame after we have run some calculations on it
            squad_rawdata[f"{position}"] += weight_calc(position, category)
        squad_rawdata[position] = squad_rawdata[position].round(1)
        final_view_headers.append(position)


squad = squad_rawdata[final_view_headers]
# Create the dir if it does not exist
if not os.path.exists('generated_data'):
   os.makedirs('generated_data')
# generates random file name for write-out of html file based on the file we use

filename = str(f"generated_data/{latest_filename}-{uuid.uuid4()}.html")
# creates a sortable html export from the dataframe 'squad'
html = generate_html(squad)
open(filename, "w", encoding="utf-8").write(html)