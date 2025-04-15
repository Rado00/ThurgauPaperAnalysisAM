"""
input data: (For example)
- microzensus/haushalte.csv
- microzensus/zielpersonen.csv
- ShapeFiles/Thurgau.shp

output data:
- microzensus/all_population.csv
"""
# Import necessary libraries
import pandas as pd
from functions.process_microcensus import *
from functions.commonFunctions import *
import warnings
pd.set_option('display.max_columns', None)

warnings.filterwarnings("ignore")

# Get the path to the current script folder
current_script_folder = os.getcwd()
functions_folder_path = os.path.join(current_script_folder, 'functions')
sys.path.append(os.path.abspath(functions_folder_path))

import functions.microcensusConstants as c


def execute_person(path):
    # Read the "zielpersonen.csv" data from the microzensus folder
    file_path_Ziel = os.path.join(path, "microzensus", "zielpersonen.csv")
    print(f"Constructed file path: {file_path_Ziel}")
    df_mz_persons = pd.read_csv(file_path_Ziel, sep=",", encoding="latin1", parse_dates=["USTag"])

    df_mz_persons["age"] = df_mz_persons["alter"]
    df_mz_persons["sex"] = df_mz_persons["gesl"] - 1  # Make zero-based
    df_mz_persons["person_id"] = df_mz_persons["HHNR"]
    df_mz_persons["person_weight"] = df_mz_persons["WP"]
    df_mz_persons["date"] = df_mz_persons["USTag"]

    # Convert Marital Status to a categorical variable (0: Single, 1: Married, 2: Separated)
    # Marital status
    df_mz_persons.loc[df_mz_persons["zivil"] == 1, "marital_status"] = c.MARITAL_STATUS_SINGLE
    df_mz_persons.loc[df_mz_persons["zivil"] == 2, "marital_status"] = c.MARITAL_STATUS_MARRIED
    df_mz_persons.loc[df_mz_persons["zivil"] == 3, "marital_status"] = c.MARITAL_STATUS_SEPARATE
    df_mz_persons.loc[df_mz_persons["zivil"] == 4, "marital_status"] = c.MARITAL_STATUS_SEPARATE
    df_mz_persons.loc[df_mz_persons["zivil"] == 5, "marital_status"] = c.MARITAL_STATUS_SINGLE
    df_mz_persons.loc[df_mz_persons["zivil"] == 6, "marital_status"] = c.MARITAL_STATUS_MARRIED
    df_mz_persons.loc[df_mz_persons["zivil"] == 7, "marital_status"] = c.MARITAL_STATUS_SEPARATE

    # Put the driving license equal to True if the person has a driving license
    df_mz_persons["driving_license"] = df_mz_persons["f20400a"] == 1

    # Convert the car availability to a categorical variable (0: Always, 1: Sometimes, 2: Never)
    df_mz_persons["car_availability"] = c.CAR_AVAILABILITY_NEVER
    df_mz_persons.loc[df_mz_persons["f42100e"] == 1, "car_availability"] = c.CAR_AVAILABILITY_ALWAYS
    df_mz_persons.loc[df_mz_persons["f42100e"] == 2, "car_availability"] = c.CAR_AVAILABILITY_SOMETIMES
    df_mz_persons.loc[df_mz_persons["f42100e"] == 3, "car_availability"] = c.CAR_AVAILABILITY_NEVER

    # Set the employed column equal to True if the person is employed
    # Employment (TODO: I know that LIMA uses a more fine-grained category here)
    df_mz_persons["employed"] = df_mz_persons["f40800_01"] != -99

    # Infer age class from age [6, 15, 18, 24, 30, 45, 65, 80]
    df_mz_persons["age_class"] = np.digitize(df_mz_persons["age"], c.AGE_CLASS_UPPER_BOUNDS)

    # Fix marital status (Makes young people, who are separated, be treated as single!)
    fix_marital_status(df_mz_persons)

    # Day of the observation
    # When the tag is 6 or 7, it is a weekend
    df_mz_persons["weekend"] = False
    df_mz_persons.loc[df_mz_persons["tag"] == 6, "weekend"] = True
    df_mz_persons.loc[df_mz_persons["tag"] == 7, "weekend"] = True

    # Here we extract a bit more than Kirill, but most likely it will be useful later
    df_mz_persons["subscriptions_ga"] = df_mz_persons["f41610a"] == 1
    df_mz_persons["subscriptions_halbtax"] = df_mz_persons["f41610b"] == 1
    df_mz_persons["subscriptions_verbund"] = df_mz_persons["f41610c"] == 1
    df_mz_persons["subscriptions_strecke"] = df_mz_persons["f41610d"] == 1
    df_mz_persons["subscriptions_gleis7"] = df_mz_persons["f41610e"] == 1
    df_mz_persons["subscriptions_junior"] = df_mz_persons["f41610f"] == 1
    df_mz_persons["subscriptions_other"] = df_mz_persons["f41610g"] == 1

    df_mz_persons["subscriptions_ga_class"] = df_mz_persons["f41651"] == 1
    df_mz_persons["subscriptions_verbund_class"] = df_mz_persons["f41653"] == 1
    df_mz_persons["subscriptions_strecke_class"] = df_mz_persons["f41654"] == 1

    # Education
    df_mz_persons["highest_education"] = np.nan
    df_mz_persons.loc[df_mz_persons["HAUSB"].isin([1, 2, 3, 4]), "highest_education"] = "primary"
    df_mz_persons.loc[df_mz_persons["HAUSB"].isin([5, 6, 7, 8, 9, 10, 11, 12]), "highest_education"] = "secondary"
    df_mz_persons.loc[df_mz_persons["HAUSB"].isin([13, 14, 15, 16]), "highest_education"] = "tertiary_professional"
    df_mz_persons.loc[df_mz_persons["HAUSB"].isin([17, 18, 19]), "highest_education"] = "tertiary_academic"
    df_mz_persons["highest_education"] = df_mz_persons["highest_education"].astype("category")

    # Parking
    df_mz_persons["parking_work"] = "unknown"
    df_mz_persons.loc[df_mz_persons["f41300"] == 1, "parking_work"] = "free"
    df_mz_persons.loc[df_mz_persons["f41300"] == 2, "parking_work"] = "paid"
    df_mz_persons.loc[df_mz_persons["f41300"] == 3, "parking_work"] = "no"
    df_mz_persons["parking_work"] = df_mz_persons["parking_work"].astype("category")

    df_mz_persons["parking_education"] = "unknown"
    df_mz_persons.loc[df_mz_persons["f41301"] == 1, "parking_education"] = "free"
    df_mz_persons.loc[df_mz_persons["f41301"] == 2, "parking_education"] = "paid"
    df_mz_persons.loc[df_mz_persons["f41301"] == 3, "parking_education"] = "no"
    df_mz_persons["parking_education"] = df_mz_persons["parking_education"].astype("category")

    df_mz_persons["parking_cost_work"] = np.maximum(0, df_mz_persons["f41400"].astype(float))
    df_mz_persons["parking_cost_education"] = np.maximum(0, df_mz_persons["f41401"].astype(float))

    # Wrap up
    final_df_mz_persons = df_mz_persons[[
        "person_id",
        "age", "sex",
        "marital_status",
        "driving_license",
        "car_availability",
        "employed",
        "highest_education",
        "parking_work", "parking_cost_work",
        "parking_education", "parking_cost_education",
        "subscriptions_ga",
        "subscriptions_halbtax",
        "subscriptions_verbund",
        "subscriptions_strecke",
        "subscriptions_gleis7",
        "subscriptions_junior",
        "subscriptions_other",
        "subscriptions_ga_class",
        "subscriptions_verbund_class",
        "subscriptions_strecke_class",
        "age_class", "person_weight",
        "weekend", "date"
    ]]
    return final_df_mz_persons


