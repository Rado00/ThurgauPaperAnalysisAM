import pandas as pd
import os

def aggregate_modal_split(base_plots_path):
    aggregated_df = pd.DataFrame()
    titles_set = set()

    # Iterate through each subdirectory in plots
    for subfolder in os.listdir(base_plots_path):
        subfolder_path = os.path.join(base_plots_path, subfolder)
        if os.path.isdir(subfolder_path):
            mode_share_csv = os.path.join(subfolder_path, "mode_share", "modalSplitCalibration.csv")
            if os.path.exists(mode_share_csv):
                try:
                    df = pd.read_csv(mode_share_csv, sep=';')
                    if aggregated_df.empty:
                        aggregated_df['Title'] = df['Title']
                        titles_set = set(df['Title'])
                    else:
                        if set(df['Title']) != titles_set:
                            print(f"⚠️ Warning: Title mismatch in {subfolder}. Skipping.")
                            continue

                    # Extract folder name after "plots_" prefix
                    folder_label = subfolder.replace("plots_", "")
                    aggregated_df[folder_label] = df['Value with Comma']

                except Exception as e:
                    print(f"❌ Failed to process {mode_share_csv}: {e}")

    # Save aggregated CSV
    output_path = os.path.join(base_plots_path, "aggregatedColumns.csv")
    aggregated_df.to_csv(output_path, sep=';', index=False)
    print(f"✅ Aggregated CSV saved to: {output_path}")

if __name__ == '__main__':
    # Assume script is run from project root or adjust accordingly
    current_dir = os.getcwd()
    plots_dir = os.path.join(os.path.dirname(current_dir), "plots")
    aggregate_modal_split(plots_dir)
