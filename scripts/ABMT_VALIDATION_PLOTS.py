import os
import sys
import matsim
import logging
import warnings
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 50)

from functions.commonFunctions import (
    setup_logging, get_log_filename, read_config
)

if __name__ == '__main__':
    setup_logging(get_log_filename())
    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()

    script_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(script_path)
    plots_path = os.path.join(os.path.dirname(parent_dir), "plots")
    scenario_path: str = os.path.join(data_path, simulation_zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    if not os.path.exists(plots_path):
        os.makedirs(plots_path)
    logging.info(f"Plots directory set to: {plots_path}")

    # =========================================================================
    # Next STEP: Read Shapefiles
    # =========================================================================
    shapefile_zone_25 = os.path.join(
        r"C:\Users\sarf\Documents\projects\corrado_matsim\DATA_ABM\2024_Paper2_Data\validation_shapefiles",
        "25_ShapeFile.shp")
    ThurgauEnlargedFixed = os.path.join(
        r"C:\Users\sarf\Documents\projects\corrado_matsim\DATA_ABM\2024_Paper2_Data\validation_shapefiles",
        "ThurgauEnlargedFixed.shp")
    ThurgauKanton_Connected = os.path.join(
        r"C:\Users\sarf\Documents\projects\corrado_matsim\DATA_ABM\2024_Paper2_Data\validation_shapefiles",
        "ThurgauKanton_Connected.shp")
    gdf = gpd.read_file(shapefile_zone_25, engine="pyogrio")
    area_polygon = gdf.iloc[0]['geometry']
    logging.info("Shapefile loaded successfully and area_polygon created")

    # =========================================================================
    # Next STEP: Load configuration
    # =========================================================================
    cfg = read_config(return_dataclass=True)
    sim_output_plots_path = os.path.join(plots_path, cfg.sim_output_folder.split("/")[-1])
    n_rows = None

    if not os.path.exists(sim_output_plots_path):
        os.makedirs(sim_output_plots_path)
        logging.info(f"Simulation output plots directory created at: {sim_output_plots_path}")

    # =========================================================================
    # Next STEP: Load Microzone Population Data and Synthetic Population Data
    # =========================================================================
    plans_sim = matsim.plan_reader_dataframe(os.path.join(output_folder_path, "output_plans.xml.gz"))
    logging.info("Output plans data loaded successfully")

    clean_person_sim = plans_sim.persons[
        ['id', 'age', 'sex', 'bikeAvailability', 'carAvail', 'employed', 'hasLicense', 'home_coordiante_x',
         'home_coordiante_y', 'householdIncome']]

    # convert age to numeric, coerce errors to NaN
    clean_person_sim['age'] = pd.to_numeric(clean_person_sim['age'], errors='coerce')
    clean_person_sim = clean_person_sim[clean_person_sim['age'] >= 6]
    clean_person_sim = clean_person_sim[
        clean_person_sim['home_coordiante_x'].notnull() & clean_person_sim['home_coordiante_y'].notnull()]
    clean_person_sim.rename(
        columns={'id': 'person_id',
                 'hasLicense': 'has_license', 'home_coordiante_x': 'home_x', 'home_coordiante_y': 'home_y',
                 'householdIncome': 'income_class'}, inplace=True)
    clean_person_sim['car_availability'] = clean_person_sim['carAvail'].apply(lambda x: False if x == 'never' else True)
    clean_person_sim.drop(columns=['carAvail'], inplace=True)
    clean_person_sim['bike_availability'] = clean_person_sim['bikeAvailability'].apply(lambda x: False if x == 'FOR_NONE' else True)
    clean_person_sim.drop(columns=['bikeAvailability'], inplace=True)
    clean_person_sim['home_x'] = clean_person_sim['home_x'].astype(float)
    clean_person_sim['home_y'] = clean_person_sim['home_y'].astype(float)
    clean_person_sim['home_coordinate'] = gpd.points_from_xy(clean_person_sim['home_x'], clean_person_sim['home_y'])
    clean_person_sim['employment_status'] = clean_person_sim['employed'].apply(lambda x: True if x == 'true' else False)
    clean_person_sim.drop(columns=['employed'], inplace=True)
    clean_person_sim['employed'] = clean_person_sim['employment_status']
    clean_person_sim.drop(columns=['employment_status'], inplace=True)
    logging.info("Cleaned person sim data successfully and shapefile created successfully")

    sim_home_points = gpd.GeoSeries(
        gpd.points_from_xy(clean_person_sim['home_x'], clean_person_sim['home_y']),
        crs=gdf.crs,
        index=clean_person_sim.index
    )
    clean_person_sim = clean_person_sim[['person_id', 'age', 'sex', 'car_availability', 'bike_availability', 'employed', 'income_class', 'home_x', 'home_y', ]]
    logging.info("Simulation persons data cleaned successfully")

    # if cfg.read_SynPop:
    #     try:
    #         plans = matsim.plan_reader_dataframe(os.path.join(scenario_path, f"population.xml.gz"))
    #         df_persons_synt = plans.persons
    #         logging.info("Synthetic population data loaded successfully")
    #     except Exception as e:
    #         logging.error("Error reading synthetic population files: " + str(e))
    #         sys.exit()

    if cfg.read_microcensus:
        try:
            df_persons_mic = pd.read_csv(os.path.join(cfg.analysis_zone_path, "microzensus", "all_population.csv"),
                                         low_memory=False, nrows=n_rows)
            clean_person_mic = df_persons_mic[
                ['person_id', 'age', 'sex', 'car_availability', 'employed', 'income_class', 'home_x', 'home_y',
                 'number_of_bikes', 'person_weight']]

            clean_person_mic = clean_person_mic[clean_person_mic['age'] >= 6]
            clean_person_mic = clean_person_mic[
                clean_person_mic['home_x'].notnull() & clean_person_mic['home_y'].notnull()]

            clean_person_mic['bike_availability'] = clean_person_mic['number_of_bikes'].apply(lambda x: True if x > 0 else False)
            clean_person_mic['has_car'] = clean_person_mic['car_availability'].apply(lambda x: True if x != 0 else False)
            clean_person_mic.drop(columns=['car_availability'], inplace=True)
            clean_person_mic['car_availability'] = clean_person_mic['has_car']
            clean_person_mic.drop(columns=['has_car'], inplace=True)
            clean_person_mic.drop(columns=['number_of_bikes'], inplace=True)
            clean_person_mic['home_x'] = clean_person_mic['home_x'].astype(float)
            clean_person_mic['home_y'] = clean_person_mic['home_y'].astype(float)
            clean_person_mic['home_coordinate'] = gpd.points_from_xy(clean_person_mic['home_x'], clean_person_mic['home_y'])

            mic_home_points = gpd.GeoSeries(gpd.points_from_xy(clean_person_mic['home_x'], clean_person_mic['home_y']),
                                            crs=gdf.crs,
                                            index=clean_person_mic.index)
            clean_person_mic = clean_person_mic[['person_id', 'age', 'sex', 'car_availability', 'bike_availability', 'employed', 'income_class', 'home_x', 'home_y', 'person_weight']]
            logging.info("Microcensus data loaded successfully")
        except Exception as e:
            logging.error("Error reading microcensus files: " + str(e))
            sys.exit()

    # =========================================================================
    # Next STEP: Data Filtering and Cleaning
    # =========================================================================
    try:
        population_all_activities_inside_sim = pd.read_csv(
            os.path.join(cfg.data_path_clean, "population_all_activities_inside_sim.csv"))
        logging.info("Population with all activities inside simulation area loaded successfully")
        population_at_least_one_activity_inside_sim = pd.read_csv(
            os.path.join(cfg.data_path_clean, "population_at_least_one_activity_inside_sim.csv"))
        logging.info("Population with at least one activity inside simulation area loaded successfully")
        population_all_activities_inside_mic = pd.read_csv(
            os.path.join(cfg.data_path_clean, "population_all_activities_inside_mic.csv"))
        logging.info("Population with all activities inside microcensus area loaded successfully")
        population_at_least_one_activity_inside_mic = pd.read_csv(
            os.path.join(cfg.data_path_clean, "population_at_least_one_activity_inside_mic.csv"))
        logging.info("Population with at least one activity inside microcensus area loaded successfully")
    except Exception as e:
        logging.error("Error reading filtered population files: " + str(e))
        sys.exit()
    try:
        population_sim_home_inside = clean_person_sim[
            sim_home_points.within(area_polygon)
        ]
        logging.info("Filtered simulation population with home inside area_polygon successfully")
    except Exception as e:
        logging.error("Error filtering simulation population with home inside area_polygon: " + str(e))
        sys.exit()

    try:
        population_mic_home_inside = clean_person_mic[
            mic_home_points.within(area_polygon)
        ]
        logging.info("Filtered microcensus population with home inside area_polygon successfully")
    except Exception as e:
        logging.error("Error filtering microcensus population with home inside area_polygon: " + str(e))
        sys.exit()

    analyse_data_sim = population_sim_home_inside
    analyse_data_mic = population_mic_home_inside

    # =========================================================================
    # Next STEP: Plot Age Distribution Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Age Distribution Comparison Plot Generation Started")

            # Define age bins (1-year intervals)
            age_bins = range(0, 101, 1)

            # Calculate age distribution for Microcensus (weighted by person_weight)
            df_mic_age = analyse_data_mic.copy()
            df_mic_age['age_bin'] = pd.cut(df_mic_age['age'], bins=age_bins, right=False)
            mic_age_dist = df_mic_age.groupby('age_bin')['person_weight'].sum()
            mic_age_pct = (mic_age_dist / mic_age_dist.sum() * 100).values

            # Calculate age distribution for Synthetic Population
            df_synt_age = analyse_data_sim.copy()
            df_synt_age['age_bin'] = pd.cut(df_synt_age['age'], bins=age_bins, right=False)
            synt_age_dist = df_synt_age.groupby('age_bin').size()
            synt_age_pct = (synt_age_dist / synt_age_dist.sum() * 100).values

            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 5))

            # Create x-axis positions (midpoints of bins)
            x_positions = [(age_bins[i] + age_bins[i + 1]) / 2 for i in range(len(age_bins) - 1)]
            bar_width = 0.3  # Thinner bars

            # Plot bars with darker colors
            ax.bar(x_positions, mic_age_pct, width=bar_width,
                   label='Population Microcensus', color='#001BB7', alpha=0.9, edgecolor='none')
            ax.bar(x_positions, synt_age_pct, width=bar_width,
                   label='Population Synthetic', color='#ff0000', alpha=0.8, edgecolor='none')

            # Formatting
            ax.set_xlabel('Age', fontsize=11)
            ax.set_ylabel('Percentage (%)', fontsize=11)
            ax.set_xlim(0, 100)
            ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
            ax.legend(title='Dataset', loc='upper right', frameon=True)
            ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)

            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'age_distribution_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Age distribution comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating age distribution comparison plot: " + str(e))
    else:
        logging.warning("Skipping age distribution comparison plot due to missing data")

    # =========================================================================
    # Next STEP: Plot Gender Distribution Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Gender Distribution Comparison Plot Generation Started")

            # Process Synthetic Population gender data
            synt_gender_counts = analyse_data_sim['sex'].value_counts()

            # Process Microcensus gender data (weighted)
            mic_gender_counts = analyse_data_mic.groupby('sex')['person_weight'].sum()

            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Define colors for male and female
            colors = ['#6b7fda', '#e8664d']  # Blue for male, Red/Orange for female

            # Plot Synthetic Population pie chart
            wedges1, texts1, autotexts1 = ax1.pie(
                synt_gender_counts.values,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 13, 'weight': 'bold', 'color': 'white'}
            )
            ax1.set_title('Gender Distribution Synthetic Population', fontsize=12, pad=20)

            # Plot Microcensus pie chart
            wedges2, texts2, autotexts2 = ax2.pie(
                mic_gender_counts.values,
                labels=None,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 13, 'weight': 'bold', 'color': 'white'}
            )
            ax2.set_title('Gender Distribution - Microcensus', fontsize=12, pad=20)

            # Add legend
            labels = ['male', 'female']
            fig.legend(labels, loc='center right', bbox_to_anchor=(1.0, 0.5),
                       frameon=False, fontsize=11)

            plt.tight_layout()
            plt.subplots_adjust(right=0.88)  # Make room for legend

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'gender_distribution_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Gender distribution comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating gender distribution comparison plot: " + str(e))
    else:
        logging.warning("Skipping gender distribution comparison plot due to missing data")

    # =========================================================================
    # Next STEP: Plot Car Availability Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Car Availability Comparison Plot Generation Started")

            # Process Synthetic Population car availability
            synt_car_counts = analyse_data_sim['car_availability'].value_counts()
            synt_car_pct = (synt_car_counts / synt_car_counts.sum() * 100)

            # Process Microcensus car availability (weighted)
            mic_car_counts = analyse_data_mic.groupby('car_availability')['person_weight'].sum()
            mic_car_pct = (mic_car_counts / mic_car_counts.sum() * 100)

            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))

            # Define categories
            categories = [False, True]
            category_labels = ['No Car', 'Has Car']
            x_pos = range(len(categories))
            bar_width = 0.35

            # Get values for each category
            mic_values = [mic_car_pct.get(cat, 0) for cat in categories]
            synt_values = [synt_car_pct.get(cat, 0) for cat in categories]

            # Create bars
            bars1 = ax.bar([x - bar_width / 2 for x in x_pos], mic_values, bar_width,
                           label='Microcensus - Car Availability', color='#001BB7', alpha=0.9)
            bars2 = ax.bar([x + bar_width / 2 for x in x_pos], synt_values, bar_width,
                           label='Synthetic - Car Availability', color='#ff0000', alpha=0.8)

            # Formatting
            ax.set_xlabel('Car Availability', fontsize=12)
            ax.set_ylabel('Percentage (%)', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(category_labels)
            ax.legend(title='Dataset', loc='upper center', frameon=True)
            ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_ylim(0, max(max(mic_values), max(synt_values)) * 1.1)

            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'car_availability_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Car availability comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating car availability comparison plot: " + str(e))
    else:
        logging.warning("Skipping car availability comparison plot due to missing data")

    # =========================================================================
    # Next STEP: Plot Bike Availability Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Bike Availability Comparison Plot Generation Started")

            # Process Synthetic Population bike availability
            synt_bike_counts = analyse_data_sim['bike_availability'].value_counts()
            synt_bike_pct = (synt_bike_counts / synt_bike_counts.sum() * 100)

            # Process Microcensus bike availability (weighted)
            mic_bike_counts = analyse_data_mic.groupby('bike_availability')['person_weight'].sum()
            mic_bike_pct = (mic_bike_counts / mic_bike_counts.sum() * 100)

            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))

            # Define categories
            categories = [False, True]
            category_labels = ['No Bike', 'Has Bike']
            x_pos = range(len(categories))
            bar_width = 0.35

            # Get values for each category
            mic_values = [mic_bike_pct.get(cat, 0) for cat in categories]
            synt_values = [synt_bike_pct.get(cat, 0) for cat in categories]

            # Create bars
            bars1 = ax.bar([x - bar_width / 2 for x in x_pos], mic_values, bar_width,
                           label='Microcensus - Bike Availability', color='#001BB7', alpha=0.9)
            bars2 = ax.bar([x + bar_width / 2 for x in x_pos], synt_values, bar_width,
                           label='Synthetic - Bike Availability', color='#ff0000', alpha=0.8)

            # Formatting
            ax.set_xlabel('Bike Availability', fontsize=12)
            ax.set_ylabel('Percentage (%)', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(category_labels)
            ax.legend(title='Dataset', loc='upper center', frameon=True)
            ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_ylim(0, max(max(mic_values), max(synt_values)) * 1.1)

            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'bike_availability_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Bike availability comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating bike availability comparison plot: " + str(e))
    else:
        logging.warning("Skipping bike availability comparison plot due to missing data")

    # =========================================================================
    # Next STEP: Plot Employment Status Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Employment Status Comparison Plot Generation Started")

            # Process Synthetic Population employment status
            synt_employed_counts = analyse_data_sim['employed'].value_counts()
            synt_employed_pct = (synt_employed_counts / synt_employed_counts.sum() * 100)

            # Process Microcensus employment status (weighted)
            mic_employed_counts = analyse_data_mic.groupby('employed')['person_weight'].sum()
            mic_employed_pct = (mic_employed_counts / mic_employed_counts.sum() * 100)

            # Create the plot
            fig, ax = plt.subplots(figsize=(8, 6))

            # Define categories
            categories = [False, True]
            category_labels = ['Not Employed', 'Employed']
            x_pos = range(len(categories))
            bar_width = 0.35

            # Get values for each category
            mic_values = [mic_employed_pct.get(cat, 0) for cat in categories]
            synt_values = [synt_employed_pct.get(cat, 0) for cat in categories]

            # Create bars
            bars1 = ax.bar([x - bar_width / 2 for x in x_pos], mic_values, bar_width,
                           label='Microcensus - Employment', color='#001BB7', alpha=0.9)
            bars2 = ax.bar([x + bar_width / 2 for x in x_pos], synt_values, bar_width,
                           label='Synthetic - Employment', color='#ff0000', alpha=0.8)

            # Formatting
            ax.set_xlabel('Employment Status', fontsize=12)
            ax.set_ylabel('Percentage (%)', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(category_labels)
            ax.legend(title='Dataset', loc='upper center', frameon=True)
            ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_ylim(0, max(max(mic_values), max(synt_values)) * 1.1)

            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'employment_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Employment status comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating employment status comparison plot: " + str(e))
    else:
        logging.warning("Skipping employment status comparison plot due to missing data")

    # =========================================================================
    # Next STEP: Plot Income Class Comparison
    # =========================================================================
    if cfg.read_SynPop and cfg.read_microcensus:
        try:
            logging.info("Income Class Comparison Plot Generation Started")

            # Define income class categories and labels
            income_bins = [0, 2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, float('inf')]
            income_labels = [
                'Under CHF 2000',
                'CHF 2000 to 4000',
                'CHF 4001 to 6000',
                'CHF 6001 to 8000',
                'CHF 8001 to 10000',
                'CHF 10001 to 12000',
                'CHF 12001 to 14000',
                'CHF 14001 to 16000'
            ]

            # Process Synthetic Population income class
            synt_income = analyse_data_sim.copy()
            synt_income['income_category'] = pd.cut(
                synt_income['income_class'],
                bins=income_bins,
                labels=income_labels,
                right=False
            )
            synt_income_counts = synt_income['income_category'].value_counts()
            synt_income_pct = (synt_income_counts / synt_income_counts.sum() * 100)

            # Process Microcensus income class (weighted)
            mic_income = analyse_data_mic.copy()
            mic_income['income_category'] = pd.cut(
                mic_income['income_class'],
                bins=income_bins,
                labels=income_labels,
                right=False
            )
            mic_income_counts = mic_income.groupby('income_category')['person_weight'].sum()
            mic_income_pct = (mic_income_counts / mic_income_counts.sum() * 100)

            # Create the plot
            fig, ax = plt.subplots(figsize=(14, 6))

            # X positions
            x_pos = range(len(income_labels))
            bar_width = 0.35

            # Get values for each category
            mic_values = [mic_income_pct.get(cat, 0) for cat in income_labels]
            synt_values = [synt_income_pct.get(cat, 0) for cat in income_labels]

            # Create bars
            bars1 = ax.bar([x - bar_width / 2 for x in x_pos], mic_values, bar_width,
                           label='Microcensus - Percentage', color='#001BB7', alpha=0.9)
            bars2 = ax.bar([x + bar_width / 2 for x in x_pos], synt_values, bar_width,
                           label='Synthetic - Percentage', color='#ff0000', alpha=0.8)

            # Formatting
            ax.set_xlabel('Income Class', fontsize=12)
            ax.set_ylabel('Percentage (%)', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(income_labels, rotation=45, ha='right')
            ax.legend(title='Dataset', loc='upper center', frameon=True)
            ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_ylim(0, max(max(mic_values), max(synt_values)) * 1.1)

            plt.tight_layout()

            # Save the plot
            output_path = os.path.join(sim_output_plots_path, 'income_class_comparison.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logging.info(f"Income class comparison plot saved to: {output_path}")

        except Exception as e:
            logging.error("Error generating income class comparison plot: " + str(e))
    else:
        logging.warning("Skipping income class comparison plot due to missing data")
