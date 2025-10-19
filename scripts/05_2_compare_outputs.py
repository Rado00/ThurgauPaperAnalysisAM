import json
import gzip
import shutil
import csv
from typing import Tuple
from collections import Counter
from pandas import DataFrame
import time
import os
import sys
import logging
import pandas as pd
import configparser
from functions.commonFunctions import *

start_time = time.time()


def generate_differences_json(before_data: dict, after_data: dict, sim_1_name, sim_2_name, plots_dir: str):
    """
    Generate differences.json showing mode transitions for each person
    """
    differences = {}

    # Get common person IDs from both datasets
    common_persons = set(before_data.keys()) & set(after_data.keys())

    for person_id in common_persons:
        before_modes = before_data[person_id]
        after_modes = after_data[person_id]

        # Create lists for before and after modes based on their counts
        before_list = []
        after_list = []

        # Build before_list by repeating each mode according to its count
        for mode, count in before_modes.items():
            before_list.extend([mode] * count)

        # Build after_list by repeating each mode according to its count
        for mode, count in after_modes.items():
            after_list.extend([mode] * count)

        # Get the minimum length to avoid index out of range
        mode_range = min(len(before_list), len(after_list))

        # Generate transitions for this person
        transitions = []
        for i in range(mode_range):
            before_mode = before_list[i]
            after_mode = after_list[i]

            # Handle PT formatting (convert back from title case)
            if before_mode == 'Pt':
                before_mode = 'PT'
            if after_mode == 'Pt':
                after_mode = 'PT'

            # Create transition string
            transition = f"{before_mode}_{after_mode}"
            transitions.append(transition)

        differences[person_id] = transitions

    # Save differences to JSON file
    differences_path = os.path.join(plots_dir, f"{sim_1_name}_{sim_2_name}_differences.json")
    with open(differences_path, 'w') as f:
        json.dump(differences, f, indent=2)

    logging.info(f"Differences JSON created successfully at: {differences_path}")
    return differences


def generate_transition_matrix_csv(before_data: dict, after_data: dict, sim_1_name, sim_2_name, plots_dir: str):
    """
    Generate a CSV file with transition matrix showing counts of each mode transition for each person
    """
    # Define all possible transitions in the exact order requested
    transition_columns = [
        "Car_Car", "Car_Car_Passenger", "Car_PT", "Car_Bike", "Car_Walk",
        "Car_Passenger_Car", "Car_Passenger_Car_Passenger", "Car_Passenger_PT", "Car_Passenger_Bike",
        "Car_Passenger_Walk",
        "PT_Car", "PT_Car_Passenger", "PT_PT", "PT_Bike", "PT_Walk",
        "Bike_Car", "Bike_Car_Passenger", "Bike_PT", "Bike_Bike", "Bike_Walk",
        "Walk_Car", "Walk_Car_Passenger", "Walk_PT", "Walk_Bike", "Walk_Walk"
    ]

    # Get common person IDs from both datasets
    common_persons = set(before_data.keys()) & set(after_data.keys())

    # Prepare CSV data
    csv_data = []

    for person_id in sorted(common_persons):  # Sort for consistent ordering
        before_modes = before_data[person_id]
        after_modes = after_data[person_id]

        # Create lists for before and after modes based on their counts
        before_list = []
        after_list = []

        # Build before_list by repeating each mode according to its count
        for mode, count in before_modes.items():
            # Normalize mode names for consistency
            normalized_mode = mode
            if mode == 'Pt':
                normalized_mode = 'PT'
            before_list.extend([normalized_mode] * count)

        # Build after_list by repeating each mode according to its count
        for mode, count in after_modes.items():
            # Normalize mode names for consistency
            normalized_mode = mode
            if mode == 'Pt':
                normalized_mode = 'PT'
            after_list.extend([normalized_mode] * count)

        # Get the minimum length to avoid index out of range
        mode_range = min(len(before_list), len(after_list))

        # Generate transitions for this person
        transitions = []
        for i in range(mode_range):
            before_mode = before_list[i]
            after_mode = after_list[i]
            transition = f"{before_mode}_{after_mode}"
            transitions.append(transition)

        # Count occurrences of each transition
        transition_counts = Counter(transitions)

        # Create row for this person
        row = [person_id]  # First column is Person Key

        # Add counts for each transition column (0 if transition doesn't exist)
        for transition in transition_columns:
            count = transition_counts.get(transition, 0)
            row.append(count)

        csv_data.append(row)

    # Create Transition_Matrixes subdirectory
    transition_matrixes_dir = os.path.join(plots_dir, "Transition_Matrixes")
    os.makedirs(transition_matrixes_dir, exist_ok=True)

    # Create CSV file in the Transition_Matrixes folder
    csv_path = os.path.join(transition_matrixes_dir, f"{sim_1_name}_{sim_2_name}_transition_matrix.csv")
    # Write CSV with headers
    headers = ["Person_Key"] + transition_columns

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(csv_data)

    logging.info(f"Transition matrix CSV created successfully at: {csv_path}")
    logging.info(f"CSV contains {len(csv_data)} persons with {len(headers)} columns")

    return csv_path


