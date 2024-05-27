# Import necessary libraries
import os
import sys
import logging
import configparser
import pandas as pd

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(filename="02_read_csv_files.log",
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

    pre_processed_data_path = os.path.join(data_path, zone_name, csv_folder, percentile)

    # Read the csv files
    try:
        df_households_synt = pd.read_csv(f'{pre_processed_data_path}\\df_households_synt.csv', low_memory=False)
        df_activity_synt = pd.read_csv(f'{pre_processed_data_path}\\df_activity_synt.csv', low_memory=False)
        df_legs_synt = pd.read_csv(f'{pre_processed_data_path}\\df_legs_synt.csv', low_memory=False)
        df_persons_synt = pd.read_csv(f'{pre_processed_data_path}\\df_persons_synt.csv', low_memory=False)
        df_routes_synt = pd.read_csv(f'{pre_processed_data_path}\\df_routes_synt.csv', low_memory=False)
        df_activity_sim = pd.read_csv(f'{pre_processed_data_path}\\df_activity_sim.csv', low_memory=False)
        df_legs_sim = pd.read_csv(f'{pre_processed_data_path}\\df_legs_sim.csv', low_memory=False)
        df_persons_sim = pd.read_csv(f'{pre_processed_data_path}\\df_persons_sim.csv', low_memory=False)
        df_routes_sim = pd.read_csv(f'{pre_processed_data_path}\\df_routes_sim.csv', low_memory=False)
        logging.info("CSV files read successfully")
    except Exception as e:
        logging.error("Error reading csv files: " + str(e))
        sys.exit()

    new_path = os.path.join(data_path, zone_name, 'microzensus')
    try:
        df_population_mic = pd.read_csv(f"{new_path}\\population.csv")
        df_trips_mic = pd.read_csv(f"{new_path}\\trips.csv")
        df_personen_geschlecht = pd.read_csv(f"{new_path}\\Personen_ZH_Sex.csv")
    except Exception as e:
        logging.error("Error reading csv files: " + str(e))
        sys.exit()

