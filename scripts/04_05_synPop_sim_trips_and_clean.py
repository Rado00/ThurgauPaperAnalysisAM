# =============================================================================
# 04_05_synPop_sim_trips_and_clean.py
# =============================================================================
# This script merges the functionality of:
#   - 04_synPop_sim_trips.py (geographic filtering of simulation trips)
#   - 05_1_generate_clean_csv_files.py (data cleaning and standardization)
#
# By combining these scripts, we avoid writing intermediate CSV files and
# re-reading them, which significantly improves performance.
#
# Output files (in clean_csv_folder):
#   - trips_all_activities_inside_sim.csv
#   - trips_at_least_one_activity_inside_sim.csv
#   - population_all_activities_inside_sim.csv
#   - population_at_least_one_activity_inside_sim.csv
#   - households_all_activities_inside_sim.csv
#   - activity_chains_sim.csv
#   - (if read_microcensus): trips_*_mic.csv, population_*_mic.csv, activity_chains_*_mic.csv
#   - (if read_SynPop): trips_synt.csv, legs_clean_synt.csv, population_clean_synth.csv, activity_chains_syn.csv
# =============================================================================

# Import necessary libraries
import matsim
import geopandas as gpd
from shapely.geometry import Point
from functions.commonFunctions import (
    setup_logging, get_log_filename, read_config, Config,
    clean_population_df, normalize_mode_column, normalize_type_column,
    normalize_sex_column, group_cars
)
import pandas as pd
import warnings
import os
import sys
import logging

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


# =============================================================================
# Helper Functions (from original 05_1)
# =============================================================================

def process_time_data(df):
    """
    Convert 'dep_time' and 'trav_time' from string to timedelta,
    then to seconds, and calculate 'arrival_time'.
    """
    df = df.copy()
    # Convert 'dep_time' from string to timedelta
    df['dep_time'] = pd.to_timedelta(df['dep_time'])
    # Convert 'dep_time' from timedelta to seconds
    df['departure_time'] = df['dep_time'].dt.total_seconds().astype(int)
    # Convert 'trav_time' from string to timedelta
    df['trav_time'] = pd.to_timedelta(df['trav_time'])
    # Convert 'trav_time' from timedelta to seconds
    df['trav_time_seconds'] = df['trav_time'].dt.total_seconds().astype(int)
    # Calculate 'arrival_time_seconds' by adding 'trav_time_seconds' to 'dep_time_seconds'
    df['arrival_time'] = df['departure_time'] + df['trav_time_seconds']
    return df


def map_person_id_to_activities(df_activities, df_persons, activity_type='Home'):
    """
    Map household IDs from df_persons to df_activities based on home coordinates and
    propagate the ID to other activities in the same plan.

    Args:
        df_activities: DataFrame containing activities with coordinates (x, y) and plan_id.
        df_persons: DataFrame containing person data with home coordinates (home_coordiante_x, home_coordiante_y) and hh_id.
        activity_type: The type of activity used to map person IDs (default 'Home').

    Returns:
        DataFrame with person_id mapped and propagated.
    """
    df_activities = df_activities.copy()
    df_persons = df_persons.copy()

    # Ensure coordinates are of type float64
    df_activities['x'] = pd.to_numeric(df_activities['x'], errors='coerce')
    df_activities['y'] = pd.to_numeric(df_activities['y'], errors='coerce')
    df_persons['home_x'] = pd.to_numeric(df_persons['home_coordiante_x'], errors='coerce')
    df_persons['home_y'] = pd.to_numeric(df_persons['home_coordiante_y'], errors='coerce')

    # Filter df_activities for rows where type is the specified activity type
    home_activities = df_activities[df_activities['type'] == activity_type]

    # Merge the household IDs from df_persons to home_activities based on coordinate match
    merged_home_activities = pd.merge(
        home_activities,
        df_persons[['person_id', 'home_x', 'home_y']],
        left_on=['x', 'y'],
        right_on=['home_x', 'home_y'],
        how='left'
    )

    # Create a mapping of plan_id to person_id
    if merged_home_activities['plan_id'].is_unique:
        plan_id_to_person_id = merged_home_activities.set_index('plan_id')['person_id']
    else:
        plan_id_to_person_id = merged_home_activities.groupby('plan_id')['person_id'].first()

    # Map the person_id to all activities in df_activities
    df_activities['person_id'] = df_activities['plan_id'].map(plan_id_to_person_id)

    # Propagate the person_id to other activities in the same plan
    df_activities['person_id'] = df_activities.groupby('plan_id')['person_id'].transform(lambda x: x.ffill().bfill())

    return df_activities


