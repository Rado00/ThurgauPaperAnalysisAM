import geopandas as gpd
import folium
from folium.plugins import HeatMap

# Load the saved GeoDataFrame
gdf_path = "municipalities_gdf.geojson"
municipalities_gdf = gpd.read_file(gdf_path)

# Create a folium map centered around Thurgau
map_center = [47.5508, 9.0455]  # Approximate center of Thurgau
m = folium.Map(location=map_center, zoom_start=12)

# Add choropleth layer for population density
folium.Choropleth(
    geo_data=municipalities_gdf,
    name='choropleth',
    data=municipalities_gdf,
    columns=['gde_nr', 'population_density'],
    key_on='feature.properties.gde_nr',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Population Density'
).add_to(m)

# Prepare data for heat map
heat_data = [[point.y, point.x] for point in municipalities_gdf.geometry.centroid]

# Add heat map layer
HeatMap(heat_data, name='heatmap', radius=15).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Save the map as an HTML file
map_path = 'population_density_map.html'
m.save(map_path)
print(f"Map saved to {map_path}")
