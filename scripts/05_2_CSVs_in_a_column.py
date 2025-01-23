import pandas as pd
import os

base_path = "C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data"
mode_share_directory = "C:/Users/muaa/Documents/3_MIEI/ThurgauPaperAnalysisAM/plots/plots_MATSim_Thurgau/mode_share"

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
                        # Customize the title based on file, column name, and index
                        if file_name == 'Mode_share_distance_comparison.csv':
                            mode = mode_mappings.get(index, '')
                            if 'Percentage Weighted Microcensus' in col:
                                title = f"% Distance {mode} Mic weighted"
                            elif 'Total Distance Simulation' in col:
                                title = f"Count Distance {mode} Thurgau Sim"
                            elif 'Percentage Simulation' in col:
                                title = f"% Distance {mode} Sim"
                            elif 'Percentage Microcensus' in col:
                                title = f"% Distance {mode} Mic by raw"
                            else:
                                continue  # Skip rows not matching the specified patterns
                            consolidated_data.append([title, value])
                            continue

                        title = f"{file_name}_{col}_{index}"
                        consolidated_data.append([title, value])
        else:
            print(f"File not found: {file_name}")

    if consolidated_data:
        output_df = pd.DataFrame(consolidated_data, columns=['Title', 'Value'])
        # Using semicolon as the delimiter
        output_df.to_csv(os.path.join(mode_share_directory, 'modalSplitCalibration.csv'), sep=';', index=False)
    else:
        print("No data found in the files.")
else:
    print(f"The directory {mode_share_directory} does not exist.")
