# Import necessary libraries
import logging
from common import *
import pandas as pd
import warnings
import geopandas as gpd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    directory = os.getcwd()
    output_plots_folder_name = sim_output_folder.split('\\')[-1]
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{output_plots_folder_name}')
    if not os.path.exists(plots_directory):
        os.makedirs(plots_directory)

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)

    # Read the clean csv files
    df_trips_mic = pd.read_csv(f'{data_path_clean}\\trips_mic.csv')
    logging.info(f"Reading the df_trips_mic csv file was successful.")

    df_mic_mode_share = df_trips_mic[
        ['person_id', 'trip_id', 'purpose', 'departure_time', 'arrival_time', 'crowfly_distance', 'mode',
         'household_weight']]
    # convert 'trav_time_x' to 'travel_time'
    df_mic_mode_share.rename(columns={'crowfly_distance': 'distance'}, inplace=True)

    df_mic_mode_share['travel_time'] = (pd.to_datetime(df_mic_mode_share['arrival_time']) - pd.to_datetime(
        df_mic_mode_share['departure_time'])).dt.total_seconds()

    df_synt_mode_share = pd.read_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_synt.csv')
    df_sim_mode_share = pd.read_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_sim.csv')

    modes_to_remove = ['truck', 'outside']

    df_synt_mode_share = df_synt_mode_share[~df_synt_mode_share['mode'].isin(modes_to_remove)]
    df_sim_mode_share = df_sim_mode_share[~df_sim_mode_share['mode'].isin(modes_to_remove)]

    # Capitalize and remove underscores from mode names for both dataframes
    df_mic_mode_share['mode'] = df_trips_mic['mode'].str.replace('_', ' ').str.title()
    df_synt_mode_share['mode'] = df_synt_mode_share['mode'].str.replace('_', ' ').str.title()
    df_sim_mode_share['mode'] = df_sim_mode_share['mode'].str.replace('_', ' ').str.title()

    logging.info(f"Modes of the all dataframes have been capitalized and underscores have been removed.")

    df_synt_mode_share['travel_time'] = pd.to_timedelta(df_synt_mode_share['travel_time']).dt.total_seconds()
    df_sim_mode_share['travel_time'] = pd.to_timedelta(df_sim_mode_share['travel_time']).dt.total_seconds()
    logging.info(f"Travel time has been converted to seconds.")

    # Multiply distance by household weight
    df_mic_mode_share['weighted__distance'] = df_mic_mode_share['distance'] * df_mic_mode_share['household_weight']
    logging.info(f"Distance has been multiplied by household weight.")

    mode_share_distance_mic = df_mic_mode_share.groupby('mode')[
        'distance'].sum().reset_index()
    mode_share_distance_mic.columns = ['Mode', 'Total Distance']

    mode_share_distance_mic['Percentage'] = (mode_share_distance_mic['Total Distance'] / mode_share_distance_mic[
        'Total Distance'].sum()) * 100

    mode_share_weighted_distance_mic = df_mic_mode_share.groupby('mode')[
        'weighted__distance'].sum().reset_index()
    mode_share_weighted_distance_mic.columns = ['Mode', 'Total Weighted Distance']

    mode_share_weighted_distance_mic['Percentage'] = (mode_share_weighted_distance_mic['Total Weighted Distance'] /
                                                      mode_share_weighted_distance_mic[
                                                          'Total Weighted Distance'].sum()) * 100

    mode_share_distance_synt = df_synt_mode_share.groupby('mode')[
        'distance'].sum().reset_index()
    mode_share_distance_synt.columns = ['Mode', 'Total Distance']
    mode_share_distance_synt['Percentage'] = (mode_share_distance_synt['Total Distance'] / mode_share_distance_synt[
        'Total Distance'].sum()) * 100

    mode_share_distance_sim = df_sim_mode_share.groupby('mode')[
        'distance'].sum().reset_index()
    mode_share_distance_sim.columns = ['Mode', 'Total Distance']
    mode_share_distance_sim['Percentage'] = (mode_share_distance_sim['Total Distance'] / mode_share_distance_sim[
        'Total Distance'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage weighted by distance
    fig.add_trace(
        go.Bar(
            x=mode_share_weighted_distance_mic['Mode'],
            y=mode_share_weighted_distance_mic['Percentage'],
            text=mode_share_weighted_distance_mic['Percentage'].round(1),
            textposition='outside',
            name='Microcensus Weighted',
            marker_color='yellow'
        )
    )

    # Add bars for microcensus modes percentage Single Leg
    fig.add_trace(go.Bar(
        x=mode_share_distance_mic['Mode'],
        y=mode_share_distance_mic['Percentage'],
        text=mode_share_distance_mic['Percentage'].round(1),
        textposition='outside',
        name='Microcensus Single',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_share_distance_synt['Mode'],
        y=mode_share_distance_synt['Percentage'],
        name='Synthetic',
        text=mode_share_distance_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_share_distance_sim['Mode'],
        y=mode_share_distance_sim['Percentage'],
        name='Simulation',
        text=mode_share_distance_sim['Percentage'].round(1),
        textposition='outside',
        marker_color='green'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage of Total Distance',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    mode_share_directory = os.path.join(plots_directory, 'mode_share')
    if not os.path.exists(mode_share_directory):
        os.makedirs(mode_share_directory)
    # Save the figure as an image with higher resolution
    fig.write_image(f"{mode_share_directory}\\Mode_share_by_Distance.png", scale=4)
    logging.info(f"Mode share by distance figure has been saved successfully.")

    df_mic_mode_share['weighted_travel_time'] = df_mic_mode_share['travel_time'] * df_mic_mode_share['household_weight']
    logging.info(f"Travel time has been multiplied by household weight.")

    mode_share_time_mic = df_mic_mode_share.groupby('mode')[
        'travel_time'].sum().reset_index()
    mode_share_time_mic.columns = ['Mode', 'Total Travel Time']
    mode_share_time_mic['Percentage'] = (mode_share_time_mic['Total Travel Time'] / mode_share_time_mic[
        'Total Travel Time'].sum()) * 100

    mode_share_weighted_time_mic = df_mic_mode_share.groupby('mode')[
        'weighted_travel_time'].sum().reset_index()

    mode_share_weighted_time_mic.columns = ['Mode', 'Total Weighted Travel Time']

    mode_share_weighted_time_mic['Percentage'] = (mode_share_weighted_time_mic['Total Weighted Travel Time'] /
                                                  mode_share_weighted_time_mic[
                                                      'Total Weighted Travel Time'].sum()) * 100

    mode_share_time_synt = df_synt_mode_share.groupby('mode')[
        'travel_time'].sum().reset_index()
    mode_share_time_synt.columns = ['Mode', 'Total Travel Time']
    mode_share_time_synt['Percentage'] = (mode_share_time_synt['Total Travel Time'] / mode_share_time_synt[
        'Total Travel Time'].sum()) * 100

    mode_share_time_sim = df_sim_mode_share.groupby('mode')[
        'travel_time'].sum().reset_index()
    mode_share_time_sim.columns = ['Mode', 'Total Travel Time']
    mode_share_time_sim['Percentage'] = (mode_share_time_sim['Total Travel Time'] / mode_share_time_sim[
        'Total Travel Time'].sum()) * 100

    # Create a figure with subplots
    fig = go.Figure()

    # Add bars for microcensus modes percentage weighted by travel time
    fig.add_trace(go.Bar(
        x=mode_share_weighted_time_mic['Mode'],
        y=mode_share_weighted_time_mic['Percentage'],
        text=mode_share_weighted_time_mic['Percentage'].round(1),
        textposition='outside',
        name='Microcensus Weighted',
        marker_color='yellow'
    ))

    # Add bars for microcensus modes percentage Single Leg
    fig.add_trace(go.Bar(
        x=mode_share_time_mic['Mode'],
        y=mode_share_time_mic['Percentage'],
        text=mode_share_time_mic['Percentage'].round(1),
        textposition='outside',
        name='Microcensus Single',
        marker_color='blue'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_share_time_synt['Mode'],
        y=mode_share_time_synt['Percentage'],
        name='Synthetic',
        text=mode_share_time_synt['Percentage'].round(1),
        textposition='outside',
        marker_color='red'
    ))

    # Add bars for synthetic legs modes percentage
    fig.add_trace(go.Bar(
        x=mode_share_time_sim['Mode'],
        y=mode_share_time_sim['Percentage'],
        name='Simulation',
        text=mode_share_time_sim['Percentage'].round(1),
        textposition='outside',
        marker_color='green'
    ))

    # Update the layout for a grouped bar chart
    fig.update_layout(
        barmode='group',
        title='Comparison of Mode Share Distribution - Percentage of Total Travel Time',
        xaxis_title='Mode of Transportation',
        yaxis_title='Percentage (%)',
        legend_title='Dataset',
        width=1200,
        height=600
    )

    # Show the figure
    # fig.show()

    # Save the figure as an image with higher resolution
    fig.write_image(f"{mode_share_directory}\\Mode_share_by_Travel_Time.png", scale=4)
    logging.info(f"Mode share by travel time figure has been saved successfully.")
    mode_share_time_mic.columns = ['Mode', 'Total Travel Time Microcensus Single', 'Percentage Microcensus Single']
    mode_share_weighted_time_mic.columns = ['Mode', 'Total Weighted Travel Time Microcensus Weighted',
                                            'Percentage Weighted Microcensus']
    mode_share_time_sim.columns = ['Mode', 'Total Travel Time Simulation', 'Percentage Simulation']
    mode_share_time_synt.columns = ['Mode', 'Total Travel Time Synthetic', 'Percentage Synthetic']

    mode_share_comparison_time = mode_share_time_mic.merge(mode_share_weighted_time_mic, on='Mode', how='outer').merge(
        mode_share_time_sim, on='Mode',
        how='outer').merge(mode_share_time_synt, on='Mode', how='outer')

    # Time is in seconds
    mode_share_comparison_time.columns = ['Mode', 'Total Travel Time Microcensus', 'Percentage Microcensus',
                                          'Total Weighted Travel Time Microcensus', 'Percentage Weighted Microcensus',
                                          'Total Travel Time Simulation', 'Percentage Simulation',
                                          'Total Travel Time Synthetic', 'Percentage Synthetic']

    mode_share_comparison_time = mode_share_comparison_time.round(2)
    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    mode_share_comparison_time.to_csv(f"{mode_share_directory}\\Mode_share_time_comparison.csv", index=False)
    logging.info(f"Mode share comparison csv file has been saved successfully.")

    mode_share_distance_mic.columns = ['Mode', 'Total Distance Microcensus Single', 'Percentage Microcensus Single']
    mode_share_weighted_distance_mic.columns = ['Mode', 'Total Weighted Distance Microcensus',
                                                'Percentage Weighted Microcensus']
    mode_share_distance_sim.columns = ['Mode', 'Total Distance Simulation', 'Percentage Simulation']
    mode_share_distance_synt.columns = ['Mode', 'Total Distance Synthetic', 'Percentage Synthetic']

    mode_share_comparison_distance = mode_share_distance_mic.merge(mode_share_weighted_distance_mic, on='Mode',
                                                                   how='outer').merge(
        mode_share_distance_sim, on='Mode',
        how='outer').merge(mode_share_distance_synt, on='Mode', how='outer')

    # Distance is in meters
    mode_share_comparison_distance.columns = ['Mode', 'Total Distance Microcensus', 'Percentage Microcensus',
                                              'Total Weighted Distance Microcensus', 'Percentage Weighted Microcensus',
                                              'Total Distance Simulation', 'Percentage Simulation',
                                              'Total Distance Synthetic', 'Percentage Synthetic']

    mode_share_comparison_distance = mode_share_comparison_distance.round(2)

    mode_share_comparison_distance.to_csv(f"{mode_share_directory}\\Mode_share_distance_comparison.csv",
                                          index=False)
    logging.info(f"Mode share comparison distance csv file has been saved successfully.")

