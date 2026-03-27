# Data Processing Pipeline - Methodology Notes

## Overview

The analysis pipeline consists of a sequence of numbered Python scripts that process raw microcensus survey data and MATSim simulation outputs into comparable modal share statistics. The pipeline is controlled by a central `config.ini` file that defines input paths, spatial boundaries, scenario parameters, and toggles for optional data sources (synthetic population, microcensus).

---

## Script 01 — Microcensus Pre-processing

**Input**: `zielpersonen.csv` (individuals), `haushalte.csv` (households) from the Swiss Mobility and Transport Microcensus (MTMC).

**Processing**:
- Extracts and standardizes person-level attributes: age, sex, marital status, driving license, car/bike availability, employment, education, transit subscriptions (GA, Halbtax, Verbund, etc.).
- Extracts household-level attributes: household size, number of cars/bikes, income class, home coordinates.
- Transforms home coordinates from CH1903 (EPSG:21781) to LV95/CH1903+ (EPSG:2056) via `pyproj`.
- Assigns age classes using bounds `[6, 15, 18, 24, 30, 45, 65, 80]`.
- Merges person and household records on `person_id` (= `HHNR`).

**Output**: `all_population.csv` containing one row per surveyed person with both person-level and household-level attributes, including `person_weight` (WP) and `household_weight` (WM).

---

## Script 02 — Microcensus Trip Filtering

**Input**: `wege.csv` (trips), `etappen.csv` (trip stages/legs), the analysis area shapefile, and `all_population.csv`.

### Mode Mapping
The 17 original microcensus transport modes are aggregated into 5 categories:
- **PT**: Train, Postauto, Ship, Tram, Bus, Coach, Taxi, Plane, other PT (modes 1–8, 11)
- **Car**: Car driver, Truck, Motorbike, Mofa (modes 9, 10, 12, 13, 16)
- **Car Passenger**: Detected via stage type 8 in the `etappen` table
- **Bike**: Bicycle/E-bike (mode 14)
- **Walk**: Walking (mode 15)

### Purpose Mapping
Activity purposes are mapped to: `home`, `work`, `education`, `shop`, `leisure`, `other`, `interaction`, `border`, `unknown`. Return trips are detected via the `wzweck2` flag.

### Trip Chain Validation
Persons are removed if their daily trip chain:
- Does **not start** with a home activity (first trip origin)
- Does **not end** with a home activity (last trip destination)
- Contains any trip with an **unknown mode**

### Distance and Time
- Crowfly (Euclidean) distance is computed from origin/destination coordinates.
- Departure/arrival times are converted to seconds from midnight.
- Activity durations are derived from consecutive trip timestamps.

### Spatial Filtering
Two geographic filters are applied using the analysis area shapefile polygon:
1. **O AND D inside**: Both trip origin and destination fall within the analysis area.
2. **O OR D inside**: At least one of origin or destination falls within the analysis area.

The `person_weight` (WP) from `all_population.csv` is merged into the trip records.

**Output**: Spatially filtered trip CSVs (`trips_all_activities_inside_mic.csv`, `trips_at_least_one_activity_inside_mic.csv`) and corresponding filtered population CSVs.

---

## Script 03 — Synthetic Population & Simulation CSV Extraction

**Input**: MATSim XML plan files (`population.xml.gz`, `households.xml.gz` for synthetic population; `output_plans.xml.gz`, `output_households.xml.gz` for simulation).

**Processing**: Parses XML plans into tabular CSV format extracting activities (type, coordinates, times) and legs (mode, distance, travel time). No filtering is applied at this stage.

**Output**: Raw CSV files for activities, legs, persons, households, and routes (both synthetic and simulated).

---

## Script 04/05 — Simulation Trip Filtering & Data Cleaning

This merged script applies the same spatial and quality filters to the simulation output as Script 02 does for the microcensus.

### Geographic Filtering
- Loads `output_trips.csv.gz` with origin/destination coordinates.
- Removes `outside` and `truck` modes.
- Applies the same **O AND D** / **O OR D** spatial filters using the analysis area shapefile.

