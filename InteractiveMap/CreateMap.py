import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import HeatMap

# Load the saved GeoDataFrame
gdf_path = "municipalities_gdf.geojson"
municipalities_gdf = gpd.read_file(gdf_path)

# Ensure the GeoDataFrame has the necessary columns
if 'population_density' not in municipalities_gdf.columns:
    print("Error: 'population_density' column is missing in GeoDataFrame")
else:
    print("GeoDataFrame loaded successfully")

# Re-project to a projected CRS for accurate centroid calculation
municipalities_gdf = municipalities_gdf.to_crs('EPSG:2056')

# Create a folium map centered around Thurgau
map_center = [47.5508, 9.0455]  # Approximate center of Thurgau
m = folium.Map(location=map_center, zoom_start=12)

# Define custom bins and colorscale for people per square kilometer (people/km²)
bins = [0, 100, 200, 400, 600, 1000, 2000, 5000]  # Use a large number instead of infinity
colorscale = 'YlOrRd'  # Using the same color scale

# Temporarily fill NaN values for the choropleth layer creation
choropleth_data = municipalities_gdf.copy()
choropleth_data['population_density'] = choropleth_data['population_density'].fillna(-1)  # Use a value outside the normal range

# Add choropleth layer for population density
choropleth = folium.Choropleth(
    geo_data=choropleth_data.to_crs('EPSG:4326'),  # Re-project back to WGS84 for display
    name='choropleth',
    data=choropleth_data,
    columns=['gde_nr', 'population_density'],
    key_on='feature.properties.gde_nr',
    fill_color=colorscale,
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Population Density (people/km²)',
    bins=bins,
    reset=True
).add_to(m)

# Load population data points with specified dtypes to avoid mixed type warnings
population_csv = "./filtered_output_persons.csv"
population_df = pd.read_csv(population_csv, dtype={
    'carAvail': str,
    'hasLicense': str,
    'person': str,
    'ptHasHalbtax': str,
    'ptHasGA': str,
    'statpopPersonId': float,
    'statpopHouseholdId': float,
    'age': float,
    'home_x': float,
    'home_y': float,
    'isFreight': str
})

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

# Add custom legend with equal spacing
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 200px; height: 200px; 
            border:2px solid grey; z-index:9999; font-size:14px;
            background-color:white; opacity: 0.9;">
    &nbsp; <b>Population Density</b> (people/km²) <br>
    &nbsp; <i>Color Scale</i> <br>
    <div style="background-color:#ffffb2; width:20px; height:20px; display:inline-block"></div>&nbsp;0-100 <br>
    <div style="background-color:#fecc5c; width:20px; height:20px; display:inline-block"></div>&nbsp;100-200 <br>
    <div style="background-color:#fd8d3c; width:20px; height:20px; display:inline-block"></div>&nbsp;200-400 <br>
    <div style="background-color:#f03b20; width:20px; height:20px; display:inline-block"></div>&nbsp;400-600 <br>
    <div style="background-color:#bd0026; width:20px; height:20px; display:inline-block"></div>&nbsp;600-1000 <br>
    <div style="background-color:#800026; width:20px; height:20px; display:inline-block"></div>&nbsp;1000-2000 <br>
    <div style="background-color:#500026; width:20px; height:20px; display:inline-block"></div>&nbsp;2000+ <br>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save the map as an HTML file
map_path = 'population_density_map.html'
m.save(map_path)
print(f"Map saved to {map_path}")
