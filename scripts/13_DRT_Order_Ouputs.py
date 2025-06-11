# Import necessary libraries
import logging
from functions.commonFunctions import *
import pandas as pd
import numpy as np



if __name__ == '__main__':
    setup_logging(get_log_filename())

    data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name, csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging, target_area = read_config()
    logging.info(f"Reading config file from {data_path} path was successful.")

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    output_plots_folder_name = os.path.basename(sim_output_folder)
    plots_directory = os.path.join(parent_directory, "plots", f"plots_{output_plots_folder_name}")
    output_folder_path: str = os.path.join(data_path, simulation_zone_name, sim_output_folder)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots", f"plots_{os.path.basename(sim_output_folder)}")


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

        # Extract metrics from drt_customer_stats_drt.csv
        cs_last = customer_stats.iloc[-1][[
            "rides", "wait_average", "wait_max", "percentage_WT_below_10",
            "inVehicleTravelTime_mean", "distance_m_mean", "totalTravelTime_mean",
            "rejections", "rejectionRate"
        ]].astype(float)

        # Extract from drt_detailed_distanceStats_drt.csv
        dds_last = detailed_distance_stats.iloc[-1][[
            "0 pax distance_m", "1 pax distance_m", "2 pax distance_m", "3 pax distance_m",
            "4 pax distance_m", "5 pax distance_m", "6 pax distance_m", "7 pax distance_m",
            "8 pax distance_m"
        ]].astype(float)

        # Extract from drt_sharing_metrics_drt.csv
        sm_last = sharing_metrics.iloc[-1][["poolingRate", "sharingFactor", "nTotal"]].astype(float)

        # Extract from drt_vehicle_stats_drt.csv
        vs_last = vehicle_stats.iloc[-1][[
            "totalServiceDuration", "totalDistance", "totalEmptyDistance", "emptyRatio",
            "totalPassengerDistanceTraveled", "averageDrivenDistance", "averageEmptyDistance",
            "averagePassengerDistanceTraveled", "d_p/d_t"
        ]].astype(float)

        # Compute detour stats
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

        # Extract modestats rows
        modestats_series = pd.Series(modestats['drt'].tail(4).values,
                                     index=[f"modestats_row_{i+1}_drt" for i in range(4)])

        # Read operator cost from text file
        with open(os.path.join(output_folder_path, "operator_costs.txt"), "r") as f:
            operator_cost = float(f.read().split(":")[-1].strip())

        # Extract pkm_modestats final row
        pkm_last = pkm_modestats.iloc[-1].drop(labels=["Iteration"])
        pkm_last.index = ["pkm_" + col for col in pkm_last.index]

        # Combine all metrics
        final_series = pd.concat([
            cs_last, dds_last, sm_last, vs_last, detour_stats,
            pd.Series({"operator_cost": operator_cost}), pkm_last, modestats_series
        ])

        # Format output DataFrame
        df_output = pd.DataFrame({
            "Title": final_series.index,
            "Value": final_series.values,
            "Value with Comma": [str(v).replace('.', ',') if isinstance(v, (float, np.float64)) else v for v in
                                 final_series.values]
        })

        # ------------------ FORMAT AND SAVE DRT METRICS ------------------

        formatted_values = []
        formatted_commas = []
        new_index = []

        for i, (key, value) in enumerate(final_series.items()):
            # Rename modestats rows
            # Rename modestats rows
            if key.startswith("modestats_row_"):
                key = f"modestats_row_{12 + i}_drt"

            # Try parsing to float
            try:
                num = float(value)
            except:
                formatted_values.append(value)
                formatted_commas.append(str(value).replace('.', ','))
                new_index.append(key)
                continue

            # Distance conversions (from meters to kilometers and round)
            if (
                    "distance_m" in key or
                    key in [
                "totalDistance", "totalEmptyDistance", "totalPassengerDistanceTraveled",
                "averageDrivenDistance", "averageEmptyDistance", "averagePassengerDistanceTraveled",
                "Tot distance", "Tot unsharedDistance", "Total distanceDetour"
            ]
            ):
                num = round(num / 1000)
                if "distance_m" in key:
                    key = key.replace("distance_m", "distance_Km")
                elif "distance" or "Distance" in key:
                    key += "_Km"

            # Convert and rename totalServiceDuration to hours
            elif key == "totalServiceDuration":
                num = round(num / 3600)
                key = "totalServiceDuration_h"

            # Custom rounding logic
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

        # Create DataFrame
        df_output = pd.DataFrame({
            "Title": new_index,
            "Value": formatted_values,
            "Value with Comma": formatted_commas
        })

        # Save to CSV with semicolon separator
        os.makedirs(plots_directory, exist_ok=True)
        df_output.to_csv(
            os.path.join(plots_directory, "drt_summary_metrics.csv"),
            index=False,
            sep=';'
        )

        logging.info("DRT summary metrics successfully saved.")

    except Exception as e:
        logging.error(f"Failed to generate DRT summary metrics: {e}")

