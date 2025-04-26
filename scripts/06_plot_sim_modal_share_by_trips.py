# # Import necessary libraries
# import logging
# import json
# from functions.commonFunctions import *
# import pandas as pd
# import warnings
# from shapely.geometry import Point
# import geopandas as gpd
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# warnings.filterwarnings('ignore')
#
# if __name__ == '__main__':
#     setup_logging("06_plot_sim_modal_share_by_trips.log")
#
#     data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
#     logging.info(f"Reading config file from {data_path} path was successful.")
#
#     output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
#     output_trips_path: str = os.path.join(output_folder_path, "output_trips.csv")
#     # Load geographic data from a shapefile
#     analysis_zone_path = os.path.join(data_path, analysis_zone_name)
#     shapefile_path = os.path.join(analysis_zone_path, f"ShapeFiles\\Zones")
#     directory = os.getcwd()
#     output_plots_folder_name = sim_output_folder.split('\\')[-1]
#     parent_directory = os.path.dirname(directory)
#     plots_directory = os.path.join(parent_directory, f'plots\\plots_{output_plots_folder_name}')
#
#     zones = [
#         "01", "02", "03", "04", "05", "06", "07", "08", "09",
#         "10", "11", "12", "13", "14", "15", "16", "17", "18",
#         "19", "20", "21", "22", "23", "24", "25"
#     ]
#
#     # Read the output trips data
#     try:
#         df_trips = pd.read_csv(output_trips_path, sep=';')
#         logging.info("Output trips data loaded successfully")
#     except Exception as e:
#         logging.error("Error loading output trips data: " + str(e))
#         sys.exit()
#
#     filtered_df_trips = df_trips[['euclidean_distance', 'longest_distance_mode', 'start_x', 'start_y', 'end_x', 'end_y']]
#
#     filtered_df_trips.columns = ['distance', 'mode', 'start_x', 'start_y', 'end_x', 'end_y']
#
#     modes_to_remove = ['car_passenger', 'pt', 'walk', 'car', 'bike']
#     df_sim_mode_share_by_trips = filtered_df_trips[filtered_df_trips['mode'].isin(modes_to_remove)]
#
#     df_start = df_sim_mode_share_by_trips[['distance', 'mode', 'start_x', 'start_y']].rename(columns={'start_x': 'x', 'start_y': 'y'})
#     df_end = df_sim_mode_share_by_trips[['distance', 'mode', 'end_x', 'end_y']].rename(columns={'end_x': 'x', 'end_y': 'y'})
#
#     # Concatenating the start and end dataframes
#     df_duplicate_points_start_end = pd.concat([df_start, df_end], ignore_index=True)
#
#     df_duplicate_points_start_end['distance'] = (df_duplicate_points_start_end['distance'] / 2).astype(int)
#
#     # df_duplicate_points_start_end.to_csv(f'{output_folder_path}\\df_duplicate_points_start_end.csv', index=False)
#     df_duplicate_points_start_end['mode'] = df_duplicate_points_start_end['mode'].str.replace('_', ' ').str.title()
#     df_duplicate_points_start_end['x_y'] = df_duplicate_points_start_end.apply(lambda row: Point(row['x'], row['y']), axis=1)
#
#     arcgis_pro_dict = {}
#
#     for zone in zones:
#         for file in os.listdir(shapefile_path):
#             if file.startswith(zone):
#                 zone_shapefile_path = os.path.join(shapefile_path, file, f"{file}.shp")
#                 gdf = gpd.read_file(zone_shapefile_path, engine="pyogrio")
#                 gdf = gdf.to_crs(epsg=2056)
#
#                 area_polygon = gdf.iloc[0]['geometry']
#
#                 filtered_df_sim_mode_share = df_duplicate_points_start_end[
#                     df_duplicate_points_start_end['x_y'].apply(lambda point: point.within(area_polygon))
#                 ]
#
#                 filtered_df_sim_mode_share = filtered_df_sim_mode_share[
#                     'mode'].value_counts().reset_index().sort_values('mode')
#                 filtered_df_sim_mode_share.columns = ['Mode', 'Count']
#
#                 filtered_df_sim_mode_share['Percentage'] = (filtered_df_sim_mode_share['Count'] /
#                                                                 filtered_df_sim_mode_share['Count'].sum()) * 100
#
#                 filtered_df_sim_mode_share.columns = ['Mode', 'Count', 'Percentage']
#
#                 arcgis_pro_dict[file] = filtered_df_sim_mode_share
#
#     data_serializable = {key: df.round(2).to_dict(orient='records') for key, df in arcgis_pro_dict.items()}
#
#     with open(f"{plots_directory}\\sim_modal_share_trips.json", "w") as outfile:
#         json.dump(data_serializable, outfile, indent=4)
#
#
#
#
