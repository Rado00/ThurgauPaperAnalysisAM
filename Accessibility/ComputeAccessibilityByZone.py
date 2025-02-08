import xml.etree.ElementTree as ET
import geopandas as gpd
import pandas as pd
import gzip
from shapely.geometry import Point


# === Step 1: Load Public Transport Stops from `transit_schedule.xml.gz` ===
def parse_transit_schedule(xml_gz_file):
    """
    Parses MATSim transit_schedule.xml.gz to extract public transport stop locations.
    Returns a GeoDataFrame with stop locations.
    """
    with gzip.open(xml_gz_file, 'rt', encoding="utf-8") as f:
        tree = ET.parse(f)
        root = tree.getroot()

    stop_data = []
    for stop in root.findall("./stopFacility"):
        stop_id = stop.get("id")
        stop_name = stop.get("name")
        x, y = float(stop.get("x")), float(stop.get("y"))
        stop_data.append({"stop_id": stop_id, "name": stop_name, "x": x, "y": y})

    stops_gdf = gpd.GeoDataFrame(stop_data, geometry=gpd.points_from_xy([s["x"] for s in stop_data],
                                                                        [s["y"] for s in stop_data]),
                                 crs="EPSG:2056")  # CH1903+ Swiss coordinate system
    return stops_gdf


# === Step 2: Load Thurgau Canton Zones (Shapefiles) ===
def load_thurgau_zones(zone_shapefiles):
    """
    Loads multiple Thurgau zone shapefiles and merges them into a single GeoDataFrame.
    """
    all_zones = []
    for shapefile in zone_shapefiles:
        print(f"Loading shapefile: {shapefile}")
        gdf = gpd.read_file(shapefile)

        if gdf.empty:
            print(f"⚠️ Warning: Shapefile {shapefile} is EMPTY!")

        gdf = gdf.to_crs("EPSG:2056")  # Ensure correct coordinate system
        gdf["zone_name"] = shapefile.split("/")[-1].replace(".shp", "")  # Extract name from file path
        all_zones.append(gdf)

    merged_zones = pd.concat(all_zones, ignore_index=True)
    return merged_zones


# === Step 3: Compute Accessibility (Join Stops with Zones) ===
def compute_accessibility(stops_gdf, zones_gdf):
    """
    Spatially joins stops with the 18 internal zones to analyze accessibility.
    Computes the number of stops per zone and assigns accessibility scores.
    """
    print("\n🔍 Checking Data Before Spatial Join")
    print(f"Total stops loaded: {len(stops_gdf)}")
    print(f"Total zones loaded: {len(zones_gdf)}")

    # Check CRS before spatial join
    print(f"Stops CRS: {stops_gdf.crs}")
    print(f"Zones CRS: {zones_gdf.crs}")

    # Ensure CRS matches
    if stops_gdf.crs != zones_gdf.crs:
        print("⚠️ CRS mismatch! Converting stops to match zones.")
        stops_gdf = stops_gdf.to_crs(zones_gdf.crs)

    stops_with_zones = gpd.sjoin(stops_gdf, zones_gdf, how="left", predicate="within")

    # Check if any stops were assigned to zones
    print("\n🚦 Checking Spatial Join Results")
    print(f"Stops assigned to zones: {len(stops_with_zones.dropna())} out of {len(stops_with_zones)}")

    if stops_with_zones.dropna().empty:
        print("⚠️ No stops were found inside the zones! Check CRS and spatial boundaries.")

    # Count stops per zone
    zone_accessibility = stops_with_zones.groupby("zone_name").size().reset_index(name="num_stops")

    # Normalize accessibility (0 to 1 scale)
    if zone_accessibility["num_stops"].max() > 0:
        zone_accessibility["accessibility_score"] = zone_accessibility["num_stops"] / zone_accessibility[
            "num_stops"].max()
    else:
        zone_accessibility["accessibility_score"] = 0  # Avoid division by zero

    return zone_accessibility


# === Run the Accessibility Analysis ===
if __name__ == "__main__":
    # File Paths
    transit_schedule_file = r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/MATSim_Thurgau/Baseline_Scenario/100pct/transit_schedule.xml.gz"

    zone_shapefiles = [
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/01_Weinfelden_Affeltrangen/01_Weinfelden_Affeltrangen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/02_Weinfelden_Amlikon-Bissegg/02_Weinfelden_Amlikon-Bissegg.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/03_Weinfelden_Berg/03_Weinfelden_Berg.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/04_Weinfelden_Birwinken/04_Weinfelden_Birwinken.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/05_Weinfelden_Bischofszell/05_Weinfelden_Bischofszell.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/06_Weinfelden_Bürglen/06_Weinfelden_Bürglen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/07_Weinfelden_Bussnang/07_Weinfelden_Bussnang.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/08_Weinfelden_Erlen/08_Weinfelden_Erlen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/09_Weinfelden_Hauptwil-Gottshaus/09_Weinfelden_Hauptwil-Gottshaus.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/10_Weinfelden_Hohentannen/10_Weinfelden_Hohentannen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/11_Weinfelden_Kradolf-Schönenberg/11_Weinfelden_Kradolf-Schönenberg.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/12_Weinfelden_Märstetten/12_Weinfelden_Märstetten.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/13_Weinfelden_Schönholzerswilen/13_Weinfelden_Schönholzerswilen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/14_Weinfelden_Sulgen/14_Weinfelden_Sulgen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/15_Weinfelden_Weinfelden/15_Weinfelden_Weinfelden.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/16_Weinfelden_Wigoltingen/16_Weinfelden_Wigoltingen.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/17_Weinfelden_Wuppenau/17_Weinfelden_Wuppenau.shp",
        r"C:/Users/muaa/OneDrive - ZHAW/000_Paper2/2024_Paper2_Data/Paper2_ShapeFiles_CH1903+_LV95/18_Weinfelden_Zihlschlacht-Sitterdorf/18_Weinfelden_Zihlschlacht-Sitterdorf.shp"
    ]

    # Load data
    stops_gdf = parse_transit_schedule(transit_schedule_file)
    zones_gdf = load_thurgau_zones(zone_shapefiles)

    # Compute accessibility
    zone_accessibility = compute_accessibility(stops_gdf, zones_gdf)

    # Save results to CSV
    zone_accessibility.to_csv("thurgau_accessibility_debug.csv", index=False)
    print("\n✅ Accessibility data saved to 'thurgau_accessibility_debug.csv'")
