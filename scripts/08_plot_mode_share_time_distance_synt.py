import os
import logging
import pandas as pd
import warnings
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime
from functions.commonFunctions import *

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, sample_for_debugging = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    directory = os.getcwd()
    output_plots_folder_name = sim_output_folder.split('\\')[-1]
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{output_plots_folder_name}')
    os.makedirs(plots_directory, exist_ok=True)

    data_path_clean = os.path.join(data_path, analysis_zone_name, "microzensus")

    df_trips_all_activities_inside_mic = pd.read_csv(f'{data_path_clean}\\trips_all_activities_inside_mic.csv')
    logging.info(f"Reading the df_trips_all_activities_inside_mic csv file was successful.")

    df_mic_mode_share = df_trips_all_activities_inside_mic[['person_id', 'trip_id', 'purpose', 'departure_time', 'arrival_time', 'crowfly_distance', 'mode', 'household_weight']]
    df_mic_mode_share.rename(columns={'crowfly_distance': 'distance'}, inplace=True)

    df_mic_mode_share['travel_time'] = (pd.to_datetime(df_mic_mode_share['arrival_time']) - pd.to_datetime(df_mic_mode_share['departure_time'])).dt.total_seconds()

    if read_SynPop:
        df_synt_mode_share = pd.read_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_synt.csv')

    df_sim_mode_share = pd.read_csv(f'{pre_processed_data_path}\\trips_all_activities_inside_sim.csv')
    df_sim_mode_share['longest_distance_mode'] = df_sim_mode_share['longest_distance_mode'].fillna(df_sim_mode_share['modes'])
    df_sim_mode_share.rename(columns={'longest_distance_mode': 'mode'}, inplace=True)

    modes_to_remove = ['truck', 'outside']
    df_mic_mode_share['mode'] = df_trips_all_activities_inside_mic['mode'].str.replace('_', ' ').str.title()
    df_sim_mode_share = df_sim_mode_share[~df_sim_mode_share['mode'].isin(modes_to_remove)]
    df_sim_mode_share['mode'] = df_sim_mode_share['mode'].str.replace('_', ' ').str.title()

    if read_SynPop:
        df_synt_mode_share = df_synt_mode_share[~df_synt_mode_share['mode'].isin(modes_to_remove)]
        df_synt_mode_share['mode'] = df_synt_mode_share['mode'].str.replace('_', ' ').str.title()

    df_sim_mode_share.rename(columns={'trav_time': 'travel_time'}, inplace=True)
    if read_SynPop:
        df_synt_mode_share['travel_time'] = pd.to_timedelta(df_synt_mode_share['travel_time']).dt.total_seconds()
    df_sim_mode_share['travel_time'] = pd.to_timedelta(df_sim_mode_share['travel_time']).dt.total_seconds()

    df_mic_mode_share['weighted__distance'] = df_mic_mode_share['distance'] * df_mic_mode_share['household_weight']

    # ---- DISTANCE CALCULATION ---- #
    def compute_percentage(df, group_col, value_col):
        df = df.groupby(group_col)[value_col].sum().reset_index()
        df.columns = ['Mode', f'Total {value_col.title()}']
        total = df[f'Total {value_col.title()}'].sum()
        df['Percentage'] = (df[f'Total {value_col.title()}'] / total) * 100
        return df

    mode_share_distance_mic = compute_percentage(df_mic_mode_share, 'mode', 'distance')
    mode_share_weighted_distance_mic = compute_percentage(df_mic_mode_share, 'mode', 'weighted__distance')
    if read_SynPop:
        mode_share_distance_synt = compute_percentage(df_synt_mode_share, 'mode', 'distance')

    df_sim_mode_share.rename(columns={'traveled_distance': 'distance'}, inplace=True)
    mode_share_distance_sim = compute_percentage(df_sim_mode_share, 'mode', 'distance')

    # ---- PLOT DISTANCE COMPARISON ---- #
    def plot_grouped_bar(dataframes, labels, title, filename, ylabel):
        modes = sorted(set.union(*[set(df['Mode']) for df in dataframes]))
        bar_width = 0.2
        x = range(len(modes))
        fig, ax = plt.subplots(figsize=(12, 6))

        for i, (df, label) in enumerate(zip(dataframes, labels)):
            y = [df[df['Mode'] == m]['Percentage'].values[0] if m in df['Mode'].values else 0 for m in modes]
            bar_positions = [p + bar_width * i for p in x]
            bars = ax.bar(bar_positions, y, width=bar_width, label=label)

            # Add percentage labels on top of bars
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


    distance_plots = [mode_share_weighted_distance_mic, mode_share_distance_mic, mode_share_distance_sim]
    labels = ['Microcensus Weighted', 'Microcensus Single', 'Simulation']
    if read_SynPop:
        distance_plots.append(mode_share_distance_synt)
        labels.append('Synthetic')

    mode_share_directory = os.path.join(plots_directory, 'mode_share')
    os.makedirs(mode_share_directory, exist_ok=True)

    plot_grouped_bar(
        distance_plots,
        labels,
        'Comparison of Mode Share Distribution - % of Total Distance',
        f"{mode_share_directory}\\Mode_share_by_Distance.png",
        'Percentage (%)'
    )
    logging.info(f"Mode share by distance figure saved.")

    # ---- TRAVEL TIME ---- #
    df_mic_mode_share['weighted_travel_time'] = df_mic_mode_share['travel_time'] * df_mic_mode_share['household_weight']
    mode_share_time_mic = compute_percentage(df_mic_mode_share, 'mode', 'travel_time')
    mode_share_weighted_time_mic = compute_percentage(df_mic_mode_share, 'mode', 'weighted_travel_time')
    if read_SynPop:
        mode_share_time_synt = compute_percentage(df_synt_mode_share, 'mode', 'travel_time')
    mode_share_time_sim = compute_percentage(df_sim_mode_share, 'mode', 'travel_time')

    # ---- PLOT TIME COMPARISON ---- #
    time_plots = [mode_share_weighted_time_mic, mode_share_time_mic, mode_share_time_sim]
    labels = ['Microcensus Weighted', 'Microcensus Single', 'Simulation']
    if read_SynPop:
        time_plots.append(mode_share_time_synt)
        labels.append('Synthetic')

    plot_grouped_bar(
        time_plots,
        labels,
        'Comparison of Mode Share Distribution - % of Total Travel Time',
        f"{mode_share_directory}\\Mode_share_by_Travel_Time.png",
        'Percentage (%)'
    )
    logging.info(f"Mode share by travel time figure saved.")

    # ---- TRIP COUNT COMPARISON ---- #

    # 1. Microcensus trip count (raw and weighted)
    mode_share_trips_mic_raw = df_mic_mode_share['mode'].value_counts(normalize=True).reset_index()
    mode_share_trips_mic_raw.columns = ['Mode', 'Percentage']
    mode_share_trips_mic_raw['Percentage'] *= 100

    mode_share_trips_mic_weighted = df_mic_mode_share.groupby('mode')['household_weight'].sum().reset_index()
    mode_share_trips_mic_weighted.columns = ['Mode', 'Weighted Count']
    total_weighted = mode_share_trips_mic_weighted['Weighted Count'].sum()
    mode_share_trips_mic_weighted['Percentage'] = (mode_share_trips_mic_weighted[
                                                       'Weighted Count'] / total_weighted) * 100
    mode_share_trips_mic_weighted = mode_share_trips_mic_weighted[['Mode', 'Percentage']]

    # 2. Simulation trip count
    mode_share_trips_sim = df_sim_mode_share['mode'].value_counts(normalize=True).reset_index()
    mode_share_trips_sim.columns = ['Mode', 'Percentage']
    mode_share_trips_sim['Percentage'] *= 100

    # 3. Synthetic (optional)
    if read_SynPop:
        mode_share_trips_synt = df_synt_mode_share['mode'].value_counts(normalize=True).reset_index()
        mode_share_trips_synt.columns = ['Mode', 'Percentage']
        mode_share_trips_synt['Percentage'] *= 100

    # Plot
    trip_plots = [mode_share_trips_mic_weighted, mode_share_trips_mic_raw, mode_share_trips_sim]
    labels = ['Microcensus Weighted', 'Microcensus Raw', 'Simulation']
    if read_SynPop:
        trip_plots.append(mode_share_trips_synt)
        labels.append('Synthetic')

    plot_grouped_bar(
        trip_plots,
        labels,
        'Comparison of Mode Share Distribution - % of Trips',
        f"{mode_share_directory}\\Mode_share_by_Trips.png",
        'Percentage (%)'
    )
    logging.info(f"Mode share by trip count figure saved.")


    # ---- SAVE CSVs ---- #
    def save_comparison_csv(*dfs, output_file):
        from functools import reduce
        merged = reduce(lambda left, right: pd.merge(left, right, on='Mode', how='outer'), dfs)
        merged = merged.round(2)
        merged.to_csv(output_file, index=False)


    # ---- SAVE CUSTOMIZED TIME CSV ---- #
    # Prepare individual columns with correct names
    mode_share_time_mic = mode_share_time_mic.rename(columns={'Percentage': 'Percentage Mic'})
    mode_share_weighted_time_mic = mode_share_weighted_time_mic.rename(
        columns={'Percentage': 'Percentage Mic Weighted'})
    mode_share_time_sim = mode_share_time_sim.rename(columns={
        'Percentage': 'Percentage Sim',
        'Total Travel_Time': 'Total Time Sim'  # This matches what compute_percentage created
    })

    # Handle synthetic
    if read_SynPop:
        mode_share_time_synt = mode_share_time_synt.rename(columns={'Percentage': 'Percentage Synt'})
    else:
        unique_modes = pd.concat([mode_share_time_mic['Mode'], mode_share_time_sim['Mode']]).unique()
        mode_share_time_synt = pd.DataFrame({
            'Mode': unique_modes,
            'Percentage Synt': [0.0] * len(unique_modes)
        })

    # Merge all into final DataFrame
    from functools import reduce

    dfs_to_merge = [
        mode_share_time_mic[['Mode', 'Percentage Mic']],
        mode_share_weighted_time_mic[['Mode', 'Percentage Mic Weighted']],
        mode_share_time_synt[['Mode', 'Percentage Synt']],
        mode_share_time_sim[['Mode', 'Total Time Sim', 'Percentage Sim']]
    ]

    merged_time = reduce(lambda left, right: pd.merge(left, right, on='Mode', how='outer'), dfs_to_merge)
    merged_time = merged_time.round(2)

    # Save
    merged_time.to_csv(f"{mode_share_directory}\\Mode_shares_time.csv", index=False)
    logging.info("Customized Mode_shares_time.csv saved successfully.")

    # ---- SAVE CUSTOMIZED DISTANCE CSV ---- #
    # Prepare individual columns with correct names
    mode_share_distance_mic = mode_share_distance_mic.rename(columns={'Percentage': 'Percentage Mic'})
    mode_share_weighted_distance_mic = mode_share_weighted_distance_mic.rename(
        columns={'Percentage': 'Percentage Mic Weighted'})
    mode_share_distance_sim = mode_share_distance_sim.rename(columns={
        'Percentage': 'Percentage Sim',
        'Total Distance': 'Total Distance Sim'
    })

    # If synthetic is active, rename and use real data; otherwise use zero-filled dataframe
    if read_SynPop:
        mode_share_distance_synt = mode_share_distance_synt.rename(columns={'Percentage': 'Percentage Synt'})
    else:
        # Create synthetic percentage = 0 dataframe for all modes in the other frames
        unique_modes = pd.concat([mode_share_distance_mic['Mode'], mode_share_distance_sim['Mode']]).unique()
        mode_share_distance_synt = pd.DataFrame({
            'Mode': unique_modes,
            'Percentage Synt': [0.0] * len(unique_modes)
        })

    # Merge all into final DataFrame
    from functools import reduce

    dfs_to_merge = [
        mode_share_distance_mic[['Mode', 'Percentage Mic']],
        mode_share_weighted_distance_mic[['Mode', 'Percentage Mic Weighted']],
        mode_share_distance_synt[['Mode', 'Percentage Synt']],
        mode_share_distance_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']]
    ]

    merged_distance = reduce(lambda left, right: pd.merge(left, right, on='Mode', how='outer'), dfs_to_merge)
    merged_distance = merged_distance.round(2)

    # Save
    merged_distance.to_csv(f"{mode_share_directory}\\Mode_shares_distance.csv", index=False)
    logging.info("Customized Mode_shares_distance.csv saved successfully.")

    # ---- SAVE CUSTOMIZED TRIP COUNT CSV ---- #

    # Step 1: Rename columns for Mic and Weighted
    mode_share_trips_mic_raw = mode_share_trips_mic_raw.rename(columns={'Percentage': 'Percentage Mic'})
    mode_share_trips_mic_weighted = mode_share_trips_mic_weighted.rename(
        columns={'Percentage': 'Percentage Mic Weighted'})

    # Step 2: Create trip counts for simulation
    mode_share_trips_sim_counts = df_sim_mode_share['mode'].value_counts().reset_index()
    mode_share_trips_sim_counts.columns = ['Mode', 'Total Trips Sim']

    mode_share_trips_sim = mode_share_trips_sim.rename(columns={'Percentage': 'Percentage Sim'})

    # Merge sim counts and percentages
    mode_share_trips_sim = pd.merge(mode_share_trips_sim_counts, mode_share_trips_sim, on='Mode', how='outer')

    # Step 3: Handle synthetic
    if read_SynPop:
        mode_share_trips_synt = mode_share_trips_synt.rename(columns={'Percentage': 'Percentage Synt'})
    else:
        unique_modes = pd.concat([mode_share_trips_mic_raw['Mode'], mode_share_trips_sim['Mode']]).unique()
        mode_share_trips_synt = pd.DataFrame({
            'Mode': unique_modes,
            'Percentage Synt': [0.0] * len(unique_modes)
        })

    # Final merge
    from functools import reduce

    dfs_to_merge = [
        mode_share_trips_mic_raw[['Mode', 'Percentage Mic']],
        mode_share_trips_mic_weighted[['Mode', 'Percentage Mic Weighted']],
        mode_share_trips_synt[['Mode', 'Percentage Synt']],
        mode_share_trips_sim[['Mode', 'Total Trips Sim', 'Percentage Sim']]
    ]

    merged_trips = reduce(lambda left, right: pd.merge(left, right, on='Mode', how='outer'), dfs_to_merge)
    merged_trips = merged_trips.round(2)

    # Save
    merged_trips.to_csv(f"{mode_share_directory}\\mode_shares_by_trip.csv", index=False)
    logging.info("Customized mode_shares_by_trip.csv saved successfully.")

    logging.info("Trip count comparison CSV saved.")

    logging.info("CSV comparison files saved successfully.")
