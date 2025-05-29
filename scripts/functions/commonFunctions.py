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


def get_log_filename():
    # Get the script file that was executed (even if this is imported)
    file_path = sys.argv[0]
    # Extract only the filename
    log_filename = os.path.basename(file_path)
    log_filename = log_filename.replace(".py", ".log")
    return log_filename


def read_config(path='config.ini'):
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)

    try:
        config = configparser.ConfigParser()
        config_path = os.path.join(parent_directory, f'config/{path}')
        config.read(config_path)

        data_path = config['config']['data_path']
        simulation_zone_name = config['config']['simulation_zone_name']
        scenario = config['config']['scenario']
        sim_output_folder = config['config']['sim_output_folder']
        percentile = config['config']['percentile']

        analysis_zone_name = config['config']['analysis_zone_name']
        csv_folder = config['config']['csv_folder']
        clean_csv_folder = config['config']['clean_csv_folder']
        shapeFileName = config['config']['shapeFileName']
        read_SynPop = config.getboolean('config', 'read_SynPop')
        read_microcensus = config.getboolean('config', 'read_microcensus')
        sample_for_debugging = config.getboolean('config', 'sample_for_debugging', fallback=False)
        target_area = config['config']['target_area']


        logging.info("Config file read successfully")
        return data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit()
