# Import necessary libraries
import matsim
import geopandas as gpd
from shapely.geometry import Point
from functions.commonFunctions import *
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    analysis_zone_path = os.path.join(data_path, analysis_zone_name)

    # Create directory for the zone
    # scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    # Read the XML data with a matsim library
    try:
        output_trips_sim = pd.read_csv(os.path.join(output_folder_path, "output_trips.csv"), sep=';', low_memory=False, encoding='utf-8', dtype=str)
        logging.info("Output Trips data loaded successfully")
    except Exception as e:
        logging.error("Error loading network data: " + str(e))
        sys.exit()

    # Load geographic data from a shapefile
    shapefile_path = os.path.join(analysis_zone_path,
                                  f"ShapeFiles\\{shapeFileName}")
    gdf = gpd.read_file(shapefile_path, engine="pyogrio")

    area_polygon = gdf.iloc[0]['geometry']
    logging.info("Shapefile loaded successfully and area_polygon created successfully")

    # Create Point geometries for origin and destination
    output_trips_sim['origin_point'] = output_trips_sim.apply(lambda row: Point(row['start_x'], row['start_y']), axis=1)
    output_trips_sim['destination_point'] = output_trips_sim.apply(lambda row: Point(row['end_x'], row['end_y']), axis=1)
    logging.info("Origin and destination points created successfully")

    # First convert coordinates to float
    output_trips_sim['start_x'] = output_trips_sim['start_x'].astype(float)
    output_trips_sim['start_y'] = output_trips_sim['start_y'].astype(float)
    output_trips_sim['end_x'] = output_trips_sim['end_x'].astype(float)
    output_trips_sim['end_y'] = output_trips_sim['end_y'].astype(float)
    logging.info("Coordinates converted to float successfully")

    # Create origin and destination GeoSeries
    origin_points = gpd.GeoSeries(gpd.points_from_xy(output_trips_sim['start_x'], output_trips_sim['start_y']),
                                  crs=gdf.crs)
    destination_points = gpd.GeoSeries(gpd.points_from_xy(output_trips_sim['end_x'], output_trips_sim['end_y']),
                                       crs=gdf.crs)
    logging.info("Origin and destination GeoSeries created successfully")

    # Use vectorized 'within'
    mask_origin_inside = origin_points.within(area_polygon)
    mask_destination_inside = destination_points.within(area_polygon)
    logging.info("Masks created successfully")

    # Filtered dataframe (O AND D inside)
    filtered_trips_inside = output_trips_sim[mask_origin_inside & mask_destination_inside]
    logging.info("Trips filtered successfully based on the shapefile polygon successfully")

    # Filtered dataframe (O OR D inside)
    filtered_trips_inside_outside = output_trips_sim[mask_origin_inside | mask_destination_inside]
    logging.info("Trips filtered successfully based on the shapefile polygon successfully")

    rest_of_trips = output_trips_sim.drop(filtered_trips_inside.index)

    # The ids of the people who have trips inside the area
    ids_inside = set(filtered_trips_inside['person'])

    # The ids of the people who have trips outside the area
    ids_rest = set(rest_of_trips['person'])

    # The ids of the people who have trips inside the area but not outside
    unique_ids = ids_inside.difference(ids_rest)

    filtered_trips_inside.to_csv(f'{pre_processed_data_path}\\trips_inside_O_and_D_sim.csv', index=False)

    filtered_trips_inside_outside.to_csv(f'{pre_processed_data_path}\\trips_inside_O_or_D_sim.csv', index=False)
    logging.info("Both Filtered trips saved successfully")

    plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
    df_persons_sim = plans_sim.persons
    logging.info("Output plans data loaded successfully")

    # Filter the population to include only those with trips inside the area
    population_with_trips_O_and_D = df_persons_sim[df_persons_sim['id'].isin(unique_ids)]
    logging.info("Population with trips inside the area filtered successfully")

    population_with_trips_O_and_D.to_csv(f'{pre_processed_data_path}\\population_with_trips_inside_O_and_D_sim.csv', index=False)

    # Filter the population to include only those with trips origin inside or destination inside the area
    population_with_trips_O_or_D = df_persons_sim[
        df_persons_sim['id'].isin(filtered_trips_inside_outside['person'])]
    logging.info("Population with trips inside the area filtered successfully")

    population_with_trips_O_or_D.to_csv(f'{pre_processed_data_path}\\population_with_trips_inside_O_or_D_sim.csv', index=False)

