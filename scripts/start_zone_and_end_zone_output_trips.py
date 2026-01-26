from functions.commonFunctions import (
    setup_logging, get_log_filename, read_config
)
import pandas as pd
import geopandas as gpd
import os
import sys
import logging
from shapely.geometry import Point
from datetime import datetime
import numpy as np

setup_logging(get_log_filename())
cfg = read_config(return_dataclass=True)

# Paths
TRIPS_FILE = "C:\\Users\\sarf\\Documents\\corrado_phd\\output_trips_6747.csv.gz"
SHAPEFILES_FOLDER = "C:\\Users\\sarf\\Documents\\projects\\corrado_matsim\\DATA_ABM\\2024_Paper2_Data\\shapesfiles"
OUTPUT_FILE = "C:\\Users\\sarf\\Documents\\corrado_phd\\output_trips_6747_with_zones.csv.gz"

try:
    # ==================== LOAD TRIPS DATA ====================
    logging.info("Loading trips data...")
    output_trips = pd.read_csv(
        TRIPS_FILE,
        sep=';',
        low_memory=False,
        encoding='utf-8',
        dtype=str,
        compression='gzip'
    )
    logging.info(f"Trips data loaded: {len(output_trips):,} trips")

    # Convert coordinates to numeric
    output_trips['start_x'] = pd.to_numeric(output_trips['start_x'], errors='coerce')
    output_trips['start_y'] = pd.to_numeric(output_trips['start_y'], errors='coerce')
    output_trips['end_x'] = pd.to_numeric(output_trips['end_x'], errors='coerce')
    output_trips['end_y'] = pd.to_numeric(output_trips['end_y'], errors='coerce')

    logging.info("Coordinates converted to numeric")

    # ==================== LOAD SHAPEFILES ====================
    logging.info("Loading shapefiles...")

    # Get list of shapefiles
    shapefile_list = []
    for i in range(1, 19):  # Assuming 18 shapefiles numbered 01 to 18
        shapefile_name = f"{i:02d}_ShapeFile.shp"
        shapefile_path = os.path.join(SHAPEFILES_FOLDER, shapefile_name)

        if os.path.exists(shapefile_path):
            shapefile_list.append((i, shapefile_path))
            logging.info(f"Found: {shapefile_name}")
        else:
            logging.warning(f"Shapefile not found: {shapefile_name}")

    if not shapefile_list:
        logging.error("No shapefiles found!")
        sys.exit(1)

    logging.info(f"Total shapefiles found: {len(shapefile_list)}")

    # Load all shapefiles into a combined GeoDataFrame
    logging.info("Reading shapefiles...")
    zones_gdf_list = []

    for zone_id, shapefile_path in shapefile_list:
        gdf = gpd.read_file(shapefile_path)
        gdf['zone_id'] = zone_id  # Add zone identifier
        zones_gdf_list.append(gdf)
        logging.info(f"Loaded zone {zone_id:02d}: {len(gdf)} features")

    # Combine all zones into one GeoDataFrame
    all_zones = pd.concat(zones_gdf_list, ignore_index=True)
    logging.info(f"Total zone features: {len(all_zones)}")
    logging.info(f"CRS: {all_zones.crs}")


    # ==================== SPATIAL JOIN FUNCTION ====================
    def find_zone(x, y, zones_gdf):
        """
        Find which zone a point (x, y) belongs to.
        Returns zone_id or 'outside' if not in any zone.
        """
        if pd.isna(x) or pd.isna(y):
            return 'outside'

        point = Point(x, y)

        # Check which zone contains the point
        for idx, zone in zones_gdf.iterrows():
            if zone.geometry.contains(point):
                return f"{zone['zone_id']:02d}"

        return 'outside'


    # ==================== ASSIGN ZONES TO TRIPS ====================
    logging.info("Assigning start zones to trips...")
    logging.info("This may take several minutes depending on the number of trips...")

    # Initialize columns
    output_trips['start_zone'] = 'outside'
    output_trips['end_zone'] = 'outside'
    output_trips['trip_type'] = ''

    # Process in batches for better progress tracking
    batch_size = 1000
    total_trips = len(output_trips)

    logging.info(f"Processing {total_trips:,} trips in batches of {batch_size:,}...")

    for i in range(0, total_trips, batch_size):
        batch_end = min(i + batch_size, total_trips)

        # Assign start zones for batch
        for idx in range(i, batch_end):
            output_trips.loc[idx, 'start_zone'] = find_zone(
                output_trips.loc[idx, 'start_x'],
                output_trips.loc[idx, 'start_y'],
                all_zones
            )

        if (i // batch_size) % 10 == 0:  # Log every 10 batches
            progress = (batch_end / total_trips) * 100
            logging.info(f"Start zones: {batch_end:,}/{total_trips:,} ({progress:.1f}%)")

    logging.info("Assigning end zones to trips...")

    for i in range(0, total_trips, batch_size):
        batch_end = min(i + batch_size, total_trips)

        # Assign end zones for batch
        for idx in range(i, batch_end):
            output_trips.loc[idx, 'end_zone'] = find_zone(
                output_trips.loc[idx, 'end_x'],
                output_trips.loc[idx, 'end_y'],
                all_zones
            )

        if (i // batch_size) % 10 == 0:  # Log every 10 batches
            progress = (batch_end / total_trips) * 100
            logging.info(f"End zones: {batch_end:,}/{total_trips:,} ({progress:.1f}%)")

    # ==================== DETERMINE TRIP TYPE ====================
    logging.info("Determining trip types...")


    def determine_trip_type(row):
        """Determine if trip is intrazonal or interzonal"""
        if row['start_zone'] == row['end_zone']:
            return 'intrazonal'
        else:
            return 'interzonal'


    output_trips['trip_type'] = output_trips.apply(determine_trip_type, axis=1)

    # ==================== SUMMARY STATISTICS ====================
    logging.info("\n" + "=" * 80)
    logging.info("ZONE ASSIGNMENT SUMMARY")
    logging.info("=" * 80)

    # Start zone distribution
    logging.info("\nStart Zone Distribution:")
    start_zone_counts = output_trips['start_zone'].value_counts().sort_index()
    for zone, count in start_zone_counts.items():
        pct = (count / len(output_trips)) * 100
        logging.info(f"  Zone {zone}: {count:,} trips ({pct:.2f}%)")

    # End zone distribution
    logging.info("\nEnd Zone Distribution:")
    end_zone_counts = output_trips['end_zone'].value_counts().sort_index()
    for zone, count in end_zone_counts.items():
        pct = (count / len(output_trips)) * 100
        logging.info(f"  Zone {zone}: {count:,} trips ({pct:.2f}%)")

    # Trip type distribution
    logging.info("\nTrip Type Distribution:")
    trip_type_counts = output_trips['trip_type'].value_counts()
    for trip_type, count in trip_type_counts.items():
        pct = (count / len(output_trips)) * 100
        logging.info(f"  {trip_type}: {count:,} trips ({pct:.2f}%)")

    # Count trips with at least one point outside
    outside_start = (output_trips['start_zone'] == 'outside').sum()
    outside_end = (output_trips['end_zone'] == 'outside').sum()
    both_outside = ((output_trips['start_zone'] == 'outside') &
                    (output_trips['end_zone'] == 'outside')).sum()

    logging.info(
        f"\nTrips with start outside zones: {outside_start:,} ({(outside_start / len(output_trips) * 100):.2f}%)")
    logging.info(f"Trips with end outside zones: {outside_end:,} ({(outside_end / len(output_trips) * 100):.2f}%)")
    logging.info(f"Trips with both points outside: {both_outside:,} ({(both_outside / len(output_trips) * 100):.2f}%)")

    # ==================== SAVE OUTPUT ====================
    logging.info("\n" + "=" * 80)
    logging.info("Saving output file...")

    output_trips.to_csv(
        OUTPUT_FILE,
        sep=';',
        index=False,
        encoding='utf-8',
        compression='gzip'
    )

    logging.info(f"Output saved to: {OUTPUT_FILE}")
    logging.info(f"Total columns: {len(output_trips.columns)}")
    logging.info(f"New columns added: start_zone, end_zone, trip_type")

    # Show sample of new columns
    logging.info("\nSample of new columns (first 10 rows):")
    logging.info("\n" + output_trips[['person', 'trip_id', 'start_zone', 'end_zone', 'trip_type']].head(10).to_string())

    logging.info("\n" + "=" * 80)
    logging.info("ZONE ASSIGNMENT COMPLETED SUCCESSFULLY!")
    logging.info("=" * 80)

    # ==================== CREATE OD MATRIX ====================
    logging.info("\nCreating Origin-Destination (OD) Matrix...")

    # Create OD matrix
    od_matrix = pd.crosstab(
        output_trips['start_zone'],
        output_trips['end_zone'],
        margins=True,
        margins_name='Total'
    )

    # Save OD matrix
    od_matrix_path = "C:\\Users\\sarf\\Documents\\corrado_phd\\od_matrix_zones.csv"
    od_matrix.to_csv(od_matrix_path, encoding='utf-8')
    logging.info(f"OD Matrix saved to: {od_matrix_path}")

    # Display OD matrix summary
    logging.info("\nOD Matrix Preview (first 5x5):")
    logging.info("\n" + od_matrix.iloc[:5, :5].to_string())

except Exception as e:
    logging.error("Error in zone assignment: " + str(e))
    import traceback

    logging.error(traceback.format_exc())
    sys.exit(1)