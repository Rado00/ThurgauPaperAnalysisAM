# Import necessary libraries
import matsim
from common import *
import pandas as pd
import contextily as ctx
import geopandas as gpd
from collections import defaultdict

if __name__ == '__main__':
    setup_logging("04_process_events_activities.log")

    data_path, zone_name, scenario, csv_folder, output_folder, percentile, clean_csv_folder = read_config()

    # Create directory for the zone
    scenario_path: str = os.path.join(data_path, zone_name, scenario, percentile)
    output_folder_path: str = os.path.join(data_path, zone_name, output_folder)

    plans = matsim.plan_reader(os.path.join(scenario_path, "population.xml.gz"))
    records = []
    for person, plan in plans:
        person_id = person.attrib['id']
        for plan_element in plan:
            if plan_element.tag == 'activity':
                records.append({
                    'id': person_id,
                    'x': float(plan_element.attrib['x']),
                    'y': float(plan_element.attrib['y']),
                    'type': plan_element.attrib['type']
                })
    activities = pd.DataFrame.from_records(records)

    # This reads in the network in a structure that contains two tables, one for links and one for nodes.
    network = matsim.read_network(os.path.join(scenario_path, "network.xml.gz"))

    # this creates a geographic dataframe
    network_geo = network.as_geo('epsg:2056')

    # Transform into a geographic dataframe
    activities_geo = gpd.GeoDataFrame(
        activities,
        geometry=gpd.points_from_xy(activities.x, activities.y),
        crs=network_geo.crs
    )

    ax = activities_geo.plot(column="type", figsize=(15, 15), legend=True, alpha=0.1)
    ctx.add_basemap(ax, crs=activities_geo.crs)

    sim_output_path = os.path.join(data_path, zone_name, output_folder)

    events = matsim.event_reader(
        f'{sim_output_path}\\output_events.xml.gz', types='left link,departure')

    # defaultdict creates a value if not there. Here, it creates the default int, which is 0
    link_counts = defaultdict(int)
    departure_counts = defaultdict(int)

    # function to identify the time period based on time of day
    def time_period(time_s):
        if time_s < 12 * 3600:
            return "morning"
        return "afternoon"


    # iterate through all the events. This takes a little while
    for event in events:
        # as for the population, the objects reflect the structure of the XML file
        period = time_period(event["time"])
        link = event["link"]

        if event["type"] == "left link":
            link_counts[(link, period)] += 1
        if event["type"] == "departure":
            mode = event["legMode"]
            departure_counts[(link, period, mode)] += 1

    # transform collected data into a data frame
    count_table = pd.DataFrame.from_records([
        {'link_id': link, 'period': period, 'link_count': link_count}
        for (link, period), link_count in link_counts.items()
    ])

    count_table = network_geo.merge(count_table, on='link_id')

    # plot counts for the morning period
    ax = count_table.query("period == 'morning'").plot(column="link_count", figsize=(15, 15), legend=True, cmap="Reds")
    ax.set_xlim((679000, 687000))
    ax.set_ylim((4.820e6, 4.832e6))
    ctx.add_basemap(ax, crs=count_table.crs)