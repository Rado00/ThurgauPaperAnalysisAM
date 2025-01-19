# Import necessary libraries
import matsim
from common import *
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

if __name__ == '__main__':
    setup_logging("03_read_create_csv_files.log")

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)

    # Read the XML data with a matsim library
    try:
        network = matsim.read_network(os.path.join(scenario_path, "network.xml.gz"))
        logging.info("Network data loaded successfully")
        plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"population.xml.gz"))
        logging.info("Population data loaded successfully")
        households_synt = matsim.household_reader(os.path.join(scenario_path, "households.xml.gz")) # dataframe types conversion failed
        logging.info("Household data loaded successfully")
        households_sim = matsim.household_reader(os.path.join(output_folder_path, "output_households.xml.gz")) # dataframe types conversion failed
        logging.info("Output household data loaded successfully")
        plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
        logging.info("Output plans data loaded successfully")
    except Exception as e:
        logging.error("Error loading network data: " + str(e))
        sys.exit()

    # Create the separated dataframe files of the loaded data
    try:
        df_households_synt = households_synt.households
        df_activity_synt = plans.activities
        df_legs_synt = plans.legs
        df_persons_synt = plans.persons
        df_routes_synt = plans.routes
        df_activity_sim = plans_sim.activities
        df_legs_sim = plans_sim.legs
        df_persons_sim = plans_sim.persons
        df_routes_sim = plans_sim.routes
        logging.info("Dataframes created successfully")
    except Exception as e:
        logging.error("Error creating dataframes: " + str(e))
        sys.exit()

    pre_processed_data_path = os.path.join(data_path, analysis_zone_name, csv_folder, percentile)
    # Create the directory for the csv files is not exists
    if not os.path.exists(pre_processed_data_path):
        os.makedirs(pre_processed_data_path)
        logging.info("Directory for csv files created successfully")

    # Create the csv files from the dataframes
    try:
        df_activity_sim.to_csv(f'{pre_processed_data_path}\\df_activity_sim.csv', index=False)
        df_activity_synt.to_csv(f'{pre_processed_data_path}\\df_activity_synt.csv', index=False)
        df_households_synt.to_csv(f'{pre_processed_data_path}\\df_households_synt.csv', index=False)
        df_legs_sim.to_csv(f'{pre_processed_data_path}\\df_legs_sim.csv', index=False)
        df_legs_synt.to_csv(f'{pre_processed_data_path}\\df_legs_synt.csv', index=False)
        df_persons_synt.to_csv(f'{pre_processed_data_path}\\df_persons_synt.csv', index=False)
        df_persons_sim.to_csv(f'{pre_processed_data_path}\\df_persons_sim.csv', index=False)
        df_routes_sim.to_csv(f'{pre_processed_data_path}\\df_routes_sim.csv', index=False)
        df_routes_synt.to_csv(f'{pre_processed_data_path}\\df_routes_synt.csv', index=False)
        logging.info("All the csv files created successfully")
    except Exception as e:
        logging.error("Error creating csv files: " + str(e))
        sys.exit()
