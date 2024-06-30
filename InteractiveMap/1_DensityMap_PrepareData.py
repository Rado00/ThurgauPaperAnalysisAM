import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# Path to GeoJSON files and population CSV
geojson_folder = "C:/Users/muaa/Documents/3_MIEI/2023_ABMT_Data/SwitzerlandShapeFiles/ThurgauMunicipalities/GeoJson"
population_csv = "./filtered_output_persons.csv"
output_gdf_path = "municipalities_gdf.geojson"

# Load population data
population_df = pd.read_csv(population_csv, dtype={'carAvail': str, 'hasLicense': str})

# Create a GeoDataFrame from the population data
population_gdf = gpd.GeoDataFrame(
    population_df,
    geometry=gpd.points_from_xy(population_df.home_x, population_df.home_y),
    crs='EPSG:2056'  # Assuming the coordinates are in CH1903+ / LV95
)

# Load and merge GeoJSON files into a single GeoDataFrame
gdfs = []
for geojson_file in os.listdir(geojson_folder):
    if geojson_file.endswith('.geojson'):
        gdf = gpd.read_file(os.path.join(geojson_folder, geojson_file))
        gdfs.append(gdf)

# Concatenate all GeoDataFrames into one
municipalities_gdf = pd.concat(gdfs, ignore_index=True)

# Ensure the coordinate systems match
population_gdf = population_gdf.to_crs(municipalities_gdf.crs)

# Spatial join to assign each person to a municipality
joined_gdf = gpd.sjoin(population_gdf, municipalities_gdf, how="left", predicate='within')

# Print the first few rows to inspect the columns
print(joined_gdf.head())

# Check the column names of joined_gdf and municipalities_gdf
print("Columns in joined_gdf:", joined_gdf.columns)
print("Columns in municipalities_gdf:", municipalities_gdf.columns)

# Use the correct column name for the municipality identifier
municipality_id_column = 'gde_nr'

# Calculate population density: count of people per municipality area
population_density = joined_gdf.groupby(municipality_id_column).size().reset_index(name='population_count')
municipalities_gdf = municipalities_gdf.merge(population_density, on=municipality_id_column, how='left')

# Re-project to a projected CRS for accurate area calculation
municipalities_gdf = municipalities_gdf.to_crs('EPSG:2056')  # Swiss coordinate system
municipalities_gdf['population_density'] = municipalities_gdf['population_count'] / municipalities_gdf['geometry'].area

# Fill NaN values with 0 for areas with no population data
municipalities_gdf['population_density'] = municipalities_gdf['population_density'].fillna(0)

# Re-project back to WGS84 for consistent GeoJSON output
municipalities_gdf = municipalities_gdf.to_crs('EPSG:4326')

# Save the resulting GeoDataFrame to a GeoJSON file
municipalities_gdf.to_file(output_gdf_path, driver='GeoJSON')
print(f"GeoDataFrame saved to {output_gdf_path}")
