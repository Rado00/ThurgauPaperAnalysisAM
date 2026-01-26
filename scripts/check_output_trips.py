from functions.commonFunctions import (
    setup_logging, get_log_filename, read_config
)
import pandas as pd
import os
import sys
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

setup_logging(get_log_filename())
cfg = read_config(return_dataclass=True)

try:
    output_trips_sim = pd.read_csv(
        "C:\\Users\\sarf\\Documents\\corrado_phd\\output_trips_6747.csv.gz",
        sep=';', low_memory=False, encoding='utf-8', dtype=str,
        compression='gzip'
    )
    logging.info("Output Trips data loaded successfully")

    # Log basic information about the dataset
    logging.info(f"Total number of trips loaded: {len(output_trips_sim):,}")
    logging.info(f"Number of columns: {len(output_trips_sim.columns)}")

    # Log column names and types
    logging.info("Column names and data types:")
    for col in output_trips_sim.columns:
        logging.info(f"  - {col}: {output_trips_sim[col].dtype}")

    # Log first few rows structure
    logging.info("\nFirst 5 rows preview:")
    logging.info("\n" + output_trips_sim.head().to_string())

    # Log memory usage
    memory_usage_mb = output_trips_sim.memory_usage(deep=True).sum() / (1024 ** 2)
    logging.info(f"\nMemory usage: {memory_usage_mb:.2f} MB")

    # Log missing values per column
    logging.info("\nMissing values per column:")
    missing_values = output_trips_sim.isnull().sum()
    for col, missing_count in missing_values.items():
        if missing_count > 0:
            missing_pct = (missing_count / len(output_trips_sim)) * 100
            logging.info(f"  - {col}: {missing_count:,} ({missing_pct:.2f}%)")

    # Log unique values for key columns
    key_columns = ['main_mode', 'longest_distance_mode', 'trip_id', 'person',
                   'dep_time', 'trav_time', 'start_activity_type', 'end_activity_type']

    logging.info("\nUnique values in key columns:")
    for col in key_columns:
        if col in output_trips_sim.columns:
            unique_count = output_trips_sim[col].nunique()
            logging.info(f"  - {col}: {unique_count:,} unique values")

            # For categorical columns with few unique values, show the distribution
            if unique_count <= 2 and col in ['main_mode', 'longest_distance_mode',
                                              'start_activity_type', 'end_activity_type']:
                value_counts = output_trips_sim[col].value_counts()
                logging.info(f"    Distribution:")
                for val, count in value_counts.items():
                    pct = (count / len(output_trips_sim)) * 100
                    logging.info(f"      {val}: {count:,} ({pct:.2f}%)")

    # Log basic statistics for numeric columns
    logging.info("\nAttempting to identify numeric columns for statistics...")
    numeric_cols = []
    for col in output_trips_sim.columns:
        try:
            pd.to_numeric(output_trips_sim[col], errors='raise')
            numeric_cols.append(col)
        except:
            pass

    if numeric_cols:
        logging.info(f"Numeric columns found: {', '.join(numeric_cols)}")
        for col in numeric_cols:
            series = pd.to_numeric(output_trips_sim[col], errors='coerce')
            logging.info(f"\nStatistics for {col}:")
            logging.info(f"  - Mean: {series.mean():.2f}")
            logging.info(f"  - Median: {series.median():.2f}")
            logging.info(f"  - Min: {series.min():.2f}")
            logging.info(f"  - Max: {series.max():.2f}")
            logging.info(f"  - Std: {series.std():.2f}")

    logging.info("\n" + "=" * 80)
    logging.info("Data structure analysis completed successfully")
    logging.info("=" * 80)

    # ==================== PLOTTING SECTION ====================

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Script directory: {script_dir}")

    # Get the parent directory
    parent_dir = os.path.dirname(script_dir)
    logging.info(f"Parent directory: {parent_dir}")

    # Check if plots folder exists in parent directory, create if not
    plots_folder = os.path.join(parent_dir, "plots")

    if not os.path.exists(plots_folder):
        os.makedirs(plots_folder)
        logging.info(f"Created plots folder: {plots_folder}")
    else:
        logging.info(f"Plots folder already exists: {plots_folder}")

    # Create output_trips subfolder
    output_trips_plots_folder = os.path.join(plots_folder, "output_trips")
    if not os.path.exists(output_trips_plots_folder):
        os.makedirs(output_trips_plots_folder)
        logging.info(f"Created output_trips folder: {output_trips_plots_folder}")
    else:
        logging.info(f"Output_trips folder already exists: {output_trips_plots_folder}")

    # Set style for better-looking plots
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10

    # Convert numeric columns for plotting
    output_trips_sim['traveled_distance_num'] = pd.to_numeric(output_trips_sim['traveled_distance'], errors='coerce')
    output_trips_sim['euclidean_distance_num'] = pd.to_numeric(output_trips_sim['euclidean_distance'], errors='coerce')
    output_trips_sim['trip_number_num'] = pd.to_numeric(output_trips_sim['trip_number'], errors='coerce')


    # Convert time columns
    def time_to_seconds(time_str):
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + int(s)
        except:
            return np.nan


    output_trips_sim['dep_time_seconds'] = output_trips_sim['dep_time'].apply(time_to_seconds)
    output_trips_sim['dep_time_hours'] = output_trips_sim['dep_time_seconds'] / 3600
    output_trips_sim['trav_time_seconds'] = output_trips_sim['trav_time'].apply(time_to_seconds)
    output_trips_sim['trav_time_minutes'] = output_trips_sim['trav_time_seconds'] / 60

    logging.info("Starting to generate plots...")

    # ===== NEW: PLOT 0 - Data Structure Overview =====
    fig = plt.figure(figsize=(16, 10))

    # Subplot 1: Column count and missing values
    ax1 = plt.subplot(2, 3, 1)
    missing_data = output_trips_sim.isnull().sum().sort_values(ascending=False)
    missing_pct = (missing_data / len(output_trips_sim)) * 100

    # Only show columns with missing values
    missing_cols = missing_data[missing_data > 0]
    if len(missing_cols) > 0:
        colors_missing = ['red' if x > 50 else 'orange' if x > 10 else 'yellow'
                          for x in (missing_cols / len(output_trips_sim)) * 100]
        missing_cols.plot(kind='barh', color=colors_missing, ax=ax1)
        ax1.set_title('Missing Values by Column', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Count', fontsize=10)
        ax1.set_ylabel('Column', fontsize=10)
        ax1.grid(alpha=0.3, axis='x')
    else:
        ax1.text(0.5, 0.5, 'No Missing Values', ha='center', va='center', fontsize=14)
        ax1.set_title('Missing Values by Column', fontsize=12, fontweight='bold')

    # Subplot 2: Data completeness percentage
    ax2 = plt.subplot(2, 3, 2)
    completeness = ((len(output_trips_sim) - output_trips_sim.isnull().sum()) / len(output_trips_sim)) * 100
    completeness_sorted = completeness.sort_values()
    colors_complete = ['green' if x > 90 else 'orange' if x > 50 else 'red' for x in completeness_sorted]
    completeness_sorted.plot(kind='barh', color=colors_complete, ax=ax2)
    ax2.set_title('Data Completeness by Column (%)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Completeness (%)', fontsize=10)
    ax2.set_xlim(0, 100)
    ax2.axvline(x=90, color='green', linestyle='--', alpha=0.5, label='90% threshold')
    ax2.legend()
    ax2.grid(alpha=0.3, axis='x')

    # Subplot 3: Unique values per column
    ax3 = plt.subplot(2, 3, 3)
    unique_counts = output_trips_sim.nunique().sort_values(ascending=False)
    top_unique = unique_counts.head(15)
    colors_unique = sns.color_palette("viridis", len(top_unique))
    top_unique.plot(kind='barh', color=colors_unique, ax=ax3)
    ax3.set_title('Unique Values per Column (Top 15)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Count', fontsize=10)
    ax3.set_xscale('log')
    ax3.grid(alpha=0.3, axis='x')

    # Subplot 4: Memory usage by column
    ax4 = plt.subplot(2, 3, 4)
    memory_by_col = output_trips_sim.memory_usage(deep=True) / (1024 ** 2)  # Convert to MB
    memory_sorted = memory_by_col.sort_values(ascending=False).head(15)
    colors_mem = sns.color_palette("rocket", len(memory_sorted))
    memory_sorted.plot(kind='barh', color=colors_mem, ax=ax4)
    ax4.set_title('Memory Usage by Column (Top 15, MB)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Memory (MB)', fontsize=10)
    ax4.grid(alpha=0.3, axis='x')

    # Subplot 5: Column data types
    ax5 = plt.subplot(2, 3, 5)
    dtype_counts = output_trips_sim.dtypes.value_counts()
    colors_dtype = sns.color_palette("Set2", len(dtype_counts))
    dtype_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors_dtype, ax=ax5, startangle=90)
    ax5.set_title('Data Types Distribution', fontsize=12, fontweight='bold')
    ax5.set_ylabel('')

    # Subplot 6: Dataset overview text
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    overview_text = f"""
    DATASET OVERVIEW

    Total Rows: {len(output_trips_sim):,}
    Total Columns: {len(output_trips_sim.columns)}
    Total Memory: {memory_usage_mb:.2f} MB

    Columns with Missing Data: {len(missing_cols)}
    Complete Columns: {len(output_trips_sim.columns) - len(missing_cols)}

    Unique Persons: {output_trips_sim['person'].nunique():,}
    Unique Trips: {output_trips_sim['trip_id'].nunique():,}

    Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    ax6.text(0.1, 0.5, overview_text, fontsize=11, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '00_data_structure_overview.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 0 saved: Data structure overview")

    # ===== PLOT 1: Mode Share Distribution =====
    plt.figure(figsize=(12, 6))
    if 'main_mode' in output_trips_sim.columns:
        mode_counts = output_trips_sim['main_mode'].value_counts()
        colors = sns.color_palette("Set2", len(mode_counts))
        plt.subplot(1, 2, 1)
        mode_counts.plot(kind='bar', color=colors)
        plt.title('Trip Distribution by Main Mode', fontsize=14, fontweight='bold')
        plt.xlabel('Mode', fontsize=12)
        plt.ylabel('Number of Trips', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)

        plt.subplot(1, 2, 2)
        plt.pie(mode_counts.values, labels=mode_counts.index, autopct='%1.1f%%',
                colors=colors, startangle=90)
        plt.title('Mode Share Percentage', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '01_mode_share.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 1 saved: Mode share distribution")

    # ===== PLOT 2: Activity Type Distribution =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    if 'start_activity_type' in output_trips_sim.columns:
        start_act = output_trips_sim['start_activity_type'].value_counts()
        colors_start = sns.color_palette("husl", len(start_act))
        start_act.plot(kind='barh', ax=axes[0], color=colors_start)
        axes[0].set_title('Start Activity Types', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Number of Trips', fontsize=12)
        axes[0].set_ylabel('Activity Type', fontsize=12)
        axes[0].grid(axis='x', alpha=0.3)

    if 'end_activity_type' in output_trips_sim.columns:
        end_act = output_trips_sim['end_activity_type'].value_counts()
        colors_end = sns.color_palette("husl", len(end_act))
        end_act.plot(kind='barh', ax=axes[1], color=colors_end)
        axes[1].set_title('End Activity Types', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Number of Trips', fontsize=12)
        axes[1].set_ylabel('Activity Type', fontsize=12)
        axes[1].grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '02_activity_types.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 2 saved: Activity type distribution")

    # ===== PLOT 3: Distance Analysis =====
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Traveled distance histogram
    axes[0, 0].hist(output_trips_sim['traveled_distance_num'].dropna(), bins=50,
                    color='steelblue', edgecolor='black', alpha=0.7)
    axes[0, 0].set_title('Traveled Distance Distribution', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Distance (m)', fontsize=10)
    axes[0, 0].set_ylabel('Frequency', fontsize=10)
    axes[0, 0].grid(alpha=0.3)

    # Euclidean distance histogram
    axes[0, 1].hist(output_trips_sim['euclidean_distance_num'].dropna(), bins=50,
                    color='coral', edgecolor='black', alpha=0.7)
    axes[0, 1].set_title('Euclidean Distance Distribution', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Distance (m)', fontsize=10)
    axes[0, 1].set_ylabel('Frequency', fontsize=10)
    axes[0, 1].grid(alpha=0.3)

    # Traveled vs Euclidean distance scatter
    axes[1, 0].scatter(output_trips_sim['euclidean_distance_num'],
                       output_trips_sim['traveled_distance_num'],
                       alpha=0.5, s=20, c='green')
    axes[1, 0].set_title('Traveled vs Euclidean Distance', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Euclidean Distance (m)', fontsize=10)
    axes[1, 0].set_ylabel('Traveled Distance (m)', fontsize=10)
    axes[1, 0].plot([0, output_trips_sim['euclidean_distance_num'].max()],
                    [0, output_trips_sim['euclidean_distance_num'].max()],
                    'r--', label='1:1 line')
    axes[1, 0].legend()
    axes[1, 0].grid(alpha=0.3)

    # Distance by mode boxplot
    if 'main_mode' in output_trips_sim.columns:
        mode_distance_data = []
        mode_labels = []
        for mode in output_trips_sim['main_mode'].unique():
            if pd.notna(mode):
                mode_data = output_trips_sim[output_trips_sim['main_mode'] == mode]['traveled_distance_num'].dropna()
                if len(mode_data) > 0:
                    mode_distance_data.append(mode_data)
                    mode_labels.append(mode)

        axes[1, 1].boxplot(mode_distance_data, labels=mode_labels)
        axes[1, 1].set_title('Distance Distribution by Mode', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Mode', fontsize=10)
        axes[1, 1].set_ylabel('Traveled Distance (m)', fontsize=10)
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '03_distance_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 3 saved: Distance analysis")

    # ===== PLOT 4: Temporal Analysis - Departure Time =====
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Departure time histogram
    axes[0].hist(output_trips_sim['dep_time_hours'].dropna(), bins=48,
                 color='purple', edgecolor='black', alpha=0.7)
    axes[0].set_title('Trip Departure Time Distribution', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Hour of Day', fontsize=12)
    axes[0].set_ylabel('Number of Trips', fontsize=12)
    axes[0].set_xlim(0, 24)
    axes[0].set_xticks(range(0, 25, 2))
    axes[0].grid(alpha=0.3)
    axes[0].axvline(x=8, color='red', linestyle='--', alpha=0.5, label='Morning Peak')
    axes[0].axvline(x=17, color='red', linestyle='--', alpha=0.5, label='Evening Peak')
    axes[0].legend()

    # Departure time by mode
    if 'main_mode' in output_trips_sim.columns:
        for mode in output_trips_sim['main_mode'].unique():
            if pd.notna(mode):
                mode_data = output_trips_sim[output_trips_sim['main_mode'] == mode]['dep_time_hours'].dropna()
                axes[1].hist(mode_data, bins=48, alpha=0.5, label=mode)

        axes[1].set_title('Departure Time by Mode', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Hour of Day', fontsize=12)
        axes[1].set_ylabel('Number of Trips', fontsize=12)
        axes[1].set_xlim(0, 24)
        axes[1].set_xticks(range(0, 25, 2))
        axes[1].legend()
        axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '04_temporal_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 4 saved: Temporal analysis")

    # ===== PLOT 5: Travel Time Analysis =====
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Travel time histogram
    axes[0, 0].hist(output_trips_sim['trav_time_minutes'].dropna(), bins=50,
                    color='teal', edgecolor='black', alpha=0.7)
    axes[0, 0].set_title('Travel Time Distribution', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Travel Time (minutes)', fontsize=10)
    axes[0, 0].set_ylabel('Frequency', fontsize=10)
    axes[0, 0].grid(alpha=0.3)

    # Travel time by mode boxplot
    if 'main_mode' in output_trips_sim.columns:
        mode_time_data = []
        mode_labels = []
        for mode in output_trips_sim['main_mode'].unique():
            if pd.notna(mode):
                mode_data = output_trips_sim[output_trips_sim['main_mode'] == mode]['trav_time_minutes'].dropna()
                if len(mode_data) > 0:
                    mode_time_data.append(mode_data)
                    mode_labels.append(mode)

        axes[0, 1].boxplot(mode_time_data, labels=mode_labels)
        axes[0, 1].set_title('Travel Time by Mode', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Mode', fontsize=10)
        axes[0, 1].set_ylabel('Travel Time (minutes)', fontsize=10)
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].grid(alpha=0.3)

    # Distance vs Travel Time scatter
    axes[1, 0].scatter(output_trips_sim['traveled_distance_num'],
                       output_trips_sim['trav_time_minutes'],
                       alpha=0.5, s=20, c='orange')
    axes[1, 0].set_title('Distance vs Travel Time', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Distance (m)', fontsize=10)
    axes[1, 0].set_ylabel('Travel Time (minutes)', fontsize=10)
    axes[1, 0].grid(alpha=0.3)

    # Average speed (km/h)
    output_trips_sim['speed_kmh'] = (output_trips_sim['traveled_distance_num'] / 1000) / (
                output_trips_sim['trav_time_minutes'] / 60)
    output_trips_sim['speed_kmh'] = output_trips_sim['speed_kmh'].replace([np.inf, -np.inf], np.nan)

    axes[1, 1].hist(output_trips_sim['speed_kmh'].dropna(), bins=50,
                    color='darkgreen', edgecolor='black', alpha=0.7)
    axes[1, 1].set_title('Average Trip Speed Distribution', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Speed (km/h)', fontsize=10)
    axes[1, 1].set_ylabel('Frequency', fontsize=10)
    axes[1, 1].set_xlim(0, 100)
    axes[1, 1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '05_travel_time_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 5 saved: Travel time analysis")

    # ===== PLOT 6: Trip Chains Analysis =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Trips per person
    trips_per_person = output_trips_sim.groupby('person').size()
    axes[0].hist(trips_per_person, bins=range(1, int(trips_per_person.max()) + 2),
                 color='magenta', edgecolor='black', alpha=0.7)
    axes[0].set_title('Trips per Person Distribution', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Number of Trips', fontsize=10)
    axes[0].set_ylabel('Number of Persons', fontsize=10)
    axes[0].grid(alpha=0.3)

    # Trip number distribution
    if 'trip_number_num' in output_trips_sim.columns:
        trip_num_counts = output_trips_sim['trip_number_num'].value_counts().sort_index()
        axes[1].bar(trip_num_counts.index, trip_num_counts.values,
                    color='brown', edgecolor='black', alpha=0.7)
        axes[1].set_title('Trip Number Distribution', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Trip Number in Chain', fontsize=10)
        axes[1].set_ylabel('Frequency', fontsize=10)
        axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '06_trip_chains.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 6 saved: Trip chains analysis")

    # ===== PLOT 7: Spatial Distribution =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Convert coordinates
    output_trips_sim['start_x_num'] = pd.to_numeric(output_trips_sim['start_x'], errors='coerce')
    output_trips_sim['start_y_num'] = pd.to_numeric(output_trips_sim['start_y'], errors='coerce')
    output_trips_sim['end_x_num'] = pd.to_numeric(output_trips_sim['end_x'], errors='coerce')
    output_trips_sim['end_y_num'] = pd.to_numeric(output_trips_sim['end_y'], errors='coerce')

    # Start locations
    axes[0].scatter(output_trips_sim['start_x_num'], output_trips_sim['start_y_num'],
                    alpha=0.3, s=10, c='blue')
    axes[0].set_title('Trip Start Locations', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('X Coordinate (m)', fontsize=10)
    axes[0].set_ylabel('Y Coordinate (m)', fontsize=10)
    axes[0].grid(alpha=0.3)

    # End locations
    axes[1].scatter(output_trips_sim['end_x_num'], output_trips_sim['end_y_num'],
                    alpha=0.3, s=10, c='red')
    axes[1].set_title('Trip End Locations', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('X Coordinate (m)', fontsize=10)
    axes[1].set_ylabel('Y Coordinate (m)', fontsize=10)
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_trips_plots_folder, '07_spatial_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 7 saved: Spatial distribution")

    # ===== PLOT 8: Mode and Activity Cross-tabulation =====
    if 'main_mode' in output_trips_sim.columns and 'end_activity_type' in output_trips_sim.columns:
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Cross-tabulation heatmap - Mode vs End Activity
        crosstab = pd.crosstab(output_trips_sim['main_mode'],
                               output_trips_sim['end_activity_type'])
        sns.heatmap(crosstab, annot=True, fmt='d', cmap='YlOrRd', ax=axes[0])
        axes[0].set_title('Mode vs End Activity Type', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('End Activity Type', fontsize=10)
        axes[0].set_ylabel('Main Mode', fontsize=10)

        # Normalized version (percentages)
        crosstab_norm = pd.crosstab(output_trips_sim['main_mode'],
                                    output_trips_sim['end_activity_type'],
                                    normalize='index') * 100
        sns.heatmap(crosstab_norm, annot=True, fmt='.1f', cmap='Blues', ax=axes[1])
        axes[1].set_title('Mode vs End Activity Type (% within mode)', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('End Activity Type', fontsize=10)
        axes[1].set_ylabel('Main Mode', fontsize=10)

        plt.tight_layout()
        plt.savefig(os.path.join(output_trips_plots_folder, '08_mode_activity_crosstab.png'), dpi=300,
                    bbox_inches='tight')
        plt.close()
        logging.info("Plot 8 saved: Mode and activity cross-tabulation")

    # ===== PLOT 9: Summary Statistics Table =====
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('tight')
    ax.axis('off')

    # Create summary statistics
    summary_data = []
    summary_data.append(['Total Trips', f'{len(output_trips_sim):,}'])
    summary_data.append(['Unique Persons', f'{output_trips_sim["person"].nunique():,}'])
    summary_data.append(['Avg Trips/Person', f'{len(output_trips_sim) / output_trips_sim["person"].nunique():.2f}'])
    summary_data.append(['', ''])
    summary_data.append(
        ['Avg Traveled Distance (km)', f'{output_trips_sim["traveled_distance_num"].mean() / 1000:.2f}'])
    summary_data.append(
        ['Avg Euclidean Distance (km)', f'{output_trips_sim["euclidean_distance_num"].mean() / 1000:.2f}'])
    summary_data.append(['Avg Travel Time (min)', f'{output_trips_sim["trav_time_minutes"].mean():.2f}'])
    summary_data.append(['Avg Speed (km/h)', f'{output_trips_sim["speed_kmh"].mean():.2f}'])
    summary_data.append(['', ''])
    summary_data.append(['Most Common Mode', output_trips_sim['main_mode'].mode()[0] if len(
        output_trips_sim['main_mode'].mode()) > 0 else 'N/A'])
    summary_data.append(['Most Common Start Activity', output_trips_sim['start_activity_type'].mode()[0] if len(
        output_trips_sim['start_activity_type'].mode()) > 0 else 'N/A'])
    summary_data.append(['Most Common End Activity', output_trips_sim['end_activity_type'].mode()[0] if len(
        output_trips_sim['end_activity_type'].mode()) > 0 else 'N/A'])

    table = ax.table(cellText=summary_data, colLabels=['Metric', 'Value'],
                     cellLoc='left', loc='center',
                     colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)

    # Style the header
    for i in range(2):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(summary_data) + 1):
        if summary_data[i - 1][0] == '':
            for j in range(2):
                table[(i, j)].set_facecolor('#FFFFFF')
        elif i % 2 == 0:
            for j in range(2):
                table[(i, j)].set_facecolor('#E7E6E6')
        else:
            for j in range(2):
                table[(i, j)].set_facecolor('#FFFFFF')

    plt.title('Output Trips Summary Statistics', fontsize=16, fontweight='bold', pad=20)
    plt.savefig(os.path.join(output_trips_plots_folder, '09_summary_statistics.png'), dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 9 saved: Summary statistics table")

    # ===== NEW: PLOT 10 - Categorical Columns Value Distribution =====
    # Identify all categorical columns (non-numeric with reasonable unique counts)
    categorical_cols = []
    for col in output_trips_sim.columns:
        unique_count = output_trips_sim[col].nunique()
        if unique_count <= 50 and unique_count > 1:  # Reasonable number of categories
            # Check if it's not already plotted as main columns
            if col not in ['main_mode', 'start_activity_type', 'end_activity_type',
                           'traveled_distance', 'euclidean_distance', 'trip_number']:
                categorical_cols.append(col)

    if len(categorical_cols) > 0:
        # Create plots for categorical columns
        num_cols = min(len(categorical_cols), 12)  # Limit to 12 columns
        cols_to_plot = categorical_cols[:num_cols]

        n_rows = (num_cols + 2) // 3  # 3 plots per row
        fig, axes = plt.subplots(n_rows, 3, figsize=(18, 5 * n_rows))
        axes = axes.flatten() if num_cols > 1 else [axes]

        for idx, col in enumerate(cols_to_plot):
            value_counts = output_trips_sim[col].value_counts().head(15)  # Top 15 values
            colors_cat = sns.color_palette("tab20", len(value_counts))

            if len(value_counts) <= 8:
                # Bar chart for fewer categories
                value_counts.plot(kind='barh', ax=axes[idx], color=colors_cat)
                axes[idx].set_xlabel('Count', fontsize=10)
            else:
                # Horizontal bar for more categories
                value_counts.plot(kind='barh', ax=axes[idx], color=colors_cat)
                axes[idx].set_xlabel('Count', fontsize=10)

            axes[idx].set_title(f'{col}\n({output_trips_sim[col].nunique()} unique values)',
                                fontsize=11, fontweight='bold')
            axes[idx].grid(alpha=0.3, axis='x')
            axes[idx].tick_params(axis='y', labelsize=9)

        # Hide empty subplots
        for idx in range(num_cols, len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()
        plt.savefig(os.path.join(output_trips_plots_folder, '10_categorical_columns.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()
        logging.info("Plot 10 saved: Categorical columns value distribution")

    # ===== NEW: PLOT 11 - Modes Column Analysis =====
    if 'modes' in output_trips_sim.columns:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Count of modes (walk-pt-walk, walk-car-walk, etc.)
        modes_counts = output_trips_sim['modes'].value_counts().head(20)
        colors_modes = sns.color_palette("Spectral", len(modes_counts))

        axes[0, 0].barh(range(len(modes_counts)), modes_counts.values, color=colors_modes)
        axes[0, 0].set_yticks(range(len(modes_counts)))
        axes[0, 0].set_yticklabels(modes_counts.index, fontsize=9)
        axes[0, 0].set_xlabel('Count', fontsize=11)
        axes[0, 0].set_title('Top 20 Mode Combinations', fontsize=12, fontweight='bold')
        axes[0, 0].grid(alpha=0.3, axis='x')

        # Count number of mode segments per trip
        output_trips_sim['mode_segments'] = output_trips_sim['modes'].apply(
            lambda x: len(str(x).split('-')) if pd.notna(x) else 0
        )
        segment_counts = output_trips_sim['mode_segments'].value_counts().sort_index()

        axes[0, 1].bar(segment_counts.index, segment_counts.values,
                       color=sns.color_palette("coolwarm", len(segment_counts)),
                       edgecolor='black')
        axes[0, 1].set_xlabel('Number of Mode Segments', fontsize=11)
        axes[0, 1].set_ylabel('Trip Count', fontsize=11)
        axes[0, 1].set_title('Mode Segments per Trip', fontsize=12, fontweight='bold')
        axes[0, 1].grid(alpha=0.3, axis='y')

        # Multimodal vs unimodal
        multimodal = (output_trips_sim['mode_segments'] > 1).sum()
        unimodal = (output_trips_sim['mode_segments'] == 1).sum()

        axes[1, 0].pie([unimodal, multimodal],
                       labels=['Unimodal', 'Multimodal'],
                       autopct='%1.1f%%',
                       colors=['lightblue', 'lightcoral'],
                       startangle=90)
        axes[1, 0].set_title('Unimodal vs Multimodal Trips', fontsize=12, fontweight='bold')

        # Main mode vs longest distance mode comparison
        if 'longest_distance_mode' in output_trips_sim.columns:
            mode_comparison = pd.crosstab(output_trips_sim['main_mode'],
                                          output_trips_sim['longest_distance_mode'])
            sns.heatmap(mode_comparison, annot=True, fmt='d', cmap='YlGnBu', ax=axes[1, 1])
            axes[1, 1].set_title('Main Mode vs Longest Distance Mode',
                                 fontsize=12, fontweight='bold')
            axes[1, 1].set_xlabel('Longest Distance Mode', fontsize=10)
            axes[1, 1].set_ylabel('Main Mode', fontsize=10)
        else:
            axes[1, 1].axis('off')

        plt.tight_layout()
        plt.savefig(os.path.join(output_trips_plots_folder, '11_modes_analysis.png'),
                    dpi=300, bbox_inches='tight')
        plt.close()
        logging.info("Plot 11 saved: Modes column analysis")

    # ===== NEW: PLOT 12 - All Columns Summary Table =====
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.axis('tight')
    ax.axis('off')

    # Create comprehensive column summary
    column_summary = []
    column_summary.append(['Column Name', 'Data Type', 'Unique Values', 'Missing', 'Missing %', 'Sample Values'])

    for col in output_trips_sim.columns:
        dtype = str(output_trips_sim[col].dtype)
        unique = output_trips_sim[col].nunique()
        missing = output_trips_sim[col].isnull().sum()
        missing_pct = f'{(missing / len(output_trips_sim) * 100):.1f}%'

        # Get sample values (top 3 most common)
        sample_vals = output_trips_sim[col].value_counts().head(3).index.tolist()
        sample_str = ', '.join([str(v)[:20] for v in sample_vals])
        if len(sample_str) > 40:
            sample_str = sample_str[:37] + '...'

        column_summary.append([col, dtype, unique, missing, missing_pct, sample_str])

    table = ax.table(cellText=column_summary[1:], colLabels=column_summary[0],
                     cellLoc='left', loc='center',
                     colWidths=[0.20, 0.12, 0.10, 0.08, 0.10, 0.40])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    # Style the header
    for i in range(6):
        table[(0, i)].set_facecolor('#2E75B6')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(column_summary)):
        for j in range(6):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#E7E6E6')
            else:
                table[(i, j)].set_facecolor('#FFFFFF')

            # Highlight missing values
            if j == 3 and column_summary[i][3] > 0:
                table[(i, j)].set_facecolor('#FFE6E6')

    plt.title('Complete Column Summary - Output Trips Dataset',
              fontsize=16, fontweight='bold', pad=20)
    plt.savefig(os.path.join(output_trips_plots_folder, '12_all_columns_summary.png'),
                dpi=300, bbox_inches='tight')
    plt.close()
    logging.info("Plot 12 saved: All columns summary table")

    # ===== Create a comprehensive README file =====
    readme_content = f"""# MATSim Output Trips Analysis
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Dataset Overview
- **Total Trips**: {len(output_trips_sim):,}
- **Unique Persons**: {output_trips_sim['person'].nunique():,}
- **Number of Columns**: {len(output_trips_sim.columns)}
- **Memory Usage**: {memory_usage_mb:.2f} MB