### Data Cleaning
- **Age filter**: Removes persons under 6 years old (consistent with microcensus).
- **Activity type cleaning**: Removes `freight_loading`, `freight_unloading`, `pt_interaction`.
- **Walk consolidation**: `access_walk` and `egress_walk` legs are merged into `walk`.
- **Orphan plan removal**: Persons left with only a single Home activity after cleaning are removed.
- **Mode normalization**: Underscores replaced, names title-cased (e.g., `car_passenger` → `Car Passenger`).

### Activity Chains
Activity chains are constructed for both microcensus (format: `H-W-L-S-H`) and simulation (format: `HOME-WORK-LEISURE-SHOP-HOME`).

**Output**: Cleaned trip and population CSVs for both spatial filter variants, plus activity chain files.

---

## Script 06 — Synthetic Population Travel Time/Distance

**Input**: Synthetic population plan files.

**Processing**: Extracts travel time, distance, and mode for each leg from XML plans.

**Output**: `travel_time_distance_mode_synt.csv` and `travel_time_distance_mode_sim.csv`.

---

## Script 07 — Mode Share Computation (Full Simulated Area)

**Input**: Cleaned trip CSVs from Script 04/05 (microcensus + simulation + optional synthetic population).

### Metrics Computed
For each transport mode:

1. **Trip-based mode share** (%):
   - Unweighted: simple trip count proportions
   - Weighted (microcensus only): trips weighted by `person_weight` (WP)

2. **Distance-based mode share** (%):
   - Unweighted: proportion of total crowfly distance (mic) / network distance (sim)
   - Weighted: `weighted_distance = crowfly_distance × person_weight`

3. **Average distance and standard deviation** per mode (both weighted and unweighted for microcensus).

4. **DRT metrics** (if DRT mode is present in simulation):
   - DRT OD trips: trips where `main_mode == 'drt'`
   - DRT multi-modal trips: trips containing DRT as a leg but with a different `main_mode`

**Output**: `Mode_shares_by_trip.csv`, `Mode_shares_distance.csv`, `Mode_shares_time.csv`, `drt_trip_metrics.csv`.

---

## Script 08 — Mode Share Computation (Target Area)

Identical logic to Script 07, but applies an **additional** spatial filter using a separate target area shapefile. Computes all metrics separately for:
- **O OR D** within target area
- **O AND D** within target area

**Output**: Target-area-specific mode share CSVs.

---

## Script 12 — Column Consolidation

**Input**: All mode share CSVs from Scripts 07 and 08.

**Processing**: Restructures all metrics into a single columnar format with columns: `Source File`, `Title`, `Value`, `Value with Comma`. Mode names are normalized to: Bike, Car, Car Passenger, PT, Walk. Values are formatted with comma decimal separator for spreadsheet compatibility.

**Output**: `modeOutputs_{scenario}_{target_area}.csv`.

---

## Script 13 — Final Reordering

**Input**: Consolidated CSV from Script 12.

**Processing**: Reorders rows by metric group in a standardized hierarchy:
1. % Trips (Simulated Area → Target Area O OR D)
2. % Distance
3. Count Trips
4. Count Distance
5. Count Travel Time
6. Average Distance
7. STD Distance
8. Repeat for O AND D filter
9. DRT metrics (appended at end)

Each group contains the 5 transport modes (Bike, Car, Car Passenger, PT, Walk) for each applicable spatial scope.

**Output**: `modeOutputs_{scenario}_{target_area}_reordered.csv` — the final analysis output.

---

## Key Design Notes

- **Coordinate system**: All spatial operations use LV95/CH1903+ (EPSG:2056). Microcensus coordinates are transformed from CH1903 at loading.
- **Distance comparability**: Microcensus uses crowfly (Euclidean) distance; simulation uses network distance from MATSim. These are reported separately.
- **Weighting**: Microcensus person weights (WP) are used for population-representative statistics. Simulation assumes uniform agent weight (1:1).
- **Dual spatial filters**: The O AND D / O OR D distinction enables sensitivity analysis on boundary effects.
