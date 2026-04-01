"""
classify_trips_csv.py
─────────────────────
Reads  data/trips_all_activities_inside_sim.csv  and adds two columns:

    pt_modes       – comma-separated sorted set of PT sub-modes used in the
                     trip (e.g. "bus", "rail", "bus, rail").
                     Empty string for non-PT trips.

    main_pt_mode   – the primary PT sub-mode (based on the boarding end of
                     the trip, i.e. the mode of the nearest transit stop to
                     the trip origin).
                     Empty string for non-PT trips.

Method
──────
Because the input CSV is trip-level only (no individual legs), PT sub-modes
are inferred spatially:

  1. The MATSim transit schedule (output_transitSchedule.xml.gz) is parsed to
     build a mapping from every stop facility to the set of transport modes
     (bus / rail / ferry) that serve it.

  2. A KD-tree is built over all stop coordinates.

  3. For each PT trip the nearest stop is found for both the trip origin
     (start_x, start_y) and the trip destination (end_x, end_y).
       • main_pt_mode  = mode of the nearest stop to the origin
       • pt_modes      = sorted unique set of {origin_mode, destination_mode}

  4. All rows are written to the output file; non-PT rows keep empty strings
     in the two new columns.

Usage
─────
  python scripts/classify_trips_csv.py

  Optional arguments:
    --input_csv     PATH   input CSV  (default: data/trips_all_activities_inside_sim.csv)
    --schedule      PATH   transit schedule .xml.gz to use for spatial lookup
                           (default: data/DRT_10_ShapeFile_10_drt_1_8_BaselineCalibDRT_52/
                                      output_transitSchedule.xml.gz)
    --output_csv    PATH   output CSV  (default: derived from input name,
                                        same folder as input)
    --chunksize     INT    rows per processing chunk  (default: 300000)
"""

import argparse
import gzip
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


# ─────────────────────────────────────────────────────────────────
# 1. Argument parsing
# ─────────────────────────────────────────────────────────────────

def parse_args():
    base = Path(__file__).parent.parent

    default_input = base / "data" / "trips_all_activities_inside_sim.csv"
    default_sched = (
        base / "data"
        / "DRT_10_ShapeFile_10_drt_1_8_BaselineCalibDRT_52"
        / "output_transitSchedule.xml.gz"
    )

    parser = argparse.ArgumentParser(
        description="Add pt_modes and main_pt_mode columns to a trips CSV."
    )
    parser.add_argument("--input_csv",  default=str(default_input))
    parser.add_argument("--schedule",   default=str(default_sched))
    parser.add_argument("--output_csv", default=None,
                        help="Output path. Default: input_stem + '_pt_classification.csv'")
    parser.add_argument("--chunksize",  type=int, default=300_000)
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────
# 2. Parse transit schedule → KD-tree + stop-mode lookup
# ─────────────────────────────────────────────────────────────────

def build_stop_index(schedule_path: str):
    """
    Returns (kd_tree, modes_list) where modes_list[i] is the set of
    transport modes served by the i-th stop in the tree.
    """
    print(f"Parsing transit schedule: {schedule_path}")

    with gzip.open(schedule_path, "rb") as fh:
        root = ET.parse(fh).getroot()

    # Collect stop locations
    stop_xy = {}          # stop_id → (x, y)
    for sf in root.findall(".//stopFacility"):
        stop_xy[sf.get("id")] = (float(sf.get("x")), float(sf.get("y")))

    # Collect which modes serve each stop
    stop_modes = {}       # stop_id → set of mode strings
    for line_el in root.findall(".//transitLine"):
        for route_el in line_el.findall("transitRoute"):
            mode_el = route_el.find("transportMode")
            if mode_el is None or not mode_el.text:
                continue
            mode = mode_el.text.strip()
            for stop_el in route_el.findall(".//stop"):
                ref = stop_el.get("refId")
                if ref:
                    stop_modes.setdefault(ref, set()).add(mode)

    # Build ordered arrays for the KD-tree
    ids_list   = list(stop_xy.keys())
    coords     = np.array([stop_xy[sid] for sid in ids_list])
    modes_list = [stop_modes.get(sid, set()) for sid in ids_list]

    tree = cKDTree(coords)

    all_modes = {m for ms in modes_list for m in ms}
    print(f"  Stops: {len(ids_list):,}  |  modes in schedule: {sorted(all_modes)}")
    return tree, modes_list


