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

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

warnings.filterwarnings('ignore')