def process_activity_and_legs_data(df_activity, df_legs, values_to_remove, modes_to_remove):
    """
    Clean and filter synthetic activity and leg data.

    Steps:
    - Remove unwanted activity types and transport modes
    - Consolidate walk modes (access_walk, egress_walk -> walk)
    - Exclude incomplete or invalid travel plans
    - Remove persons left with only a single 'Home' activity (after cleaning)
      unless that was their original state

    Args:
        df_activity: DataFrame of activities
        df_legs: DataFrame of legs/trips
        values_to_remove: List of activity types to remove
        modes_to_remove: List of transport modes to remove

    Returns:
        Tuple of (filtered_activities_df, filtered_legs_df)
    """
    df_activity = df_activity.copy()
    df_legs = df_legs.copy()

    logging.info("The columns of df_activity are: " + ", ".join(df_activity.columns))
    # Identify persons with only one 'Home' activity initially
    if 'person_id' not in df_activity.columns and 'id' in df_activity.columns:
        df_activity['person_id'] = df_activity['id']
        logging.info("'person_id' column created from 'id' column in df_activity")

    initial_single_home = df_activity.groupby('person_id').filter(
        lambda x: len(x) == 1 and x['type'].eq('Home').all()
    )

    # Filter the activity DataFrame
    df_activity_filtered = df_activity[~df_activity['type'].isin(values_to_remove)]

    # Find all 'plan_id' values where 'type' is 'outside'
    plan_ids_to_remove = df_activity_filtered[df_activity_filtered['type'] == 'outside']['plan_id'].unique()

    # Filter out all rows with these 'plan_id' values
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['plan_id'].isin(plan_ids_to_remove)]

    # Additional filter to remove 'outside'
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['type'].isin(['outside'])]

    # Combine 'Access Walk' and 'Egress Walk' into 'Walk' in legs DataFrame
    logging.info("The columns of df_legs are: " + ", ".join(df_legs.columns))

    if 'main_mode' not in df_legs.columns and 'mode' in df_legs.columns:
        df_legs['main_mode'] = df_legs['mode']
        logging.info("'main_mode' column created from 'mode' column in df_legs")

    df_legs['main_mode'] = df_legs['main_mode'].replace({'access_walk': 'walk', 'egress_walk': 'walk'})
    logging.info("Combined 'access_walk' and 'egress_walk' into 'walk' in legs DataFrame")

    # Remove specified modes from the legs DataFrame
    df_legs_filtered = df_legs[~df_legs['main_mode'].isin(modes_to_remove)]

    # Identify persons who now only have one 'Home' activity
    final_single_home = df_activity_filtered.groupby('person_id').filter(
        lambda x: len(x) == 1 and x['type'].eq('Home').all()
    )
    logging.info('Identified persons with only one Home activity after cleaning')

    # Exclude persons who initially had only one 'Home' activity
    final_single_home = final_single_home[~final_single_home['person_id'].isin(initial_single_home['person_id'])]

    # Remove these persons from the filtered data
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['person_id'].isin(final_single_home['person_id'])]

    return df_activity_filtered, df_legs_filtered


def create_trips_dataframe(df_activity):
    """
    Create trips DataFrame from activity DataFrame.

    Each trip connects consecutive activities (based on consecutive IDs).

    Args:
        df_activity: DataFrame of activities

    Returns:
        DataFrame of trips with departure/arrival times and coordinates
    """
    new_trips = []

    for i in range(len(df_activity) - 1):
        current_row = df_activity.iloc[i]
        next_row = df_activity.iloc[i + 1]

        # Check if the IDs are consecutive
        if current_row['id'] + 1 == next_row['id']:
            new_trips.append({
                'trip_id': current_row['id'],
                'departure_time': current_row['end_time'],
                'arrival_time': next_row['start_time'],
                'start_coor_x': current_row['x'],
                'start_coor_y': current_row['y'],
                'ziel_coor_x': next_row['x'],
                'ziel_coor_y': next_row['y'],
            })

    return pd.DataFrame(new_trips)


def safe_convert_time(time_str):
    """
    Safely convert time string to datetime, floored to 30-minute bins.

    Args:
        time_str: Time string in format 'HH:MM:SS'

    Returns:
        time object floored to 30 minutes, or None if conversion fails
    """
    try:
        return pd.to_datetime(time_str, format='%H:%M:%S', errors='raise').floor('30T').time()
    except ValueError:
        return None


def create_activity_chain_mic(group):
    """Create activity chain string for microcensus data."""
    chain = '-'.join(
        ['H'] + [purpose[0] for purpose in group['purpose'].tolist()]
    )
    return pd.Series({'activity_chain': chain})


def create_activity_chain_syn(group):
    """Create activity chain string for synthetic/simulation data."""
    chain = '-'.join([purpose[0].upper() for purpose in group['type'].tolist()])
    return pd.Series({'activity_chain': chain})