# ─────────────────────────────────────────────────────────────────
# 3. Resolve a set of modes for one coordinate pair
# ─────────────────────────────────────────────────────────────────

_MODE_PRIORITY = ["rail", "bus", "ferry"]   # for multi-mode stops


def resolve_mode(tree: cKDTree, modes_list: list, x: float, y: float,
                 max_dist: float = 5000.0) -> str:
    """Return the dominant transport mode of the nearest stop within max_dist."""
    dist, idx = tree.query([x, y], k=1)
    if dist > max_dist:
        return "unknown"
    mset = modes_list[idx]
    if not mset:
        return "unknown"
    if len(mset) == 1:
        return next(iter(mset))
    # Prefer rail > bus > ferry when a stop serves multiple modes
    return next((m for m in _MODE_PRIORITY if m in mset), sorted(mset)[0])


# ─────────────────────────────────────────────────────────────────
# 4. Process the trips CSV in chunks
# ─────────────────────────────────────────────────────────────────

def process(input_csv: str, output_csv: str, tree: cKDTree,
            modes_list: list, chunksize: int):

    print(f"\nProcessing: {input_csv}")
    print(f"Output  →   {output_csv}")

    first_chunk = True
    total_rows  = 0
    pt_rows     = 0

    for chunk in pd.read_csv(input_csv, chunksize=chunksize, low_memory=False):
        total_rows += len(chunk)

        # Initialise new columns as empty string for all rows
        chunk["pt_modes"]     = ""
        chunk["main_pt_mode"] = ""

        # Work only on PT rows
        pt_mask = chunk["main_mode"] == "pt"
        pt_idx  = chunk.index[pt_mask]
        pt_rows += pt_mask.sum()

        if pt_mask.any():
            pt_sub = chunk.loc[pt_idx]

            # Mode at trip origin
            origin_modes = [
                resolve_mode(tree, modes_list, row.start_x, row.start_y)
                for row in pt_sub.itertuples(index=False)
            ]

            # Mode at trip destination
            dest_modes = [
                resolve_mode(tree, modes_list, row.end_x, row.end_y)
                for row in pt_sub.itertuples(index=False)
            ]

            # Combine into the two output columns
            combined_modes = [
                ", ".join(sorted({o, d} - {"unknown"})) or "unknown"
                for o, d in zip(origin_modes, dest_modes)
            ]

            chunk.loc[pt_idx, "main_pt_mode"] = origin_modes
            chunk.loc[pt_idx, "pt_modes"]     = combined_modes

        # Write to output (header only on first chunk)
        chunk.to_csv(
            output_csv,
            index=False,
            mode="w" if first_chunk else "a",
            header=first_chunk,
        )
        first_chunk = False

        if total_rows % 600_000 == 0:
            print(f"  … processed {total_rows:,} rows")

    print(f"\nDone.")
    print(f"  Total rows:  {total_rows:,}")
    print(f"  PT trips:    {pt_rows:,}")


# ─────────────────────────────────────────────────────────────────
# 5. Summary stats on the output
# ─────────────────────────────────────────────────────────────────

def print_summary(output_csv: str):
    print("\nSummary of PT classification:")
    chunks = []
    for chunk in pd.read_csv(output_csv, chunksize=300_000,
                             usecols=["main_mode", "pt_modes", "main_pt_mode"]):
        chunks.append(chunk[chunk["main_mode"] == "pt"])
    pt = pd.concat(chunks, ignore_index=True)

    print("\n  main_pt_mode distribution:")
    print(pt["main_pt_mode"].value_counts().to_string())
    print("\n  pt_modes combinations:")
    print(pt["pt_modes"].value_counts().to_string())


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    input_path = Path(args.input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    sched_path = Path(args.schedule)
    if not sched_path.exists():
        raise FileNotFoundError(f"Transit schedule not found: {sched_path}")

    # Derive output path if not given
    if args.output_csv:
        output_path = Path(args.output_csv)
    else:
        stem = input_path.stem          # trips_all_activities_inside_sim
        output_path = input_path.parent / f"{stem}_pt_classification.csv"

    tree, modes_list = build_stop_index(str(sched_path))

    process(
        input_csv  = str(input_path),
        output_csv = str(output_path),
        tree       = tree,
        modes_list = modes_list,
        chunksize  = args.chunksize,
    )

    print_summary(str(output_path))
    print(f"\nOutput file: {output_path}")


if __name__ == "__main__":
    main()
