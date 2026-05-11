"""
Aggrega tutti i file modeOutputs_*_reordered.csv presenti in
plots/ModeShareOutputs_Reordered/ in un unico CSV wide-format.

Per ogni CSV:
  - estrae il nome simulazione dal filename (es. "25_drt_70_8_Service_Zone_25_Fvero"
    da "modeOutputs_20260415_174340_DRT_25_ShapeFile_25_drt_70_8_Service_Zone_25_Fvero_25_ShapeFile.shp_reordered.csv")
  - prende la colonna "Value with Comma" (numeri con virgola decimale)
  - la aggiunge come colonna del CSV aggregato, etichettata col nome simulazione

Le colonne nell'output sono ordinate secondo COLUMN_ORDER. Eventuali simulazioni
mancanti vengono segnalate; eventuali simulazioni presenti ma non in COLUMN_ORDER
vengono aggiunte in coda con warning.

Uso:
  python aggregate_modeshare_outputs.py
  python aggregate_modeshare_outputs.py --input-dir "..." --output "..."
  python aggregate_modeshare_outputs.py --column-order-file column_order.txt
"""

import argparse
import re
import sys
from pathlib import Path
import pandas as pd


COLUMN_ORDER = [
    "01_drt_5_8_01_1", "01_drt_3_8_01_2", "01_drt_2_8_01_3", "01_drt_1_8_01_4",
    "02_drt_3_8_02_1", "02_drt_2_8_02_2", "02_drt_1_8_02_3",
    "03_drt_7_8_03_1", "03_drt_4_8_03_2", "03_drt_3_8_03_3", "03_drt_2_8_03_4", "03_drt_1_8_03_5",
    "04_drt_3_8_04_1", "04_drt_2_8_04_2", "04_drt_1_8_04_3",
    "05_drt_12_8_05_1", "05_drt_8_8_05_2", "05_drt_5_8_05_3", "05_drt_3_8_05_4", "05_drt_2_8_05_5",
    "06_drt_8_8_06_1", "06_drt_5_8_06_2", "06_drt_3_8_06_3", "06_drt_2_8_06_4", "06_drt_1_8_06_5",
    "07_drt_5_8_07_1", "07_drt_3_8_07_2", "07_drt_2_8_07_3", "07_drt_1_8_07_4",
    "08_drt_7_8_08_1", "08_drt_4_8_08_2", "08_drt_3_8_08_3", "08_drt_2_8_08_4", "08_drt_1_8_08_5",
    "09_drt_4_8_09_1", "09_drt_2_8_09_2", "09_drt_1_8_09_4",
    "10_drt_1_8_10_1",
    "11_drt_7_8_11_1", "11_drt_4_8_11_2", "11_drt_3_8_11_3", "11_drt_2_8_11_4", "11_drt_1_8_11_5",
    "12_drt_5_8_12_1", "12_drt_3_8_12_2", "12_drt_2_8_12_3", "12_drt_1_8_12_4",
    "13_drt_2_8_13_1", "13_drt_1_8_13_2",
    "14_drt_8_8_14_1", "14_drt_5_8_14_2", "14_drt_3_8_14_3", "14_drt_2_8_14_4", "14_drt_1_8_14_5",
    "15_drt_23_8_15_1", "15_drt_14_8_15_2", "15_drt_9_8_15_3", "15_drt_6_8_15_4", "15_drt_4_8_15_5",
    "16_drt_5_8_16_1", "16_drt_3_8_16_2", "16_drt_2_8_16_3", "16_drt_1_8_16_4",
    "17_drt_2_8_17_1", "17_drt_1_8_17_2",
    "18_drt_4_8_18_1", "18_drt_3_8_18_2", "18_drt_2_8_18_3", "18_drt_1_8_18_4",
    "19_drt_33_8_19_1", "19_drt_21_8_19_2", "19_drt_13_8_19_3", "19_drt_8_8_19_4", "19_drt_6_8_19_5",
    "20_drt_57_8_20_1", "20_drt_36_8_20_2", "20_drt_22_8_20_3", "20_drt_14_8_20_4", "20_drt_10_8_20_5",
    "21_drt_32_8_21_1", "21_drt_20_8_21_2", "21_drt_12_8_21_3", "21_drt_8_8_21_4", "21_drt_5_8_21_5",
    "22_drt_16_8_22_1", "22_drt_10_8_22_2", "22_drt_6_8_22_3", "22_drt_4_8_22_4", "22_drt_3_8_22_5",
    "23_drt_55_8_23_1", "23_drt_35_8_23_2", "23_drt_21_8_23_3", "23_drt_14_8_23_4", "23_drt_9_8_23_5",
    "24_drt_36_8_24_1", "24_drt_23_8_24_2", "24_drt_14_8_24_3", "24_drt_9_8_24_4", "24_drt_6_8_24_5",
    "25_drt_112_8_25_1", "25_drt_70_8_25_2", "25_drt_43_8_25_3", "25_drt_28_8_25_4", "25_drt_19_8_25_5",
    "25_drt_70_8_Price_Zone_25_0", "25_drt_70_8_Price_Zone_25_NH",
    "25_drt_70_8_Price_Zone_25_5", "25_drt_70_8_Price_Zone_25_10",
    "25_drt_70_8_Service_Zone_25_Fvero", "25_drt_70_8_Service_Zone_25_S",
]


