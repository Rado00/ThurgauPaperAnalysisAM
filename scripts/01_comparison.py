# Import necessary libraries
import os
import sys
import logging
import configparser
import pandas as pd


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(filename="01_comparison_logs.log",
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
        percentile = config['config']['percentile']
        logging.info("Config file read successfully")
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit()

    # Create directory for the zone
    scenario_path = os.path.join(data_path, zone_name, scenario, percentile)
    output_folder_path = os.path.join(data_path, 'output', zone_name)


