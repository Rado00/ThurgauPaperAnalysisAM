# common.py
import os
import sys
import logging
import configparser
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration dataclass for the analysis pipeline.

    Provides centralized access to all configuration values and computed paths.
    """
    # Base configuration
    data_path: str
    simulation_zone_name: str
    scenario: str
    sim_output_folder: str
    percentile: str
    analysis_zone_name: str
    csv_folder: str
    clean_csv_folder: str
    shapeFileName: str
    read_SynPop: bool
    read_microcensus: bool
    sample_for_debugging: bool
    target_area: str

    # Computed paths (as properties for convenience)
    @property
    def analysis_zone_path(self) -> str:
        """Path to the analysis zone directory."""
        return os.path.join(self.data_path, self.analysis_zone_name)

    @property
    def output_folder_path(self) -> str:
        """Path to the simulation output folder."""
        return os.path.join(self.data_path, self.simulation_zone_name, self.sim_output_folder)

    @property
    def pre_processed_data_path(self) -> str:
        """Path to pre-processed CSV files."""
        return os.path.join(self.data_path, self.analysis_zone_name, self.csv_folder, self.percentile)

    @property
    def data_path_clean(self) -> str:
        """Path to cleaned CSV output files."""
        return os.path.join(self.data_path, self.analysis_zone_name, self.clean_csv_folder, self.percentile)

    @property
    def scenario_path(self) -> str:
        """Path to the scenario directory."""
        return os.path.join(self.data_path, self.simulation_zone_name, self.scenario, self.percentile)

    @property
    def microcensus_path(self) -> str:
        """Path to microcensus data."""
        return os.path.join(self.data_path, self.analysis_zone_name, 'microzensus')

    @property
    def shapefile_path(self) -> str:
        """Full path to the shapefile."""
        return os.path.join(self.analysis_zone_path, "ShapeFiles", self.shapeFileName)

    @property
    def nrows(self) -> Optional[int]:
        """Number of rows to read for debugging (None = all rows)."""
        return 1000 if self.sample_for_debugging else None


# =============================================================================
# Common Data Transformation Functions
# =============================================================================

def clean_population_df(df, person_col='person', min_age=6):
    """Standard cleaning for population dataframes.

    Steps:
    - Rename person column to 'person_id'
    - Remove rows with missing age
    - Convert age to integer
    - Filter out persons below minimum age

    Args:
        df: DataFrame to clean
        person_col: Name of the person ID column (default: 'person')
        min_age: Minimum age to include (default: 6)

    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    if person_col in df.columns and person_col != 'person_id':
        df = df.rename(columns={person_col: 'person_id'})
    df = df.dropna(subset=['age'])
    df['age'] = df['age'].astype(int)
    df = df[df['age'] >= min_age]
    return df


def normalize_mode_column(df, col='mode'):
    """Standardize mode names by replacing underscores and title-casing.

    Example: 'access_walk' -> 'Access Walk'

    Args:
        df: DataFrame to modify
        col: Column name to normalize (default: 'mode')

    Returns:
        DataFrame with normalized column
    """
    df = df.copy()
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace('_', ' ').str.title()
    return df


def normalize_type_column(df, col='type'):
    """Standardize type/activity names by replacing underscores and title-casing.

    Example: 'pt_interaction' -> 'Pt Interaction'

    Args:
        df: DataFrame to modify
        col: Column name to normalize (default: 'type')

    Returns:
        DataFrame with normalized column
    """
    df = df.copy()
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace('_', ' ').str.title()
    return df


def normalize_sex_column(df, col='sex'):
    """Standardize sex values to 'male'/'female'.

    Handles multiple input formats:
    - 'm'/'f' -> 'male'/'female'
    - 0/1 -> 'male'/'female'

    Args:
        df: DataFrame to modify
        col: Column name to normalize (default: 'sex')

    Returns:
        DataFrame with normalized column
    """
    df = df.copy()
    if col in df.columns:
        mapping = {'m': 'male', 'f': 'female', 0: 'male', 1: 'female'}
        df[col] = df[col].replace(mapping)
    return df


def group_cars(value):
    """Group car counts: 0, 1, 2, or '3+' for 3 or more.

    Args:
        value: Car count value (string or int)

    Returns:
        String representation: '0', '1', '2', or '3+'
    """
    try:
        value_int = int(value)
    except (ValueError, TypeError):
        return value

    if value_int >= 3:
        return '3+'
    else:
        return str(value_int)


# =============================================================================
# Logging Functions
# =============================================================================

def setup_logging(log_filename):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    log_path = os.path.join("logs", log_filename)
    
    logging.basicConfig(filename=log_path,
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


def read_config(path='config.ini', return_dataclass=False):
    """Read configuration from INI file.

    Args:
        path: Path to config file (default: 'config.ini')
        return_dataclass: If True, return Config dataclass; if False, return tuple (default: False)

    Returns:
        Config dataclass if return_dataclass=True, otherwise tuple of values (backward compatible)
    """
    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)

    try:
        config = configparser.ConfigParser()
        config_path = os.path.join(parent_directory, 'config', path)
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

        if return_dataclass:
            # Return Config dataclass for new scripts
            return Config(
                data_path=data_path,
                simulation_zone_name=simulation_zone_name,
                scenario=scenario,
                sim_output_folder=sim_output_folder,
                percentile=percentile,
                analysis_zone_name=analysis_zone_name,
                csv_folder=csv_folder,
                clean_csv_folder=clean_csv_folder,
                shapeFileName=shapeFileName,
                read_SynPop=read_SynPop,
                read_microcensus=read_microcensus,
                sample_for_debugging=sample_for_debugging,
                target_area=target_area
            )
        else:
            # Return tuple for backward compatibility with existing scripts
            return data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit()
