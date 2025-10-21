import pandas as pd
import os


def aggregate_modal_split(base_plots_path):
    aggregated_df = pd.DataFrame()
    master_titles = []  # Will store the complete list of titles from the first file
    titles_set = set()

    # Path to the ModeShareOutputs_inOneColumn directory
    mode_share_outputs_path = os.path.join(base_plots_path, "ModeShareOutputs_inOneColumn")

    if not os.path.exists(mode_share_outputs_path):
        print(f"❌ Directory not found: {mode_share_outputs_path}")
        return

    # Iterate through CSV files in ModeShareOutputs_inOneColumn
    for filename in sorted(os.listdir(mode_share_outputs_path)):  # Sort to ensure consistent order
        if filename.startswith("modeOutputs_") and filename.endswith(".csv"):
            file_path = os.path.join(mode_share_outputs_path, filename)

            try:
                df = pd.read_csv(file_path, sep=';')

                # Check if file is empty
                if df.empty:
                    print(f"⚠️ Warning: {filename} is empty. Skipping.")
                    continue

                # Check for required columns
                if 'Title' not in df.columns or 'Value with Comma' not in df.columns:
                    print(f"⚠️ Warning: {filename} missing required columns ('Title' or 'Value with Comma'). Skipping.")
                    print(f"   Available columns: {list(df.columns)}")
                    continue

                # Extract simulation name from filename
                simulation_name = filename.replace("modeOutputs_", "").replace(".csv", "")

                # If this is the first file, initialize with its structure
                if aggregated_df.empty:
                    aggregated_df['Title'] = df['Title']
                    master_titles = df['Title'].tolist()
                    titles_set = set(master_titles)

                    # If the first file has more titles than others, use it as the master
                    if 'DRT' in ' '.join(master_titles):
                        print(f"📋 Using {filename} as master structure (includes DRT)")
                else:
                    # If current file has MORE titles than master (e.g., includes DRT), update master
                    current_titles = df['Title'].tolist()
                    if len(current_titles) > len(master_titles):
                        print(
                            f"📋 Updating master structure from {filename} (has {len(current_titles)} rows vs {len(master_titles)})")

                        # Rebuild aggregated_df with new master structure
                        new_aggregated_df = pd.DataFrame({'Title': current_titles})

                        # Copy existing columns, filling missing rows with empty strings
                        for col in aggregated_df.columns:
                            if col != 'Title':
                                # Map old values to new structure
                                old_dict = dict(zip(aggregated_df['Title'], aggregated_df[col]))
                                new_aggregated_df[col] = new_aggregated_df['Title'].map(old_dict).fillna('')

                        aggregated_df = new_aggregated_df
                        master_titles = current_titles
                        titles_set = set(master_titles)

                # Map current file's values to master structure
                value_dict = dict(zip(df['Title'], df['Value with Comma']))
                aggregated_df[simulation_name] = aggregated_df['Title'].map(value_dict).fillna('')

                print(f"✅ Processed: {filename} -> Column: {simulation_name} ({len(df)} rows)")

            except pd.errors.EmptyDataError:
                print(f"⚠️ Warning: {filename} is empty or corrupted. Skipping.")
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")

    # Save aggregated CSV
    if not aggregated_df.empty:
        output_path = os.path.join(mode_share_outputs_path, "aggregatedColumns.csv")
        aggregated_df.to_csv(output_path, sep=';', index=False)
        print(f"\n✅ Aggregated CSV saved to: {output_path}")
        print(f"📊 Total columns aggregated: {len(aggregated_df.columns) - 1}")
        print(f"📋 Total rows: {len(aggregated_df)}")
    else:
        print("⚠️ No data was aggregated. Check if files exist and match the pattern.")


if __name__ == '__main__':
    # Assume script is run from project root or adjust accordingly
    current_dir = os.getcwd()
    plots_dir = os.path.join(os.path.dirname(current_dir), "plots")
    aggregate_modal_split(plots_dir)