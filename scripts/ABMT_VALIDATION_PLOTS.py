import os
import sys
import matsim
import logging
import warnings
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 50)

from functions.commonFunctions import (
    setup_logging, get_log_filename, read_config
)


def create_comparison_bar_plot(
        data_dict,
        categories,
        category_labels,
        title,
        xlabel,
        ylabel,
        output_path,
        colors=None
):
    """
    Generic function to create comparison bar plots

    Args:
        data_dict: Dictionary with dataset names as keys and values as lists
        categories: List of category values
        category_labels: List of labels for categories
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        output_path: Path to save the plot
        colors: Optional dictionary of colors for each dataset
    """
    if colors is None:
        colors = {
            'Microcensus': '#001BB7',
            'Synthetic': '#ff0000',
            'Simulation': '#00aa00'
        }

    fig, ax = plt.subplots(figsize=(10, 6))

    x_pos = range(len(categories))
    bar_width = 0.8 / len(data_dict)  # Dynamic width based on number of datasets

    for idx, (dataset_name, values) in enumerate(data_dict.items()):
        offset = (idx - (len(data_dict) - 1) / 2) * bar_width
        bars = ax.bar(
            [x + offset for x in x_pos],
            values,
            bar_width,
            label=dataset_name,
            color=colors.get(dataset_name, '#999999'),
            alpha=0.9
        )

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, pad=20)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(category_labels, rotation=45 if len(category_labels) > 5 else 0, ha='right')
    ax.legend(title='Dataset', loc='best', frameon=True)
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    # Set y-limit with some headroom
    max_val = max([max(vals) for vals in data_dict.values()])
    ax.set_ylim(0, max_val * 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logging.info(f"Plot saved to: {output_path}")


def load_and_clean_simulation_data(output_folder_path, area_polygon, gdf_crs):
    """Load and clean simulation output data"""
    logging.info("Loading simulation output plans...")

    plans_sim = matsim.plan_reader_dataframe(
        os.path.join(output_folder_path, "output_plans.xml.gz")
    )
    logging.info("Output plans data loaded successfully")

    # ============================================================================
    # DIAGNOSTIC LOGGING - Understanding the data structure
    # ============================================================================
    logging.info("\n" + "=" * 80)
    logging.info("SIMULATION DATA STRUCTURE DIAGNOSTICS")
    logging.info("=" * 80)

    # Check what dataframes are available
    logging.info("\n📊 Available dataframes in plans object:")
    available_dfs = []
    for attr in dir(plans_sim):
        if not attr.startswith('_'):
            obj = getattr(plans_sim, attr)
            if isinstance(obj, pd.DataFrame):
                available_dfs.append(attr)
                logging.info(f"  ✓ {attr}: {len(obj)} records")

    # Detailed info about persons dataframe
    if hasattr(plans_sim, 'persons'):
        logging.info("\n👥 PERSONS DataFrame:")
        logging.info(f"  Shape: {plans_sim.persons.shape}")
        logging.info(f"  Columns ({len(plans_sim.persons.columns)}): {list(plans_sim.persons.columns)}")
        logging.info("\n  Column Details:")
        for col in plans_sim.persons.columns:
            dtype = plans_sim.persons[col].dtype
            n_unique = plans_sim.persons[col].nunique()
            n_null = plans_sim.persons[col].isnull().sum()
            logging.info(f"    {col}:")
            logging.info(f"      - Type: {dtype}")
            logging.info(f"      - Unique values: {n_unique}")
            logging.info(f"      - Null: {n_null} ({n_null / len(plans_sim.persons) * 100:.1f}%)")

            # Show sample values for categorical columns
            if n_unique < 20:
                unique_vals = plans_sim.persons[col].unique()
                logging.info(f"      - Values: {unique_vals[:10]}")

    # Detailed info about legs/trips dataframe
    if hasattr(plans_sim, 'legs'):
        logging.info("\n🚗 LEGS/TRIPS DataFrame:")
        logging.info(f"  Shape: {plans_sim.legs.shape}")
        logging.info(f"  Columns ({len(plans_sim.legs.columns)}): {list(plans_sim.legs.columns)}")
        logging.info("\n  Column Details:")
        for col in plans_sim.legs.columns[:15]:  # First 15 columns to avoid too much output
            dtype = plans_sim.legs[col].dtype
            n_unique = plans_sim.legs[col].nunique()
            n_null = plans_sim.legs[col].isnull().sum()
            logging.info(f"    {col}:")
            logging.info(f"      - Type: {dtype}")
            logging.info(f"      - Unique values: {n_unique}")
            logging.info(f"      - Null: {n_null} ({n_null / len(plans_sim.legs) * 100:.1f}%)")

            # Show sample values for categorical columns
            if n_unique < 20 and n_unique > 0:
                unique_vals = plans_sim.legs[col].unique()
                logging.info(f"      - Values: {unique_vals[:10]}")

        # Mode distribution
        if 'mode' in plans_sim.legs.columns:
            logging.info("\n  🚦 MODE DISTRIBUTION:")
            mode_counts = plans_sim.legs['mode'].value_counts()
            for mode, count in mode_counts.head(10).items():
                pct = count / len(plans_sim.legs) * 100
                logging.info(f"    {mode}: {count} ({pct:.1f}%)")

    # Detailed info about activities dataframe
    if hasattr(plans_sim, 'activities'):
        logging.info("\n📍 ACTIVITIES DataFrame:")
        logging.info(f"  Shape: {plans_sim.activities.shape}")
        logging.info(f"  Columns ({len(plans_sim.activities.columns)}): {list(plans_sim.activities.columns)}")

        # Activity type distribution
        if 'type' in plans_sim.activities.columns:
            logging.info("\n  🎯 ACTIVITY TYPE DISTRIBUTION:")
            activity_counts = plans_sim.activities['type'].value_counts()
            for activity, count in activity_counts.head(10).items():
                pct = count / len(plans_sim.activities) * 100
                logging.info(f"    {activity}: {count} ({pct:.1f}%)")

    # Sample records
    logging.info("\n📋 SAMPLE PERSON RECORD (first record):")
    if len(plans_sim.persons) > 0:
        sample = plans_sim.persons.iloc[0]
        for col, val in sample.items():
            logging.info(f"  {col}: {val}")

    logging.info("\n" + "=" * 80)
    logging.info("END OF DIAGNOSTICS")
    logging.info("=" * 80 + "\n")

    # ============================================================================
    # Continue with normal data processing
    # ============================================================================

    clean_person_sim = plans_sim.persons[[
        'id', 'age', 'sex', 'bikeAvailability', 'carAvail', 'employed',
        'hasLicense', 'home_coordiante_x', 'home_coordiante_y', 'householdIncome'
    ]].copy()

    # Clean and transform data
    clean_person_sim['age'] = pd.to_numeric(clean_person_sim['age'], errors='coerce')
    clean_person_sim = clean_person_sim[clean_person_sim['age'] >= 6]
    clean_person_sim = clean_person_sim[
        clean_person_sim['home_coordiante_x'].notnull() &
        clean_person_sim['home_coordiante_y'].notnull()
        ]

    # Rename columns
    clean_person_sim.rename(columns={
        'id': 'person_id',
        'hasLicense': 'has_license',
        'home_coordiante_x': 'home_x',
        'home_coordiante_y': 'home_y',
        'householdIncome': 'income_class'
    }, inplace=True)

    # Transform categorical variables
    clean_person_sim['car_availability'] = clean_person_sim['carAvail'].apply(
        lambda x: False if x == 'never' else True
    )
    clean_person_sim.drop(columns=['carAvail'], inplace=True)

    clean_person_sim['bike_availability'] = clean_person_sim['bikeAvailability'].apply(
        lambda x: False if x == 'FOR_NONE' else True
    )
    clean_person_sim.drop(columns=['bikeAvailability'], inplace=True)

    clean_person_sim['employed'] = clean_person_sim['employed'].apply(
        lambda x: True if x == 'true' else False
    )

    # Create geometry
    clean_person_sim['home_x'] = clean_person_sim['home_x'].astype(float)
    clean_person_sim['home_y'] = clean_person_sim['home_y'].astype(float)

    # Filter by area
    sim_home_points = gpd.GeoSeries(
        gpd.points_from_xy(clean_person_sim['home_x'], clean_person_sim['home_y']),
        crs=gdf_crs,
        index=clean_person_sim.index
    )

    population_sim_home_inside = clean_person_sim[sim_home_points.within(area_polygon)]

    # Select final columns
    population_sim_home_inside = population_sim_home_inside[[
        'person_id', 'age', 'sex', 'car_availability', 'bike_availability',
        'employed', 'income_class', 'home_x', 'home_y'
    ]]

    logging.info(f"Simulation data cleaned. Population size: {len(population_sim_home_inside)}")

    # Return both cleaned data and original plans for additional validations
    return population_sim_home_inside, plans_sim


def load_and_clean_microcensus_data(analysis_zone_path, area_polygon, gdf_crs, n_rows=None):
    """Load and clean Microcensus data"""
    logging.info("Loading Microcensus data...")

    df_persons_mic = pd.read_csv(
        os.path.join(analysis_zone_path, "microzensus", "all_population.csv"),
        low_memory=False,
        nrows=n_rows
    )

    # ============================================================================
    # DIAGNOSTIC LOGGING - Understanding the Microcensus data structure
    # ============================================================================
    logging.info("\n" + "=" * 80)
    logging.info("MICROCENSUS DATA STRUCTURE DIAGNOSTICS")
    logging.info("=" * 80)

    logging.info(f"\n📊 Microcensus DataFrame:")
    logging.info(f"  Shape: {df_persons_mic.shape}")
    logging.info(f"  Columns ({len(df_persons_mic.columns)}): {list(df_persons_mic.columns)}")

    logging.info("\n  Column Details:")
    for col in df_persons_mic.columns[:20]:  # First 20 columns
        dtype = df_persons_mic[col].dtype
        n_unique = df_persons_mic[col].nunique()
        n_null = df_persons_mic[col].isnull().sum()
        logging.info(f"    {col}:")
        logging.info(f"      - Type: {dtype}")
        logging.info(f"      - Unique values: {n_unique}")
        logging.info(f"      - Null: {n_null} ({n_null / len(df_persons_mic) * 100:.1f}%)")

        # Show sample values for categorical columns
        if n_unique < 20 and n_unique > 0:
            unique_vals = df_persons_mic[col].unique()
            logging.info(f"      - Values: {unique_vals[:10]}")

    logging.info("\n📋 SAMPLE MICROCENSUS RECORD (first record):")
    if len(df_persons_mic) > 0:
        sample = df_persons_mic.iloc[0]
        for col, val in sample.items():
            logging.info(f"  {col}: {val}")

    logging.info("\n" + "=" * 80)
    logging.info("END OF MICROCENSUS DIAGNOSTICS")
    logging.info("=" * 80 + "\n")

    # ============================================================================
    # Continue with normal data processing
    # ============================================================================

    clean_person_mic = df_persons_mic[[
        'person_id', 'age', 'sex', 'car_availability', 'employed',
        'income_class', 'home_x', 'home_y', 'number_of_bikes', 'person_weight'
    ]].copy()

    # Filter and clean
    clean_person_mic = clean_person_mic[clean_person_mic['age'] >= 6]
    clean_person_mic = clean_person_mic[
        clean_person_mic['home_x'].notnull() &
        clean_person_mic['home_y'].notnull()
        ]

    # Transform variables
    clean_person_mic['bike_availability'] = clean_person_mic['number_of_bikes'].apply(
        lambda x: True if x > 0 else False
    )
    clean_person_mic['car_availability'] = clean_person_mic['car_availability'].apply(
        lambda x: True if x != 0 else False
    )
    clean_person_mic.drop(columns=['number_of_bikes'], inplace=True)

    # Create geometry and filter by area
    clean_person_mic['home_x'] = clean_person_mic['home_x'].astype(float)
    clean_person_mic['home_y'] = clean_person_mic['home_y'].astype(float)

    mic_home_points = gpd.GeoSeries(
        gpd.points_from_xy(clean_person_mic['home_x'], clean_person_mic['home_y']),
        crs=gdf_crs,
        index=clean_person_mic.index
    )

    population_mic_home_inside = clean_person_mic[mic_home_points.within(area_polygon)]

    # Select final columns
    population_mic_home_inside = population_mic_home_inside[[
        'person_id', 'age', 'sex', 'car_availability', 'bike_availability',
        'employed', 'income_class', 'home_x', 'home_y', 'person_weight'
    ]]

    logging.info(f"Microcensus data cleaned. Population size: {len(population_mic_home_inside)}")
    return population_mic_home_inside


def plot_age_distribution(analyse_data_sim, analyse_data_mic, output_path):
    """Generate age distribution comparison plot with side-by-side bars"""
    logging.info("Generating age distribution comparison plot...")

    try:
        # Define age bins (1-year intervals)
        age_bins = range(0, 101, 1)

        # Microcensus (weighted)
        df_mic_age = analyse_data_mic.copy()
        df_mic_age['age_bin'] = pd.cut(df_mic_age['age'], bins=age_bins, right=False)
        mic_age_dist = df_mic_age.groupby('age_bin')['person_weight'].sum()
        mic_age_pct = (mic_age_dist / mic_age_dist.sum() * 100).values

        # Simulation
        df_sim_age = analyse_data_sim.copy()
        df_sim_age['age_bin'] = pd.cut(df_sim_age['age'], bins=age_bins, right=False)
        sim_age_dist = df_sim_age.groupby('age_bin').size()
        sim_age_pct = (sim_age_dist / sim_age_dist.sum() * 100).values

        # Create plot with side-by-side bars
        fig, ax = plt.subplots(figsize=(14, 6))
        x_positions = [(age_bins[i] + age_bins[i + 1]) / 2 for i in range(len(age_bins) - 1)]
        bar_width = 0.4  # Width of each bar

        # Offset bars to be side-by-side
        offset = bar_width / 2

        ax.bar([x - offset for x in x_positions], mic_age_pct, width=bar_width,
               label='Microcensus', color='#001BB7', alpha=0.9, edgecolor='none')
        ax.bar([x + offset for x in x_positions], sim_age_pct, width=bar_width,
               label='Simulation', color='#ff0000', alpha=0.8, edgecolor='none')

        ax.set_xlabel('Age', fontsize=12)
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_title('Age Distribution Comparison', fontsize=14, pad=20)
        ax.set_xlim(-1, 101)
        ax.set_xticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        ax.legend(title='Dataset', loc='upper right', frameon=True, fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Age distribution plot saved to: {output_path}")

    except Exception as e:
        logging.error(f"Error generating age distribution plot: {str(e)}")


def plot_gender_distribution(analyse_data_sim, analyse_data_mic, output_path):
    """Generate gender distribution comparison plot"""
    logging.info("Generating gender distribution comparison plot...")

    try:
        # Process data
        sim_gender_counts = analyse_data_sim['sex'].value_counts()
        mic_gender_counts = analyse_data_mic.groupby('sex')['person_weight'].sum()

        # Create plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        colors = ['#6b7fda', '#e8664d']

        # Simulation pie chart
        wedges1, texts1, autotexts1 = ax1.pie(
            sim_gender_counts.values,
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 13, 'weight': 'bold', 'color': 'white'}
        )
        ax1.set_title('Gender Distribution - Simulation', fontsize=12, pad=20)

        # Microcensus pie chart
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
        plt.subplots_adjust(right=0.88)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Gender distribution plot saved to: {output_path}")

    except Exception as e:
        logging.error(f"Error generating gender distribution plot: {str(e)}")


def plot_mode_share_comparison(plans_sim_full, population_sim_ids, output_path):
    """
    Generate mode share comparison plot
    CRITICAL validation for transportation modeling!
    """
    logging.info("Generating mode share comparison plot...")

    try:
        if not hasattr(plans_sim_full, 'legs'):
            logging.warning("No legs dataframe available - skipping mode share plot")
            return

        # Get legs for people in our study area
        legs_sim = plans_sim_full.legs.copy()

        # Filter to only include legs from people in study area
        legs_sim_filtered = legs_sim[legs_sim['plan_id'].astype(str).str.split('_').str[0].isin(
            population_sim_ids.astype(str)
        )]

        logging.info(f"Total legs: {len(legs_sim)}, Filtered legs (study area): {len(legs_sim_filtered)}")

        # Get mode distribution
        mode_counts = legs_sim_filtered['mode'].value_counts()
        mode_pct = (mode_counts / mode_counts.sum() * 100)

        # Filter out non-passenger modes
        passenger_modes = ['walk', 'car', 'pt', 'bike', 'car_passenger', 'drt']
        mode_pct_filtered = mode_pct[mode_pct.index.isin(passenger_modes)]

        # Define display order and labels
        mode_order = ['walk', 'car', 'pt', 'bike', 'car_passenger', 'drt']
        mode_labels_map = {
            'walk': 'Walk',
            'car': 'Car',
            'pt': 'Public Transport',
            'bike': 'Bike',
            'car_passenger': 'Car Passenger',
            'drt': 'DRT'
        }

        # Create ordered data
        modes_ordered = [m for m in mode_order if m in mode_pct_filtered.index]
        mode_labels = [mode_labels_map[m] for m in modes_ordered]
        mode_values = [mode_pct_filtered[m] for m in modes_ordered]

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c']
        bars = ax.bar(range(len(mode_values)), mode_values, color=colors[:len(mode_values)], alpha=0.8)

        ax.set_xlabel('Mode of Transportation', fontsize=12)
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_title('Mode Share Distribution - Simulation', fontsize=14, pad=20)
        ax.set_xticks(range(len(mode_labels)))
        ax.set_xticklabels(mode_labels, rotation=15, ha='right')
        ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)

        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, mode_values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Log the distribution
        logging.info("Mode share distribution:")
        for mode, pct in zip(mode_labels, mode_values):
            logging.info(f"  {mode}: {pct:.1f}%")

        logging.info(f"Mode share plot saved to: {output_path}")

    except Exception as e:
        logging.error(f"Error generating mode share plot: {str(e)}")