def delete_json_files(plots_dir: str, sim_1_name: str, sim_2_name: str):
    """
    Delete all JSON files generated during the process
    """
    json_files_to_delete = [
        f"before_{sim_1_name}.json",
        f"after_{sim_2_name}.json",
        f"{sim_1_name}_{sim_2_name}_differences.json"
    ]

    for json_file in json_files_to_delete:
        file_path = os.path.join(plots_dir, json_file)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Deleted JSON file: {file_path}")
        except Exception as e:
            logging.error(f"Error deleting {file_path}: {str(e)}")


def analyze_transition_data_and_create_summary(csv_path: str, plots_dir: str, sim_1_name: str, sim_2_name: str):
    """
    Analyze the transition matrix CSV and create a summary CSV with percentages
    """
    try:
        # Read the transition matrix CSV
        df = pd.read_csv(csv_path)

        # Remove the Person_Key column for analysis (keep only transition columns)
        transition_columns = [col for col in df.columns if col != 'Person_Key']

        # Calculate the sum for each transition column
        column_sums = df[transition_columns].sum()

        # Calculate total transitions
        total_transitions = column_sums.sum()

        # Create summary data with percentages
        summary_data = []

        for transition, count in column_sums.items():
            if count > 0:  # Only include transitions that actually occurred
                percentage = (count / total_transitions) * 100
                summary_data.append({
                    'mode_transition': transition,
                    'count': count,
                    'percentage': f"{percentage:.1f}%"
                })

        # Sort by count in descending order
        summary_data.sort(key=lambda x: x['count'], reverse=True)

        # Create summary CSV
        summary_csv_path = os.path.join(plots_dir, f"{sim_1_name}_{sim_2_name}_transition_summary.csv")


    #CREATE AN SAVE CSV transition FILE
        # Create dataframe for proper formatting like drt_summary_metrics.csv
        df_summary = pd.DataFrame(summary_data).copy()

        # Remove the '%' from percentage and convert to float
        df_summary['percentage_value'] = df_summary['percentage'].str.replace('%', '').astype(float)

        # Create 'Value with Comma' column (replacing . with ,)
        df_summary['Pct Value with Comma'] = df_summary['percentage_value'].apply(lambda x: f"{x:.2f}".replace('.', ','))

        # Keep only the columns we want and create a clean copy
        df_final = df_summary[['mode_transition', 'percentage_value', 'Pct Value with Comma']].copy()
        df_final.columns = ['Mode Transition', 'Pct Value', 'Pct Value with Comma']

        # Round Value to 2 decimal places
        df_final['Pct Value'] = df_final['Pct Value'].round(2)

        # Save with semicolon separator like drt_summary_metrics.csv
        df_final.to_csv(summary_csv_path, index=False, sep=';')

        logging.info(f"Transition summary CSV created successfully at: {summary_csv_path}")
        logging.info(
            f"Summary contains {len(summary_data)} transition types with total of {total_transitions} transitions")

        logging.info("Top transitions:")
        for i, row in enumerate(summary_data):
            logging.info(f"{i + 1}. {row['mode_transition']}: {row['percentage']}")

        return summary_csv_path

    except Exception as e:
        logging.error(f"Error analyzing transition data: {str(e)}")
        raise


