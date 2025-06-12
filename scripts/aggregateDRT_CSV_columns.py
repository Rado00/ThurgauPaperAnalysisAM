import pandas as pd
import os
import logging
from functions.commonFunctions import read_config, setup_logging, get_log_filename

def aggregate_drt_summary_metrics(plots_root_directory):
    aggregated_df = pd.DataFrame()
    titles_set = set()
    source_file_set = set()

    # Iterate over all subfolders like plots_*
    for subfolder in os.listdir(plots_root_directory):
        if not subfolder.startswith("plots_"):
            continue

        folder_path = os.path.join(plots_root_directory, subfolder)
        drt_csv_path = os.path.join(folder_path, "drt_summary_metrics.csv")

        if os.path.isfile(drt_csv_path):
            try:
                df = pd.read_csv(drt_csv_path, sep=';')

                if aggregated_df.empty:
                    aggregated_df[['Source File', 'Title']] = df[['Source File', 'Title']]
                    titles_set = set(df['Title'])
                    source_file_set = set(df['Source File'])
                else:
                    if set(df['Title']) != titles_set or set(df['Source File']) != source_file_set:
                        logging.warning(f"⚠️ Title or Source File mismatch in {subfolder}. Skipping.")
                        continue

                folder_label = subfolder.replace("plots_", "")

                for col in df.columns:
                    if col not in ['Source File', 'Title', 'Value']:
                        new_col_name = f"{col} ({folder_label})"
                        aggregated_df[new_col_name] = df[col]

            except Exception as e:
                logging.error(f"❌ Failed to process {drt_csv_path}: {e}")

    # Save final CSV
    output_path = os.path.join(plots_root_directory, "aggregatedColumns_drt.csv")
    aggregated_df.to_csv(output_path, sep=';', index=False)
    logging.info(f"✅ Aggregated DRT summary saved to: {output_path}")

if __name__ == '__main__':
    setup_logging(get_log_filename())

    # Read config and construct the correct plots directory
    (
        data_path, simulation_zone_name, scenario, sim_output_folder,
        percentile, analysis_zone_name, csv_folder, clean_csv_folder,
        shapeFileName, read_SynPop, read_microcensus,
        sample_for_debugging, target_area
    ) = read_config()

    output_plots_folder_name = os.path.basename(sim_output_folder)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots")

    logging.info(f"Reading config file from {data_path} successful.")
    aggregate_drt_summary_metrics(plots_directory)
