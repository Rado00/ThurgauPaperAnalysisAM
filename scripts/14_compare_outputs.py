import json
import os
import gzip
import shutil
from typing import Tuple
import pandas as pd
from pandas import DataFrame

# TODO adjust this number based on your actual data size for testing
num_rows = 500

def process_transport_data(df1, df2, simulation_1_name: str, simulation_2_name: str) -> Tuple[dict, dict, dict]:

    # Define the target modes (normalized to lowercase for processing)
    target_modes = ['car', 'car_passenger', 'bike', 'pt', 'walk']

    # Find common person IDs between both dataframes
    common_persons = set(df1['person'].unique()) & set(df2['person'].unique())
    print(f"Number of common persons: {len(common_persons)}")

    def count_modes_by_person(df, persons):
        """Count transportation modes for each person"""
        person_mode_counts = {}

        for person_id in persons:
            # Initialize all modes to 0
            mode_counts = {mode.title(): 0 for mode in target_modes}

            # Get data for this person
            person_data = df[df['person'] == person_id]

            # TODO: Ensure 'longest_distance_mode' column is the correct one to analyze
            # Count occurrences of each mode
            mode_counter = person_data['longest_distance_mode'].value_counts()

            # Map the modes to our target format
            for mode, count in mode_counter.items():
                mode_lower = mode.lower()
                if mode_lower in target_modes:
                    # Convert to title case for JSON output
                    if mode_lower == 'pt':
                        mode_key = 'PT'
                    elif mode_lower == 'car_passenger':
                        mode_key = 'Car_Passenger'
                    else:
                        mode_key = mode_lower.title()

                    mode_counts[mode_key] = count

            person_mode_counts[str(person_id)] = mode_counts

        return person_mode_counts

    # Process both datasets
    before_data = count_modes_by_person(df1, common_persons)
    after_data = count_modes_by_person(df2, common_persons)

    # Calculate differences (after - before)
    difference_data = {}
    for person_id in before_data.keys():
        person_diff = {}
        for mode in before_data[person_id].keys():
            person_diff[mode] = after_data[person_id][mode] - before_data[person_id][mode]
        difference_data[person_id] = person_diff

    # --- Save DataFrame into plots folder in parent of the script directory ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_of_script = os.path.dirname(script_dir)
    # TODO change "plots" to what ever folder you want to save to
    plots_dir = os.path.join(parent_of_script, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # Save to JSON files
    with open(f'{plots_dir}/before_{simulation_1_name}.json', 'w') as f:
        json.dump(before_data, f, indent=2)

    with open(f'{plots_dir}/after_{simulation_2_name}.json', 'w') as f:
        json.dump(after_data, f, indent=2)

    with open(f'{plots_dir}/differences_{simulation_1_name}_{simulation_2_name}.json', 'w') as f:
        json.dump(difference_data, f, indent=2)

    print("JSON files created successfully!")
    return before_data, after_data, difference_data


def read_output_trips(base_path: str) -> tuple[DataFrame, str]:

    gz_path = os.path.join(base_path, "output_trips.csv.gz")
    csv_path = os.path.join(base_path, "output_trips.csv")

    # Case 1: compressed file exists
    if os.path.isfile(gz_path):
        extracted_csv = csv_path  # same directory
        with gzip.open(gz_path, 'rb') as f_in, open(extracted_csv, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"Extracted {gz_path} → {extracted_csv}")
        # TODO number of rows to read for testing
        return pd.read_csv(extracted_csv, sep=';', low_memory=False, nrows=num_rows), base_path.split("\\")[-1]

    # Case 2: normal CSV exists (ensure it's a file, not folder)
    elif os.path.isfile(csv_path):
        print(f"Reading {csv_path}")
        # TODO number of rows to read for testing
        return pd.read_csv(csv_path, sep=';', low_memory=False, nrows=num_rows), base_path.split("\\")[-1]

    else:
        raise FileNotFoundError("Neither output_trips.csv.gz nor output_trips.csv file found in given path.")

# main execution
if __name__ == "__main__":
    # TODO change these paths to your actual data folders
    simulation_1_folder = r"E:\CM\2023_ABMT_Data\Thurgau\BaselineCalibration28"
    simulation_2_folder = r"E:\CM\2023_ABMT_Data\Thurgau\BaselineCalibration_28_onlyUseEndtime"

    df_1, sim_1_name = read_output_trips(simulation_1_folder)
    df_2, sim_2_name = read_output_trips(simulation_2_folder)

    process_transport_data(df_1, df_2, sim_1_name, sim_2_name)
