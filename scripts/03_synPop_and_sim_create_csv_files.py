# Import necessary libraries
import matsim
from functions.commonFunctions import *
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)

    # Read the XML data with a matsim library
    try:
        plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
        logging.info("Output plans data loaded successfully")

        if read_SynPop:
            households_synt = matsim.household_reader(os.path.join(scenario_path, "households.xml.gz")) # dataframe types conversion failed
            logging.info("Synthetic Household data loaded successfully")
            plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"population.xml.gz"))
            logging.info("Synthetic Population data loaded successfully")

    except Exception as e:
        logging.error("Error loading data: " + str(e))
        sys.exit()

    # Create the separated dataframe files of the loaded data
    try:
        df_activity_sim = plans_sim.activities
        df_persons_sim = plans_sim.persons
        df_routes_sim = plans_sim.routes

        if read_SynPop:
            df_activity_synt = plans.activities
            df_persons_synt = plans.persons
            df_routes_synt = plans.routes
            df_households_synt = households_synt.households

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
        df_persons_sim.to_csv(f'{pre_processed_data_path}\\df_persons_sim.csv', index=False)
        df_routes_sim.to_csv(f'{pre_processed_data_path}\\df_routes_sim.csv', index=False)

        if read_SynPop:
            df_activity_synt.to_csv(f'{pre_processed_data_path}\\df_activity_synt.csv', index=False)
            df_persons_synt.to_csv(f'{pre_processed_data_path}\\df_persons_synt.csv', index=False)
            df_routes_synt.to_csv(f'{pre_processed_data_path}\\df_routes_synt.csv', index=False)
            df_households_synt.to_csv(f'{pre_processed_data_path}\\df_households_synt.csv', index=False)


        logging.info("All the csv files created successfully")
    except Exception as e:
        logging.error("Error creating csv files: " + str(e))
        sys.exit()
