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
    mode_share_directory = os.path.join(plots_directory, 'outputs_mode_share')

    # Create ModeShareOutputs_inOneColumn directory in plots folder (parallel to Compare_simulations)
    plots_root = os.path.join(parent_directory, "plots")
    one_column_directory = os.path.join(plots_root, "ModeShareOutputs_inOneColumn")
    os.makedirs(one_column_directory, exist_ok=True)

    # Extract scenario name from sim_output_folder for the filename
    scenario_name = os.path.basename(sim_output_folder)

    specific_files = {
        "trip": "Mode_shares_by_trip.csv",
        "trip_target": f"Mode_shares_by_trip_{target_area}.csv",
        "distance": "Mode_shares_distance.csv",
        "distance_target": f"Mode_shares_distance_{target_area}.csv",
        "time_target": f"Mode_shares_time_{target_area}.csv"
    }

    mode_mappings = {
        "Bike": "Bike",
        "Car": "Car",
        "Car Passenger": "Car Passenger",
        "Pt": "PT",
        "Walk": "Walk"
    }

    desired_order = [
        "% Trips Bike - Simulated Area",
        "% Trips Car - Simulated Area",
        "% Trips Car Passenger - Simulated Area",
        "% Trips PT - Simulated Area",
        "% Trips Walk - Simulated Area",

        "% Trips Bike - Target Area",
        "% Trips Car - Target Area",
        "% Trips Car Passenger - Target Area",
        "% Trips PT - Target Area",
        "% Trips Walk - Target Area",

        "% Distance Bike  - Simulated Area",
        "% Distance Car  - Simulated Area",
        "% Distance Car Passenger  - Simulated Area",
        "% Distance PT  - Simulated Area",
        "% Distance Walk  - Simulated Area",

        "% Distance Bike  - Target Area",
        "% Distance Car  - Target Area",
        "% Distance Car Passenger  - Target Area",
        "% Distance PT  - Target Area",
        "% Distance Walk  - Target Area",

        "Count Trips Bike - Simulated Area",
        "Count Trips Car - Simulated Area",
        "Count Trips Car Passenger - Simulated Area",
        "Count Trips PT - Simulated Area",
        "Count Trips Walk - Simulated Area",

        "Count Trips Bike - Target Area",
        "Count Trips Car - Target Area",
        "Count Trips Car Passenger - Target Area",
        "Count Trips PT - Target Area",
        "Count Trips Walk - Target Area",

        "Count Distance Bike  - Simulated Area",
        "Count Distance Car  - Simulated Area",
        "Count Distance Car Passenger  - Simulated Area",
        "Count Distance PT  - Simulated Area",
        "Count Distance Walk  - Simulated Area",

        "Count Distance Bike  - Target Area",
        "Count Distance Car  - Target Area",
        "Count Distance Car Passenger  - Target Area",
        "Count Distance PT  - Target Area",
        "Count Distance Walk  - Target Area",

        "Count TravelTime Bike Target Area",
        "Count TravelTime Car Target Area",
        "Count TravelTime Car Passenger Target Area",
        "Count TravelTime PT Target Area",
        "Count TravelTime Walk Target Area",

        "Average Distance Sim Bike  - Simulated Area",
        "Average Distance Sim Car  - Simulated Area",
        "Average Distance Sim Car Passenger  - Simulated Area",
        "Average Distance Sim PT  - Simulated Area",
        "Average Distance Sim Walk  - Simulated Area",

        "Average Distance Sim Bike  - Target Area",
        "Average Distance Sim Car  - Target Area",
        "Average Distance Sim Car Passenger  - Target Area",
        "Average Distance Sim PT  - Target Area",
        "Average Distance Sim Walk  - Target Area",

        "STD Distance Sim Bike  - Simulated Area",
        "STD Distance Sim Car  - Simulated Area",
        "STD Distance Sim Car Passenger  - Simulated Area",
        "STD Distance Sim PT  - Simulated Area",
        "STD Distance Sim Walk  - Simulated Area",

        "STD Distance Sim Bike  - Target Area",
        "STD Distance Sim Car  - Target Area",
        "STD Distance Sim Car Passenger  - Target Area",
        "STD Distance Sim PT  - Target Area",
        "STD Distance Sim Walk  - Target Area"
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

        # Trips for Target Area
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["trip_target"]),
            [
                lambda mode, row: (f"% Trips {mode} - Target Area O OR D", row["Percentage Sim OR"]),
                lambda mode, row: (f"Count Trips {mode} - Target Area O OR D", row["Total Trips Sim OR"]),
                lambda mode, row: (f"% Trips {mode} - Target Area O AND D", row["Percentage Sim AND"]),
                lambda mode, row: (f"Count Trips {mode} - Target Area O AND D", row["Total Trips Sim AND"])
            ]
        )

        # Distance for Simulated Area
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["distance"]),
            [
                lambda mode, row: (f"% Distance {mode}  - Simulated Area", row["Percentage Sim"]),
                lambda mode, row: (f"Count Distance {mode}  - Simulated Area", row["Total Distance Sim"]),
                lambda mode, row: (f"Average Distance Sim {mode}  - Simulated Area", row["Average Distance Sim"]),
                lambda mode, row: (f"STD Distance Sim {mode}  - Simulated Area", row["STD Distance Sim"]),
            ]
        )

        # Distance for Target Area
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["distance_target"]),
            [
                lambda mode, row: (f"% Distance {mode}  - Target Area O OR D", row["Percentage Sim OR"]),
                lambda mode, row: (f"Count Distance {mode}  - Target Area O OR D", row["Total Distance Sim OR"]),
                lambda mode, row: (f"Average Distance Sim {mode}  - Target Area O OR D", row["Average Distance Sim OR"]),
                lambda mode, row: (f"STD Distance Sim {mode}  - Target Area O OR D", row["STD Distance Sim OR"]),
                lambda mode, row: (f"% Distance {mode}  - Target Area O AND D", row["Percentage Sim AND"]),
                lambda mode, row: (f"Count Distance {mode}  - Target Area O AND D", row["Total Distance Sim AND"]),
                lambda mode, row: (f"Average Distance Sim {mode}  - Target Area O AND D", row["Average Distance Sim AND"]),
                lambda mode, row: (f"STD Distance Sim {mode}  - Target Area O AND D", row["STD Distance Sim AND"]),
            ]
        )

        # Travel Time for Target Area
        consolidated_data += read_and_extract(
            os.path.join(mode_share_directory, specific_files["time_target"]),
            [
                lambda mode, row: (f"Count TravelTime {mode} Target Area O OR D", row["Total Time Sim OR"]),
                lambda mode, row: (f"Count TravelTime {mode} Target Area O AND D", row["Total Time Sim AND"])
            ]
        )

        # Create and sort DataFrame
        if consolidated_data:
            output_df = pd.DataFrame(consolidated_data, columns=['Title', 'Value'])
            output_df['Order'] = output_df['Title'].apply(
                lambda x: desired_order.index(x) if x in desired_order else len(desired_order))
            output_df = output_df.sort_values('Order').drop('Order', axis=1)
            output_df['Value with Comma'] = output_df['Value'].astype(str).str.replace('.', ',', regex=False)

            # Add empty first column
            output_df.insert(0, 'Source File', '')

            # Reorder columns to match drt_summary_metrics format
            output_df = output_df[['Source File', 'Title', 'Value', 'Value with Comma']]

            # Read and append DRT summary metrics if it exists
            drt_file_path = os.path.join(mode_share_directory, 'drt_summary_metrics.csv')
            if os.path.exists(drt_file_path):
                drt_df = pd.read_csv(drt_file_path, sep=';')
                # Concatenate the dataframes
                output_df = pd.concat([output_df, drt_df], ignore_index=True)
                print("DRT summary metrics appended successfully.")
            else:
                print(f"DRT file not found at: {drt_file_path}")

            output_df.to_csv(os.path.join(one_column_directory, f'modeOutputs_{scenario_name}.csv'), sep=';', index=False)
            output_df.to_csv(os.path.join(one_column_directory, f'modeOutputs_{scenario_name}_en.csv'), index=False)
            print("Data successfully saved.")
        else:
            print("No data found in the files.")
    else:
        print(f"The directory {mode_share_directory} does not exist.")
