import os
import logging
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import numpy as np
from functions.commonFunctions import *
from functools import reduce

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')


def compute_percentage(df, group_col, value_col):
    df = df.groupby(group_col)[value_col].sum().reset_index()
    df.columns = ['Mode', f'Total {value_col.title()}']
    total = df[f'Total {value_col.title()}'].sum()
    df[f'Percentage {value_col.title()}'] = (df[f'Total {value_col.title()}'] / total) * 100
    return df


def save_custom_csv(file_path, *dfs):
    merged = reduce(lambda left, right: pd.merge(left, right, on='Mode', how='outer'), dfs)
    merged = merged.round(2)
    merged.to_csv(file_path, index=False)
    logging.info(f"Saved file: {file_path}")


def plot_grouped_bar(dataframes, labels, title, filename, ylabel):
    modes = sorted(set.union(*[set(df['Mode']) for df in dataframes]))
    bar_width = 0.2
    x = range(len(modes))
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (df, label) in enumerate(zip(dataframes, labels)):
        percentage_col = [col for col in df.columns if col.lower().startswith('percentage')][0]
        y = [df[df['Mode'] == m][percentage_col].values[0] if m in df['Mode'].values else 0 for m in modes]
        bar_positions = [p + bar_width * i for p in x]
        ax.bar(bar_positions, y, width=bar_width, label=label)
        for xpos, height in zip(bar_positions, y):
            if height > 0:
                ax.text(xpos, height + 0.5, f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

    ax.set_xticks([p + bar_width * (len(dataframes) - 1) / 2 for p in x])
    ax.set_xticklabels(modes, rotation=45)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()


def filter_out_modes(df, mode_col='mode', modes_to_exclude=None):
    if modes_to_exclude is None:
        modes_to_exclude = ['Outside']
    return df[~df[mode_col].isin(modes_to_exclude)].copy()


def load_and_prepare_data(file_path, mode_col='mode', modes_to_exclude=None):
    df = pd.read_csv(file_path)
    if mode_col in df.columns:
        df[mode_col] = df[mode_col].astype(str).str.replace('_', ' ').str.title()
        df = filter_out_modes(df, mode_col, modes_to_exclude)
    return df


def main():
    setup_logging(get_log_filename())
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), f'plots/plots_{os.path.basename(sim_output_folder)}')
    mode_share_directory = os.path.join(plots_directory, 'outputs_mode_share')
    os.makedirs(mode_share_directory, exist_ok=True)
    logging.info(f"Data path: {data_path}")

    try:
        df_mic = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_mic.csv"))
        logging.info(f"Mic Data loaded from {data_path_clean}")
        # Simulation trips now use 'main_mode' column instead of 'mode'
        df_sim = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_sim.csv"), mode_col='main_mode')
        logging.info(f"Sim Data loaded from {data_path_clean}")

        if read_SynPop:
            df_synt = load_and_prepare_data(os.path.join(data_path_clean, "travel_time_distance_mode_synt.csv"))
            logging.info(f"Synt Data loaded from {data_path_clean}")

    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return

    # DISTANCE MIC - Create weighted_distance column first
    if 'person_weight' not in df_mic.columns:
        df_mic['person_weight'] = 1.0
        logging.info("person_weight missing in Mic Data, defaulting to 1.0 (unweighted)")
    df_mic['weighted_distance'] = df_mic['crowfly_distance'] * df_mic['person_weight']
    logging.info(f"weighted_distance column created in Mic Data")

    if 'person_weight' in df_mic.columns:
        # weighted_distance already created above
        logging.info(f"Weighted Mic Data loaded from {data_path_clean}")
        # Calculate weighted mean and weighted std correctly
        def weighted_mean(group):
            return (group['crowfly_distance'] * group['person_weight']).sum() / group[
                'person_weight'].sum()

        def weighted_std(group):
            w_mean = weighted_mean(group)
            variance = ((group['person_weight'] * (group['crowfly_distance'] - w_mean) ** 2).sum() /
                        group['person_weight'].sum())
            return np.sqrt(variance)

        average_distance_by_mode_mic_wt = df_mic.groupby('mode').apply(
            lambda x: pd.Series({
                'Average Distance Mic WT': weighted_mean(x),
                'STD Distance Mic WT': weighted_std(x)
            }),
            include_groups=False  # This ensures clean output
        ).reset_index()
        logging.info(f"Average Distance Mic WT columns created in Mic Data")

        # Rename the 'mode' column to 'Mode' to match other dataframes
        average_distance_by_mode_mic_wt.rename(columns={'mode': 'Mode'}, inplace=True)

    # Remove outside from sim and synt again in case they're added back
    try:
        df_sim = filter_out_modes(df_sim, 'main_mode')
        if read_SynPop:
            df_synt = filter_out_modes(df_synt, 'mode')

        logging.info(f"Sim Data filtered to remove 'Outside' modes")
        # DISTANCE
        dist_mic = compute_percentage(df_mic, 'mode', 'crowfly_distance').rename(columns={'Percentage Crowfly_Distance': 'Percentage Mic'})
        dist_mic_wt = compute_percentage(df_mic, 'mode', 'weighted_distance').rename(columns={'Percentage Weighted_Distance': 'Percentage Mic Weighted'})
        dist_sim = compute_percentage(df_sim, 'main_mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Sim', 'Total Distance': 'Total Distance Sim'})
        logging.info(f"Distance percentages computed for Mic and Sim Data")
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return

    if read_SynPop:
        dist_synt = compute_percentage(df_synt, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': dist_sim['Mode'], 'Percentage Synt': [0.0]*len(dist_sim)})

    average_distance_by_mode_mic = df_mic.groupby('mode')['crowfly_distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_mic.columns = ['Mode', 'Average Distance Mic', 'STD Distance Mic']
    logging.info(f"Average Distance Mic columns created in Mic Data")
    # average_distance_by_mode_mic_wt already calculated correctly above (lines 91-105) - DON'T recalculate!
    average_distance_by_mode_sim = df_sim.groupby('main_mode')['distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_sim.columns = ['Mode', 'Average Distance Sim', 'STD Distance Sim']
    logging.info(f"Average Distance Sim columns created in Sim Data")
    if read_SynPop:
        average_distance_by_mode_synt = df_synt.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
        average_distance_by_mode_synt.columns = ['Mode', 'Average Distance Synt', 'STD Distance Synt']
        logging.info(f"Average Distance Synt columns created in Synt Data")

    try:
        plot_grouped_bar([dist_mic_wt, dist_mic, dist_sim, dist_synt] if read_SynPop else [dist_mic_wt, dist_mic, dist_sim],
                         ['Microcensus Weighted', 'Microcensus Single', 'Simulation', 'Synthetic'] if read_SynPop else ['Microcensus Weighted', 'Microcensus Single', 'Simulation'],
                         'Comparison of Mode Share Distribution - % of Total Distance',
                         f"{mode_share_directory}/Mode_share_by_Distance.png", 'Percentage (%)')


        save_custom_csv(f"{mode_share_directory}/Mode_shares_distance.csv",
                        dist_mic[['Mode', 'Percentage Mic']],
                        dist_mic_wt[['Mode', 'Percentage Mic Weighted']],
                        dist_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']],
                        average_distance_by_mode_mic_wt[['Mode', 'Average Distance Mic WT', 'STD Distance Mic WT']],
                        average_distance_by_mode_sim[['Mode', 'Average Distance Sim', 'STD Distance Sim']]
                        )
        logging.info(f"Saved {mode_share_directory}/Mode_shares_distance.csv without Synthetic data")
    except Exception as e:
        logging.error(f"Error plotting or saving distance data: {e}")
        return

    if read_SynPop:
        save_custom_csv(f"{mode_share_directory}/Mode_shares_distance.csv",
                        dist_mic[['Mode', 'Percentage Mic']],
                        dist_mic_wt[['Mode', 'Percentage Mic Weighted']],
                        dist_synt[['Mode', 'Percentage Synt']],
                        dist_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']],
                        average_distance_by_mode_mic_wt[['Mode', 'Average Distance Mic WT', 'STD Distance Mic WT']],
                        average_distance_by_mode_sim[['Mode', 'Average Distance Sim', 'STD Distance Sim']],
                        average_distance_by_mode_synt[['Mode', 'Average Distance Synt', 'STD Distance Synt']]
                        )
        logging.info(f"Saved {mode_share_directory}/Mode_shares_distance.csv with Synthetic data")

    # TIME (CSV only, microcensus columns removed)
    df_sim['travel_time'] = pd.to_numeric(df_sim['travel_time'], errors='coerce')
    if read_SynPop:
        df_synt['travel_time'] = pd.to_numeric(df_synt['travel_time'], errors='coerce')

    time_sim = compute_percentage(df_sim, 'main_mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Sim', 'Total Travel_Time': 'Total Time Sim'})
    time_synt = compute_percentage(df_synt, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': time_sim['Mode'], 'Percentage Synt': [0.0]*len(time_sim)})
    logging.info("Plotting mode shares distribution")

    save_custom_csv(f"{mode_share_directory}/Mode_shares_time.csv",
                    time_synt[['Mode', 'Percentage Synt']],
                    time_sim[['Mode', 'Total Time Sim', 'Percentage Sim']])
    logging.info(f"Saved {mode_share_directory}/Mode_shares_time.csv after time sim.")

    try:
        # TRIPS
        trips_mic_raw = df_mic['mode'].value_counts(normalize=True).reset_index()
        trips_mic_raw.columns = ['Mode', 'Percentage Mic']
        trips_mic_raw['Percentage Mic'] *= 100

        trips_mic_wt = df_mic.groupby('mode')['person_weight'].sum().reset_index()
        trips_mic_wt.columns = ['Mode', 'Weighted Count']
        total_weighted = trips_mic_wt['Weighted Count'].sum()
        trips_mic_wt['Percentage Mic Weighted'] = (trips_mic_wt['Weighted Count'] / total_weighted) * 100
        trips_mic_wt = trips_mic_wt[['Mode', 'Percentage Mic Weighted']]

        # Simulation trips use 'main_mode' column
        trips_sim_counts = df_sim['main_mode'].value_counts().reset_index()
        trips_sim_counts.columns = ['Mode', 'Total Trips Sim']
        trips_sim_perc = df_sim['main_mode'].value_counts(normalize=True).reset_index()
        trips_sim_perc.columns = ['Mode', 'Percentage Sim']
        trips_sim_perc['Percentage Sim'] *= 100
        trips_sim = pd.merge(trips_sim_counts, trips_sim_perc, on='Mode', how='outer')
        logging.info("Trip mode shares for Mic and Sim Data computed")

        if read_SynPop:
            trips_synt = df_synt['mode'].value_counts(normalize=True).reset_index()
            trips_synt.columns = ['Mode', 'Percentage Synt']
            trips_synt['Percentage Synt'] *= 100
            logging.info("Trip mode shares for Mic and Sim Data computed ans synthetic")
        else:
            unique_modes = pd.concat([trips_mic_raw['Mode'], trips_sim['Mode']]).unique()
            trips_synt = pd.DataFrame({'Mode': unique_modes, 'Percentage Synt': [0.0] * len(unique_modes)})
            logging.info("Trip mode shares for Mic and Sim Data computed without synthetic")
    except Exception as e:
        logging.error(f"Error computing trip mode shares: {e}")
        return

    # =========================================================================
    # DRT Trip Metrics
    # =========================================================================
    # DRT OD Trips: trips where main_mode is 'drt' (or 'Drt' after title-casing)
    drt_od_trips = (df_sim['main_mode'].str.lower() == 'drt').sum()
    logging.info("drt od trips calculated")

    # DRT Multi-modal Trips: trips where 'drt' appears in modes column but main_mode is NOT 'drt'
    # The 'modes' column contains leg sequences like "walk-drt-walk" or "drt-pt-drt"
    if 'modes' in df_sim.columns:
        has_drt_in_modes = df_sim['modes'].str.contains('drt', case=False, na=False)
        main_mode_not_drt = df_sim['main_mode'].str.lower() != 'drt'
        drt_multimodal_trips = (has_drt_in_modes & main_mode_not_drt).sum()
    else:
        drt_multimodal_trips = 0
        logging.warning("'modes' column not found in df_sim - DRT multi-modal trips set to 0")

    logging.info(f"DRT OD Trips: {drt_od_trips}, DRT Multi-modal Trips: {drt_multimodal_trips}")
    try:
        plot_grouped_bar([trips_mic_wt, trips_mic_raw, trips_sim, trips_synt] if read_SynPop else [trips_mic_wt, trips_mic_raw, trips_sim],
                         ['Microcensus Weighted', 'Microcensus Raw', 'Simulation', 'Synthetic'] if read_SynPop else ['Microcensus Weighted', 'Microcensus Raw', 'Simulation'],
                         'Comparison of Mode Share Distribution - % of Trips',
                         f"{mode_share_directory}/Mode_share_by_Trips.png", 'Percentage (%)')

        save_custom_csv(f"{mode_share_directory}/Mode_shares_by_trip.csv",
                        trips_mic_raw[['Mode', 'Percentage Mic']],
                        trips_mic_wt[['Mode', 'Percentage Mic Weighted']],
                        trips_synt[['Mode', 'Percentage Synt']],
                        trips_sim[['Mode', 'Total Trips Sim', 'Percentage Sim']])

        # Save DRT metrics to a separate row in a CSV (will be picked up by script 12)
        drt_metrics_df = pd.DataFrame([
            {'Mode': 'DRT OD Trips', 'Value': drt_od_trips},
            {'Mode': 'DRT Multi-modal Trips', 'Value': drt_multimodal_trips}
        ])
        drt_metrics_df.to_csv(f"{mode_share_directory}/drt_trip_metrics.csv", index=False)
        logging.info(f"DRT trip metrics saved to {mode_share_directory}/drt_trip_metrics.csv")
    except Exception as e:
        logging.error(f"Error plotting or saving trip data: {e}")
        return


if __name__ == '__main__':
    main()