# modeOutputs_[<YYYYMMDD>_<HHMMSS>_]DRT_<zone>_ShapeFile_<CANDIDATE>_<target>_ShapeFile.shp_reordered.csv
# Il timestamp e' opzionale: alcuni file non lo hanno (es. quelli con suffisso _PhD).
SIM_NAME_RE = re.compile(
    r"^modeOutputs_"
    r"(?:\d{8}_\d{6}_)?"
    r"DRT_\d+_ShapeFile_"
    r"(?P<candidate>.+?)"
    r"_\d+_ShapeFile\.shp_reordered\.csv$"
)


def resolve_sim_name(candidate: str, column_order: list[str]) -> str:
    """Match il candidato contro COLUMN_ORDER tramite match esatto o longest-prefix.

    Esempi:
      '25_drt_70_8_Service_Zone_25_Fvero' -> match esatto.
      '01_drt_1_8_01_4_PhD' -> prefix '01_drt_1_8_01_4' seguito da '_PhD' -> '01_drt_1_8_01_4'.
      '00_drt_1_8_Baseline_Final_PhD_FIX' -> nessun match -> ritorna invariato (finira' in extras).
    """
    if candidate in column_order:
        return candidate
    matches = [name for name in column_order if candidate.startswith(name + "_")]
    if matches:
        return max(matches, key=len)
    return candidate


