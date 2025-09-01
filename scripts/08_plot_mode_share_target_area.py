import os
import logging
import pandas as pd
import warnings
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime
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


def load_and_prepare_data(file_path, target_area_gdf, x_col, y_col, mode_col='mode', modes_to_exclude=None):
    df = pd.read_csv(file_path)
    if mode_col in df.columns:
        df[mode_col] = df[mode_col].astype(str).str.replace('_', ' ').str.title()
        df = filter_out_modes(df, mode_col, modes_to_exclude)

    if all(col in df.columns for col in ['origin_x', 'origin_y', 'destination_x', 'destination_y']):
        gdf_origin = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['origin_x'], df['origin_y']), crs=target_area_gdf.crs)
        gdf_dest = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['destination_x'], df['destination_y']), crs=target_area_gdf.crs)
        origin_within = gdf_origin.geometry.within(target_area_gdf.unary_union)
        dest_within = gdf_dest.geometry.within(target_area_gdf.unary_union)
        df = df[origin_within | dest_within]

    elif x_col in df.columns and y_col in df.columns:
        gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x_col], df[y_col]), crs=target_area_gdf.crs)
        within = gdf_points.geometry.within(target_area_gdf.unary_union)
        df = df[within]

    return df


def main():
    setup_logging(get_log_filename())
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots", f"plots_{os.path.basename(sim_output_folder)}")
    mode_share_directory = os.path.join(plots_directory, 'mode_share')
    os.makedirs(mode_share_directory, exist_ok=True)

    shape_path = os.path.join(data_path, "Paper2_ShapeFiles_CH1903+_LV95_easyNames", target_area)
    target_area = gpd.read_file(shape_path)

    df_mic = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_mic.csv"), target_area, 'start_coor_x', 'start_coor_y')
    df_sim = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_sim.csv"), target_area, 'start_x', 'start_y')
    print("Number of microcensus trips after filtering:", len(df_mic))
    print("Number of unique persons in microcensus data:",
          df_mic['person_id'].nunique() if 'person_id' in df_mic.columns else 'person_id column not found')

    if read_SynPop:
        df_synt = load_and_prepare_data(os.path.join(data_path_clean, "travel_time_distance_mode_synt.csv"), target_area, 'start_coor_x', 'start_coor_y')

    if 'household_weight' in df_mic.columns:
        df_mic['weighted_distance'] = df_mic['crowfly_distance'] * df_mic['household_weight']

    df_sim = filter_out_modes(df_sim, 'mode')
    if read_SynPop:
        df_synt = filter_out_modes(df_synt, 'mode')

    dist_mic = compute_percentage(df_mic, 'mode', 'crowfly_distance').rename(columns={'Percentage Crowfly_Distance': 'Percentage Mic'})
    dist_mic_wt = compute_percentage(df_mic, 'mode', 'weighted_distance').rename(columns={'Percentage Weighted_Distance': 'Percentage Mic Weighted'})
    dist_sim = compute_percentage(df_sim, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Sim', 'Total Distance': 'Total Distance Sim'})
    dist_synt = compute_percentage(df_synt, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': dist_sim['Mode'], 'Percentage Synt': [0.0]*len(dist_sim)})

    average_distance_by_mode_mic_wt = df_mic.groupby('mode')['weighted_distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_mic_wt.columns = ['Mode', 'Average Distance Mic WT', 'STD Distance Mic WT']
    average_distance_by_mode_sim = df_sim.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_sim.columns = ['Mode', 'Average Distance Sim', 'STD Distance Sim']
    if read_SynPop:
        average_distance_by_mode_synt = df_synt.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
        average_distance_by_mode_synt.columns = ['Mode', 'Average Distance Synt', 'STD Distance Synt']

    plot_grouped_bar([dist_mic_wt, dist_mic, dist_sim, dist_synt] if read_SynPop else [dist_mic_wt, dist_mic, dist_sim],
                     ['Microcensus Weighted', 'Microcensus Single', 'Simulation', 'Synthetic'] if read_SynPop else ['Microcensus Weighted', 'Microcensus Single', 'Simulation'],
                     'Comparison of Mode Share Distribution - % of Total Distance',
                     f"{mode_share_directory}/Mode_share_by_Distance_target_area.png", 'Percentage (%)')

    # save_custom_csv(f"{mode_share_directory}/Mode_shares_distance_target_area.csv",
    #                 dist_mic[['Mode', 'Percentage Mic']],
    #                 dist_mic_wt[['Mode', 'Percentage Mic Weighted']],
    #                 dist_synt[['Mode', 'Percentage Synt']],
    #                 dist_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']])

    save_custom_csv(f"{mode_share_directory}/Mode_shares_distance_target_area.csv",
                    dist_mic[['Mode', 'Percentage Mic']],
                    dist_mic_wt[['Mode', 'Percentage Mic Weighted']],
                    dist_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']],
                    average_distance_by_mode_mic_wt[['Mode', 'Average Distance Mic WT', 'STD Distance Mic WT']],
                    average_distance_by_mode_sim[['Mode', 'Average Distance Sim', 'STD Distance Sim']]
                    )

    if read_SynPop:
        save_custom_csv(f"{mode_share_directory}/Mode_shares_distance_target_area_target_area.csv",
                        dist_mic[['Mode', 'Percentage Mic']],
                        dist_mic_wt[['Mode', 'Percentage Mic Weighted']],
                        dist_synt[['Mode', 'Percentage Synt']],
                        dist_sim[['Mode', 'Total Distance Sim', 'Percentage Sim']],
                        average_distance_by_mode_mic_wt[['Mode', 'Average Distance Mic WT', 'STD Distance Mic WT']],
                        average_distance_by_mode_sim[['Mode', 'Average Distance Sim', 'STD Distance Sim']],
                        average_distance_by_mode_synt[['Mode', 'Average Distance Synt', 'STD Distance Synt']]
                        )

    df_sim['travel_time'] = pd.to_numeric(df_sim['travel_time'], errors='coerce')
    if read_SynPop:
        df_synt['travel_time'] = pd.to_numeric(df_synt['travel_time'], errors='coerce')

    time_sim = compute_percentage(df_sim, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Sim', 'Total Travel_Time': 'Total Time Sim'})
    time_synt = compute_percentage(df_synt, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': time_sim['Mode'], 'Percentage Synt': [0.0]*len(time_sim)})

    save_custom_csv(f"{mode_share_directory}/Mode_shares_time_target_area.csv",
                    time_synt[['Mode', 'Percentage Synt']],
                    time_sim[['Mode', 'Total Time Sim', 'Percentage Sim']])

    trips_mic_raw = df_mic['mode'].value_counts(normalize=True).reset_index()
    trips_mic_raw.columns = ['Mode', 'Percentage Mic']
    trips_mic_raw['Percentage Mic'] *= 100

    trips_mic_wt = df_mic.groupby('mode')['household_weight'].sum().reset_index()
    trips_mic_wt.columns = ['Mode', 'Weighted Count']
    total_weighted = trips_mic_wt['Weighted Count'].sum()
    trips_mic_wt['Percentage Mic Weighted'] = (trips_mic_wt['Weighted Count'] / total_weighted) * 100
    trips_mic_wt = trips_mic_wt[['Mode', 'Percentage Mic Weighted']]

    trips_sim_counts = df_sim['mode'].value_counts().reset_index()
    trips_sim_counts.columns = ['Mode', 'Total Trips Sim']
    trips_sim_perc = df_sim['mode'].value_counts(normalize=True).reset_index()
    trips_sim_perc.columns = ['Mode', 'Percentage Sim']
    trips_sim_perc['Percentage Sim'] *= 100
    trips_sim = pd.merge(trips_sim_counts, trips_sim_perc, on='Mode', how='outer')

    if read_SynPop:
        trips_synt = df_synt['mode'].value_counts(normalize=True).reset_index()
        trips_synt.columns = ['Mode', 'Percentage Synt']
        trips_synt['Percentage Synt'] *= 100
    else:
        unique_modes = pd.concat([trips_mic_raw['Mode'], trips_sim['Mode']]).unique()
        trips_synt = pd.DataFrame({'Mode': unique_modes, 'Percentage Synt': [0.0] * len(unique_modes)})

    plot_grouped_bar([trips_mic_wt, trips_mic_raw, trips_sim, trips_synt] if read_SynPop else [trips_mic_wt, trips_mic_raw, trips_sim],
                     ['Microcensus Weighted', 'Microcensus Raw', 'Simulation', 'Synthetic'] if read_SynPop else ['Microcensus Weighted', 'Microcensus Raw', 'Simulation'],
                     'Comparison of Mode Share Distribution - % of Trips',
                     f"{mode_share_directory}/Mode_share_by_Trips_target_area.png", 'Percentage (%)')

    save_custom_csv(f"{mode_share_directory}/Mode_shares_by_trip_target_area.csv",
                    trips_mic_raw[['Mode', 'Percentage Mic']],
                    trips_mic_wt[['Mode', 'Percentage Mic Weighted']],
                    trips_synt[['Mode', 'Percentage Synt']],
                    trips_sim[['Mode', 'Total Trips Sim', 'Percentage Sim']])


if __name__ == '__main__':
    main()