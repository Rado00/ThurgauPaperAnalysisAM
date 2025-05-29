import pandas as pd
import os
from functions.commonFunctions import *

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    output_plots_folder_name = os.path.basename(sim_output_folder)
    plots_directory = os.path.join(parent_directory, "plots", f"plots_{output_plots_folder_name}")
    mode_share_directory = os.path.join(plots_directory, 'mode_share')

    specific_files = {
        "trip": "Mode_shares_by_trip.csv",
        "trip_target": "Mode_shares_by_trip_target_area.csv",
        "distance": "Mode_shares_distance.csv",
        "distance_target": "Mode_shares_distance_target_area.csv",
        "time_target": "Mode_shares_time_target_area.csv"
    }

    mode_mappings = {
        "Bike": "Bike",
        "Car": "Car",
        "Car Passenger": "Car Passenger",
        "Pt": "PT",
        "Walk": "Walk"
    }

    desired_order = [
        "% Trips Bike - Simulated Area", "% Trips Car - Simulated Area", "% Trips Car Passenger - Simulated Area", "% Trips PT - Simulated Area", "% Trips Walk - Simulated Area",
        "% Trips Bike - Weinfelden", "% Trips Car - Weinfelden", "% Trips Car Passenger - Weinfelden", "% Trips PT - Weinfelden", "% Trips Walk - Weinfelden",
        "% Distance Bike  - Simulated Area", "% Distance Car  - Simulated Area", "% Distance Car Passenger  - Simulated Area", "% Distance PT  - Simulated Area", "% Distance Walk  - Simulated Area",
        "% Distance Bike  - Weinfelden", "% Distance Car  - Weinfelden", "% Distance Car Passenger  - Weinfelden", "% Distance PT  - Weinfelden", "% Distance Walk  - Weinfelden",
        "Count Trips Bike - Simulated Area", "Count Trips Car - Simulated Area", "Count Trips Car Passenger - Simulated Area", "Count Trips PT - Simulated Area", "Count Trips Walk - Simulated Area",
        "Count Trips Bike - Weinfelden", "Count Trips Car - Weinfelden", "Count Trips Car Passenger - Weinfelden", "Count Trips PT - Weinfelden", "Count Trips Walk - Weinfelden",
        "Count Distance Bike  - Simulated Area", "Count Distance Car  - Simulated Area", "Count Distance Car Passenger  - Simulated Area", "Count Distance PT  - Simulated Area", "Count Distance Walk  - Simulated Area",
        "Count Distance Bike  - Weinfelden", "Count Distance Car  - Weinfelden", "Count Distance Car Passenger  - Weinfelden", "Count Distance PT  - Weinfelden", "Count Distance Walk  - Weinfelden",
        "Count TravelTime Bike Weinfelden", "Count TravelTime Car Weinfelden", "Count TravelTime Car Passenger Weinfelden", "Count TravelTime PT Weinfelden", "Count TravelTime Walk Weinfelden"
    ]

    if os.path.exists(mode_share_directory):
        consolidated_data = []

        def read_and_extract(filepath, extract_funcs):
            if not os.path.exists(filepath):
                print(f"File not found: {filepath}")
                return []
            df = pd.read_csv(filepath)
            results = []
            for _, row in df.iterrows():
                mode = row['Mode']
                if mode in mode_mappings:
                    mapped_mode = mode_mappings[mode]
                    for func in extract_funcs:
                        results.append(func(mapped_mode, row))
            return results

        # Extract percentage and count for trips (Simulated Area)
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["trip"]),
            [
                lambda mode, row: (f"% Trips {mode} - Simulated Area", row["Percentage Sim"]),
                lambda mode, row: (f"Count Trips {mode} - Simulated Area", row["Total Trips Sim"])
            ]
        )

        # Trips for Weinfelden
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["trip_target"]),
            [
                lambda mode, row: (f"% Trips {mode} - Weinfelden", row["Percentage Sim"]),
                lambda mode, row: (f"Count Trips {mode} - Weinfelden", row["Total Trips Sim"])
            ]
        )

        # Distance for Simulated Area
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["distance"]),
            [
                lambda mode, row: (f"% Distance {mode}  - Simulated Area", row["Percentage Sim"]),
                lambda mode, row: (f"Count Distance {mode}  - Simulated Area", row["Total Distance Sim"])
            ]
        )

        # Distance for Weinfelden
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["distance_target"]),
            [
                lambda mode, row: (f"% Distance {mode}  - Weinfelden", row["Percentage Sim"]),
                lambda mode, row: (f"Count Distance {mode}  - Weinfelden", row["Total Distance Sim"])
            ]
        )

        # Travel Time for Weinfelden
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["time_target"]),
            [
                lambda mode, row: (f"Count TravelTime {mode} Weinfelden", row["Total Time Sim"])
            ]
        )

        # Create and sort DataFrame
        if consolidated_data:
            output_df = pd.DataFrame(consolidated_data, columns=['Title', 'Value'])
            output_df['Order'] = output_df['Title'].apply(lambda x: desired_order.index(x) if x in desired_order else len(desired_order))
            output_df = output_df.sort_values('Order').drop('Order', axis=1)
            output_df['Value with Comma'] = output_df['Value'].astype(str).str.replace('.', ',', regex=False)
            output_df.to_csv(os.path.join(mode_share_directory, 'modalSplitCalibration.csv'), sep=';', index=False)
            print("Data successfully saved.")
        else:
            print("No data found in the files.")
    else:
        print(f"The directory {mode_share_directory} does not exist.")
