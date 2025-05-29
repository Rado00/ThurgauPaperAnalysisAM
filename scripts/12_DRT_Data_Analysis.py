# Import necessary libraries
import logging
from functions.commonFunctions import *
import pandas as pd
import warnings
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots


if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

warnings.filterwarnings('ignore')

