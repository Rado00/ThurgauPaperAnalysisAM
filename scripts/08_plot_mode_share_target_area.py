# Import necessary libraries
from random import sample
import warnings
import matsim
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pandas as pd
from functools import reduce
from functions.commonFunctions import *

pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
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
    bar_width = 0.12
    x = range(len(modes))
    fig, ax = plt.subplots(figsize=(15, 6))

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
        modes_to_exclude = ['Outside', 'outside']
    return df[~df[mode_col].isin(modes_to_exclude)].copy()


def load_and_prepare_data(file_path, target_area_gdf, both_in, x_col, y_col, mode_col='mode', modes_to_exclude=None):
    df = pd.read_csv(file_path)
    if mode_col in df.columns:
        df[mode_col] = df[mode_col].astype(str).str.replace('_', ' ').str.title()
        df = filter_out_modes(df, mode_col, modes_to_exclude)

    if all(col in df.columns for col in ['origin_x', 'origin_y', 'destination_x', 'destination_y', 'start_x', 'start_y', 'end_x', 'end_y']):
        if 'origin_x' in df.columns:
            gdf_origin = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['origin_x'], df['origin_y']), crs=target_area_gdf.crs)
            gdf_dest = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['destination_x'], df['destination_y']), crs=target_area_gdf.crs)
        else:
            gdf_origin = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['start_x'], df['start_y']), crs=target_area_gdf.crs)
            gdf_dest = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['end_x'], df['end_y']), crs=target_area_gdf.crs)
        origin_within = gdf_origin.geometry.within(target_area_gdf.unary_union)
        dest_within = gdf_dest.geometry.within(target_area_gdf.unary_union)
        if both_in:
            df = df[origin_within & dest_within]
        else:
            df = df[origin_within | dest_within]

    return df

# Calculate weighted mean and weighted std correctly
def weighted_mean(group):
    return (group['crowfly_distance'] * group['household_weight']).sum() / group['household_weight'].sum()

def weighted_std(group):
    w_mean = weighted_mean(group)
    variance = ((group['household_weight'] * (group['crowfly_distance'] - w_mean) ** 2).sum() /
                group['household_weight'].sum())
    return np.sqrt(variance)
    
    
