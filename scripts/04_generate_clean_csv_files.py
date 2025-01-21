# Import necessary libraries
from common import *
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


# Functions
def process_time_data(df):
    """
    Function to convert 'dep_time' and 'trav_time' from string to timedelta,
    then to seconds, and calculate 'arrival_time'.
    """
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

    :param df_activities: DataFrame containing activities with coordinates (x, y) and plan_id.
    :param df_persons: DataFrame containing person data with home coordinates (home_x, home_y) and hh_id.
    :param activity_type: The type of activity used to map person IDs (default 'Home').
    :return: DataFrame with person_id mapped and propagated.
    """
    # Ensure coordinates are of type float64
    df_activities['x'] = pd.to_numeric(df_activities['x'], errors='coerce')
    df_activities['y'] = pd.to_numeric(df_activities['y'], errors='coerce')
    df_persons['home_x'] = pd.to_numeric(df_persons['home_x'], errors='coerce')
    df_persons['home_y'] = pd.to_numeric(df_persons['home_y'], errors='coerce')

    # Filter df_activities for rows where type is the specified activity type
    home_activities = df_activities[df_activities['type'] == activity_type]

    # Merge the household IDs from df_persons to home_activities based on coordinate match
    merged_home_activities = pd.merge(
        home_activities,
        df_persons[['hh_id', 'home_x', 'home_y']],
        left_on=['x', 'y'],
        right_on=['home_x', 'home_y'],
        how='left'
    )

    # Create a mapping of plan_id to hh_id
    if merged_home_activities['plan_id'].is_unique:
        plan_id_to_hh_id = merged_home_activities.set_index('plan_id')['hh_id']
    else:
        plan_id_to_hh_id = merged_home_activities.groupby('plan_id')['hh_id'].first()

    # Map the hh_id as person_id to all activities in df_activities
    df_activities['person_id'] = df_activities['plan_id'].map(plan_id_to_hh_id)

    # Propagate the person_id to other activities in the same plan
    df_activities['person_id'] = df_activities.groupby('plan_id')['person_id'].transform(lambda x: x.ffill().bfill())

    return df_activities


def process_activity_and_legs_data(df_activity, df_legs, values_to_remove, modes_to_remove):
    # Identify persons with only one 'Home' activity initially
    initial_single_home = df_activity.groupby('person_id').filter(lambda x: len(x) == 1 and x['type'].eq('Home').all())

    # Filter the activity DataFrame
    df_activity_filtered = df_activity[~df_activity['type'].isin(values_to_remove)]

    # Find all 'plan_id' values where 'type' is 'outside'
    plan_ids_to_remove = df_activity_filtered[df_activity_filtered['type'] == 'outside']['plan_id'].unique()

    # Filter out all rows with these 'plan_id' values
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['plan_id'].isin(plan_ids_to_remove)]

    # Additional filter to remove 'outside'
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['type'].isin(['outside'])]

    # Combine 'Access Walk' and 'Egress Walk' into 'Walk' in legs DataFrame
    df_legs['mode'] = df_legs['mode'].replace({'access_walk': 'walk', 'egress_walk': 'walk'})

    # Remove specified modes from the legs DataFrame
    df_legs_filtered = df_legs[~df_legs['mode'].isin(modes_to_remove)]

    # Identify persons who now only have one 'Home' activity
    final_single_home = df_activity_filtered.groupby('person_id').filter(
        lambda x: len(x) == 1 and x['type'].eq('Home').all())

    # Exclude persons who initially had only one 'Home' activity
    final_single_home = final_single_home[~final_single_home['person_id'].isin(initial_single_home['person_id'])]

    # Remove these persons from the filtered data
    df_activity_filtered = df_activity_filtered[~df_activity_filtered['person_id'].isin(final_single_home['person_id'])]

    return df_activity_filtered, df_legs_filtered


def create_trips_dataframe(df_activity):
    # List to hold new trip entries
    new_trips = []

    # Iterate over the activity DataFrame
    for i in range(len(df_activity) - 1):
        # Get current and next row
        current_row = df_activity.iloc[i]
        next_row = df_activity.iloc[i + 1]

        # Check if the IDs are consecutive
        if current_row['id'] + 1 == next_row['id']:
            # Create a new trip entry
            new_trips.append({
                'trip_id': current_row['id'],
                'departure_time': current_row['end_time'],
                'arrival_time': next_row['start_time'],
                'start_coor_x': current_row['x'],
                'start_coor_y': current_row['y'],
                'ziel_coor_x': next_row['x'],
                'ziel_coor_y': next_row['y'],

            })

    # Create a DataFrame from the list of new trips
    df_trips = pd.DataFrame(new_trips)

    return df_trips


def safe_convert_time(time_str):
    try:
        # Convert to datetime, then to time, and floor to 30-minute bins
        return pd.to_datetime(time_str, format='%H:%M:%S', errors='raise').floor('30T').time()
    except ValueError:
        # Handle invalid time data (e.g., return None or a default time)
        return None


# Group all numbers count car larger equal 3 to 3+
def group_cars(value):
    # Convert to integer if the value is a string
    try:
        value_int = int(value)
    except ValueError:
        # Return the value as is if it's not a number
        return value

    # Group all values less than or equal to 3 into '3+'
    if value_int >= 3:
        return '3+'
    else:
        return str(value_int)


# Function to create activity chains
def create_activity_chain_mic(group):
    chain = '-'.join(
        ['H'] + [purpose[0] for purpose in group['purpose'].tolist()])  # Add 'H' at the start of each chain
    return pd.Series({'activity_chain': chain})


# Function to create uppercase activity chains
def create_activity_chain_syn(group):
    chain = '-'.join([purpose[0].upper() for purpose in group['type'].tolist()])
    return pd.Series({'activity_chain': chain})


def execute_household_just_person_household_weight(path):
    df_mz_households = pd.read_csv(
        "%s\\microzensus\\haushalte.csv" % path, sep=",", encoding="latin1")
    df_mz_households["person_id"] = df_mz_households["HHNR"]
    df_mz_households["household_weight"] = df_mz_households["WM"]

    return df_mz_households[["person_id", "household_weight"]]


if __name__ == '__main__':
    setup_logging("04_generate_clean_csv_files.log")

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    analysis_zone_path = os.path.join(data_path, analysis_zone_name)
    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    # Read the csv files
    try:
        # df_households_synt = pd.read_csv(f'{pre_processed_data_path}\\df_households_synt.csv', low_memory=False)
        # df_activity_synt = pd.read_csv(f'{pre_processed_data_path}\\df_activity_synt.csv', low_memory=False)
        # df_legs_synt = pd.read_csv(f'{pre_processed_data_path}\\df_legs_synt.csv', low_memory=False)
        # df_persons_synt = pd.read_csv(f'{pre_processed_data_path}\\df_persons_synt.csv', low_memory=False)
        # df_routes_synt = pd.read_csv(f'{pre_processed_data_path}\\df_routes_synt.csv', low_memory=False)
        df_activity_sim = pd.read_csv(f'{pre_processed_data_path}\\df_activity_sim.csv', low_memory=False)
        df_legs_sim = pd.read_csv(f'{pre_processed_data_path}\\df_legs_sim.csv', low_memory=False)
        df_persons_sim = pd.read_csv(f'{pre_processed_data_path}\\df_persons_sim.csv', low_memory=False)
        df_routes_sim = pd.read_csv(f'{pre_processed_data_path}\\df_routes_sim.csv', low_memory=False)
        logging.info("CSV files read successfully")
    except Exception as e:
        logging.error("Error reading csv files: " + str(e))
        sys.exit()

    new_path = os.path.join(data_path, analysis_zone_name, 'microzensus')
    try:
        df_population_mic = pd.read_csv(f"{new_path}\\population.csv")
        df_trips_mic = pd.read_csv(f"{new_path}\\trips.csv")
    except Exception as e:
        logging.error("Error reading csv files: " + str(e))
        sys.exit()

    # Run the function for both df_legs_synt and df_legs_sim
    # df_legs_synt = process_time_data(df_legs_synt)
    df_legs_sim = process_time_data(df_legs_sim)

    # Rename the column 'id' to 'person_id'
    # df_persons_synt.rename(columns={'id': 'hh_id'}, inplace=True)
    df_persons_sim.rename(columns={'id': 'hh_id'}, inplace=True)

    # df_activity_synt_filtered = map_person_id_to_activities(df_activity_synt, df_persons_synt)
    df_activity_sim_filtered = map_person_id_to_activities(df_activity_sim, df_persons_sim)

    values_to_remove = ['freight_unloading', 'freight_loading', 'pt interaction']
    modes_to_remove = ['truck', 'outside']

    # Process synthetic data
    # df_activity_synt_filtered, df_legs_synt_filtered = process_activity_and_legs_data(df_activity_synt, df_legs_synt,
    #                                                                                   values_to_remove, modes_to_remove)

    # Process simulated data
    df_activity_sim_filtered, df_legs_sim_filtered = process_activity_and_legs_data(df_activity_sim, df_legs_sim,
                                                                                    values_to_remove, modes_to_remove)

    # df_activity_synt = df_activity_synt_filtered
    df_activity_sim = df_activity_sim_filtered

    # df_legs_synt = df_legs_synt_filtered
    df_legs_sim = df_legs_sim_filtered

    # df_trips_synt = create_trips_dataframe(df_activity_synt)
    df_trips_sim = create_trips_dataframe(df_activity_sim)

    # df_trips_synt = df_trips_synt.dropna()
    df_trips_sim = df_trips_sim.dropna()

    # Apply the conversion function to the DataFrame
    # df_trips_synt['departure_time'] = df_trips_synt['departure_time'].apply(safe_convert_time)
    # df_trips_synt['arrival_time'] = df_trips_synt['arrival_time'].apply(safe_convert_time)

    df_trips_sim['departure_time'] = df_trips_sim['departure_time'].apply(safe_convert_time)
    df_trips_sim['arrival_time'] = df_trips_sim['arrival_time'].apply(safe_convert_time)

    # Convert seconds to datetime and resample times to 15-minute bins
    df_trips_mic['departure_time'] = pd.to_datetime(df_trips_mic['departure_time'], unit='s').dt.floor('30T').dt.time
    df_trips_mic['arrival_time'] = pd.to_datetime(df_trips_mic['arrival_time'], unit='s').dt.floor('30T').dt.time

    # Capitalize and remove underscores from mode names for both dataframes
    df_trips_mic['mode'] = df_trips_mic['mode'].str.replace('_', ' ').str.title()
    # df_legs_synt['mode'] = df_legs_synt['mode'].str.replace('_', ' ').str.title()
    df_legs_sim['mode'] = df_legs_sim['mode'].str.replace('_', ' ').str.title()

    # Capitalize and remove underscores from type names
    df_trips_mic['purpose'] = df_trips_mic['purpose'].str.replace('_', ' ').str.title()
    # df_activity_synt['type'] = df_activity_synt['type'].str.replace('_', ' ').str.title()
    df_activity_sim['type'] = df_activity_sim['type'].str.replace('_', ' ').str.title()

    # Remove rows where 'age' is NaN
    # df_persons_synt = df_persons_synt.dropna(subset=['age'])
    # df_persons_synt['age'] = df_persons_synt['age'].astype(int)

    df_persons_sim = df_persons_sim.dropna(subset=['age'])
    df_persons_sim['age'] = df_persons_sim['age'].astype(int)

    # Filter out persons younger than 6
    # df_persons_synt = df_persons_synt[df_persons_synt['age'] >= 6]
    df_persons_sim = df_persons_sim[df_persons_sim['age'] >= 6]

    # Apply the grouping function to the 'number_of_cars' column
    df_population_mic['number_of_cars'] = df_population_mic['number_of_cars'].apply(group_cars)

    # Mapping '0' to 'male' and '1' to 'female'
    df_population_mic['sex'] = df_population_mic['sex'].replace({0: 'male', 1: 'female'})
    # df_persons_synt['sex'] = df_persons_synt['sex'].replace({'m': 'male', 'f': 'female'})
    df_persons_sim['sex'] = df_persons_sim['sex'].replace({'m': 'male', 'f': 'female'})

    # Remove rows where 'type' is 'Home' and both 'end_time' and 'start_time' are not NaN
    # df_activity_synt_1 = df_activity_synt[~(
    #         (df_activity_synt['type'] == 'Home') & (df_activity_synt['end_time'].notna()) & (
    #     df_activity_synt['start_time'].notna()))]
    # Remove rows where 'type' is 'Home' and both 'end_time' and 'start_time' are not NaN
    df_activity_sim_1 = df_activity_sim[~(
            (df_activity_sim['type'] == 'Home') & (df_activity_sim['end_time'].notna()) & (
        df_activity_sim['start_time'].notna()))]

    df_activity_chains_mic = df_trips_mic.groupby(['person_id']).apply(create_activity_chain_mic).reset_index()
    df_activity_chains_sim = df_activity_sim.groupby(['plan_id']).apply(create_activity_chain_syn).reset_index()
    # df_activity_chains_syn = df_activity_synt.groupby(['plan_id']).apply(create_activity_chain_syn).reset_index()

    # Replace all 'H' with 'H-H' in the 'activity_chain' column
    # df_activity_chains_syn['activity_chain'] = df_activity_chains_syn['activity_chain'].replace({'H': 'H-H'})
    df_activity_chains_sim['activity_chain'] = df_activity_chains_sim['activity_chain'].replace({'H': 'H-H'})
    df_activity_chains_mic['activity_chain'] = df_activity_chains_mic['activity_chain'].replace({'H': 'H-H'})

    # All person id and household weight values
    reference_population = execute_household_just_person_household_weight(analysis_zone_path)

    # Merge the 'household_weight' column from df_population_mic to df_trips_mic based on 'person_id'
    df_trips_mic = pd.merge(df_trips_mic, df_population_mic[['person_id', 'household_weight']], on='person_id',
                            how='left')

    df_trips_mic['household_weight'] = df_trips_mic.apply(
        lambda row: row['household_weight'] if pd.notnull(row['household_weight']) else
        reference_population.loc[reference_population['person_id'] == row['person_id'], 'household_weight'].values[0]
        if row['person_id'] in reference_population['person_id'].values else None,
        axis=1
    )

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    # Ensure the directory exists
    if not os.path.exists(data_path_clean):
        os.makedirs(data_path_clean)
    # Write the CSV files
    df_trips_mic.to_csv(f'{data_path_clean}\\trips_mic.csv', index=False)
    # df_trips_synt.to_csv(f'{data_path_clean}\\trips_synt.csv', index=False)
    df_trips_sim.to_csv(f'{data_path_clean}\\trips_sim.csv', index=False)

    # df_activity_chains_syn.to_csv(f'{data_path_clean}\\activity_chains_syn.csv', index=False)
    df_activity_chains_sim.to_csv(f'{data_path_clean}\\activity_chains_sim.csv', index=False)
    df_activity_chains_mic.to_csv(f'{data_path_clean}\\activity_chains_mic.csv', index=False)

    df_population_mic.to_csv(f'{data_path_clean}\\population_clean_mic.csv', index=False)
    # df_persons_synt.to_csv(f'{data_path_clean}\\population_clean_synth.csv', index=False)
    df_persons_sim.to_csv(f'{data_path_clean}\\population_clean_sim.csv', index=False)

    # df_legs_synt.to_csv(f'{data_path_clean}\\legs_clean_synt.csv', index=False)
    df_legs_sim.to_csv(f'{data_path_clean}\\legs_clean_sim.csv', index=False)
