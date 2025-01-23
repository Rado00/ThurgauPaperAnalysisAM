import pandas as pd
import os
from common import *

if __name__ == '__main__':
    setup_logging("05_2_CSVs_in_a_column.log")

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{analysis_zone_name}')
    mode_share_directory = os.path.join(plots_directory, 'mode_share')

    # List of specific CSV files to read
    specific_files = [
        'mode_share_trip_comparison.csv',
        'Mode_share_distance_comparison.csv',
        'Mode_share_time_comparison.csv'
    ]

    # Mode mappings for index
    mode_mappings = {
        0: 'Bike',
        1: 'Car',
        2: 'Car Passenger',
        3: 'PT',
        4: 'Walk'
    }

    # Verify the directory exists
    if os.path.exists(mode_share_directory):
        consolidated_data = []
        for file_name in specific_files:
            file_path = os.path.join(mode_share_directory, file_name)
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                if not df.empty:
                    for col in df.columns:
                        for index, value in df[col].items():
                            mode = mode_mappings.get(index, '')
                            if file_name == 'Mode_share_distance_comparison.csv':
                                if 'Percentage Microcensus' in col:
                                    title = f"% Distance {mode} Mic by raw"
                                elif 'Percentage Weighted Microcensus' in col:
                                    title = f"% Distance {mode} Mic weighted"
                                elif 'Total Distance Simulation' in col:
                                    title = f"Count Distance {mode} Thurgau Sim"
                                elif 'Percentage Simulation' in col:
                                    title = f"% Distance {mode} Sim"
                                elif 'Percentage Synthetic' in col:
                                    title = f"% Distance {mode} Synthetic"
                                else:
                                    continue
                            elif file_name == 'mode_share_trip_comparison.csv':
                                if 'Number_Percentage' in col:
                                    title = f"% Trips {mode} Mic by raw"
                                elif 'Household_Percentage' in col:
                                    title = f"% Trips {mode} Mic weighted"
                                elif 'Simulation_Count' in col:
                                    title = f"Count Trips {mode} Thurgau Sim"
                                elif 'Simulation_Percentage' in col:
                                    title = f"% Trips {mode} Sim"
                                elif 'Synthetic_Percentage' in col:
                                    title = f"% Trips {mode} Synthetic"
                                else:
                                    continue
                            elif file_name == 'Mode_share_time_comparison.csv':
                                if 'Percentage Microcensus' in col:
                                    title = f"% TravelTime {mode} Mic by raw"
                                elif 'Percentage Weighted Microcensus' in col:
                                    title = f"% TravelTime {mode} Mic weighted"
                                elif 'Percentage Simulation' in col:
                                    title = f"% TravelTime {mode} Sim"
                                elif 'Total Travel Time Simulation' in col:
                                    title = f"Count TravelTime {mode} Thurgau Sim"
                                elif 'Percentage Synthetic' in col:
                                    title = f"% TravelTime {mode} Synthetic"
                                else:
                                    continue
                            else:
                                continue  # Skip unrecognized files or columns
                            consolidated_data.append([title, value])
            else:
                print(f"File not found: {file_name}")

        if consolidated_data:
            output_df = pd.DataFrame(consolidated_data, columns=['Title', 'Value'])
            output_df.to_csv(os.path.join(mode_share_directory, 'modalSplitCalibration.csv'), sep=';', index=False)
            print("Data successfully saved.")
        else:
            print("No data found in the files.")
    else:
        print(f"The directory {mode_share_directory} does not exist.")
