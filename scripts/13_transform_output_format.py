"""
Reorder the columnar output so that for each metric, values are grouped together
with Simulated Area first, followed by Target Area O AND D, then Target Area O OR D.

The output remains in 2-column format (Title, Value) but with reordered rows.
"""

import pandas as pd
import os
import sys
import logging
from functions.commonFunctions import *

def transform_output_format(input_csv_path, output_csv_path):
    """
    Reorder rows so that for each metric, Simulated Area comes first,
    followed by Target Area O AND D, then Target Area O OR D
    
    Args:
        input_csv_path: Path to input CSV (columnar format)
        output_csv_path: Path to output CSV (reordered format)
    """
    # Read the input CSV
    df_input = pd.read_csv(input_csv_path, sep=';')
    
    logging.info(f"Read {len(df_input)} rows from {input_csv_path}")
    
    # Dictionary to group rows by base metric
    metric_groups = {}
    other_rows = []  # For DRT and other metrics without area specification
    
    # Process each row
    for idx, row in df_input.iterrows():
        title = row['Title']
        
        # Extract the base metric and area
        if ' - Simulated Area' in title:
            base_metric = title.replace(' - Simulated Area', '')
            area_type = 'Simulated Area'
            area_order = 1
        elif ' - Target Area O AND D' in title:
            base_metric = title.replace(' - Target Area O AND D', '')
            area_type = 'Target Area O AND D'
            area_order = 2
        elif ' - Target Area O OR D' in title:
            base_metric = title.replace(' - Target Area O OR D', '')
            area_type = 'Target Area O OR D'
            area_order = 3
        elif 'Target Area O AND D' in title:
            base_metric = title.replace(' Target Area O AND D', '')
            area_type = 'Target Area O AND D'
            area_order = 2
        elif 'Target Area O OR D' in title:
            base_metric = title.replace(' Target Area O OR D', '')
            area_type = 'Target Area O OR D'
            area_order = 3
        else:
            # Metrics without area specification (DRT, etc.)
            other_rows.append(row.to_dict())
            continue
        
        # Group by base metric
        if base_metric not in metric_groups:
            metric_groups[base_metric] = []
        
        metric_groups[base_metric].append({
            'Title': title,
            'Value': row['Value'],
            'Value with Comma': row['Value with Comma'],
            'Source File': row['Source File'],
            'area_order': area_order,
            'base_metric': base_metric
        })
    
    # Build the final ordered list following the exact pattern specified
    ordered_rows = []
    
    # Define all 5 modes in order
    modes = ['Bike', 'Car', 'Car Passenger', 'PT', 'Walk']
    
    # Define the exact order as specified
    exact_order = []
    
    # 1. % Trips (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'% Trips {mode} - Simulated Area')
    for mode in modes:
        exact_order.append(f'% Trips {mode} - Target Area O OR D')
    
    # 2. % Distance (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'% Distance {mode}  - Simulated Area')
    for mode in modes:
        exact_order.append(f'% Distance {mode}  - Target Area O OR D')
    
    # 3. Count Trips (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'Count Trips {mode} - Simulated Area')
    for mode in modes:
        exact_order.append(f'Count Trips {mode} - Target Area O OR D')
    
    # 4. Count Distance (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'Count Distance {mode}  - Simulated Area')
    for mode in modes:
        exact_order.append(f'Count Distance {mode}  - Target Area O OR D')
    
    # 5. Count TravelTime (all 5 modes) - Target Area O OR D only
    for mode in modes:
        exact_order.append(f'Count TravelTime {mode} Target Area O OR D')
    
    # 6. Average Distance (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'Average Distance Sim {mode}  - Simulated Area')
    for mode in modes:
        exact_order.append(f'Average Distance Sim {mode}  - Target Area O OR D')
    
    # 7. STD Distance (all 5 modes) - Simulated Area, then all 5 modes - Target Area O OR D
    for mode in modes:
        exact_order.append(f'STD Distance Sim {mode}  - Simulated Area')
    for mode in modes:
        exact_order.append(f'STD Distance Sim {mode}  - Target Area O OR D')
    
    # DRT metrics will be added from other_rows after the main metrics
    
    # 8. % Trips (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'% Trips {mode} - Target Area O AND D')
    
    # 9. % Distance (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'% Distance {mode}  - Target Area O AND D')
    
    # 10. Count Trips (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'Count Trips {mode} - Target Area O AND D')
    
    # 11. Count Distance (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'Count Distance {mode}  - Target Area O AND D')
    
    # 12. Count TravelTime (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'Count TravelTime {mode} Target Area O AND D')
    
    # 13. Average Distance (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'Average Distance Sim {mode}  - Target Area O AND D')
    
    # 14. STD Distance (all 5 modes) - Target Area O AND D
    for mode in modes:
        exact_order.append(f'STD Distance Sim {mode}  - Target Area O AND D')
    
    # Create a dictionary for quick lookup
    all_rows_dict = {}
    for group_rows in metric_groups.values():
        for row in group_rows:
            all_rows_dict[row['Title']] = row
    
    # Add rows in the exact order specified
    for title in exact_order:
        if title in all_rows_dict:
            ordered_rows.append(all_rows_dict[title])
    
    # Add any remaining rows that weren't in the exact order list
    added_titles = set(exact_order)
    for group_rows in metric_groups.values():
        for row in group_rows:
            if row['Title'] not in added_titles:
                ordered_rows.append(row)
                added_titles.add(row['Title'])
    
    # Add other rows (DRT metrics, etc.) at the end
    ordered_rows.extend(other_rows)
    
    # Create output DataFrame
    df_output = pd.DataFrame(ordered_rows)
    
    # Keep only the necessary columns in the right order
    df_output = df_output[['Source File', 'Title', 'Value', 'Value with Comma']]
    
    # Save to CSV
    # df_output.to_csv(output_csv_path, sep=';', index=False)
    logging.info(f"Reordered output saved to {output_csv_path}")
    
    return df_output


