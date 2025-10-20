import pandas as pd
import os


def aggregate_modal_split(base_plots_path):
    aggregated_df = pd.DataFrame()
    titles_set = set()

    # Path to the ModeShareOutputs_inOneColumn directory
    mode_share_outputs_path = os.path.join(base_plots_path, "ModeShareOutputs_inOneColumn")

    if not os.path.exists(mode_share_outputs_path):
        print(f"❌ Directory not found: {mode_share_outputs_path}")
        return

    # Iterate through CSV files in ModeShareOutputs_inOneColumn
    for filename in os.listdir(mode_share_outputs_path):
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

                # Initialize the aggregated dataframe with Title column
                if aggregated_df.empty:
                    aggregated_df['Title'] = df['Title']
                    titles_set = set(df['Title'])
                else:
                    # Check for title consistency
                    if set(df['Title']) != titles_set:
                        print(f"⚠️ Warning: Title mismatch in {filename}. Skipping.")
                        print(f"   Expected {len(titles_set)} titles, found {len(df['Title'])} titles")
                        continue

                # Extract simulation name from filename
                # Remove "modeOutputs_" prefix and ".csv" suffix
                simulation_name = filename.replace("modeOutputs_", "").replace(".csv", "")

                # Add the column with the simulation name as header
                aggregated_df[simulation_name] = df['Value with Comma']

                print(f"✅ Processed: {filename} -> Column: {simulation_name}")

            except pd.errors.EmptyDataError:
                print(f"⚠️ Warning: {filename} is empty or corrupted. Skipping.")
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")

    # Save aggregated CSV
    if not aggregated_df.empty:
        output_path = os.path.join(mode_share_outputs_path, "aggregatedColumns.csv")
        aggregated_df.to_csv(output_path, sep=';', index=False)
        print(f"\n✅ Aggregated CSV saved to: {output_path}")
        print(f"📊 Total columns aggregated: {len(aggregated_df.columns) - 1}")  # -1 for Title column
    else:
        print("⚠️ No data was aggregated. Check if files exist and match the pattern.")


if __name__ == '__main__':
    # Assume script is run from project root or adjust accordingly
    current_dir = os.getcwd()
    plots_dir = os.path.join(os.path.dirname(current_dir), "plots")
    aggregate_modal_split(plots_dir)