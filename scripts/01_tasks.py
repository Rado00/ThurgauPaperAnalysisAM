"""
This is the main script to do the tasks.

Author: Corrado Muratori
Date: 2024-05-28
"""

# Import necessary libraries
from common import *


if __name__ == '__main__':
    setup_logging("01_tasks.log")

    data_path, zone_name, scenario, csv_folder, output_folder, percentile = read_config()