if __name__ == '__main__':
    setup_logging(get_log_filename())
    
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, \
        csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, \
        sample_for_debugging, target_area = read_config()
    
    logging.info(f"Reading config file from {data_path} path was successful.")
    print(data_path)
    print(simulation_zone_name)
    
    print(target_area)
    
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    
    # Define paths
    plots_root = os.path.join(parent_directory, "plots")
    one_column_directory = os.path.join(plots_root, "ModeShareOutputs_inOneColumn")
    output_directory = os.path.join(plots_root, "ModeShareOutputs_Reordered")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    # Extract scenario name
    scenario_name = os.path.basename(sim_output_folder)
    
    # Define input and output file paths
    input_file = os.path.join(one_column_directory, f'modeOutputs_{scenario_name}_{target_area}.csv')
    output_file = os.path.join(output_directory, f'modeOutputs_{scenario_name}_{target_area}_reordered.csv')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Transform the output
    try:
        df_result = transform_output_format(input_file, output_file)
        
        directory = os.getcwd()
        parent_directory = os.path.dirname(directory)
        output_plots_folder_name = os.path.basename(sim_output_folder)
        plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots", f"plots_{output_plots_folder_name}")
        
        
        new_row = pd.DataFrame({
            'Source File': [f'Target Area shapefile is {target_area}'],
            'Title': [None],
            'Value': [None],
            'Value with Comma': [None]
        })
        
        df = pd.concat([new_row, df_result], ignore_index=True)
        
        mode_share_directory = os.path.join(plots_directory, 'outputs_mode_share')
        
        drt_summary_metrics_path = os.path.join(mode_share_directory, "drt_summary_metrics.csv")
        
        df_drt_summary_metrics = pd.read_csv(drt_summary_metrics_path, sep=";")
        
        logging.info(f"Reordering completed successfully!")
        logging.info(f"Output shape: {df_result.shape}")
        
        # Display first few rows
        print("\nFirst 15 rows of reordered output:")
        final_result = pd.concat([df, df_drt_summary_metrics], ignore_index=True)
        final_result.to_csv(output_file, sep=';', index=False)
        
        print(final_result.head(15))
        
    except Exception as e:
        logging.error(f"Error during transformation: {str(e)}")
        sys.exit(1)
