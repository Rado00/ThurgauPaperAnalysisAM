"""
Batch runner per calcolare il mode share su tutti i CSV di una cartella
di confronto (tipicamente 2_trips_all_activities_for_Comparison_fixed).

Per ogni file CSV nella cartella sorgente:
  1. Estrae il numero di zona dal nome del file (pattern _<N>_ShapeFile_).
  2. Aggiorna config.ini:
       - target_area = <N>_ShapeFile.shp
       - sim_output_folder = <filename_stem>  (per output distinti)
  3. Copia il CSV in {data_path}/{analysis_zone_name}/{clean_csv_folder}/{percentile}/
     con nome trips_all_activities_inside_sim.csv (sovrascrive).
  4. Lancia in sequenza gli script in SCRIPTS_TO_RUN.

Alla fine ripristina il config.ini originale.

Output finali raccolti in:
  plots/ModeShareOutputs_Reordered/modeOutputs_<stem>_<N>_ShapeFile.shp_reordered.csv

Uso:
  python batch_run_modeshare.py
  python batch_run_modeshare.py --source "C:\\path\\to\\folder" --dry-run

Requisiti: conda env ThurgauAnalysisEnv attivo (o lo stesso usato dal .bat).
"""

import argparse
import configparser
import re
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ---------- defaults (override via CLI) ----------
DEFAULT_SOURCE = (
    r"C:\Users\corra\OneDrive - ZHAW\000_Paper2\2024_Paper2_Data"
    r"\MATSim_Thurgau\2_trips_all_activities_for_Comparison_fixed"
)

SCRIPTS_TO_RUN = [
    "07_plot_mode_share.py",
    "08_plot_mode_share_target_area.py",
    # "10_plot_the_clean_csv_files.py",   # uncomment solo se hai population/households CSV
    # "11_DRT_Order_Ouputs.py",           # uncomment solo se hai i CSV DRT operativi
    "12_CSVs_in_a_column.py",
    "13_transform_output_format.py",
]

ZONE_RE = re.compile(r"_(\d+)_ShapeFile", re.IGNORECASE)
TRIPS_SUFFIX_RE = re.compile(r"_trips_all_activities_inside_sim(_fx)?$", re.IGNORECASE)


def extract_zone(filename: str) -> str | None:
    m = ZONE_RE.search(filename)
    return m.group(1) if m else None


def stem_for_sim_output_folder(filename: str) -> str:
    stem = Path(filename).stem
    return TRIPS_SUFFIX_RE.sub("", stem)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Cartella sorgente con i CSV")
    parser.add_argument("--config", default=None, help="Path config.ini (auto-detect di default)")
    parser.add_argument("--scripts-dir", default=None, help="Cartella scripts (auto-detect di default)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra cosa farebbe, senza eseguire")
    parser.add_argument("--start-from", type=int, default=1, help="Indice 1-based da cui riprendere")
    args = parser.parse_args()

    scripts_dir = Path(args.scripts_dir) if args.scripts_dir else Path(__file__).resolve().parent
    repo_root = scripts_dir.parent
    config_path = Path(args.config) if args.config else (repo_root / "config" / "config.ini")
    source = Path(args.source)

    if not config_path.exists():
        print(f"ERROR: config.ini non trovato: {config_path}")
        return 1
    if not source.exists():
        print(f"ERROR: cartella sorgente non trovata: {source}")
        return 1

    config = configparser.ConfigParser()
    config.read(config_path)

    data_path = Path(config.get("config", "data_path"))
    analysis_zone = config.get("config", "analysis_zone_name")
    clean_csv_folder = config.get("config", "clean_csv_folder")
    percentile = config.get("config", "percentile")

    dest_folder = data_path / analysis_zone / clean_csv_folder / percentile
    dest_file = dest_folder / "trips_all_activities_inside_sim.csv"

    csv_files = sorted(source.glob("*.csv"))
    if not csv_files:
        print(f"WARNING: nessun CSV in {source}")
        return 0

    print(f"Trovati {len(csv_files)} CSV in {source}")
    print(f"Config: {config_path}")
    print(f"Destinazione: {dest_file}")
    print(f"Scripts da lanciare per ogni file: {SCRIPTS_TO_RUN}")
    print()

    # Backup config.ini
    backup_path = config_path.with_suffix(f".ini.bak.{datetime.now():%Y%m%d_%H%M%S}")
    if not args.dry_run:
        shutil.copy2(config_path, backup_path)
        print(f"Backup config: {backup_path}\n")

    log_path = repo_root / "logs" / f"batch_modeshare_{datetime.now():%Y%m%d_%H%M%S}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str]] = []

    try:
        for i, csv_file in enumerate(csv_files, 1):
            if i < args.start_from:
                continue

            print(f"\n[{i}/{len(csv_files)}] {csv_file.name}")

            zone = extract_zone(csv_file.name)
            if not zone:
                msg = "zone non estraibile dal nome (pattern _<N>_ShapeFile_ assente)"
                print(f"  SKIP: {msg}")
                failures.append((csv_file.name, msg))
                continue

            stem = stem_for_sim_output_folder(csv_file.name)
            target_area = f"{zone}_ShapeFile.shp"

            print(f"  zone={zone}  target_area={target_area}")
            print(f"  sim_output_folder={stem}")

            if args.dry_run:
                continue

            # Update config.ini
            config.set("config", "target_area", target_area)
            config.set("config", "sim_output_folder", stem)
            with open(config_path, "w") as f:
                config.write(f)

            # Copy CSV
            dest_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(csv_file, dest_file)

            # Run scripts
            file_failed = False
            for script in SCRIPTS_TO_RUN:
                print(f"  -> {script}")
                with open(log_path, "a", encoding="utf-8") as logf:
                    logf.write(f"\n{'='*80}\n[{i}/{len(csv_files)}] {csv_file.name} -> {script}\n{'='*80}\n")
                    logf.flush()
                    result = subprocess.run(
                        [sys.executable, script],
                        cwd=scripts_dir,
                        stdout=logf,
                        stderr=subprocess.STDOUT,
                    )
                if result.returncode != 0:
                    msg = f"{script} ha fallito (exit {result.returncode})"
                    print(f"     ERROR: {msg} -- vedi {log_path}")
                    failures.append((csv_file.name, msg))
                    file_failed = True
                    break

            if not file_failed:
                print("  OK")

    finally:
        # Ripristina config
        if not args.dry_run and backup_path.exists():
            shutil.copy2(backup_path, config_path)
            print(f"\nConfig ripristinato da {backup_path}")

    print(f"\nLog completo: {log_path}")
    if failures:
        print(f"\n{len(failures)} fallimenti:")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        return 2
    print("\nTutti i file processati con successo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
