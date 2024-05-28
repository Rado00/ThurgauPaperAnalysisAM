# common.py
import os
import sys
import logging
import configparser


def setup_logging(log_filename):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(filename=f"logs\\{log_filename}",
                        level=logging.INFO,
                        format='%(levelname)s   %(asctime)s   %(message)s')
    logging.info("All setting of the logging is done")


def read_config():
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)

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
        return data_path, zone_name, scenario, csv_folder, output_folder, percentile
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit()
