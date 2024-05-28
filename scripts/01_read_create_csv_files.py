# Import necessary libraries
import os
import sys
import matsim
import logging
import configparser

if __name__ == '__main__':
    # Check there exists a logs folder
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Set up logging
    logging.basicConfig(filename="logs\\01_read_create_csv_files.log",
                        level=logging.INFO,
                        format='%(levelname)s   %(asctime)s   %(message)s')
    logging.info("All setting of the logging is done")

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)

    # read config file
    try:
        config = configparser.ConfigParser()
        config_path = os.path.join(parent_directory, 'config/config.ini')
        config.read(config_path)
        data_path = config['config']['data_path']
        zone_name = config['config']['zone_name']
        scenario = config['config']['scenario']
        csv_folder = config['config']['csv_folder']
        output_folder = config['config']['output_folder']
        percentile = config['config']['percentile']
        logging.info("Config file read successfully")
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit()

    # Create directory for the zone
    scenario_path = os.path.join(data_path, zone_name, scenario, percentile)
    output_folder_path = os.path.join(data_path, zone_name, output_folder)

    # Read the xml data with matsim library
    try:
        network = matsim.read_network(os.path.join(scenario_path, "network.xml.gz"))
        plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"imputed_population.xml.gz"))
        households_synt = matsim.household_reader(os.path.join(scenario_path, "households.xml.gz")) # dataframe types conversion failed
        households_sim = matsim.household_reader(os.path.join(output_folder_path, "output_households.xml.gz")) # dataframe types conversion failed
        plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
        logging.info("Network data loaded successfully")
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

    pre_processed_data_path = os.path.join(data_path, zone_name, csv_folder, percentile)
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
