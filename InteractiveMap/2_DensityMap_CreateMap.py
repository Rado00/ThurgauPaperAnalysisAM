import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import HeatMap

# Load the saved GeoDataFrame
gdf_path = "municipalities_gdf.geojson"
municipalities_gdf = gpd.read_file(gdf_path)

# Re-project to a projected CRS for accurate centroid calculation
municipalities_gdf = municipalities_gdf.to_crs('EPSG:2056')

# Create a folium map centered around Thurgau
map_center = [47.5508, 9.0455]  # Approximate center of Thurgau
m = folium.Map(location=map_center, zoom_start=12)

# Add choropleth layer for population density
choropleth = folium.Choropleth(
    geo_data=municipalities_gdf.to_crs('EPSG:4326'),  # Re-project back to WGS84 for display
    name='choropleth',
    data=municipalities_gdf,
    columns=['gde_nr', 'population_density'],
    key_on='feature.properties.gde_nr',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Population Density'
).add_to(m)

# Load population data points
population_csv = "./filtered_output_persons.csv"
population_df = pd.read_csv(population_csv, dtype={'carAvail': str, 'hasLicense': str})

# Create a GeoDataFrame from the population data
population_gdf = gpd.GeoDataFrame(
    population_df,
    geometry=gpd.points_from_xy(population_df.home_x, population_df.home_y),
    crs='EPSG:2056'  # Assuming the coordinates are in CH1903+ / LV95
)

# Ensure the coordinate systems match
population_gdf = population_gdf.to_crs('EPSG:4326')

# Prepare data for heat map using home coordinates
heat_data = [[point.y, point.x] for point in population_gdf.geometry]

# Debug output: print first few heatmap data points
print("First few heatmap data points:", heat_data[:5])

# Create a feature group for the heatmap layer
heatmap_group = folium.FeatureGroup(name='Heatmap').add_to(m)

# Add the heatmap layer to the feature group
HeatMap(heat_data, name='heatmap', radius=15, blur=10, max_zoom=1).add_to(heatmap_group)

# Add layer control to toggle between choropleth and heat map
folium.LayerControl().add_to(m)

# Save the map as an HTML file
map_path = 'population_density_map.html'
m.save(map_path)
print(f"Map saved to {map_path}")
