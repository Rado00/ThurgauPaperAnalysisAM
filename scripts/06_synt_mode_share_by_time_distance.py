# Import necessary libraries
import matsim
from functions.commonFunctions import *
import pandas as pd

pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)
import warnings

warnings.filterwarnings("ignore")


# Function to compute average of start and end coordinates
def compute_avg_coordinates(start_link, end_link, link_data):
    start_coords = link_data.get(str(start_link), [None, None])
    end_coords = link_data.get(str(end_link), [None, None])

    if None in start_coords or None in end_coords:
        return None, None  # Handle missing values

    avg_x = (float(start_coords[0]) + float(end_coords[0])) / 2
    avg_y = (float(start_coords[1]) + float(end_coords[1])) / 2
    return avg_x, avg_y


if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)

    # Read the XML data with a matsim library
    try:
        plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"population.xml.gz"))
        logging.info("Population data loaded successfully")
    except Exception as e:
        logging.error("Error loading network data: " + str(e))
        sys.exit()

    # Create the separated dataframe files of the loaded data
    try:
        df_routes_synt = plans.routes
        df_legs_synt = plans.legs
        df_activity_synt = plans.activities
        logging.info("Dataframes created successfully")
    except Exception as e:
        logging.error("Error creating dataframes: " + str(e))
        sys.exit()

    # Create a dictionary of link data for synthetic and simulation
    link_dict_synt = df_activity_synt.set_index("link")[["x", "y"]].apply(
        lambda row: [row["x"], row["y"]], axis=1).to_dict()

    link_dict_synt_str = {str(key): value for key, value in link_dict_synt.items()}

    merged_synt_df = pd.merge(df_routes_synt, df_legs_synt, on='id', how='inner')
    df_synt_mode_share_time_distance = merged_synt_df[['id',  'plan_id', 'start_link', 'end_link', 'dep_time',
       'trav_time_x', 'distance', 'mode']]

    # convert 'trav_time_x' to 'travel_time'
    df_synt_mode_share_time_distance.rename(columns={'trav_time_x': 'travel_time'}, inplace=True)

    df_synt_mode_share_time_distance[["x", "y"]] = df_synt_mode_share_time_distance.apply(
        lambda row: compute_avg_coordinates(row["start_link"], row["end_link"], link_dict_synt_str), axis=1,
        result_type="expand")

    df_synt_mode_share_time_distance.to_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_synt.csv', index=False)
    logging.info("Dataframe saved as csv file successfully")