## Columns in Dataset
{chr(10).join([f"- {col} ({output_trips_sim[col].nunique():,} unique values)" for col in output_trips_sim.columns])}

## Generated Plots

### 00_data_structure_overview.png
Comprehensive overview of dataset structure including:
- Missing values by column
- Data completeness percentages
- Unique values per column
- Memory usage by column
- Data types distribution
- Overall dataset statistics

### 01_mode_share.png
Distribution of trips by main transportation mode (bar chart and pie chart)

### 02_activity_types.png
Distribution of start and end activity types

### 03_distance_analysis.png
- Traveled distance distribution
- Euclidean distance distribution
- Traveled vs Euclidean distance comparison
- Distance distribution by mode (boxplot)

### 04_temporal_analysis.png
- Departure time distribution over 24 hours
- Departure time by transportation mode

### 05_travel_time_analysis.png
- Travel time distribution
- Travel time by mode
- Distance vs travel time relationship
- Average trip speed distribution

### 06_trip_chains.png
- Number of trips per person
- Trip number distribution in trip chains

### 07_spatial_distribution.png
- Geographic distribution of trip start locations
- Geographic distribution of trip end locations

### 08_mode_activity_crosstab.png
- Cross-tabulation of mode and activity type
- Normalized percentages showing mode choice by activity