def extract_sim_name(filename: str, column_order: list[str]) -> str | None:
    m = SIM_NAME_RE.match(filename)
    if not m:
        return None
    return resolve_sim_name(m.group("candidate"), column_order)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    default_input = repo_root / "plots" / "ModeShareOutputs_Reordered"
    default_output = repo_root / "plots" / "ModeShareOutputs_Aggregated.csv"

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", default=str(default_input))
    parser.add_argument("--output", default=str(default_output))
    parser.add_argument("--column-order-file",
                        help="Text file con un nome simulazione per riga (override COLUMN_ORDER)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)

    if not input_dir.is_dir():
        print(f"ERROR: input dir non trovata: {input_dir}")
        return 1

    if args.column_order_file:
        column_order = [
            line.strip()
            for line in Path(args.column_order_file).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    else:
        column_order = COLUMN_ORDER

    csv_files = sorted(input_dir.glob("modeOutputs_*_reordered.csv"))
    print(f"Trovati {len(csv_files)} file in {input_dir}\n")

    sim_to_df: dict[str, pd.DataFrame] = {}
    sim_to_meta: dict[str, str] = {}  # nome sim -> stringa "Target Area shapefile is ..."
    skipped: list[tuple[str, str]] = []
    duplicates: list[tuple[str, str, str]] = []

    for csv_file in csv_files:
        sim = extract_sim_name(csv_file.name, column_order)
        if not sim:
            skipped.append((csv_file.name, "regex non match"))
            continue

        df = pd.read_csv(csv_file, sep=";", dtype=str, keep_default_na=False)
        if "Title" not in df.columns or "Value with Comma" not in df.columns:
            skipped.append((csv_file.name, f"colonne attese mancanti: {df.columns.tolist()}"))
            continue

        # Metadata row: Title vuoto, Source File contiene "Target Area shapefile"
        meta_mask = df["Title"].str.strip().eq("") & df["Source File"].str.contains("Target Area", na=False)
        meta_value = df.loc[meta_mask, "Source File"].iloc[0] if meta_mask.any() else ""

        # Data rows: Title non vuoto
        data = df.loc[df["Title"].str.strip().ne(""), ["Title", "Value with Comma"]].copy()
        data = data.rename(columns={"Value with Comma": sim})

        if sim in sim_to_df:
            duplicates.append((sim, str(csv_files[0]), csv_file.name))
            continue

        sim_to_df[sim] = data
        sim_to_meta[sim] = meta_value

    if not sim_to_df:
        print("ERROR: nessun file processabile.")
        return 1

    # Outer merge su Title, preservando l'ordine del primo CSV
    first_sim = next(iter(sim_to_df))
    merged = sim_to_df[first_sim][["Title"]].copy()
    for sim, d in sim_to_df.items():
        merged = merged.merge(d, on="Title", how="outer")

    # Determina ordine colonne
    available_in_order = [s for s in column_order if s in sim_to_df]
    extras = [s for s in sim_to_df if s not in column_order]
    missing = [s for s in column_order if s not in sim_to_df]

    final_sim_cols = available_in_order + extras
    merged = merged[["Title"] + final_sim_cols]

    # Aggiungi colonna Source File (vuota per ogni riga dati)
    merged.insert(0, "Source File", "")

    # Riga metadata in cima: Source File = "" / Title = "Target Area shapefile" / sim cols = <target_area_per_sim>
    meta_row = {"Source File": "", "Title": "Target Area shapefile"}
    for sim in final_sim_cols:
        # Estrai solo "<N>_ShapeFile.shp" dalla stringa "Target Area shapefile is <N>_ShapeFile.shp"
        raw = sim_to_meta.get(sim, "")
        m = re.search(r"Target Area shapefile is\s+(.+)", raw)
        meta_row[sim] = m.group(1).strip() if m else ""

    final = pd.concat([pd.DataFrame([meta_row]), merged], ignore_index=True)

    # Save
    output.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(output, sep=";", index=False, encoding="utf-8-sig")

    print(f"Output: {output}")
    print(f"Shape:  {final.shape}  ({final.shape[0]} righe x {final.shape[1]} colonne)")
    print(f"Simulazioni aggregate: {len(final_sim_cols)}")
    print()

    if missing:
        print(f"WARNING: {len(missing)} sim in COLUMN_ORDER ma NON trovate nei file:")
        for m in missing:
            print(f"  - {m}")
        print()
    if extras:
        print(f"WARNING: {len(extras)} sim trovate ma NON in COLUMN_ORDER (aggiunte in coda):")
        for e in extras:
            print(f"  - {e}")
        print()
    if skipped:
        print(f"WARNING: {len(skipped)} file scartati:")
        for n, reason in skipped:
            print(f"  - {n}: {reason}")
        print()
    if duplicates:
        print(f"WARNING: {len(duplicates)} sim duplicate (mantenuta la prima):")
        for sim, first, dup in duplicates:
            print(f"  - {sim}: gia' visto in {first}, scartato {dup}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