def main():
    setup_logging(get_log_filename())
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots", f"plots_{os.path.basename(sim_output_folder)}")
    mode_share_directory = os.path.join(plots_directory, 'outputs_mode_share')
    os.makedirs(mode_share_directory, exist_ok=True)

    shape_path = os.path.join(data_path, "Paper2_ShapeFiles_CH1903+_LV95_easyNames", target_area)
    target_area = gpd.read_file(shape_path)

    df_mic_origin_or_destination = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_mic.csv"), target_area, False, 'start_coor_x', 'start_coor_y')
    df_mic_origin_and_destination = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_mic.csv"), target_area, True, 'start_coor_x', 'start_coor_y')
    df_sim_origin_or_destination = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_sim.csv"), target_area, False, 'start_x', 'start_y')
    df_sim_origin_and_destination = load_and_prepare_data(os.path.join(data_path_clean, "trips_all_activities_inside_sim.csv"), target_area, True, 'start_x', 'start_y')

    if read_SynPop:
        df_synt = load_and_prepare_data(os.path.join(data_path_clean, "travel_time_distance_mode_synt.csv"), target_area, False, 'start_coor_x', 'start_coor_y')
    
    df_sim_origin_or_destination = filter_out_modes(df_sim_origin_or_destination, 'mode')
    df_sim_origin_and_destination = filter_out_modes(df_sim_origin_and_destination, 'mode')

    if read_SynPop:
        df_synt = filter_out_modes(df_synt, 'mode')

    

    if read_SynPop:
        dist_synt = compute_percentage(df_synt, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': df_sim_origin_or_destination['Mode'], 'Percentage Synt': [0.0]*len(df_sim_origin_or_destination)})
    
    if 'household_weight' in df_mic_origin_or_destination.columns:
        df_mic_origin_or_destination['weighted_distance'] = df_mic_origin_or_destination['crowfly_distance'] * df_mic_origin_or_destination['household_weight']
    
    if 'household_weight' in df_mic_origin_or_destination.columns:
        df_mic_origin_and_destination['weighted_distance'] = df_mic_origin_and_destination['crowfly_distance'] * df_mic_origin_and_destination['household_weight']
        
    dist_mic_origin_or_destination = compute_percentage(df_mic_origin_or_destination, 'mode', 'crowfly_distance').rename(columns={'Percentage Crowfly_Distance': 'Percentage Mic OR'})
    dist_mic_wt_origin_or_destination = compute_percentage(df_mic_origin_or_destination, 'mode', 'weighted_distance').rename(columns={'Percentage Weighted_Distance': 'Percentage Mic Weighted OR'})

    dist_mic_origin_and_destination = compute_percentage(df_mic_origin_and_destination, 'mode', 'crowfly_distance').rename(columns={'Percentage Crowfly_Distance': 'Percentage Mic AND'})
    dist_mic_wt_origin_and_destination = compute_percentage(df_mic_origin_and_destination, 'mode', 'weighted_distance').rename(columns={'Percentage Weighted_Distance': 'Percentage Mic Weighted AND'})

    dist_sim_origin_or_destination = compute_percentage(df_sim_origin_or_destination, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Sim OR', 'Total Distance': 'Total Distance Sim OR'})
    dist_sim_origin_and_destination = compute_percentage(df_sim_origin_and_destination, 'mode', 'distance').rename(columns={'Percentage Distance': 'Percentage Sim AND', 'Total Distance': 'Total Distance Sim AND'})

    average_distance_by_mode_mic_wt_origin_or_destination = df_mic_origin_or_destination.groupby('mode').apply(
        lambda x: pd.Series({
            'Average Distance Mic WT OR': weighted_mean(x),
            'STD Distance Mic WT OR': weighted_std(x)
        }),
        include_groups=False
    ).reset_index()
    
    # Rename the 'mode' column to 'Mode' to match other dataframes
    average_distance_by_mode_mic_wt_origin_or_destination.rename(columns={'mode': 'Mode'}, inplace=True)
    
    average_distance_by_mode_mic_wt_origin_and_destination = df_mic_origin_and_destination.groupby('mode').apply(
        lambda x: pd.Series({
            'Average Distance Mic WT AND': weighted_mean(x),
            'STD Distance Mic WT AND': weighted_std(x)
        }),
        include_groups=False
    ).reset_index()
    # Rename the 'mode' column to 'Mode' to match other dataframes
    average_distance_by_mode_mic_wt_origin_and_destination.rename(columns={'mode': 'Mode'}, inplace=True)
    
    average_distance_by_mode_sim_origin_or_destination = df_sim_origin_or_destination.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_sim_origin_or_destination.columns = ['Mode', 'Average Distance Sim OR', 'STD Distance Sim OR']
    
    average_distance_by_mode_sim_origin_and_destination = df_sim_origin_and_destination.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
    average_distance_by_mode_sim_origin_and_destination.columns = ['Mode', 'Average Distance Sim AND', 'STD Distance Sim AND']
    
    if read_SynPop:
        average_distance_by_mode_synt = df_synt.groupby('mode')['distance'].agg(['mean', 'std']).reset_index()
        average_distance_by_mode_synt.columns = ['Mode', 'Average Distance Synt', 'STD Distance Synt']
    
    plot_grouped_bar([dist_mic_wt_origin_or_destination, dist_mic_origin_or_destination, dist_mic_wt_origin_and_destination, dist_mic_origin_and_destination, 
                      dist_sim_origin_or_destination, dist_sim_origin_and_destination, dist_synt] if read_SynPop 
                     else [dist_mic_wt_origin_or_destination, dist_mic_origin_or_destination, dist_mic_wt_origin_and_destination, dist_mic_origin_and_destination, dist_sim_origin_or_destination, dist_sim_origin_and_destination],
                     ['Microcensus Weighted OR', 'Microcensus Single OR', 'Microcensus Weighted AND', 'Microcensus Single AND', 
                      'Simulation Origin or Destination', 'Simulation Origin and Destination', 'Synthetic'] if read_SynPop 
                     else ['Microcensus Weighted OR', 'Microcensus Single OR', 'Microcensus Weighted AND', 'Microcensus Single AND', 'Simulation Origin or Destination', 
                           'Simulation Origin and Destination'],
                     'Comparison of Mode Share Distribution - % of Total Distance',
                     f"{mode_share_directory}/Mode_share_by_Distance_target_area.png", 'Percentage (%)')
    
    save_custom_csv(f"{mode_share_directory}/Mode_shares_distance_target_area.csv",
                    dist_mic_origin_or_destination[['Mode', 'Percentage Mic OR']],
                    dist_mic_wt_origin_or_destination[['Mode', 'Percentage Mic Weighted OR']],
                    dist_mic_origin_and_destination[['Mode', 'Percentage Mic AND']],
                    dist_mic_wt_origin_and_destination[['Mode', 'Percentage Mic Weighted AND']],
                    dist_sim_origin_or_destination[['Mode', 'Total Distance Sim OR', 'Percentage Sim OR']],
                    dist_sim_origin_and_destination[['Mode', 'Total Distance Sim AND', 'Percentage Sim AND']],
                    average_distance_by_mode_mic_wt_origin_or_destination[['Mode', 'Average Distance Mic WT OR', 'STD Distance Mic WT OR']],
                    average_distance_by_mode_mic_wt_origin_and_destination[['Mode', 'Average Distance Mic WT AND', 'STD Distance Mic WT AND']],
                    average_distance_by_mode_sim_origin_or_destination[['Mode', 'Average Distance Sim OR', 'STD Distance Sim OR']],
                    average_distance_by_mode_sim_origin_and_destination[['Mode', 'Average Distance Sim AND', 'STD Distance Sim AND']]
                    )
    
    if read_SynPop:
        save_custom_csv(f"{mode_share_directory}/Mode_shares_distance_target_area_target_area.csv",
                        dist_mic_origin_or_destination[['Mode', 'Percentage Mic OR']],
                        dist_mic_wt_origin_or_destination[['Mode', 'Percentage Mic Weighted OR']],
                        dist_mic_origin_and_destination[['Mode', 'Percentage Mic AND']],
                        dist_mic_wt_origin_and_destination[['Mode', 'Percentage Mic Weighted AND']],
                        dist_synt[['Mode', 'Percentage Synt']],
                        dist_sim_origin_or_destination[['Mode', 'Total Distance Sim OR', 'Percentage Sim OR']],
                        dist_sim_origin_and_destination[['Mode', 'Total Distance Sim AND', 'Percentage Sim AND']],
                        average_distance_by_mode_mic_wt_origin_or_destination[['Mode', 'Average Distance Mic WT OR', 'STD Distance Mic WT OR']],
                        average_distance_by_mode_mic_wt_origin_and_destination[['Mode', 'Average Distance Mic WT AND', 'STD Distance Mic WT AND']],
                        average_distance_by_mode_sim_origin_or_destination[['Mode', 'Average Distance Sim OR', 'STD Distance Sim OR']],
                        average_distance_by_mode_sim_origin_and_destination[['Mode', 'Average Distance Sim AND', 'STD Distance Sim AND']],
                        average_distance_by_mode_synt[['Mode', 'Average Distance Synt', 'STD Distance Synt']]
                        )
    
    df_sim_origin_or_destination['travel_time'] = pd.to_numeric(df_sim_origin_or_destination['travel_time'], errors='coerce')
    df_sim_origin_and_destination['travel_time'] = pd.to_numeric(df_sim_origin_and_destination['travel_time'], errors='coerce')
    if read_SynPop:
        df_synt['travel_time'] = pd.to_numeric(df_synt['travel_time'], errors='coerce')
    
    time_sim_origin_or_destination = compute_percentage(df_sim_origin_or_destination, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Sim OR', 'Total Travel_Time': 'Total Time Sim OR'})
    time_sim_origin_and_destination = compute_percentage(df_sim_origin_and_destination, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Sim AND', 'Total Travel_Time': 'Total Time Sim AND'})
    time_synt = compute_percentage(df_synt, 'mode', 'travel_time').rename(columns={'Percentage Travel_Time': 'Percentage Synt'}) if read_SynPop else pd.DataFrame({'Mode': time_sim_origin_or_destination['Mode'], 'Percentage Synt': [0.0]*len(time_sim_origin_or_destination)})
    
    save_custom_csv(f"{mode_share_directory}/Mode_shares_time_target_area.csv",
                    time_synt[['Mode', 'Percentage Synt']],
                    time_sim_origin_or_destination[['Mode', 'Total Time Sim OR', 'Percentage Sim OR']],
                    time_sim_origin_and_destination[['Mode', 'Total Time Sim AND', 'Percentage Sim AND']])
    
    trips_mic_raw_origin_or_destination = df_mic_origin_or_destination['mode'].value_counts(normalize=True).reset_index()
    trips_mic_raw_origin_or_destination.columns = ['Mode', 'Percentage Mic OR']
    trips_mic_raw_origin_or_destination['Percentage Mic OR'] *= 100
    
    trips_mic_raw_origin_and_destination = df_mic_origin_and_destination['mode'].value_counts(normalize=True).reset_index()
    trips_mic_raw_origin_and_destination.columns = ['Mode', 'Percentage Mic AND']
    trips_mic_raw_origin_and_destination['Percentage Mic AND'] *= 100
    
    trips_mic_wt_origin_or_destination = df_mic_origin_or_destination.groupby('mode')['household_weight'].sum().reset_index()
    trips_mic_wt_origin_or_destination.columns = ['Mode', 'Weighted Count OR']
    total_weighted_origin_or_destination = trips_mic_wt_origin_or_destination['Weighted Count OR'].sum()
    trips_mic_wt_origin_or_destination['Percentage Mic Weighted OR'] = (trips_mic_wt_origin_or_destination['Weighted Count OR'] / total_weighted_origin_or_destination) * 100
    trips_mic_wt_origin_or_destination = trips_mic_wt_origin_or_destination[['Mode', 'Percentage Mic Weighted OR']]
    
    trips_mic_wt_origin_and_destination = df_mic_origin_and_destination.groupby('mode')['household_weight'].sum().reset_index()
    trips_mic_wt_origin_and_destination.columns = ['Mode', 'Weighted Count AND']
    total_weighted_origin_and_destination = trips_mic_wt_origin_and_destination['Weighted Count AND'].sum()
    trips_mic_wt_origin_and_destination['Percentage Mic Weighted AND'] = (trips_mic_wt_origin_and_destination['Weighted Count AND'] / total_weighted_origin_and_destination) * 100
    trips_mic_wt_origin_and_destination = trips_mic_wt_origin_and_destination[['Mode', 'Percentage Mic Weighted AND']]
    
    trips_sim_counts_origin_or_destination = df_sim_origin_or_destination['mode'].value_counts().reset_index()
    trips_sim_counts_origin_or_destination.columns = ['Mode', 'Total Trips Sim OR']
    trips_sim_perc_origin_or_destination = df_sim_origin_or_destination['mode'].value_counts(normalize=True).reset_index()
    trips_sim_perc_origin_or_destination.columns = ['Mode', 'Percentage Sim OR']
    trips_sim_perc_origin_or_destination['Percentage Sim OR'] *= 100
    trips_sim_origin_or_destination = pd.merge(trips_sim_counts_origin_or_destination, trips_sim_perc_origin_or_destination, on='Mode', how='outer')
    
    trips_sim_counts_origin_and_destination = df_sim_origin_and_destination['mode'].value_counts().reset_index()
    trips_sim_counts_origin_and_destination.columns = ['Mode', 'Total Trips Sim AND']
    trips_sim_perc_origin_and_destination = df_sim_origin_and_destination['mode'].value_counts(normalize=True).reset_index()
    trips_sim_perc_origin_and_destination.columns = ['Mode', 'Percentage Sim AND']
    trips_sim_perc_origin_and_destination['Percentage Sim AND'] *= 100
    trips_sim_origin_and_destination = pd.merge(trips_sim_counts_origin_and_destination, trips_sim_perc_origin_and_destination, on='Mode', how='outer')
    
    if read_SynPop:
        trips_synt = df_synt['mode'].value_counts(normalize=True).reset_index()
        trips_synt.columns = ['Mode', 'Percentage Synt']
        trips_synt['Percentage Synt'] *= 100
    else:
        unique_modes = pd.concat([trips_mic_raw_origin_or_destination['Mode'], trips_sim_origin_or_destination['Mode']]).unique()
        trips_synt = pd.DataFrame({'Mode': unique_modes, 'Percentage Synt': [0.0] * len(unique_modes)})
    
    plot_grouped_bar([trips_mic_wt_origin_or_destination, trips_mic_raw_origin_or_destination, trips_mic_wt_origin_and_destination, trips_mic_raw_origin_and_destination, 
                      trips_sim_origin_or_destination, trips_sim_origin_and_destination, trips_synt] if read_SynPop 
                     else [trips_mic_wt_origin_or_destination, trips_mic_raw_origin_or_destination, trips_mic_wt_origin_and_destination, 
                           trips_mic_raw_origin_and_destination, trips_sim_origin_or_destination, trips_sim_origin_and_destination],
                     ['Microcensus Weighted OR', 'Microcensus Raw OR', 'Microcensus Weighted AND', 'Microcensus Raw AND',
                      'Simulation OR', 'Simulation AND', 'Synthetic'] if read_SynPop else ['Microcensus Weighted OR', 'Microcensus Raw OR', 'Microcensus Weighted AND', 'Microcensus Raw AND', 
                                                                                           'Simulation OR', 'Simulation AND'],
                     'Comparison of Mode Share Distribution - % of Trips',
                     f"{mode_share_directory}/Mode_share_by_Trips_target_area.png", 'Percentage (%)')
    
    save_custom_csv(f"{mode_share_directory}/Mode_shares_by_trip_target_area.csv",
                    trips_mic_raw_origin_or_destination[['Mode', 'Percentage Mic OR']],
                    trips_mic_wt_origin_or_destination[['Mode', 'Percentage Mic Weighted OR']],
                    trips_mic_raw_origin_and_destination[['Mode', 'Percentage Mic AND']],
                    trips_mic_wt_origin_and_destination[['Mode', 'Percentage Mic Weighted AND']],
                    trips_synt[['Mode', 'Percentage Synt']],
                    trips_sim_origin_or_destination[['Mode', 'Total Trips Sim OR', 'Percentage Sim OR']],
                    trips_sim_origin_and_destination[['Mode', 'Total Trips Sim AND', 'Percentage Sim AND']])
        


if __name__ == '__main__':
    main()
