# Import necessary libraries
import pandas as pd
import matsim
from common import *
import geopandas as gpd
from shapely.geometry import Point
import os
import sys
import logging
import seaborn as sns
import matplotlib.pyplot as plt
pd.set_option('display.max_columns', 15)
pd.set_option('display.max_rows', 20)
import warnings
warnings.filterwarnings('ignore')


# FUNCTION THAT SELECTS ACTIVITIES THAT ARE INSIDE THE ZONE
def filter_activities_in_the_zone(dataframe, zone_shapefile):
    # Create a GeoDataFrame from the dataframe
    geometry = [Point(xy) for xy in zip(dataframe['x'], dataframe['y'])]
    geo_df = gpd.GeoDataFrame(dataframe, geometry=geometry)

    # Ensure the GeoDataFrame has the same CRS as the shapefile
    geo_df = geo_df.set_crs(zone_shapefile.crs, allow_override=True)

    # Perform spatial join to select points within the shape
    points_within_shape = gpd.sjoin(geo_df, zone_shapefile, how='inner', predicate='within')

    points_within_shape.rename(columns={'id_left': 'id'}, inplace=True)

    # Return the original columns along with the spatial join results
    return points_within_shape[dataframe.columns.tolist()]


if __name__ == '__main__':
    setup_logging("04_2_synPop_sim_analysis.log")

    data_path, zone_name, scenario, csv_folder, output_folder, percentile, clean_csv_folder, shapeFileName = read_config()

    output_data_path = os.path.join(data_path, zone_name, output_folder)

    try:
        plans_sim = matsim.plan_reader_dataframe(os.path.join(output_data_path, "output_plans.xml.gz"))
    except Exception as e:
        logging.error("Error loading simulation data: " + str(e))
        sys.exit()

# COMMENT IT IF YOU HAVE THE FILTERED CSV FILE AND YOU ONLY WANT TO CHANGE PLOTS
    try:
        # Load the shapefile
        shape_file_path = os.path.join(data_path, zone_name, "ShapeFiles", shapeFileName)
        shape = gpd.read_file(shape_file_path)

        # Process activities to find those within the shape
        activitiesInTheZone = filter_activities_in_the_zone(plans_sim.activities, shape)

        unique_plan_ids = activitiesInTheZone['plan_id'].unique()

        all_activities = plans_sim.activities
    
        # Filter the activities for the unique plan IDs
        activitiesOfPlansThatPassInTheZone = all_activities[all_activities['plan_id'].isin(unique_plan_ids)]

        # COMMENT IF YOU WANT ONLY THE ACTIVITIES THAT ARE INSIDE THE ZONE
        activitiesOfPlansThatPassInTheZone.to_csv('Plans_has_at_least_one_activity_Frauenfeld.csv', index=False)

    # UNCOMMENT IF YOU WANT ONLY THE ACTIVITIES THAT ARE INSIDE THE ZONE
        # Save the resulting DataFrame to a new CSV file
        # activitiesInTheZone.to_csv('Frauenfeld_Activities.csv', index=False)


    except Exception as e:
        logging.error("Error processing simulation data: " + str(e))
        sys.exit()

    # Frauenfeld Activities Data Analysis
    # Load the data
    # activitiesInTheZone = pd.read_csv('Frauenfeld_Activities.csv')
    activitiesInTheZone = pd.read_csv('Plans_has_at_least_one_activity_Frauenfeld.csv')

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, f'plots\\plots_{zone_name}')

    if not os.path.exists(plots_directory):
        os.makedirs(plots_directory)
        logging.info("Directory for plots created successfully")

    nan_counts = activitiesInTheZone.isna().sum()

    # Define colors for the bars
    colors = ['#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9']

    # Plot the NaN values using a bar chart
    plt.figure(figsize=(22, 10))
    bars = plt.bar(nan_counts.index, nan_counts.values, color=colors, edgecolor='black')

    # Add data labels on top of the bars only if the count is greater than 0
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            plt.text(bar.get_x() + bar.get_width() / 3.5, yval, int(yval), va='bottom')

    # Customize the chart
    plt.title('Number of NaN Values per Column', fontsize=16, fontweight='bold')
    plt.xlabel('Columns', fontsize=14)
    plt.ylabel('Number of NaN Values', fontsize=14)
    plt.xticks(rotation=0, fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(0, nan_counts.max() + 10000)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show the plot
    plt.tight_layout()
    plt.savefig(f'{plots_directory}\\nan_values.png')
    # plt.show()

    aiz = activitiesInTheZone.shape[0] # Number of activities in the zone
    ap = plans_sim.activities.shape[0] # Number of activities in the simulation
    sizes = [aiz, ap-aiz]
    labels = ['Inside Frauenfeld', 'Outside Frauenfeld']
    colors = ['#ff9999', '#66b3ff']

    # Explode the first slice slightly
    explode = (0.1, 0)  # explode 1st slice

    # Plotting the pie chart
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct='%1.1f%%',
        startangle=140,
        shadow=True,
        wedgeprops={'edgecolor': 'black'}
    )

    # Customizing text properties
    for text in texts:
        text.set_fontsize(14)
        text.set_color('black')

    for autotext in autotexts:
        autotext.set_fontsize(14)
        autotext.set_color('white')
        autotext.set_weight('bold')

    # Adding a legend
    plt.legend(wedges, labels, title="Zones", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    # Adding a title
    plt.title('Activities in Thurgau and Frauenfeld', fontsize=18, fontweight='bold')

    # Display the chart
    plt.tight_layout()

    # Display the chart
    plt.savefig(f'{plots_directory}\\pie_chart.png')
    # plt.show()

    # Plot
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    activity_types = activitiesInTheZone['type'].unique()
    activity_types_values = activitiesInTheZone['type'].value_counts()
    bars = ax.bar(activity_types, activity_types_values, color=sns.color_palette("pastel"))

    # Labels and title
    ax.set_xlabel('Activity Type', fontsize=14, weight='bold')
    ax.set_ylabel('Count', fontsize=14, weight='bold')
    ax.set_title('Activity Counts by Type in Frauenfeld', fontsize=16, weight='bold')

    # Rotate x labels for better readability
    ax.set_xticklabels(activity_types, rotation=45, ha='right', fontsize=12)

    # Add value labels on top of the bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate('{}'.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', fontsize=12, color='black')

    # Improve layout
    plt.tight_layout()
    plt.savefig(f'{plots_directory}\\Type _of_activities.png')
    # plt.show()



