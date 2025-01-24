# Import necessary libraries
import matsim
from common import *
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)
import warnings
warnings.filterwarnings("ignore")

if __name__ == '__main__':
    setup_logging("05_synt_and_sim_mode_share_by_time_distance.log")

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)

    # Read the XML data with a matsim library
    try:
        # plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"population.xml.gz"))
        logging.info("Population data loaded successfully")
        plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
        logging.info("Output plans data loaded successfully")
    except Exception as e:
        logging.error("Error loading network data: " + str(e))
        sys.exit()

    # Create the separated dataframe files of the loaded data
    try:
        # df_routes_synt = plans.routes
        # df_legs_synt = plans.legs
        df_legs_sim = plans_sim.legs
        df_routes_sim = plans_sim.routes
        logging.info("Dataframes created successfully")
    except Exception as e:
        logging.error("Error creating dataframes: " + str(e))
        sys.exit()

    # merged_synt_df = pd.merge(df_routes_synt, df_legs_synt, on='id', how='inner')
    # df_synt_mode_share_time_distance = merged_synt_df[['id',  'plan_id', 'start_link', 'end_link', 'dep_time',
    #    'trav_time_x', 'distance', 'mode']]

    # convert 'trav_time_x' to 'travel_time'
    # df_synt_mode_share_time_distance.rename(columns={'trav_time_x': 'travel_time'}, inplace=True)

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)
    # Create the directory for the csv files is not exists
    if not os.path.exists(pre_processed_data_path):
        os.makedirs(pre_processed_data_path)
        logging.info("Directory for csv files created successfully")
    # df_synt_mode_share_time_distance.to_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_synt.csv', index=False)
    logging.info("Dataframe saved as csv file successfully")

    merged_sim_df = pd.merge(df_routes_sim, df_legs_sim, on='id', how='inner')
    logging.info("Dataframes of Simulation are merged successfully")
    df_sim_mode_share_time_distance = merged_sim_df[['id',  'plan_id', 'start_link', 'end_link', 'dep_time',
       'trav_time_x', 'distance', 'mode']]

    # convert 'trav_time_x' to 'travel_time'
    df_sim_mode_share_time_distance.rename(columns={'trav_time_x': 'travel_time'}, inplace=True)

    df_sim_mode_share_time_distance.to_csv(f'{pre_processed_data_path}\\travel_time_distance_mode_sim.csv', index=False)
    logging.info("Dataframe of simulation is saved as csv file successfully")

