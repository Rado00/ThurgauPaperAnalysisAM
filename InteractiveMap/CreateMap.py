import geopandas as gpd
import folium
import warnings
import numpy as np
from folium.plugins import HeatMap
from branca.colormap import linear
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Settings
pd.set_option('display.max_columns', None)
warnings.filterwarnings("ignore")

# Load the shapefile
shapefile_path = r".\weinfelden_zones\\Weinfelden_Zones.shp"
gdf = gpd.read_file(shapefile_path)
gdf = gdf[['Shape_Leng', 'Shape_Area', 'geometry']]
gdf['car'] = np.random.randint(30, 40, gdf.shape[0])
gdf['bus'] = np.random.randint(10, 50, gdf.shape[0])
gdf['train'] = 100 - gdf['car'] - gdf['bus']

# Reproject to EPSG:4326
gdf_4326 = gdf.to_crs(epsg=4326)
print("Original CRS:", gdf_4326.crs)

def embed_fig(fig):
    """ Convert Matplotlib figure 'fig' into a <img> tag for HTML use using base64 encoding. """
    buf = BytesIO()
    fig.savefig(buf, format='png')
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"

# Create pie charts
for idx, row in gdf_4326.iterrows():
    fig, ax = plt.subplots(figsize=(1.2, 1.2))
    labels = ['Car', 'Train', 'Bus']
    sizes = [row['car'], row['train'], row['bus']]
    ax.pie(sizes, labels=labels, autopct=lambda p: f'{p:.1f}%', startangle=90, textprops={'fontsize': 8})
    ax.axis('equal')
    plt.close(fig)
    gdf_4326.at[idx, 'pie_chart'] = embed_fig(fig)

# Calculate centroid for map centering
centroid = gdf_4326.geometry.centroid
map_center = [centroid.y.mean(), centroid.x.mean()]

# Create the Folium map
mymap = folium.Map(location=map_center, zoom_start=10, tiles='OpenStreetMap')

population_csv = "filtered_output_persons.csv"
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

# Create a feature group for the heatmap layer
heatmap_group = folium.FeatureGroup(name='Heatmap').add_to(mymap)

# Add the heatmap layer to the feature group
HeatMap(heat_data, name='heatmap', radius=15, blur=10, max_zoom=1).add_to(heatmap_group)

# Add additional tile layers with proper attributions
folium.TileLayer('CartoDB positron', name='CartoDB Positron', attr="Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.").add_to(mymap)
folium.TileLayer(tiles='https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png', name='OpenRailwayMap', attr="Map data: © OpenRailwayMap contributors").add_to(mymap)

# Color maps
pop_colormap = linear.YlOrRd_09.scale(gdf_4326['car'].min(), gdf_4326['car'].max()).add_to(mymap)
pop_colormap.caption = 'car'

train_colormap = linear.YlOrRd_09.scale(gdf_4326['train'].min(), gdf_4326['train'].max()).add_to(mymap)
train_colormap.caption = 'train'

bus_colormap = linear.YlOrRd_09.scale(gdf_4326['bus'].min(), gdf_4326['bus'].max()).add_to(mymap)
bus_colormap.caption = 'bus'

def apply_style(feature, colormap, property_name):
    return {
        'fillColor': colormap(feature['properties'][property_name]),
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7
    }

# Add GeoJson layers with Pie Chart Popups
features = ['car', 'train', 'bus']
for feature in features:
    if feature == 'car':
        colormap = pop_colormap
    elif feature == 'train':
        colormap = train_colormap
    else:
        colormap = bus_colormap
    folium.GeoJson(
        gdf_4326.to_json(),
        name=feature.capitalize(),
        style_function=lambda x, colormap=colormap, property_name=feature: apply_style(x, colormap, property_name),
        tooltip=folium.GeoJsonTooltip(fields=[feature]),
        popup=folium.GeoJsonPopup(fields=['pie_chart'], labels=False)
    ).add_to(mymap)

# Custom CSS to hide default popup frame
style = """
<style>
    .leaflet-popup-content-wrapper, .leaflet-popup-tip {
        background: transparent;
        box-shadow: none;
        border: none;
    }
</style>
"""
mymap.get_root().html.add_child(folium.Element(style))

# Custom HTML legend for population density
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 180px; height: 200px; 
            background-color: white; z-index:9999; font-size:14px;
            border:2px solid grey; padding: 10px;">
<b>Population Density</b><br>
(people/km²) <br>
<i style="background: #ffffcc; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 0-100<br>
<i style="background: #ffeda0; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 100-200<br>
<i style="background: #feb24c; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 200-400<br>
<i style="background: #fd8d3c; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 400-600<br>
<i style="background: #fc4e2a; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 600-1000<br>
<i style="background: #e31a1c; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 1000-2000<br>
<i style="background: #bd0026; width: 18px; height: 18px; float: left; opacity: 0.7;"></i> 2000+<br>
</div>
'''
mymap.get_root().html.add_child(folium.Element(legend_html))

# Add Layer control once
folium.LayerControl().add_to(mymap)

# Save and display the map
mymap.save("map.html")
mymap  # Display the map in a Jupyter Notebook
