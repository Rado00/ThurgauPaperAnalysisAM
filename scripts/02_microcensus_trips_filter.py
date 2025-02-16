"""
input data: (For example)
- microzensus\wege.csv
- microzensus\etappen.csv
- shapefiles\shapefile.shp

output data:
- microzensus\trips.csv
- plots\plots_{analysis_zone_name}\purpose_distribution_Total_microcensus.png
- plots\plots_{analysis_zone_name}\purpose_distribution_pct_microcensus.png

- Remove persons with trips with unknown mode or unknown purpose
- Remove persons with trips not ending with 'home'
- Remove persons with trips not starting with 'home'
"""
import logging

# Import necessary libraries
import pyproj
import numpy as np
import pandas as pd
import plotly.express as px
import geopandas as gpd
from shapely.geometry import Point
from common import *
import warnings

warnings.filterwarnings("ignore")

# Get the path to the current script folder
current_script_folder = os.getcwd()
dataFunctions_folder_path = os.path.join(current_script_folder, 'dataFunctions')
sys.path.append(os.path.abspath(dataFunctions_folder_path))


def execute(path):
    # Specify encoding
    encoding = "latin1"

    df_mz_trips = pd.read_csv(f"{path}\\microzensus\\wege.csv", encoding=encoding)
    df_mz_stages = pd.read_csv(f"{path}\\microzensus\\etappen.csv", encoding=encoding)

    df_mz_trips = df_mz_trips[[
        "HHNR", "WEGNR", "f51100", "f51400", "wzweck1", "wzweck2", "wmittel",
        "S_X_CH1903", "S_Y_CH1903", "Z_X_CH1903", "Z_Y_CH1903", "W_X_CH1903", "W_Y_CH1903",
        "w_rdist", 'dauer2'
    ]]

    df_mz_stages = df_mz_stages[[
        "HHNR", "WEGNR", "ETNR", "f51300"
    ]]

    # First, adjust the modes
    df_mz_trips.loc[df_mz_trips["wmittel"] == -99, "mode"] = "unknown"  # Pseudo stage
    df_mz_trips.loc[df_mz_trips["wmittel"] == 1, "mode"] = "pt"  # Plane
    df_mz_trips.loc[df_mz_trips["wmittel"] == 2, "mode"] = "pt"  # Train
    df_mz_trips.loc[df_mz_trips["wmittel"] == 3, "mode"] = "pt"  # Postauto
    df_mz_trips.loc[df_mz_trips["wmittel"] == 4, "mode"] = "pt"  # Ship
    df_mz_trips.loc[df_mz_trips["wmittel"] == 5, "mode"] = "pt"  # Tram
    df_mz_trips.loc[df_mz_trips["wmittel"] == 6, "mode"] = "pt"  # Bus
    df_mz_trips.loc[df_mz_trips["wmittel"] == 7, "mode"] = "pt"  # other PT
    df_mz_trips.loc[df_mz_trips["wmittel"] == 8, "mode"] = "pt"  # Reisecar -> I think this is a coach in Swiss German?
    df_mz_trips.loc[df_mz_trips["wmittel"] == 9, "mode"] = "car"  # Car
    df_mz_trips.loc[df_mz_trips["wmittel"] == 10, "mode"] = "car"  # Truck
    df_mz_trips.loc[df_mz_trips["wmittel"] == 11, "mode"] = "pt"  # Taxi
    df_mz_trips.loc[df_mz_trips["wmittel"] == 12, "mode"] = "car"  # Motorbike
    df_mz_trips.loc[df_mz_trips["wmittel"] == 13, "mode"] = "car"  # Mofa
    df_mz_trips.loc[df_mz_trips["wmittel"] == 14, "mode"] = "bike"  # Bicycle / E-bike
    df_mz_trips.loc[df_mz_trips["wmittel"] == 15, "mode"] = "walk"  # Walking
    df_mz_trips.loc[df_mz_trips["wmittel"] == 16, "mode"] = "car"  # "Machines similar to a vehicle"
    df_mz_trips.loc[df_mz_trips["wmittel"] == 17, "mode"] = "unknown"  # Other / don't know

    df_mz_trips["mode_detailed"] = df_mz_trips["mode"]
    df_mz_trips.loc[df_mz_trips["wmittel"] == 1, "mode_detailed"] = "plane"
    df_mz_trips.loc[df_mz_trips["wmittel"] == 11, "mode_detailed"] = "taxi"

    # Find passenger trips
    df_mz_stages["is_car_passenger"] = df_mz_stages["f51300"] == 8
    df_passengers = df_mz_stages[["HHNR", "WEGNR", "is_car_passenger"]].groupby(["HHNR", "WEGNR"]).sum().reset_index()
    df_mz_trips = pd.merge(df_mz_trips, df_passengers, on=["HHNR", "WEGNR"], how="left")
    df_mz_trips.loc[df_mz_trips["is_car_passenger"] > 0, "mode_detailed"] = "car_passenger"
    df_mz_trips.loc[df_mz_trips["is_car_passenger"] > 0, "mode"] = "car_passenger"
    del df_mz_trips["is_car_passenger"]

    # Second, adjust the purposes
    df_mz_trips.loc[df_mz_trips["wzweck1"] == -99, "purpose"] = "unknown"  # Pseudo stage
    df_mz_trips.loc[df_mz_trips["wzweck1"] == -98, "purpose"] = "unknown"  # No answer
    df_mz_trips.loc[df_mz_trips["wzweck1"] == -97, "purpose"] = "unknown"  # Don't know
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 1, "purpose"] = "interaction"  # Transfer, change of mode, park car
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 2, "purpose"] = "work"  # Work
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 3, "purpose"] = "education"  # Education
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 4, "purpose"] = "shop"  # Shopping
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 5, "purpose"] = "other"  # Chores, use of public services
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 6, "purpose"] = "work"  # Business activity
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 7, "purpose"] = "work"  # Business trip
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 8, "purpose"] = "leisure"  # Leisure
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 9, "purpose"] = "other"  # Bring children
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 10, "purpose"] = "other"  # Bring others (disabled, ...)
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 11, "purpose"] = "home"  # Return home
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 12, "purpose"] = "unknown"  # Other
    df_mz_trips.loc[df_mz_trips["wzweck1"] == 13, "purpose"] = "border"  # Going out of country

    # Adjust trips back home
    df_mz_trips.loc[df_mz_trips["wzweck2"] > 1, "purpose"] = "home"

    # Adjust times
    df_mz_trips.loc[:, "departure_time"] = df_mz_trips["f51100"] * 60
    df_mz_trips.loc[:, "arrival_time"] = df_mz_trips["f51400"] * 60

    # Adjust id
    df_mz_trips.loc[:, "person_id"] = df_mz_trips["HHNR"]
    df_mz_trips.loc[:, "trip_id"] = df_mz_trips["WEGNR"]

    # Adjust coordinates
    for mz_attribute, df_attribute in [("Z", "destination"), ("S", "origin"), ("W", "home")]:
        coords = df_mz_trips[["%s_X_CH1903" % mz_attribute, "%s_Y_CH1903" % mz_attribute]].values
        transformer = pyproj.Transformer.from_crs("epsg:21781", "epsg:2056")  # Correct CRS codes for CH1903 to CH1903+
        x, y = transformer.transform(coords[:, 0], coords[:, 1])
        df_mz_trips.loc[:, "%s_x" % df_attribute] = x
        df_mz_trips.loc[:, "%s_y" % df_attribute] = y

        # Add crowfly distance
    df_mz_trips.loc[:, "crowfly_distance"] = np.sqrt(
        (df_mz_trips["origin_x"] - df_mz_trips["destination_x"]) ** 2 +
        (df_mz_trips["origin_y"] - df_mz_trips["destination_y"]) ** 2
    )

    # Add activity durations by joining the trips with themselves
    df_mz_trips.loc[:, "previous_trip_id"] = df_mz_trips["trip_id"] - 1

    df_durations = pd.merge(
        df_mz_trips[["person_id", "trip_id", "departure_time"]],
        df_mz_trips[["person_id", "previous_trip_id", "arrival_time"]],
        left_on=["person_id", "trip_id"], right_on=["person_id", "previous_trip_id"]
    )

    df_durations.loc[:, "activity_duration"] = df_durations["arrival_time"] - df_durations["departure_time"]

    df_mz_trips = pd.merge(
        df_mz_trips, df_durations[["person_id", "trip_id", "activity_duration"]],
        on=["person_id", "trip_id"], how="left"
    )

    # Filter persons for which we do not have sufficient information
    unknown_ids = set(df_mz_trips[
                          (df_mz_trips["mode"] == "unknown") | (df_mz_trips["purpose"] == "unknown")
                          ]["person_id"])

    print("  Removed %d persons with trips with unknown mode or unknown purpose" % len(unknown_ids))
    df_mz_trips = df_mz_trips[~df_mz_trips["person_id"].isin(unknown_ids)]

    # Filter persons which do not start or end with "home"
    df_end = df_mz_trips[["person_id", "trip_id", "purpose"]].sort_values("trip_id", ascending=False).drop_duplicates(
        "person_id")
    df_end = df_end[df_end["purpose"] != "home"]

    before_length = len(np.unique(df_mz_trips["person_id"]))
    df_mz_trips = df_mz_trips[~df_mz_trips["person_id"].isin(df_end["person_id"])]
    after_length = len(np.unique(df_mz_trips["person_id"]))
    print("  Removed %d persons with trips not ending with 'home'" % (before_length - after_length,))

    df_start = df_mz_trips[["person_id", "trip_id", "origin_x", "origin_y", "home_x", "home_y"]]
    df_start = df_start[
        (df_start["trip_id"] == 1) & ((df_start["origin_x"] != df_start["home_x"]) |
                                      (df_start["origin_y"] != df_start["home_y"]))
        ]

    before_length = len(np.unique(df_mz_trips["person_id"]))
    df_mz_trips = df_mz_trips[~df_mz_trips["person_id"].isin(df_start["person_id"])]
    after_length = len(np.unique(df_mz_trips["person_id"]))
    print("  Removed %d persons with trips not starting at home location" % (before_length - after_length,))

    # Parking cost
    df_mz_stages = pd.read_csv(f"{path}\\microzensus\\etappen.csv", encoding="latin1")

    df_cost = pd.DataFrame(df_mz_stages[["HHNR", "WEGNR", "f51330"]], copy=True)
    df_cost.columns = ["person_id", "trip_id", "parking_cost"]
    df_cost["parking_cost"] = np.maximum(0, df_cost["parking_cost"])
    df_cost = df_cost.groupby(["person_id", "trip_id"]).sum().reset_index()

    df_mz_trips = pd.merge(df_mz_trips, df_cost, on=["person_id", "trip_id"], how="left")
    assert (not np.any(np.isnan(df_mz_trips["parking_cost"])))

    # Network distance
    df_mz_trips["network_distance"] = df_mz_trips["w_rdist"] * 1000.0

    return df_mz_trips