def execute_household(path):
    df_mz_households = pd.read_csv(
        "%s\\microzensus\\haushalte.csv" % path, sep=",", encoding="latin1")

    # Simple attributes
    df_mz_households["home_structure"] = df_mz_households["W_STRUKTUR_AGG_2000"]
    df_mz_households["household_size"] = df_mz_households["hhgr"]
    df_mz_households["number_of_cars"] = np.maximum(0, df_mz_households["f30100"])
    df_mz_households["number_of_bikes"] = df_mz_households["f32200a"]
    df_mz_households["person_id"] = df_mz_households["HHNR"]
    df_mz_households["household_weight"] = df_mz_households["WM"]

    # Income
    df_mz_households["income_class"] = df_mz_households["F20601"] - 1  # Turn into zero-based class
    df_mz_households["income_class"] = np.maximum(-1, df_mz_households["income_class"])  # Make all "invalid" entries -1

    # Convert coordinates to LV95
    coords = df_mz_households[["W_X_CH1903", "W_Y_CH1903"]].values
    transformer = pyproj.Transformer.from_crs(c.CH1903, c.CH1903_PLUS)
    x, y = transformer.transform(coords[:, 0], coords[:, 1])
    df_mz_households.loc[:, "home_x"] = x
    df_mz_households.loc[:, "home_y"] = y

    # Class variable for number of cars
    df_mz_households["number_of_cars_class"] = 0
    df_mz_households.loc[df_mz_households["number_of_cars"] > 0, "number_of_cars_class"] = np.minimum(
        c.MAX_NUMBER_OF_CARS_CLASS, df_mz_households["number_of_cars"])

    # Bike availability depends on household size. (TODO: Would it make sense to use the same concept for cars?)
    df_mz_households["number_of_bikes_class"] = c.BIKE_AVAILABILITY_FOR_NONE
    df_mz_households.loc[
        df_mz_households["number_of_bikes"] > 0, "number_of_bikes_class"] = c.BIKE_AVAILABILITY_FOR_SOME
    df_mz_households.loc[
        df_mz_households["number_of_bikes"] >= df_mz_households["household_size"],
        "number_of_bikes_class"] = c.BIKE_AVAILABILITY_FOR_ALL

    # Household size class
    assign_household_class(df_mz_households)

    # Region information
    # (acc. to Analyse der SP-Befragung 2015 zur Verkehrsmodus- und Routenwahl)
    df_mz_households["canton_id"] = df_mz_households["W_KANTON"]
    final_df_mz_households = impute_sp_region(df_mz_households)

    return final_df_mz_households[[
        "person_id", "household_size", "number_of_cars", "number_of_bikes", "income_class",
        "home_x", "home_y", "household_size_class", "number_of_cars_class", "number_of_bikes_class", "household_weight",
        "sp_region", "canton_id"]]


def get_log_filename():
    # Get the full path of the script
    file_path = __file__
    # Extract only the file name
    log_filename = os.path.basename(file_path)
    log_filename = log_filename.replace(".py", ".log")
    return log_filename


if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName = read_config()
    analysis_zone_path = os.path.join(data_path, analysis_zone_name)

    df_mz_persons = execute_person(analysis_zone_path)
    logging.info(f"Person data loaded and excuted successfully from the {analysis_zone_path} folder.")
    df_mz_households = execute_household(analysis_zone_path)
    logging.info(f"Household data loaded and excuted successfully from the {analysis_zone_path} folder.")

    df = pd.merge(df_mz_persons, df_mz_households, on='person_id', how='left')

    df.to_csv(analysis_zone_path + '\\microzensus\\all_population.csv', index=False)