import geopandas as gpd
from owslib.wms import WebMapService

# Define the WMS service URL
wms_url = 'https://wms.geo.admin.ch/?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities&lang=de'
wms = WebMapService(wms_url, version='1.3.0')

# List available layers to find the one you need (e.g., municipal boundaries)
print(list(wms.contents))

# Assuming 'ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill' is the layer for municipalities
layer_name = 'ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill'

# Get bounding box and coordinate reference system (CRS)
bounding_box = wms[layer_name].boundingBoxWGS84
crs = 'EPSG:4326'  # WGS 84

# Fetch the data as GeoDataFrame using WMS request
gdf = gpd.read_file(f"{wms_url}service=WMS&version=1.3.0&request=GetMap&layers={layer_name}&bbox={bounding_box[0]},{bounding_box[1]},{bounding_box[2]},{bounding_box[3]}&width=3000&height=3000&srs={crs}&format=image/png")

# Display the GeoDataFrame
print(gdf.head())

# Save the GeoDataFrame to a GeoJSON file if needed
gdf.to_file("thurgau_municipalities.geojson", driver="GeoJSON")