def plot_activity_type_comparison(plans_sim_full, population_sim_ids, output_path):
    """
    Generate activity type distribution plot
    Excludes 'interaction' activities which are MATSim artifacts
    """
    logging.info("Generating activity type distribution plot...")

    try:
        if not hasattr(plans_sim_full, 'activities'):
            logging.warning("No activities dataframe available - skipping activity plot")
            return

        # Get activities for people in our study area
        activities_sim = plans_sim_full.activities.copy()

        # Filter to only include activities from people in study area
        activities_sim_filtered = activities_sim[
            activities_sim['plan_id'].astype(str).str.split('_').str[0].isin(
                population_sim_ids.astype(str)
            )
        ]

        logging.info(
            f"Total activities: {len(activities_sim)}, Filtered activities (study area): {len(activities_sim_filtered)}")

        # Filter out "interaction" activities (these are MATSim artifacts, not real activities)
        activities_real = activities_sim_filtered[
            ~activities_sim_filtered['type'].str.contains('interaction', case=False, na=False)
        ]

        # Get activity type distribution
        activity_counts = activities_real['type'].value_counts()
        activity_pct = (activity_counts / activity_counts.sum() * 100)

        # Define activity order and labels
        activity_order = ['home', 'work', 'leisure', 'shop', 'education', 'other', 'outside']
        activity_labels_map = {
            'home': 'Home',
            'work': 'Work',
            'leisure': 'Leisure',
            'shop': 'Shopping',
            'education': 'Education',
            'other': 'Other',
            'outside': 'Outside Area'
        }

        # Create ordered data
        activities_ordered = [a for a in activity_order if a in activity_pct.index]
        activity_labels = [activity_labels_map.get(a, a.title()) for a in activities_ordered]
        activity_values = [activity_pct[a] for a in activities_ordered]

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6', '#34495e']
        bars = ax.bar(range(len(activity_values)), activity_values,
                      color=colors[:len(activity_values)], alpha=0.8)

        ax.set_xlabel('Activity Type', fontsize=12)
        ax.set_ylabel('Percentage (%)', fontsize=12)
        ax.set_title('Activity Type Distribution - Simulation', fontsize=14, pad=20)
        ax.set_xticks(range(len(activity_labels)))
        ax.set_xticklabels(activity_labels, rotation=15, ha='right')
        ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)

        # Add value labels on bars
        for bar, val in zip(bars, activity_values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Log the distribution
        logging.info("Activity type distribution (excluding interactions):")
        for activity, pct in zip(activity_labels, activity_values):
            logging.info(f"  {activity}: {pct:.1f}%")

        logging.info(f"Activity type plot saved to: {output_path}")

    except Exception as e:
        logging.error(f"Error generating activity type plot: {str(e)}")


def plot_departure_time_distribution(plans_sim_full, population_sim_ids, output_path):
    """
    Generate departure time distribution plot
    Shows when people start their trips throughout the day
    """
    logging.info("Generating departure time distribution plot...")

    try:
        if not hasattr(plans_sim_full, 'legs'):
            logging.warning("No legs dataframe available - skipping departure time plot")
            return

        # Get legs for people in our study area
        legs_sim = plans_sim_full.legs.copy()

        # Filter to only include legs from people in study area
        legs_sim_filtered = legs_sim[legs_sim['plan_id'].astype(str).str.split('_').str[0].isin(
            population_sim_ids.astype(str)
        )]

        # Convert departure time to numeric (seconds since midnight)
        legs_sim_filtered['dep_time_numeric'] = pd.to_numeric(
            legs_sim_filtered['dep_time'],
            errors='coerce'
        )

        # Filter out invalid times
        legs_valid = legs_sim_filtered[legs_sim_filtered['dep_time_numeric'].notna()].copy()

        # Convert seconds to hours
        legs_valid['dep_hour'] = legs_valid['dep_time_numeric'] / 3600.0

        # Filter to 0-24 hours (exclude outliers)
        legs_valid = legs_valid[(legs_valid['dep_hour'] >= 0) & (legs_valid['dep_hour'] < 24)]

        logging.info(f"Valid departure times for plotting: {len(legs_valid)}")

        # Create 30-minute bins
        bins = np.arange(0, 24.5, 0.5)  # 0:00 to 24:00 in 30-min intervals
        bin_labels = []
        for i in range(len(bins) - 1):
            hour = int(bins[i])
            minute = int((bins[i] % 1) * 60)
            bin_labels.append(f"{hour:02d}:{minute:02d}")

        # Count trips in each bin
        hist, _ = np.histogram(legs_valid['dep_hour'], bins=bins)
        hist_pct = (hist / hist.sum() * 100)

        # Create plot
        fig, ax = plt.subplots(figsize=(14, 6))

        x_pos = np.arange(len(hist_pct))
        bars = ax.bar(x_pos, hist_pct, width=0.8, color='#3498db', alpha=0.8, edgecolor='none')

        ax.set_xlabel('Time of Day', fontsize=12)
        ax.set_ylabel('Percentage of Trips (%)', fontsize=12)
        ax.set_title('Departure Time Distribution - Simulation', fontsize=14, pad=20)

        # Set x-axis labels (show every 2 hours)
        tick_indices = range(0, len(bin_labels), 4)  # Every 2 hours
        ax.set_xticks([x_pos[i] for i in tick_indices])
        ax.set_xticklabels([bin_labels[i] for i in tick_indices], rotation=45, ha='right')

        ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_xlim(-0.5, len(hist_pct) - 0.5)

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        # Log peak hours
        peak_idx = np.argmax(hist_pct)
        peak_time = bin_labels[peak_idx]
        peak_pct = hist_pct[peak_idx]
        logging.info(f"Peak departure time: {peak_time} ({peak_pct:.2f}% of trips)")

        logging.info(f"Departure time plot saved to: {output_path}")

    except Exception as e:
        logging.error(f"Error generating departure time plot: {str(e)}")


def main():
    """Main execution function"""

    # Setup logging
    setup_logging(get_log_filename())

    # Read configuration
    cfg = read_config(return_dataclass=True)

    # Setup paths
    script_path = os.path.abspath(__file__)
    parent_dir = os.path.dirname(script_path)
    plots_path = os.path.join(os.path.dirname(parent_dir), "plots")

    shapefile_name = "25_ShapeFile.shp"
    # Load shapefiles
    shapefile_path = os.path.join(
        r"/home/sarf/projects/amir/validation_shapefiles/",
        shapefile_name
    )

    # Create output directory
    sim_output_plots_path = os.path.join(plots_path, cfg.sim_output_folder.split("/")[-1], shapefile_name)

    os.makedirs(sim_output_plots_path, exist_ok=True)
    logging.info(f"Plots directory: {sim_output_plots_path}")

    gdf = gpd.read_file(shapefile_path, engine="pyogrio")
    area_polygon = gdf.iloc[0]['geometry']
    logging.info("Shapefile loaded successfully")

    # Load and clean data
    output_folder_path = os.path.join(cfg.data_path, cfg.simulation_zone_name, cfg.sim_output_folder)

    population_sim, plans_sim_full = load_and_clean_simulation_data(
        output_folder_path,
        area_polygon,
        gdf.crs
    )

    if cfg.read_microcensus:
        population_mic = load_and_clean_microcensus_data(
            cfg.analysis_zone_path,
            area_polygon,
            gdf.crs,
            n_rows=None
        )
    else:
        logging.warning("Microcensus reading is disabled in config")
        sys.exit(0)

    # Generate comparison plots
    if cfg.read_microcensus:
        # Age distribution
        plot_age_distribution(
            population_sim,
            population_mic,
            os.path.join(sim_output_plots_path, 'age_distribution_comparison.png')
        )

        # Gender distribution
        plot_gender_distribution(
            population_sim,
            population_mic,
            os.path.join(sim_output_plots_path, 'gender_distribution_comparison.png')
        )

        # Car availability
        sim_car_counts = population_sim['car_availability'].value_counts()
        sim_car_pct = (sim_car_counts / sim_car_counts.sum() * 100)
        mic_car_counts = population_mic.groupby('car_availability')['person_weight'].sum()
        mic_car_pct = (mic_car_counts / mic_car_counts.sum() * 100)

        categories = [False, True]
        data_dict = {
            'Microcensus': [mic_car_pct.get(cat, 0) for cat in categories],
            'Simulation': [sim_car_pct.get(cat, 0) for cat in categories]
        }

        create_comparison_bar_plot(
            data_dict,
            categories,
            ['No Car', 'Has Car'],
            'Car Availability Comparison',
            'Car Availability',
            'Percentage (%)',
            os.path.join(sim_output_plots_path, 'car_availability_comparison.png')
        )

        # Bike availability
        sim_bike_counts = population_sim['bike_availability'].value_counts()
        sim_bike_pct = (sim_bike_counts / sim_bike_counts.sum() * 100)
        mic_bike_counts = population_mic.groupby('bike_availability')['person_weight'].sum()
        mic_bike_pct = (mic_bike_counts / mic_bike_counts.sum() * 100)

        data_dict = {
            'Microcensus': [mic_bike_pct.get(cat, 0) for cat in categories],
            'Simulation': [sim_bike_pct.get(cat, 0) for cat in categories]
        }

        create_comparison_bar_plot(
            data_dict,
            categories,
            ['No Bike', 'Has Bike'],
            'Bike Availability Comparison',
            'Bike Availability',
            'Percentage (%)',
            os.path.join(sim_output_plots_path, 'bike_availability_comparison.png')
        )

        # Employment status
        sim_employed_counts = population_sim['employed'].value_counts()
        sim_employed_pct = (sim_employed_counts / sim_employed_counts.sum() * 100)
        mic_employed_counts = population_mic.groupby('employed')['person_weight'].sum()
        mic_employed_pct = (mic_employed_counts / mic_employed_counts.sum() * 100)

        data_dict = {
            'Microcensus': [mic_employed_pct.get(cat, 0) for cat in categories],
            'Simulation': [sim_employed_pct.get(cat, 0) for cat in categories]
        }

        create_comparison_bar_plot(
            data_dict,
            categories,
            ['Not Employed', 'Employed'],
            'Employment Status Comparison',
            'Employment Status',
            'Percentage (%)',
            os.path.join(sim_output_plots_path, 'employment_comparison.png')
        )

        # Income class
        income_bins = [0, 2000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, float('inf')]
        income_labels = [
            'Under CHF 2000',
            'CHF 2000-4000',
            'CHF 4001-6000',
            'CHF 6001-8000',
            'CHF 8001-10000',
            'CHF 10001-12000',
            'CHF 12001-14000',
            'CHF 14001-16000',
            'Over CHF 16000'  # Missing label added!
        ]

        # Simulation income - convert to numeric and handle NaN
        sim_income = population_sim.copy()
        sim_income['income_class_numeric'] = pd.to_numeric(
            sim_income['income_class'],
            errors='coerce'
        )
        # Filter out NaN values
        sim_income_valid = sim_income[sim_income['income_class_numeric'].notna()].copy()

        if len(sim_income_valid) > 0:
            sim_income_valid['income_category'] = pd.cut(
                sim_income_valid['income_class_numeric'],
                bins=income_bins,
                labels=income_labels,
                right=False
            )
            sim_income_counts = sim_income_valid['income_category'].value_counts()
            sim_income_pct = (sim_income_counts / sim_income_counts.sum() * 100)

            # Log how many were filtered
            n_filtered = len(sim_income) - len(sim_income_valid)
            if n_filtered > 0:
                logging.warning(f"Filtered {n_filtered} simulation records with invalid income values")
        else:
            logging.error("No valid income data in simulation population")
            sim_income_pct = pd.Series(dtype=float)

        # Microcensus income - convert to numeric and handle NaN
        mic_income = population_mic.copy()
        mic_income['income_class_numeric'] = pd.to_numeric(
            mic_income['income_class'],
            errors='coerce'
        )
        # Filter out NaN values
        mic_income_valid = mic_income[mic_income['income_class_numeric'].notna()].copy()

        if len(mic_income_valid) > 0:
            mic_income_valid['income_category'] = pd.cut(
                mic_income_valid['income_class_numeric'],
                bins=income_bins,
                labels=income_labels,
                right=False
            )
            mic_income_counts = mic_income_valid.groupby('income_category')['person_weight'].sum()
            mic_income_pct = (mic_income_counts / mic_income_counts.sum() * 100)

            # Log how many were filtered
            n_filtered = len(mic_income) - len(mic_income_valid)
            if n_filtered > 0:
                logging.warning(f"Filtered {n_filtered} microcensus records with invalid income values")
        else:
            logging.error("No valid income data in microcensus population")
            mic_income_pct = pd.Series(dtype=float)

        # Only plot if we have valid data from both sources
        if len(sim_income_pct) > 0 and len(mic_income_pct) > 0:
            data_dict = {
                'Microcensus': [mic_income_pct.get(cat, 0) for cat in income_labels],
                'Simulation': [sim_income_pct.get(cat, 0) for cat in income_labels]
            }

            create_comparison_bar_plot(
                data_dict,
                income_labels,
                income_labels,
                'Income Class Comparison',
                'Income Class',
                'Percentage (%)',
                os.path.join(sim_output_plots_path, 'income_class_comparison.png')
            )
        else:
            logging.warning("Skipping income class comparison plot due to insufficient valid data")

    # =========================================================================
    # NEW VALIDATIONS - Mode Share, Activities, Departure Times
    # =========================================================================

    if cfg.read_microcensus:
        # Extract person IDs for filtering legs/activities
        population_sim_ids = population_sim['person_id']

        # Mode Share Validation
        plot_mode_share_comparison(
            plans_sim_full,
            population_sim_ids,
            os.path.join(sim_output_plots_path, 'mode_share_distribution.png')
        )

        # Activity Type Validation
        plot_activity_type_comparison(
            plans_sim_full,
            population_sim_ids,
            os.path.join(sim_output_plots_path, 'activity_type_distribution.png')
        )

        # Departure Time Validation
        plot_departure_time_distribution(
            plans_sim_full,
            population_sim_ids,
            os.path.join(sim_output_plots_path, 'departure_time_distribution.png')
        )

    logging.info("All validation plots generated successfully")

    # ============================================================================
    # VALIDATION SUMMARY
    # ============================================================================
    logging.info("\n" + "=" * 80)
    logging.info("VALIDATION SUMMARY")
    logging.info("=" * 80)

    logging.info("\n✅ COMPLETED VALIDATIONS:")
    logging.info("  1. Age Distribution")
    logging.info("  2. Gender Distribution")
    logging.info("  3. Car Availability")
    logging.info("  4. Bike Availability")
    logging.info("  5. Employment Status")
    logging.info("  6. Income Class Distribution")
    logging.info("  7. Mode Share Distribution (NEW!)")
    logging.info("  8. Activity Type Distribution (NEW!)")
    logging.info("  9. Departure Time Distribution (NEW!)")

    logging.info("\n📊 KEY STATISTICS:")
    logging.info(f"  - Simulation population (filtered): {len(population_sim)}")
    logging.info(f"  - Microcensus population (filtered): {len(population_mic)}")
    logging.info(f"  - Population ratio: {len(population_sim) / len(population_mic):.1f}:1")

    if hasattr(plans_sim_full, 'legs'):
        logging.info(f"  - Total trips analyzed: {len(plans_sim_full.legs)}")
    if hasattr(plans_sim_full, 'activities'):
        logging.info(f"  - Total activities analyzed: {len(plans_sim_full.activities)}")

    logging.info("\n💡 ADDITIONAL VALIDATIONS THAT COULD BE ADDED:")

    if hasattr(plans_sim_full, 'activities'):
        logging.info("  ⚪ ACTIVITY CHAINS validation:")
        logging.info("     - Combine activities into sequences (H-W-H, H-W-L-H, etc.)")
        logging.info("     - Compare top 10 activity chain patterns with microcensus")

    if hasattr(plans_sim_full, 'legs'):
        if 'start_x' in plans_sim_full.legs.columns or 'x' in plans_sim_full.activities.columns:
            logging.info("  ⚪ ORIGIN-DESTINATION validation:")
            logging.info("     - Use activity/leg coordinates")
            logging.info("     - Group by zones/districts")
            logging.info("     - Create O-D matrices and flow maps")

    logging.info("\n💡 See CODE_REVIEW_SUMMARY.md for implementation examples")
    logging.info("=" * 80 + "\n")


if __name__ == '__main__':
    main()