### 09_summary_statistics.png
Key summary statistics table

### 10_categorical_columns.png
Value distributions for all categorical columns in the dataset

### 11_modes_analysis.png
Detailed analysis of mode combinations:
- Top mode combinations
- Mode segments per trip
- Unimodal vs multimodal trips
- Main mode vs longest distance mode comparison

### 12_all_columns_summary.png
Complete summary table of all columns including data types, unique values, missing values, and sample data

## Key Statistics
- **Average Traveled Distance**: {output_trips_sim['traveled_distance_num'].mean() / 1000:.2f} km
- **Average Euclidean Distance**: {output_trips_sim['euclidean_distance_num'].mean() / 1000:.2f} km
- **Average Travel Time**: {output_trips_sim['trav_time_minutes'].mean():.2f} minutes
- **Average Speed**: {output_trips_sim['speed_kmh'].mean():.2f} km/h
- **Most Common Mode**: {output_trips_sim['main_mode'].mode()[0] if len(output_trips_sim['main_mode'].mode()) > 0 else 'N/A'}

## Mode Share
{chr(10).join([f"- {mode}: {count:,} trips ({count / len(output_trips_sim) * 100:.1f}%)"
               for mode, count in output_trips_sim['main_mode'].value_counts().items()])}

## Activity Distribution
### Start Activities
{chr(10).join([f"- {act}: {count:,} trips ({count / len(output_trips_sim) * 100:.1f}%)"
               for act, count in output_trips_sim['start_activity_type'].value_counts().items()])}