def process_transport_data(df1, df2, simulation_1_name: str, simulation_2_name: str, mode_column_input) -> Tuple[
    dict, dict, dict]:
    # Define the target modes (normalized to lowercase for processing)
    target_modes = ['car', 'car_passenger', 'pt', 'bike', 'walk']

    # Find common person IDs between both dataframes
    common_persons = set(df1['person'].unique()) & set(df2['person'].unique())
    logging.info(f"Number of common persons: {len(common_persons)}")

    def count_modes_by_person(df, persons):
        """Count transportation modes for each person"""
        person_mode_counts = {}

        for person_id in persons:
            # Initialize all modes to 0
            mode_counts = {mode.title(): 0 for mode in target_modes}

            # Get data for this person
            person_data = df[df['person'] == person_id]

            # Count occurrences of each mode
            mode_counter = person_data[mode_column_input].value_counts()

            # Map the modes to our target format
            for mode, count in mode_counter.items():
                mode_lower = mode.lower()
                if mode_lower in target_modes:
                    # Convert to title case for JSON output
                    if mode_lower == 'pt':
                        mode_key = 'Pt'  # Keep as 'Pt' for consistency with your example
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

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_of_script = os.path.dirname(script_dir)
    compare_simulations_dir = os.path.join(parent_of_script, "plots//Compare_simulations")
    os.makedirs(compare_simulations_dir, exist_ok=True)

    try:
        with open(f'{compare_simulations_dir}/before_{simulation_1_name}.json', 'w') as f:
            json.dump(before_data, f, indent=2)

        with open(f'{compare_simulations_dir}/after_{simulation_2_name}.json', 'w') as f:
            json.dump(after_data, f, indent=2)

        logging.info(f"JSON files created successfully in the {compare_simulations_dir} directory.")
    except Exception as e:
        logging.error("Error saving JSON files: " + str(e))
        raise

    # Generate differences JSON
    differences_data = generate_differences_json(before_data, after_data, simulation_1_name, simulation_2_name,
                                                 compare_simulations_dir)

    # Generate transition matrix CSV
    csv_path = generate_transition_matrix_csv(before_data, after_data, simulation_1_name, simulation_2_name,
                                              compare_simulations_dir)

    # NEW: Delete JSON files after CSV generation
    delete_json_files(compare_simulations_dir, simulation_1_name, simulation_2_name)

    # NEW: Analyze transition data and create summary CSV
    summary_csv_path = analyze_transition_data_and_create_summary(csv_path, compare_simulations_dir, simulation_1_name,
                                                                  simulation_2_name)

    return before_data, after_data, differences_data


def read_output_trips(base_path: str, num_rows) -> tuple[DataFrame, str]:

    if num_rows == -1:
        num_rows = None

    try:
        if os.path.isfile(base_path):
            logging.info(f"Reading {base_path}")
            return pd.read_csv(base_path, sep=',', low_memory=False, nrows=num_rows), base_path.split("\\")[-1]

        else:
            raise FileNotFoundError("Neither output_trips.csv.gz nor output_trips.csv file found in given path.")
    except Exception as e:
        logging.error("Error reading output_trips file: " + str(e))
        raise


# main execution
if __name__ == "__main__":

    setup_logging(get_log_filename())

    # if you want to read all rows, set num_rows = -1
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_of_script = os.path.dirname(script_dir)
    # TODO change "plots" to what ever folder you want to save to
    config = configparser.ConfigParser()
    config.read(f'{parent_of_script}\\config\\config.ini')
    section = 'config_compare'

    try:
        doing_comparison = config.getboolean(section, 'doing_comparison')
        comparison_num_rows = config.getint(section, 'comparison_num_rows')
        comparison_mode_column = config.get(section, 'comparison_mode_column')
        sim_output_folder_1 = config.get(section, '1_sim_output_folder')
        sim_output_folder_2 = config.get(section, '2_sim_output_folder')
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit(1)

    if not doing_comparison:
        logging.info("Comparison is disabled in the config file. Exiting.")
        sys.exit(0)

    try:
        df_1, sim_1_name = read_output_trips(sim_output_folder_1, num_rows=comparison_num_rows)
        df_2, sim_2_name = read_output_trips(sim_output_folder_2, num_rows=comparison_num_rows)
        logging.info(f"Data loaded: {sim_1_name} with {len(df_1)} rows, {sim_2_name} with {len(df_2)} rows")
    except Exception as e:
        logging.error("Error loading data: " + str(e))
        sys.exit(1)

    before_data, after_data, differences_data = process_transport_data(df_1, df_2, sim_1_name, sim_2_name, comparison_mode_column)
    end_time = time.time()
    logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")