def create_activity_chain(group):
    chain = '-'.join(
        ['h'] + [purpose[0] for purpose in group['purpose'].tolist()])  # Add 'H' at the start of each chain
    return pd.Series({'activity_chain': chain})


if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    analysis_zone_path = os.path.join(data_path, analysis_zone_name)
    trips = execute(analysis_zone_path)
    logging.info("Microcensus trips filtered successfully")

    # Load geographic data from a shapefile
    shapefile_path = os.path.join(analysis_zone_path,
                                  f"ShapeFiles\\{shapeFileName}")
    gdf = gpd.read_file(shapefile_path, engine="pyogrio")

    area_polygon = gdf.iloc[0]['geometry']
    logging.info("Shapefile loaded successfully and area_polygon created successfully")

    # Create Point geometries for origin and destination
    trips['origin_point'] = trips.apply(lambda row: Point(row['origin_x'], row['origin_y']), axis=1)
    trips['destination_point'] = trips.apply(lambda row: Point(row['destination_x'], row['destination_y']), axis=1)

    # Filter trips where both origin and destination are within the given city polygon shapefile
    filtered_trips = trips[
        trips['origin_point'].apply(lambda point: point.within(area_polygon)) &
        trips['destination_point'].apply(lambda point: point.within(area_polygon))
        ]

    logging.info("Trips filtered successfully based on the shapefile polygon successfully")
    # Create activity chains
    df_activity_chains = filtered_trips.groupby(['person_id']).apply(create_activity_chain).reset_index()

    filtered_trips.to_csv(analysis_zone_path + '\\microzensus\\trips.csv')
    logging.info(f"Trips saved successfully in the microzensus folder in the {analysis_zone_path} directory successfully")
    df_mz_trips = filtered_trips

    # Capitalize and remove underscores from mode names
    df_mz_trips['mode'] = df_mz_trips['mode'].str.replace('_', ' ').str.upper()

    # Calculate total counts for each mode
    mode_counts = df_mz_trips['mode'].value_counts().reset_index()
    mode_counts.columns = ['Mode', 'Count']

    # Plot total counts
    fig1 = px.bar(mode_counts, x='Mode', y='Count', title='Mode Share Distribution - Total Counts',
                  labels={'Count': 'Total Count', 'Mode': 'Mode of Transportation'})
    fig1.update_layout(width=600, height=600)
    # fig1.show()

    # Calculate percentage distribution for each mode
    mode_counts['Percentage'] = (mode_counts['Count'] / mode_counts['Count'].sum()) * 100

    # Plot percentage distribution
    fig2 = px.bar(mode_counts, x='Mode', y='Percentage', title='Mode Share Distribution - Percentage',
                  labels={'Percentage': 'Percentage (%)', 'Mode': 'Mode of Transportation'})
    fig2.update_layout(width=600, height=600)
    # fig2.show()


    # Convert seconds to datetime and resample times to 15-minute bins
    df_mz_trips['departure_time'] = pd.to_datetime(df_mz_trips['departure_time'], unit='s').dt.floor('30T').dt.time
    df_mz_trips['arrival_time'] = pd.to_datetime(df_mz_trips['arrival_time'], unit='s').dt.floor('30T').dt.time
    logging.info("The departure and arrival times are converted to datetime and resampled into bins successfully")

    # Count occurrences in each 15-minute bin
    departure_counts = df_mz_trips.groupby('departure_time').size().reset_index(name='Count')
    departure_counts['Type'] = 'Departures'
    departure_counts = departure_counts.rename(columns={'departure_time': 'Time'})

    arrival_counts = df_mz_trips.groupby('arrival_time').size().reset_index(name='Count')
    arrival_counts['Type'] = 'Arrivals'
    arrival_counts = arrival_counts.rename(columns={'arrival_time': 'Time'})
    logging.info("The arrival_counts and departure_counts are calculated successfully")

    # Combine data
    time_counts = pd.concat([departure_counts, arrival_counts], axis=0)

    # Plot using Plotly Express
    fig = px.bar(time_counts, x='Time', y='Count', color='Type',
                 title='Departure and Arrival Times over a Day',
                 labels={'Count': 'Count', 'Time': 'Time of Day'},
                 barmode='group')

    # Customize x-axis ticks and scale y-axis
    fig.update_xaxes(type='category', tickangle=45, dtick=1)
    fig.update_yaxes(range=[0, time_counts['Count'].max()])

    # Show plot
    fig.update_layout(width=1200, height=600)
    # fig.show()

    # Capitalize and remove underscores from purpose names
    df_mz_trips['purpose'] = df_mz_trips['purpose'].str.replace('_', ' ').str.upper()

    # Calculate total counts for each purpose
    purpose_counts = df_mz_trips['purpose'].value_counts().reset_index()
    purpose_counts.columns = ['Purpose', 'Count']

    # Plot total counts
    fig1 = px.bar(purpose_counts, x='Purpose', y='Count', title='Purpose Distribution - Total Counts',
                  labels={'Count': 'Total Count', 'Purpose': 'Purpose'})
    fig1.update_layout(width=600, height=600)
    # fig1.show()
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{analysis_zone_name}')
    if not os.path.exists(plots_directory):
        os.makedirs(plots_directory)
    fig1.write_image(f"{plots_directory}\\purpose_distribution_Total_microcensus.png", scale=4)
    logging.info(f"Purpose distribution total microcensus plotted successfully and saved in the {plots_directory} directory")

    # Calculate percentage distribution for each purpose
    purpose_counts['Percentage'] = (purpose_counts['Count'] / purpose_counts['Count'].sum()) * 100

    # Plot percentage distribution
    fig2 = px.bar(purpose_counts, x='Purpose', y='Percentage', title='Purpose Distribution - Percentage',
                  labels={'Percentage': 'Percentage (%)', 'Purpose': 'Purpose'})
    fig2.update_layout(width=600, height=600)
    # fig2.show()

    fig2.write_image(f"{plots_directory}\\purpose_distribution_pct_microcensus.png", scale=4)

    logging.info(f"There exist {df_activity_chains.activity_chain.nunique()} number of unique activity chains.")

    filtered_trips[['HHNR', 'WEGNR', 'purpose']]

    filtered_trips[trips.person_id == 101196]

    # Calculate total counts for each activity chain
    chain_counts = df_activity_chains['activity_chain'].value_counts().reset_index()
    chain_counts.columns = ['Activity Chain', 'Count']

    # Plot total counts
    fig = px.bar(chain_counts, x='Activity Chain', y='Count', title='Activity Chain Distribution - Total Counts',
                 labels={'Count': 'Total Count', 'Activity Chain': 'Activity Chain'})
    fig.update_layout(width=1600, height=800)
    # fig.show()
    fig.write_image(f"{plots_directory}\\activity_chain_distribution_Total_microcensus.png", scale=4)
    logging.info(f"Activity chain distribution total microcensus plotted successfully and saved in the {plots_directory} directory")