### End Activities
{chr(10).join([f"- {act}: {count:,} trips ({count / len(output_trips_sim) * 100:.1f}%)"
               for act, count in output_trips_sim['end_activity_type'].value_counts().items()])}

## Column Details
"""

    for col in output_trips_sim.columns:
        unique = output_trips_sim[col].nunique()
        missing = output_trips_sim[col].isnull().sum()
        missing_pct = (missing / len(output_trips_sim) * 100)
        readme_content += f"\n### {col}\n"
        readme_content += f"- Data Type: {output_trips_sim[col].dtype}\n"
        readme_content += f"- Unique Values: {unique:,}\n"
        readme_content += f"- Missing Values: {missing:,} ({missing_pct:.2f}%)\n"

        if unique <= 20:
            readme_content += f"- Values: {', '.join([str(v) for v in output_trips_sim[col].value_counts().head(20).index.tolist()])}\n"

    readme_path = os.path.join(output_trips_plots_folder, 'README.md')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    logging.info(f"README file created: {readme_path}")

    logging.info("\n" + "=" * 80)
    logging.info("All plots have been generated successfully!")
    logging.info(f"Total plots created: 13")
    logging.info(f"Plots saved in: {output_trips_plots_folder}")
    logging.info("=" * 80)

except Exception as e:
    logging.error("Error loading output_trips.csv.gz: " + str(e))
    import traceback

    logging.error(traceback.format_exc())
    sys.exit()