def extract_just_personID_and_household_weight_from_hausalteCSV(path):
    """Extract person ID and household weight from microcensus households CSV."""
    df_mz_households = pd.read_csv(os.path.join(path, "microzensus", "haushalte.csv"), sep=",", encoding="latin1")
    df_mz_households["person_id"] = df_mz_households["HHNR"]
    df_mz_households["household_weight"] = df_mz_households["WM"]
    return df_mz_households[["person_id", "household_weight"]]


# =============================================================================
# Main Script
# =============================================================================

if __name__ == '__main__':
    setup_logging(get_log_filename())

    # =========================================================================
    # STEP 1: Load configuration
    # =========================================================================
    cfg = read_config(return_dataclass=True)
    logging.info(f"sample_for_debugging = {cfg.sample_for_debugging}, nrows = {cfg.nrows}")

    # Create output directories if they don't exist
    if not os.path.exists(cfg.pre_processed_data_path):
        os.makedirs(cfg.pre_processed_data_path)
    if not os.path.exists(cfg.data_path_clean):
        os.makedirs(cfg.data_path_clean)

    # =========================================================================
    # STEP 2: Load simulation output trips (from original script 04)
    # =========================================================================
    try:
        output_trips_sim = pd.read_csv(
            os.path.join(cfg.output_folder_path, "output_trips.csv.gz"),
            sep=';', low_memory=False, encoding='utf-8', dtype=str,
            compression='gzip', nrows=cfg.nrows
        )
        logging.info("Output Trips data loaded successfully")
    except Exception as e:
        logging.error("Error loading output_trips.csv.gz: " + str(e))
        sys.exit()

    # =========================================================================
    # STEP 3: Load shapefile for geographic filtering
    # =========================================================================
    gdf = gpd.read_file(cfg.shapefile_path, engine="pyogrio")
    logging.info(f"Shapefile loaded: {cfg.shapefile_path}")
    logging.info(f"Shapefile CRS: {gdf.crs}, number of features: {len(gdf)}")
    area_polygon = gdf.unary_union
    logging.info(f"Area polygon created using unary_union of all {len(gdf)} features")

    # =========================================================================
    # STEP 4: Convert coordinate columns to float and create geometry points
    # =========================================================================
    output_trips_sim['start_x'] = output_trips_sim['start_x'].astype(float)
    output_trips_sim['start_y'] = output_trips_sim['start_y'].astype(float)
    output_trips_sim['end_x'] = output_trips_sim['end_x'].astype(float)
    output_trips_sim['end_y'] = output_trips_sim['end_y'].astype(float)

    # Create Point geometries for origin and destination
    output_trips_sim['origin_point'] = gpd.points_from_xy(output_trips_sim['start_x'], output_trips_sim['start_y'])
    output_trips_sim['destination_point'] = gpd.points_from_xy(output_trips_sim['end_x'], output_trips_sim['end_y'])
    logging.info("Origin and destination points created successfully")

    # =========================================================================
    # STEP 5: Filter out unwanted modes (outside, truck)
    # =========================================================================
    output_trips_sim = output_trips_sim.query("main_mode not in ['outside', 'truck']").reset_index(drop=True)

    # Create origin and destination GeoSeries for spatial filtering
    origin_points = gpd.GeoSeries(
        gpd.points_from_xy(output_trips_sim['start_x'], output_trips_sim['start_y']),
        crs=gdf.crs
    )
    destination_points = gpd.GeoSeries(
        gpd.points_from_xy(output_trips_sim['end_x'], output_trips_sim['end_y']),
        crs=gdf.crs
    )
    logging.info("Origin and destination GeoSeries created successfully")

    # =========================================================================
    # STEP 6: Filter trips by geographic area (O AND D inside, O OR D inside)
    # =========================================================================
    try:
        # Filtered dataframe (O AND D inside)
        filtered_trips_inside = output_trips_sim[
            origin_points.within(area_polygon) &
            destination_points.within(area_polygon)
            ]
        logging.info(f"O and D Trips filtered: {len(filtered_trips_inside)} of {len(output_trips_sim)} trips retained")
    except Exception as e:
        logging.error("Error in filtering O and D Trips: " + str(e))
        sys.exit()

    try:
        # Filtered dataframe (O OR D inside)
        filtered_trips_inside_outside = output_trips_sim[
            origin_points.within(area_polygon) |
            destination_points.within(area_polygon)
            ]
        logging.info(f"O or D Trips filtered: {len(filtered_trips_inside_outside)} of {len(output_trips_sim)} trips retained")
    except Exception as e:
        logging.error("Error in filtering O or D Trips: " + str(e))
        sys.exit()

    try:
        # =========================================================================
        # STEP 7: Identify persons with all activities inside vs at least one inside
        # =========================================================================
        rest_of_trips = output_trips_sim.drop(filtered_trips_inside.index)

        # The ids of the people who have trips inside the area
        ids_inside = set(filtered_trips_inside['person'])
        # The ids of the people who have trips outside the area
        ids_rest = set(rest_of_trips['person'])
        # The ids of the people who have trips inside the area but not outside
        unique_ids = ids_inside.difference(ids_rest)

        # Save intermediate filtered trips (needed by other scripts)
        filtered_trips_inside.to_csv(os.path.join(cfg.pre_processed_data_path, "trips_inside_O_and_D_sim.csv"), index=False)
        filtered_trips_inside_outside.to_csv(os.path.join(cfg.pre_processed_data_path, "trips_inside_O_or_D_sim.csv"), index=False)
        logging.info("Both Filtered trips saved successfully")
    except Exception as e:
        logging.error("Error in filtering trips_inside_O_or_D_sim.csv: " + str(e))                                                                          
    try:
        # =========================================================================
        # STEP 8: Load simulation persons data
        # =========================================================================
        df_persons_sim = pd.read_csv(
            os.path.join(cfg.output_folder_path, "output_persons.csv.gz"),
            sep=';', low_memory=False, encoding='utf-8', dtype=str,
            compression='gzip', nrows=cfg.nrows
        )
        logging.info("Output persons data loaded successfully")

        df_persons_sim['home_coordiante_x'] = pd.to_numeric(df_persons_sim['home_coordiante_x'], errors='coerce')
        df_persons_sim['home_coordiante_y'] = pd.to_numeric(df_persons_sim['home_coordiante_y'], errors='coerce')

        # Remove rows with missing coordinates
        df_persons_sim = df_persons_sim.dropna(subset=['home_coordiante_x', 'home_coordiante_y'])

        # Create geometry from coordinates
        sim_geometry = [Point(xy) for xy in zip(df_persons_sim['home_coordiante_x'],
                                                df_persons_sim['home_coordiante_y'])]

        # Create GeoDataFrame from persons data
        sim_gdf_persons = gpd.GeoDataFrame(df_persons_sim, geometry=sim_geometry)

        sim_gdf_persons.crs = sim_gdf_persons.crs

        # Spatial join to filter points inside the polygon
        population_home_inside_sim = gpd.sjoin(sim_gdf_persons, gdf, how='inner', predicate='within')
        logging.info(f"The columns of the population_home_inside_sim are {population_home_inside_sim.columns}")

        df_population_home_inside_sim = clean_population_df(
            population_home_inside_sim, person_col='person', min_age=6
        )

        all_trips_population_home_inside = output_trips_sim[
            output_trips_sim['person'].isin(df_population_home_inside_sim['person_id'])
        ]

        filtered_trips_population_home_inside_sim = all_trips_population_home_inside[[
            "person", "start_link", "end_link", "dep_time", "trav_time", "euclidean_distance",
            "main_mode", "modes", "start_x", "start_y", "end_x", "end_y"
        ]].copy()

        df_population_home_inside_sim.to_csv(os.path.join(cfg.data_path_clean, "population_home_inside_sim.csv"),
                                             index=False)

        filtered_trips_population_home_inside_sim.to_csv(
            os.path.join(cfg.data_path_clean, "trips_population_home_inside_sim.csv"), index=False)

    except Exception as e:
        logging.error("Error in filtering population_home_inside_sim.csv: " + str(e))

    try:
        # =========================================================================
        # STEP 9: Filter population based on trip locations
        # =========================================================================
        # Population with ALL trips inside the area
        population_with_trips_O_and_D = df_persons_sim[df_persons_sim['person'].isin(unique_ids)]
        logging.info("Population with all trips inside the area filtered successfully")

        # Population with at least one trip inside the area
        population_with_trips_O_or_D = df_persons_sim[
            df_persons_sim['person'].isin(filtered_trips_inside_outside['person'])
        ]
        logging.info("Population with at least one trip inside filtered successfully")

    except Exception as e:
        logging.error("Error in filtering population_with_trips_O_or_D.csv: " + str(e))

    try:
        # =========================================================================
        # STEP 10: Create trip datasets for each population filter
        # =========================================================================
        # All trips for persons with ALL activities inside
        trips_all_activities_inside = output_trips_sim[
            output_trips_sim['person'].isin(population_with_trips_O_and_D['person'])
        ]

        # All trips for persons with at least one activity inside
        trips_at_least_one_activity_inside = output_trips_sim[
            output_trips_sim['person'].isin(population_with_trips_O_or_D['person'])
        ]

        # Save to pre-processed path (needed by other scripts)
        population_with_trips_O_and_D.to_csv(
            os.path.join(cfg.pre_processed_data_path, "population_all_activities_inside_sim.csv"), index=False
        )
        population_with_trips_O_or_D.to_csv(
            os.path.join(cfg.pre_processed_data_path, "population_at_least_one_activity_inside_sim.csv"), index=False
        )
        trips_all_activities_inside.to_csv(
            os.path.join(cfg.pre_processed_data_path, "trips_all_activities_inside_sim.csv"), index=False
        )
        trips_at_least_one_activity_inside.to_csv(
            os.path.join(cfg.pre_processed_data_path, "trips_at_least_one_activity_inside_sim.csv"), index=False
        )
        logging.info("Population and trips CSVs saved to pre-processed path")

    except Exception as e:
        logging.error("Error in filtering trips_at_least_one_activity_inside.csv: " + str(e))

    try:
        # =========================================================================
        # STEP 11: Load activity data (from original script 03 output)
        # =========================================================================
        try:
            df_activity_sim = pd.read_csv(
                os.path.join(cfg.pre_processed_data_path, "df_activity_sim.csv"), low_memory=False
            )
            logging.info("Activity data loaded successfully")
        except Exception as e:
            logging.error("Error reading df_activity_sim.csv: " + str(e))
            sys.exit()
    except Exception as e:
        logging.error("Error in filtering df_activity_sim.csv: " + str(e))

    try:
        # =========================================================================
        # STEP 12: Load optional synthetic population data
        # =========================================================================
        if cfg.read_SynPop:
            try:
                df_households_synt = pd.read_csv(os.path.join(cfg.pre_processed_data_path, "df_households_synt.csv"), low_memory=False)
                df_activity_synt = pd.read_csv(os.path.join(cfg.pre_processed_data_path, "df_activity_synt.csv"), low_memory=False)
                df_legs_synt = pd.read_csv(os.path.join(cfg.pre_processed_data_path, "df_legs_synt.csv"), low_memory=False)
                df_persons_synt = pd.read_csv(os.path.join(cfg.pre_processed_data_path, "df_persons_synt.csv"), low_memory=False)
                df_routes_synt = pd.read_csv(os.path.join(cfg.pre_processed_data_path, "df_routes_synt.csv"), low_memory=False)
                logging.info("Synthetic population data loaded successfully")
            except Exception as e:
                logging.error("Error reading synthetic population files: " + str(e))
                sys.exit()

        # =========================================================================
        # STEP 13: Load optional microcensus data
        # =========================================================================
        if cfg.read_microcensus:
            try:
                df_population_all_activities_inside_mic = pd.read_csv(
                    os.path.join(cfg.microcensus_path, "population_all_activities_inside_Mic.csv")
                )
                df_population_at_least_one_activity_inside_mic = pd.read_csv(
                    os.path.join(cfg.microcensus_path, "population_at_least_one_activity_inside_Mic.csv")
                )
                df_trips_all_activities_inside_mic = pd.read_csv(
                    os.path.join(cfg.microcensus_path, "trips_all_activities_inside_Mic.csv")
                )
                df_trips_at_least_one_activity_inside_mic = pd.read_csv(
                    os.path.join(cfg.microcensus_path, "trips_at_least_one_activity_inside_Mic.csv")
                )
                df_population_home_inside_mic = pd.read_csv(
                    os.path.join(cfg.microcensus_path, "population_home_inside_mic.csv"))
                df_trips_home_inside_mic = pd.read_csv(os.path.join(cfg.microcensus_path, "trips_home_inside_mic.csv"))
                logging.info("Microcensus data loaded successfully")
            except Exception as e:
                logging.error("Error reading microcensus files: " + str(e))
                sys.exit()
    except Exception as e:
        logging.error("Error reading microcensus files: " + str(e))

    try:
        # =========================================================================
        # STEP 14: Process time data for trips
        # =========================================================================
        # Keep references to DataFrames in memory (already loaded above)
        df_trips_all_activities_inside_sim = trips_all_activities_inside.copy()
        df_trips_at_least_one_activity_inside_sim = trips_at_least_one_activity_inside.copy()

        df_trips_all_activities_inside_sim = process_time_data(df_trips_all_activities_inside_sim)
        df_trips_at_least_one_activity_inside_sim = process_time_data(df_trips_at_least_one_activity_inside_sim)

        if cfg.read_SynPop:
            df_legs_synt = process_time_data(df_legs_synt)

        logging.info("Time data processed successfully")

        # =========================================================================
        # STEP 15: Clean population DataFrames (using common function)
        # =========================================================================
        # Use the common helper function instead of repeating code
        df_population_all_activities_inside_sim = clean_population_df(
            population_with_trips_O_and_D, person_col='person', min_age=6
        )
        df_population_at_least_one_activity_inside_sim = clean_population_df(
            population_with_trips_O_or_D, person_col='person', min_age=6
        )
    except Exception as e:
        logging.error("Error reading synthetic population files: " + str(e))

    if cfg.read_SynPop:
        df_persons_synt = df_persons_synt.rename(columns={'id': 'hh_id'})
        df_persons_synt = clean_population_df(df_persons_synt, person_col='hh_id', min_age=6)
        df_persons_synt = normalize_sex_column(df_persons_synt)

    logging.info("Population DataFrames cleaned successfully")

    # =========================================================================
    # STEP 16: Load and filter households
    # =========================================================================
    try:
        households_sim = matsim.household_reader(os.path.join(cfg.output_folder_path, "output_households.xml.gz"))
        df_households_sim = households_sim.households
        logging.info("output_households.xml.gz loaded successfully")
    except Exception as e:
        logging.error("Error loading output_households.xml.gz: " + str(e))
        sys.exit()

    try:
        # Set of relevant person_ids
        valid_person_ids = set(df_population_at_least_one_activity_inside_sim['person_id'].unique())

        # Filter households where at least one person is in valid_person_ids
        df_households_sim['members'] = df_households_sim['members'].apply(
            lambda x: eval(x) if isinstance(x, str) else x
        )
        df_households_sim_filtered = df_households_sim[
            df_households_sim['members'].apply(lambda members: any(pid in valid_person_ids for pid in members))
        ]
        df_households_sim_filtered.to_csv(
            os.path.join(cfg.data_path_clean, "households_all_activities_inside_sim.csv"), index=False
        )
        logging.info("Filtered households saved successfully")
    except Exception as e:
        logging.error("Error filtering households_all_activities_inside_sim.csv: " + str(e))

    try:
        # =========================================================================
        # STEP 17: Map person IDs to activities
        # =========================================================================
        df_activity_population_all_activities_inside_sim = map_person_id_to_activities(
            df_activity_sim, df_population_all_activities_inside_sim
        )

        if cfg.read_SynPop:
            df_activity_synt_filtered = map_person_id_to_activities(df_activity_synt, df_persons_synt)

        logging.info("Person IDs mapped to activities successfully")

        # =========================================================================
        # STEP 18: Process and filter activity/legs data
        # =========================================================================
        values_to_remove = ['freight_unloading', 'freight_loading', 'pt interaction']
        modes_to_remove = ['truck', 'outside']

        # Process simulation data
        # Note: Use df_activity_population_all_activities_inside_sim which has person_id mapped
        df_activity_population_all_activities_inside_sim_filtered, df_trips_all_activities_inside_sim_filtered = \
            process_activity_and_legs_data(
                df_activity_population_all_activities_inside_sim, df_trips_all_activities_inside_sim,
                values_to_remove, modes_to_remove
            )

        df_activity_population_all_activities_inside_sim = df_activity_population_all_activities_inside_sim_filtered
        df_activity_population_all_activities_inside_sim = normalize_type_column(
            df_activity_population_all_activities_inside_sim
        )
        logging.info("Activity DataFrame cleaned successfully")

        if cfg.read_SynPop:
            df_activity_synt_filtered, df_legs_synt_filtered = process_activity_and_legs_data(
                df_activity_synt, df_legs_synt, values_to_remove, modes_to_remove
            )
            df_activity_synt = normalize_type_column(df_activity_synt_filtered)
            df_activity_chains_syn = df_activity_synt.groupby(['plan_id']).apply(create_activity_chain_syn).reset_index()
            logging.info("Activity Chains synt cleaned successfully")

            df_legs_synt = normalize_mode_column(df_legs_synt_filtered)

            df_trips_synt = create_trips_dataframe(df_activity_synt)
            df_trips_synt = df_trips_synt.dropna()
            df_trips_synt['departure_time'] = df_trips_synt['departure_time'].apply(safe_convert_time)
            df_trips_synt['arrival_time'] = df_trips_synt['arrival_time'].apply(safe_convert_time)

        logging.info("Activity and legs data processed successfully")

    except Exception as e:
        logging.error("Error cleaning activity and legs data: " + str(e))

    try:
        # =========================================================================
        # STEP 19: Process microcensus data (if enabled)
        # =========================================================================
        if cfg.read_microcensus:
            # Process trips - at least one activity inside
            df_trips_at_least_one_activity_inside_mic = df_trips_at_least_one_activity_inside_mic.dropna()
            df_trips_at_least_one_activity_inside_mic['departure_time'] = \
                df_trips_at_least_one_activity_inside_mic['departure_time'].apply(safe_convert_time)
            df_trips_at_least_one_activity_inside_mic['arrival_time'] = \
                df_trips_at_least_one_activity_inside_mic['arrival_time'].apply(safe_convert_time)
            df_trips_at_least_one_activity_inside_mic['departure_time'] = \
                pd.to_datetime(df_trips_at_least_one_activity_inside_mic['departure_time'], unit='s').dt.floor(
                    '30T').dt.time
            df_trips_at_least_one_activity_inside_mic['arrival_time'] = \
                pd.to_datetime(df_trips_at_least_one_activity_inside_mic['arrival_time'], unit='s').dt.floor(
                    '30T').dt.time
            df_trips_at_least_one_activity_inside_mic = normalize_mode_column(df_trips_at_least_one_activity_inside_mic)

            # Process trips - all activities inside
            df_trips_all_activities_inside_mic = df_trips_all_activities_inside_mic.dropna()
            df_trips_all_activities_inside_mic['departure_time'] = \
                df_trips_all_activities_inside_mic['departure_time'].apply(safe_convert_time)
            df_trips_all_activities_inside_mic['arrival_time'] = \
                df_trips_all_activities_inside_mic['arrival_time'].apply(safe_convert_time)
            df_trips_all_activities_inside_mic['departure_time'] = \
                pd.to_datetime(df_trips_all_activities_inside_mic['departure_time'], unit='s').dt.floor('30T').dt.time
            df_trips_all_activities_inside_mic['arrival_time'] = \
                pd.to_datetime(df_trips_all_activities_inside_mic['arrival_time'], unit='s').dt.floor('30T').dt.time
            df_trips_all_activities_inside_mic = normalize_mode_column(df_trips_all_activities_inside_mic)

            df_trips_home_inside_mic = df_trips_home_inside_mic.dropna()
            df_trips_home_inside_mic['departure_time'] = df_trips_home_inside_mic[
                'departure_time'].apply(safe_convert_time)
            df_trips_home_inside_mic['arrival_time'] = df_trips_home_inside_mic[
                'arrival_time'].apply(safe_convert_time)
            df_trips_home_inside_mic['departure_time'] = \
                pd.to_datetime(df_trips_home_inside_mic['departure_time'], unit='s').dt.floor('30T').dt.time
            df_trips_home_inside_mic['arrival_time'] = \
                pd.to_datetime(df_trips_home_inside_mic['arrival_time'], unit='s').dt.floor('30T').dt.time
            df_trips_home_inside_mic = normalize_mode_column(df_trips_home_inside_mic)

            # Process population data using common functions
            df_population_at_least_one_activity_inside_mic['number_of_cars'] = \
                df_population_at_least_one_activity_inside_mic['number_of_cars'].apply(group_cars)
            df_population_at_least_one_activity_inside_mic = normalize_sex_column(
                df_population_at_least_one_activity_inside_mic
            )
            df_population_all_activities_inside_mic['number_of_cars'] = \
                df_population_all_activities_inside_mic['number_of_cars'].apply(group_cars)
            df_population_all_activities_inside_mic = normalize_sex_column(df_population_all_activities_inside_mic)

            df_population_home_inside_mic['number_of_cars'] = df_population_home_inside_mic['number_of_cars'].apply(
                group_cars)
            df_population_home_inside_mic = normalize_sex_column(df_population_home_inside_mic)

            # Create activity chains
            df_activity_chains_at_least_one_activity_mic = \
                df_trips_at_least_one_activity_inside_mic.groupby(['person_id']).apply(
                    create_activity_chain_mic).reset_index()
            df_activity_chains_all_activities_inside_mic = \
                df_trips_all_activities_inside_mic.groupby(['person_id']).apply(create_activity_chain_mic).reset_index()

            logging.info("Microcensus data processed successfully")

    except Exception as e:
        logging.error("Error in Process microcensus data" + str(e))

    try:
        # =========================================================================
        # STEP 20: Create activity chains for simulation data
        # =========================================================================
        df_activity_chains_sim = df_activity_sim.groupby(['plan_id']).apply(create_activity_chain_syn).reset_index()
        logging.info("Activity chains created successfully")

        # =========================================================================
        # STEP 21: Save all output files
        # =========================================================================
        if cfg.read_microcensus:
            # Microcensus outputs
            df_trips_at_least_one_activity_inside_mic.to_csv(
                os.path.join(cfg.data_path_clean, "trips_at_least_one_activity_inside_mic.csv"), index=False
            )
            df_trips_all_activities_inside_mic.to_csv(
                os.path.join(cfg.data_path_clean, "trips_all_activities_inside_mic.csv"), index=False
            )
            df_activity_chains_at_least_one_activity_mic.to_csv(
                os.path.join(cfg.data_path_clean, "activity_chains_at_least_one_activity_inside_mic.csv"), index=False
            )
            df_activity_chains_all_activities_inside_mic.to_csv(
                os.path.join(cfg.data_path_clean, "activity_chains_all_activities_inside_mic.csv"), index=False
            )
            df_population_all_activities_inside_mic.to_csv(
                os.path.join(cfg.data_path_clean, "population_all_activities_inside_mic.csv"), index=False
            )
            df_population_at_least_one_activity_inside_mic.to_csv(
                os.path.join(cfg.data_path_clean, "population_at_least_one_activity_inside_mic.csv"), index=False
            )
            df_population_home_inside_mic.to_csv(os.path.join(cfg.data_path_clean, "population_home_inside_mic.csv"))

            df_trips_home_inside_mic.to_csv(os.path.join(cfg.data_path_clean, "trips_home_inside_mic.csv"))

            logging.info("Microcensus outputs saved successfully")

            if cfg.read_SynPop:
                # Synthetic population outputs
                df_trips_synt.to_csv(os.path.join(cfg.data_path_clean, "trips_synt.csv"), index=False)
                df_activity_chains_syn.to_csv(os.path.join(cfg.data_path_clean, "activity_chains_syn.csv"), index=False)
                df_persons_synt.to_csv(os.path.join(cfg.data_path_clean, "population_clean_synth.csv"), index=False)
                df_legs_synt.to_csv(os.path.join(cfg.data_path_clean, "legs_clean_synt.csv"), index=False)
                logging.info("Synthetic population outputs saved successfully")

        # Simulation outputs
        logging.info("Simulation Population is started to save in csv files.")
        df_activity_chains_sim.to_csv(os.path.join(cfg.data_path_clean, "activity_chains_sim.csv"), index=False)
        df_population_all_activities_inside_sim.to_csv(
            os.path.join(cfg.data_path_clean, "population_all_activities_inside_sim.csv"), index=False
        )
        df_population_at_least_one_activity_inside_sim.to_csv(
            os.path.join(cfg.data_path_clean, "population_at_least_one_activity_inside_sim.csv"), index=False
        )
        logging.info("Simulation Population is finished to save in csv files.")
    except Exception as e:
        logging.error("Error in Process synthetic population data" + str(e))

    try:
        # =========================================================================
        # STEP 22: Create final filtered trips output
        # =========================================================================
        # All activities inside
        # Include main_mode (for modal split) and modes (legs sequence like "walk-car-walk")
        filtered_trips_all_activities_inside_sim = df_trips_all_activities_inside_sim[[
            "person", "trip_number", "start_link", "end_link", "dep_time", "trav_time", "euclidean_distance",
            "main_mode", "modes", "start_x", "start_y", "end_x", "end_y", "start_activity_type", "end_activity_type"
        ]].copy()

        filtered_trips_all_activities_inside_sim.rename(
            columns={'trav_time': 'travel_time', 'euclidean_distance': 'distance'},
            inplace=True
        )
        filtered_trips_all_activities_inside_sim.dropna(subset=['main_mode'], inplace=True)
        filtered_trips_all_activities_inside_sim = filtered_trips_all_activities_inside_sim[
            ~filtered_trips_all_activities_inside_sim['main_mode'].isin(['truck'])
        ]

        # At least one activity inside
        filtered_trips_at_least_one_activity_inside_sim = df_trips_at_least_one_activity_inside_sim[[
            "person", "start_link", "end_link", "dep_time", "trav_time", "euclidean_distance",
            "main_mode", "modes", "start_x", "start_y", "end_x", "end_y"
        ]].copy()

        filtered_trips_at_least_one_activity_inside_sim.rename(
            columns={'trav_time': 'travel_time', 'euclidean_distance': 'distance'},
            inplace=True
        )
        filtered_trips_at_least_one_activity_inside_sim.dropna(subset=['main_mode'], inplace=True)
        filtered_trips_at_least_one_activity_inside_sim = filtered_trips_at_least_one_activity_inside_sim[
            ~filtered_trips_at_least_one_activity_inside_sim['main_mode'].isin(['truck'])
        ]

        # Save final trip outputs
        filtered_trips_at_least_one_activity_inside_sim.to_csv(
            os.path.join(cfg.data_path_clean, "trips_at_least_one_activity_inside_sim.csv"), index=False
        )
        filtered_trips_all_activities_inside_sim.to_csv(
            os.path.join(cfg.data_path_clean, "trips_all_activities_inside_sim.csv"), index=False
        )

        logging.info("All output files saved successfully")
        logging.info("Script completed successfully")

    except Exception as e:
        logging.error("Error in Process synthetic population data" + str(e))
