# Import necessary libraries
import logging
from functions.commonFunctions import *
import pandas as pd
import numpy as np
import os

if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    output_plots_folder_name = os.path.basename(sim_output_folder)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots", f"plots_{output_plots_folder_name}")
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)

    # ------------------ EXTRACT AND SAVE DRT METRICS ------------------
    try:
        # Load CSVs from output_folder_path
        customer_stats = pd.read_csv(os.path.join(output_folder_path, "drt_customer_stats_drt.csv"), sep=";")
        detailed_distance_stats = pd.read_csv(os.path.join(output_folder_path, "drt_detailed_distanceStats_drt.csv"), sep=";")
        sharing_metrics = pd.read_csv(os.path.join(output_folder_path, "drt_sharing_metrics_drt.csv"), sep=";")
        vehicle_stats = pd.read_csv(os.path.join(output_folder_path, "drt_vehicle_stats_drt.csv"), sep=";")
        detours = pd.read_csv(os.path.join(output_folder_path, "output_drt_detours_drt.csv"), sep=";", dtype={'person': str})
        modestats = pd.read_csv(os.path.join(output_folder_path, "modestats.csv"), sep=";")
        pkm_modestats = pd.read_csv(os.path.join(output_folder_path, "pkm_modestats.csv"), sep=";")

        # Extract metrics
        cs_last = customer_stats.iloc[-1][[
            "rides", "wait_average", "wait_max", "percentage_WT_below_10",
            "inVehicleTravelTime_mean", "distance_m_mean", "totalTravelTime_mean",
            "rejections", "rejectionRate"
        ]].astype(float)

        dds_last = detailed_distance_stats.iloc[-1][[
            "0 pax distance_m", "1 pax distance_m", "2 pax distance_m", "3 pax distance_m",
            "4 pax distance_m", "5 pax distance_m", "6 pax distance_m", "7 pax distance_m",
            "8 pax distance_m"
        ]].astype(float)

        sm_last = sharing_metrics.iloc[-1][["poolingRate", "sharingFactor", "nTotal"]].astype(float)

        vs_last = vehicle_stats.iloc[-1][[
            "totalServiceDuration", "totalDistance", "totalEmptyDistance", "emptyRatio",
            "totalPassengerDistanceTraveled", "averageDrivenDistance", "averageEmptyDistance",
            "averagePassengerDistanceTraveled", "d_p/d_t"
        ]].astype(float)

        data_detours = detours[~detours['person'].str.contains("Tot", na=False)]
        for col in ['distance', 'unsharedDistance', 'distanceDetour', 'time', 'unsharedTime', 'timeDetour']:
            data_detours[col] = pd.to_numeric(data_detours[col], errors='coerce')

        tot_distance = data_detours['distance'].sum()
        tot_unshared_distance = data_detours['unsharedDistance'].sum()
        percent_unshared = (tot_unshared_distance / tot_distance) * 100 if tot_distance else 0
        total_distance_detour = (data_detours['distanceDetour'] * data_detours['distance']).sum()
        avg_distance_detour_ratio = total_distance_detour / tot_distance if tot_distance else 0
        total_time_detour = data_detours['timeDetour'].sum()

        detour_stats = pd.Series({
            "Tot distance": tot_distance,
            "Tot unsharedDistance": tot_unshared_distance,
            "% unsharedDistance": percent_unshared,
            "Total distanceDetour": total_distance_detour,
            "Average distanceDetour ratio": avg_distance_detour_ratio,
            "Total timeDetour": total_time_detour
        })

        modestats_series = pd.Series(modestats['drt'].tail(4).values,
                                     index=[f"modestats_row_{i+1}_drt" for i in range(4)])

        with open(os.path.join(output_folder_path, "operator_costs.txt"), "r") as f:
            operator_cost = float(f.read().split(":")[-1].strip())

        pkm_last = pkm_modestats.iloc[-1].drop(labels=["Iteration"])
        pkm_last.index = ["pkm_" + col for col in pkm_last.index]

        final_series = pd.concat([
            cs_last, dds_last, sm_last, vs_last, detour_stats,
            pd.Series({"operator_cost": operator_cost}), pkm_last, modestats_series
        ])

        # Initial source mapping BEFORE renaming or conversion
        source_map = {**{k: "drt_customer_stats_drt.csv" for k in cs_last.index},
                      **{k.replace(" distance_m", " distance_Km"): "drt_detailed_distanceStats_drt.csv" for k in dds_last.index},
                      **{k: "drt_sharing_metrics_drt.csv" for k in sm_last.index},
                      **{k: "drt_vehicle_stats_drt.csv" for k in vs_last.index},
                      **{k: "output_drt_detours_drt.csv" for k in detour_stats.index},
                      **{f"modestats_row_{56 + i}_drt": "modestats.csv" for i in range(4)},
                      **{k: "pkm_modestats.csv" for k in pkm_last.index},
                      "operator_cost": "operator_costs.txt"}

        formatted_values = []
        formatted_commas = []
        new_index = []
        source_files = []

        for i, (key, value) in enumerate(final_series.items()):
            if key.startswith("modestats_row_"):
                key = f"modestats_row_{56 + i}_drt"

            try:
                num = float(value)
            except:
                formatted_values.append(value)
                formatted_commas.append(str(value).replace('.', ','))
                new_index.append(key)
                source_files.append(source_map.get(key, "output_drt_detours_drt.csv"))
                continue

            if " distance_m" in key:
                num = round(num / 1000)
                key = key.replace(" distance_m", " distance_Km")

            elif key in [
                "totalDistance", "totalEmptyDistance", "totalPassengerDistanceTraveled",
                "averageDrivenDistance", "averageEmptyDistance", "averagePassengerDistanceTraveled",
                "Tot distance", "Tot unsharedDistance", "Total distanceDetour"]:
                num = round(num / 1000)
                key += "_Km"

            elif key == "totalServiceDuration":
                num = round(num / 3600)
                key = "totalServiceDuration_h"

            elif key in ["poolingRate", "sharingFactor", "Average distanceDetour ratio"]:
                int_part = int(num)
                frac_part = round(num - int_part, 3)
                num = round(int_part + frac_part, 3)
            elif key == "% unsharedDistance":
                num = round(num, 1)
            elif key.startswith("modestats_row_"):
                num = round(num, 6)
            elif abs(num) >= 1000:
                num = round(num)

            formatted_values.append(num)
            formatted_commas.append(str(num).replace('.', ','))
            new_index.append(key)

            if key in [
                "totalServiceDuration_h", "totalDistance_Km", "totalEmptyDistance_Km", "emptyRatio",
                "totalPassengerDistanceTraveled_Km", "averageDrivenDistance_Km", "averageEmptyDistance_Km",
                "averagePassengerDistanceTraveled_Km", "d_p/d_t"
            ]:
                source_files.append("drt_vehicle_stats_drt.csv")
            else:
                source_files.append(source_map.get(key, "output_drt_detours_drt.csv"))

        df_output = pd.DataFrame({
            "Source File": source_files,
            "Title": new_index,
            "Value": formatted_values,
            "Value with Comma": formatted_commas
        })

        os.makedirs(plots_directory, exist_ok=True)
        df_output.to_csv(
            os.path.join(plots_directory, "drt_summary_metrics.csv"),
            index=False,
            sep=';'
        )

        logging.info("DRT summary metrics successfully saved.")

    except Exception as e:
        logging.error(f"Failed to generate DRT summary metrics: {e}")
