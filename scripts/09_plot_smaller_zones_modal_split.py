import json
import gzip
import matsim
import pyproj
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point
from functions.commonFunctions import *
import warnings

pd.set_option('display.max_columns', 100)
pd.set_option('display.max_rows', 100)
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    setup_logging(get_log_filename())
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()
    analysis_zone_path = os.path.join(data_path, analysis_zone_name)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    directory = os.getcwd()
    output_plots_folder_name = os.path.basename(sim_output_folder)
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, "plots", f"plots_{output_plots_folder_name}")
    logging.info(f"Reading data from {output_folder_path}")

    # Load geographic data from a shapefile
    shapefile_path = os.path.join(analysis_zone_path, "ShapeFiles", "Zones")

    zones = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09",
        "10", "11", "12", "13", "14", "15", "16", "17", "18",
        "19", "20", "21", "22", "23", "24", "25"
    ]

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)
    df_synt_mode_share = pd.read_csv(os.path.join(pre_processed_data_path, "travel_time_distance_mode_synt.csv"))
    logging.info(
        f"Read {len(df_synt_mode_share)} rows from {os.path.join(pre_processed_data_path, 'travel_time_distance_mode_synt.csv')}")

    df_sim_mode_share = pd.read_csv(os.path.join(pre_processed_data_path, "travel_time_distance_mode_sim.csv"))
    logging.info(
        f"Read {len(df_sim_mode_share)} rows from {os.path.join(pre_processed_data_path, 'travel_time_distance_mode_sim.csv')}")

    modes_to_remove = ['truck', 'outside']

    df_synt_mode_share = df_synt_mode_share[~df_synt_mode_share['mode'].isin(modes_to_remove)]
    df_sim_mode_share = df_sim_mode_share[~df_sim_mode_share['mode'].isin(modes_to_remove)]
    logging.info(f"Removed {len(modes_to_remove)} modes from the data")

    df_synt_mode_share['mode'] = df_synt_mode_share['mode'].str.replace('_', ' ').str.title()
    df_sim_mode_share['mode'] = df_sim_mode_share['mode'].str.replace('_', ' ').str.title()
    logging.info(f"Renamed modes in the data")

    df_synt_mode_share['travel_time'] = pd.to_timedelta(df_synt_mode_share['travel_time']).dt.total_seconds()
    df_sim_mode_share['travel_time'] = pd.to_timedelta(df_sim_mode_share['travel_time']).dt.total_seconds()
    logging.info(f"Converted travel time to seconds")

    df_synt_mode_share['x_y'] = df_synt_mode_share.apply(lambda row: Point(row['x'], row['y']), axis=1)
    df_sim_mode_share['x_y'] = df_sim_mode_share.apply(lambda row: Point(row['start_x'], row['start_y']), axis=1)

    arcgis_pro_dict = {}

    for zone in zones:
        for file in os.listdir(shapefile_path):
            if file.startswith(zone):
                zone_shapefile_path = os.path.join(shapefile_path, file, f"{file}.shp")
                gdf = gpd.read_file(zone_shapefile_path, engine="pyogrio")
                gdf = gdf.to_crs(epsg=2056)

                area_polygon = gdf.iloc[0]['geometry']

                filtered_df_synt_mode_share = df_synt_mode_share[
                    df_synt_mode_share['x_y'].apply(lambda point: point.within(area_polygon))
                ]
                filtered_df_sim_mode_share = df_sim_mode_share[
                    df_sim_mode_share['x_y'].apply(lambda point: point.within(area_polygon))
                ]

                filtered_mode_share_distance_synt = filtered_df_synt_mode_share.groupby('mode')[
                    'distance'].sum().reset_index()
                filtered_mode_share_distance_synt.columns = ['Mode', 'Total Distance']
                filtered_mode_share_distance_synt['Percentage'] = (filtered_mode_share_distance_synt['Total Distance'] /
                                                                   filtered_mode_share_distance_synt[
                                                                       'Total Distance'].sum()) * 100

                filtered_mode_share_distance_sim = filtered_df_sim_mode_share.groupby('mode')[
                    'distance'].sum().reset_index()
                filtered_mode_share_distance_sim.columns = ['Mode', 'Total Distance']
                filtered_mode_share_distance_sim['Percentage'] = (filtered_mode_share_distance_sim['Total Distance'] /
                                                                  filtered_mode_share_distance_sim[
                                                                      'Total Distance'].sum()) * 100

                # Create a figure with subplots
                fig = go.Figure()

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_distance_synt['Mode'],
                    y=filtered_mode_share_distance_synt['Percentage'],
                    name='Synthetic',
                    text=filtered_mode_share_distance_synt['Percentage'].round(1),
                    textposition='outside',
                    marker_color='red'
                ))

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_distance_sim['Mode'],
                    y=filtered_mode_share_distance_sim['Percentage'],
                    name='Simulation',
                    text=filtered_mode_share_distance_sim['Percentage'].round(1),
                    textposition='outside',
                    marker_color='green'
                ))

                # Update the layout for a grouped bar chart
                fig.update_layout(
                    barmode='group',
                    title=f'Comparison of Mode Share Distribution - Percentage of Total Distance for Zone {file}',
                    xaxis_title='Mode of Transportation',
                    yaxis_title='Percentage (%)',
                    legend_title='Dataset',
                    width=1200,
                    height=600
                )

                mode_share_directory = os.path.join(plots_directory, 'mode_share', file)
                if not os.path.exists(mode_share_directory):
                    os.makedirs(mode_share_directory)

                fig.write_image(os.path.join(mode_share_directory, f"{file}_Mode_share_by_Distance.png"), scale=4)
                logging.info(f"Mode share by distance figure for zone {file} has been saved successfully.")

                filtered_mode_share_time_synt = filtered_df_synt_mode_share.groupby('mode')[
                    'travel_time'].sum().reset_index()
                filtered_mode_share_time_synt.columns = ['Mode', 'Total Travel Time']
                filtered_mode_share_time_synt['Percentage'] = (filtered_mode_share_time_synt['Total Travel Time'] /
                                                               filtered_mode_share_time_synt[
                                                                   'Total Travel Time'].sum()) * 100

                filtered_mode_share_time_sim = filtered_df_sim_mode_share.groupby('mode')[
                    'travel_time'].sum().reset_index()
                filtered_mode_share_time_sim.columns = ['Mode', 'Total Travel Time']
                filtered_mode_share_time_sim['Percentage'] = (filtered_mode_share_time_sim['Total Travel Time'] /
                                                              filtered_mode_share_time_sim[
                                                                  'Total Travel Time'].sum()) * 100

                # Create a figure with subplots
                fig = go.Figure()

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_time_synt['Mode'],
                    y=filtered_mode_share_time_synt['Percentage'],
                    name='Synthetic',
                    text=filtered_mode_share_time_synt['Percentage'].round(1),
                    textposition='outside',
                    marker_color='red'
                ))

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_time_sim['Mode'],
                    y=filtered_mode_share_time_sim['Percentage'],
                    name='Simulation',
                    text=filtered_mode_share_time_sim['Percentage'].round(1),
                    textposition='outside',
                    marker_color='green'
                ))

                # Update the layout for a grouped bar chart
                fig.update_layout(
                    barmode='group',
                    title=f'Comparison of Mode Share Distribution - Percentage of Total Travel Time for Zone {file}',
                    xaxis_title='Mode of Transportation',
                    yaxis_title='Percentage (%)',
                    legend_title='Dataset',
                    width=1200,
                    height=600
                )

                fig.write_image(os.path.join(mode_share_directory, f"{file}_Mode_share_by_Travel_Time.png"), scale=4)
                logging.info(f"Mode share by travel time figure for zone {file} has been saved successfully.")

                filtered_mode_share_number_synt = filtered_df_synt_mode_share[
                    'mode'].value_counts().reset_index().sort_values('mode')
                filtered_mode_share_number_sim = filtered_df_sim_mode_share[
                    'mode'].value_counts().reset_index().sort_values('mode')

                filtered_mode_share_number_synt.columns = ['Mode', 'Count']
                filtered_mode_share_number_sim.columns = ['Mode', 'Count']

                filtered_mode_share_number_synt['Percentage'] = (filtered_mode_share_number_synt['Count'] /
                                                                 filtered_mode_share_number_synt[
                                                                     'Count'].sum()) * 100
                filtered_mode_share_number_sim['Percentage'] = (filtered_mode_share_number_sim['Count'] /
                                                                filtered_mode_share_number_sim['Count'].sum()) * 100

                # Create a figure with subplots
                fig = go.Figure()

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_number_synt['Mode'],
                    y=filtered_mode_share_number_synt['Percentage'],
                    name='Synthetic',
                    text=filtered_mode_share_number_synt['Percentage'].round(1),
                    textposition='outside',
                    marker_color='red'
                ))

                # Add bars for synthetic legs modes percentage
                fig.add_trace(go.Bar(
                    x=filtered_mode_share_number_sim['Mode'],
                    y=filtered_mode_share_number_sim['Percentage'],
                    name='Simulation',
                    text=filtered_mode_share_number_sim['Percentage'].round(1),
                    textposition='outside',
                    marker_color='green'
                ))

                # Update the layout for a grouped bar chart
                fig.update_layout(
                    barmode='group',
                    title=f'Comparison of Mode Share Distribution - Percentage By Number for Zone {file}',
                    xaxis_title='Mode of Transportation',
                    yaxis_title='Percentage (%)',
                    legend_title='Dataset',
                    width=1200,
                    height=600
                )

                fig.write_image(os.path.join(mode_share_directory, f"{file}_Mode_share_by_Number.png"), scale=4)
                mode_share_comparison_time_csv = (
                    filtered_mode_share_distance_synt.merge(filtered_mode_share_distance_sim, on='Mode', how='outer',
                                                            suffixes=('_dist_synt', '_dist_sim'))
                    .merge(filtered_mode_share_time_synt, on='Mode', how='outer', suffixes=('_time_synt', '_time_sim'))
                    .merge(filtered_mode_share_time_sim, on='Mode', how='outer',
                           suffixes=('_time_sim_1', '_time_sim_2'))
                    .merge(filtered_mode_share_number_synt, on='Mode', how='outer', suffixes=('_num_synt', '_num_sim'))
                    .merge(filtered_mode_share_number_sim, on='Mode', how='outer',
                           suffixes=('_num_sim_1', '_num_sim_2'))
                )

                mode_share_comparison_time_csv.columns = ['Mode', 'Total Distance Synthetic',
                                                          'Percentage Distance Synthetic',
                                                          'Total Distance Simulation', 'Percentage Distance Simulation',
                                                          'Total Travel Time Synthetic',
                                                          'Percentage Travel Time Synthetic',
                                                          'Total Travel Time Simulation',
                                                          'Percentage Travel Time Simulation',
                                                          'Count Synthetic', 'Percentage Count Synthetic',
                                                          'Count Simulation', 'Percentage Count Simulation']
                mode_share_comparison_time_csv.to_csv(os.path.join(mode_share_directory, f"{file}_Mode_share_comparison.csv"), index=False)

                dataframe_arcgis_pro = mode_share_comparison_time_csv[
                    ['Mode', 'Percentage Distance Synthetic', 'Percentage Distance Simulation',
                     'Percentage Travel Time Synthetic', 'Percentage Travel Time Simulation',
                     'Percentage Count Synthetic', 'Percentage Count Simulation']]
                arcgis_pro_dict[file] = dataframe_arcgis_pro

    data_serializable = {key: df.round(2).to_dict(orient='records') for key, df in arcgis_pro_dict.items()}

    with open(os.path.join(plots_directory, "arcgis_pro_dict.json"), "w") as outfile:
        json.dump(data_serializable, outfile, indent=4)