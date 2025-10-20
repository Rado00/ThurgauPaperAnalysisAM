from pandas import DataFrame
import time
from datetime import datetime
import pandas as pd
from functions.commonFunctions import *

start_time = time.time()


def _fmt_mode(m):
    """Format a mode string like 'car_ride' -> 'Car Ride'; handle None/NaN."""
    if pd.isna(m) or m is None:
        return "None"
    return str(m).replace('_', ' ').title()


def _fmt_mode_series(s: pd.Series) -> pd.Series:
    """
    Safe, vectorized formatter for mode series that may be categorical.
    Returns a Pandas 'string' dtype series usable with .str.cat.
    """
    # keep NaN → "None" at the end
    ss = s.astype('string')  # doesn't force conversion to object; preserves NaN
    ss = ss.str.replace('_', ' ', regex=False).str.title()
    return ss.fillna('None')


# ---------------------------
# Summary generation
# ---------------------------
def generate_summary_file(
        df1_post_freight: pd.DataFrame,
        df2_post_freight: pd.DataFrame,
        merged_counts: pd.DataFrame,
        df1_filtered: pd.DataFrame,
        df2_filtered: pd.DataFrame,
        detailed_expanded: bool = False,
        output_path: str = None,
        first_file_name: str = "",
        second_file_name: str = ""
) -> None:
    """
    Generate a summary report text file with statistics about outside mode,
    same-mode drops, and transitions between datasets.

    CORRECTED VERSION: Now properly tracks all extra records as None_ transitions
    """
    logging.info("Starting summary file generation")
    t0 = time.time()

    lines = []
    # Create the empty DataFrame
    transition_columns = ["Mode Transition", "Records", "Pct Value", "Pct Value with Comma"]
    transition_df = pd.DataFrame(columns=transition_columns)

    # ----- Outside statistics (on post-freight, pre-outside)
    logging.info("Calculating outside mode statistics (post-freight data)")
    outside_count_1 = (df1_post_freight['mode'] == 'outside').sum()
    outside_count_2 = (df2_post_freight['mode'] == 'outside').sum()
    n1 = len(df1_post_freight)
    n2 = len(df2_post_freight)
    outside_1_pct = (outside_count_1 / n1 * 100) if n1 else 0.0
    outside_2_pct = (outside_count_2 / n2 * 100) if n2 else 0.0

    new_data_list = [{
        "Mode Transition": "Outside 1",
        "Records": int(outside_count_1),
        "Pct Value": round(outside_1_pct, 2),
        "Pct Value with Comma": f"{outside_1_pct:.2f}".replace('.', ',')
    }, {
        "Mode Transition": "Outside 2",
        "Records": int(outside_count_2),
        "Pct Value": round(outside_2_pct, 2),
        "Pct Value with Comma": f"{outside_2_pct:.2f}".replace('.', ',')
    }]

    transition_df = pd.concat([transition_df, pd.DataFrame(new_data_list)], ignore_index=True)

    lines.append(f"outside records in data 1: ( {int(outside_count_1)} records - {outside_1_pct:.2f}% )\n")
    lines.append(f"outside records in data 2: ( {int(outside_count_2)} records - {outside_2_pct:.2f}% )\n")
    lines.append("-" * 85 + "\n")

    # ----- Same modes section (what was dropped as equal/common)
    lines.append("Same Modes\n")
    mode_summary = (
        merged_counts.groupby('mode', observed=True)['to_drop']
        .sum()
        .reset_index()
        .sort_values('to_drop', ascending=False)
    )

    total_clean_records = max(len(df1_post_freight), len(df2_post_freight))
    new_data_list = []
    for _, r in mode_summary.iterrows():
        mode_fmt = _fmt_mode(r['mode'])
        pct = (r['to_drop'] / total_clean_records * 100) if total_clean_records else 0.0
        lines.append(f"{mode_fmt}_{mode_fmt} ( {int(r['to_drop'])} records - {pct:.2f}% )\n")
        # Add to transition summary DataFrame
        pct_value = round((r['to_drop'] / total_clean_records * 100), 2) if total_clean_records else 0.0
        pct_value_with_comma = f"{pct_value:.2f}".replace('.', ',')
        new_data_list.append({
            "Mode Transition": f"{mode_fmt}_{mode_fmt}",
            "Records": int(r['to_drop']),
            "Pct Value": pct_value,
            "Pct Value with Comma": pct_value_with_comma})

    lines.append("\n")
    lines.append("Total Number of Same Modes is "f"{int(mode_summary['to_drop'].sum())} records\n\n")

    transition_df = pd.concat([transition_df, pd.DataFrame(new_data_list)], ignore_index=True)
    lines.append("-" * 85 + "\n")

    # ----- Transitions (different modes between datasets)
    lines.append("Mode Transitions (Different Modes Between Datasets)\n\n")
    logging.info("Computing transitions summary")

    # CORRECTED LOGIC: Track ALL differences at record level
    # Get total record counts per person in filtered datasets
    person_counts_1 = df1_filtered.groupby('person').size().reset_index(name='total_records_1')
    person_counts_2 = df2_filtered.groupby('person').size().reset_index(name='total_records_2')

    # Merge to see who has more/fewer records
    person_totals = pd.merge(
        person_counts_1, person_counts_2,
        on='person', how='outer'
    ).fillna(0)

    person_totals['diff'] = person_totals['total_records_2'] - person_totals['total_records_1']

    # Per-person mode counts in the filtered sets
    c1 = df1_filtered.groupby(['person', 'mode'], observed=True).size().reset_index(name='n1')
    c2 = df2_filtered.groupby(['person', 'mode'], observed=True).size().reset_index(name='n2')

    # Persons present in both / only left / only right
    p1 = pd.Index(c1['person'].unique())
    p2 = pd.Index(c2['person'].unique())
    common_persons = p1.intersection(p2)
    only_left_persons = p1.difference(p2)
    only_right_persons = p2.difference(p1)

    # Common persons: calculate transitions
    common = (
        c1[c1['person'].isin(common_persons)]
        .merge(c2[c2['person'].isin(common_persons)], on='person', how='inner', suffixes=('_first', '_second'))
    )
    if not common.empty:
        left = _fmt_mode_series(common['mode_first'])
        right = _fmt_mode_series(common['mode_second'])
        common['display'] = left.str.cat(right, sep='_')
        common['cnt'] = (common['n1'] * common['n2']).astype('int64')
        common_agg = common.groupby('display', as_index=False)['cnt'].sum()
        common_per_person = common.groupby(['person', 'display'], as_index=False)['cnt'].sum()
    else:
        common_agg = pd.DataFrame(columns=['display', 'cnt'])
        common_per_person = pd.DataFrame(columns=['person', 'display', 'cnt'])

    # CORRECTED: For persons with extra records in Dataset 2, attribute to None_ transitions
    # Only left: persons only in Dataset 1
    left_only = c1[c1['person'].isin(only_left_persons)].copy()
    if not left_only.empty:
        left_only['display'] = _fmt_mode_series(left_only['mode']).str.cat(
            pd.Series(['None'] * len(left_only), index=left_only.index, dtype='string'),
            sep='_'
        )
        left_only['cnt'] = left_only['n1'].astype('int64')
        left_only_agg = left_only.groupby('display', as_index=False)['cnt'].sum()
        left_only_per_person = left_only.groupby(['person', 'display'], as_index=False)['cnt'].sum()
    else:
        left_only_agg = pd.DataFrame(columns=['display', 'cnt'])
        left_only_per_person = pd.DataFrame(columns=['person', 'display', 'cnt'])

    # CORRECTED: Only right + persons with NET POSITIVE records in Dataset 2
    # This captures ALL extra records, not just persons completely absent from Dataset 1
    persons_with_extra = person_totals[person_totals['diff'] > 0]['person'].values
    logging.info(f"Found {len(persons_with_extra)} persons with extra records in Dataset 2")
    logging.info(f"Total extra records to attribute: {int(person_totals[person_totals['diff'] > 0]['diff'].sum())}")

    right_with_extra = c2[c2['person'].isin(persons_with_extra)].copy()

    if not right_with_extra.empty:
        # For each person, we need to know how many extra records they have
        right_with_extra = right_with_extra.merge(
            person_totals[['person', 'diff']],
            on='person',
            how='left'
        )

        # Calculate what portion of each mode should be attributed to "None_Mode"
        # Group by person to get total mode counts
        person_mode_totals = right_with_extra.groupby('person').agg({
            'n2': 'sum',
            'diff': 'first'
        }).reset_index()

        # For simplicity, distribute extra records proportionally across modes
        # Or we can just take all records for persons only in Dataset 2
        right_only_persons_set = set(only_right_persons)

        # Separate completely new persons vs persons with extra records
        completely_new = right_with_extra[right_with_extra['person'].isin(right_only_persons_set)].copy()
        has_extra_but_exists = right_with_extra[~right_with_extra['person'].isin(right_only_persons_set)].copy()

        # For completely new persons, count all their records
        if not completely_new.empty:
            completely_new['display'] = pd.Series(['None'] * len(completely_new),
                                                  index=completely_new.index,
                                                  dtype='string').str.cat(
                _fmt_mode_series(completely_new['mode']),
                sep='_'
            )
            completely_new['cnt'] = completely_new['n2'].astype('int64')
            new_persons_agg = completely_new.groupby('display', as_index=False)['cnt'].sum()
        else:
            new_persons_agg = pd.DataFrame(columns=['display', 'cnt'])

        # For persons with extra records, attribute the DIFFERENCE proportionally
        if not has_extra_but_exists.empty:
            # Calculate proportion of each mode for each person
            person_mode_props = has_extra_but_exists.groupby('person')['n2'].sum().reset_index(name='total_modes')
            has_extra_but_exists = has_extra_but_exists.merge(person_mode_props, on='person')
            has_extra_but_exists['mode_proportion'] = has_extra_but_exists['n2'] / has_extra_but_exists['total_modes']

            # Distribute the diff proportionally to modes
            has_extra_but_exists['extra_for_mode'] = (has_extra_but_exists['diff'] *
                                                      has_extra_but_exists['mode_proportion']).round().astype('int64')

            has_extra_but_exists['display'] = pd.Series(['None'] * len(has_extra_but_exists),
                                                        index=has_extra_but_exists.index,
                                                        dtype='string').str.cat(
                _fmt_mode_series(has_extra_but_exists['mode']),
                sep='_'
            )
            extra_records_agg = has_extra_but_exists.groupby('display', as_index=False)['extra_for_mode'].sum()
            extra_records_agg.columns = ['display', 'cnt']
        else:
            extra_records_agg = pd.DataFrame(columns=['display', 'cnt'])

        # Combine both types of "None_" records
        right_only_agg = pd.concat([new_persons_agg, extra_records_agg], ignore_index=True)
        if not right_only_agg.empty:
            right_only_agg = right_only_agg.groupby('display', as_index=False)['cnt'].sum()

        # For detailed per-person tracking
        right_only_per_person = pd.concat([
            completely_new.groupby(['person', 'display'], as_index=False)['cnt'].sum(),
            has_extra_but_exists.groupby(['person', 'display'], as_index=False)['extra_for_mode'].sum().rename(
                columns={'extra_for_mode': 'cnt'})
        ], ignore_index=True)

    else:
        right_only_agg = pd.DataFrame(columns=['display', 'cnt'])
        right_only_per_person = pd.DataFrame(columns=['person', 'display', 'cnt'])

    # Concatenate all aggregated transitions
    all_transitions = pd.concat([common_agg, left_only_agg, right_only_agg], ignore_index=True)
    all_transitions = all_transitions.groupby('display', as_index=False)['cnt'].sum()
    all_transitions = all_transitions.sort_values('cnt', ascending=False)

    # Write summary
    new_data_list = []
    for _, r in all_transitions.iterrows():
        pct = (r['cnt'] / total_clean_records * 100) if total_clean_records else 0.0
        lines.append(f"{r['display']} ( {int(r['cnt'])} records - {pct:.2f}% )\n")
        pct_value = round(pct, 2)
        pct_value_with_comma = f"{pct_value:.2f}".replace('.', ',')
        new_data_list.append({
            "Mode Transition": r['display'],
            "Records": int(r['cnt']),
            "Pct Value": pct_value,
            "Pct Value with Comma": pct_value_with_comma
        })

    transition_df = pd.concat([transition_df, pd.DataFrame(new_data_list)], ignore_index=True)
    lines.append("\n")
    lines.append("Total Number of Different Modes is "f"{int(all_transitions['cnt'].sum())} records\n\n")
    lines.append("-" * 85 + "\n")

    logging.info(f"Summary file generation completed in {time.time() - t0:.2f} seconds")

    # Save summary text file
    output_file = output_path if output_path else 'summary_report.txt'
    if os.path.isdir(output_file):
        output_file = os.path.join(output_file, f'{first_file_name}_{second_file_name}_summary_report.txt')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    logging.info(f"Summary report saved to '{output_file}'")

    # Save CSV
    csv_file = output_file.replace('.txt', '.csv')
    transition_df.to_csv(csv_file, sep=';', index=False, encoding='utf-8-sig')
    logging.info(f"Summary CSV saved to '{csv_file}'")


def analyze_transport_modes(
        file1: str,
        file2: str,
        detailed_expanded: bool = False,
        nrows: int = None,
        output_path: str = None,
        first_file_name: str = "",
        second_file_name: str = ""
):
    """
    Analyze transport mode changes between two simulation outputs.
    CORRECTED VERSION: Properly tracks all extra records
    """
    logging.info("=" * 60)
    logging.info("Starting transport mode analysis")
    logging.info(f"Input file 1: {file1}")
    logging.info(f"Input file 2: {file2}")

    # Load data
    logging.info("Loading CSV files...")
    t_load = time.time()
    nrows_arg = None if (nrows is None or nrows == -1) else nrows
    df1 = pd.read_csv(file1, nrows=nrows_arg)
    df2 = pd.read_csv(file2, nrows=nrows_arg)
    logging.info(f"Data loaded in {time.time() - t_load:.2f} seconds")
    logging.info(f"Data 1 initial shape: {df1.shape}")
    logging.info(f"Data 2 initial shape: {df2.shape}")

    # ----- Filter out freight
    logging.info("Filtering out freight records...")
    freight_1 = (df1['mode'] == 'freight').sum()
    freight_2 = (df2['mode'] == 'freight').sum()
    df1_post_freight = df1.loc[df1['mode'] != 'freight'].copy()
    df2_post_freight = df2.loc[df2['mode'] != 'freight'].copy()
    logging.info(f"Removed {int(freight_1)} freight records from Data 1")
    logging.info(f"Removed {int(freight_2)} freight records from Data 2")
    logging.info(f"Data 1 after freight filter: {len(df1_post_freight)} records")
    logging.info(f"Data 2 after freight filter: {len(df2_post_freight)} records")
    df1 = df1_post_freight
    df2 = df2_post_freight

    # ----- Convert person IDs
    logging.info("Converting person IDs to int32...")
    df1['person'] = pd.to_numeric(df1['person'], errors='coerce').astype('Int64')
    df2['person'] = pd.to_numeric(df2['person'], errors='coerce').astype('Int64')
    n1_before, n2_before = len(df1), len(df2)
    df1 = df1.dropna(subset=['person']).copy()
    df2 = df2.dropna(subset=['person']).copy()
    logging.info(f"Dropped {n1_before - len(df1)} non-numeric person IDs in Data 1")
    logging.info(f"Dropped {n2_before - len(df2)} non-numeric person IDs in Data 2")
    df1['person'] = df1['person'].astype('int32')
    df2['person'] = df2['person'].astype('int32')

    # ----- Drop outside mode
    logging.info("Filtering out 'outside' mode records...")
    outside_1 = (df1['mode'] == 'outside').sum()
    outside_2 = (df2['mode'] == 'outside').sum()
    df1_clean = df1.loc[df1['mode'] != 'outside'].copy()
    df2_clean = df2.loc[df2['mode'] != 'outside'].copy()
    logging.info(f"Removed {int(outside_1)} outside records from Data 1")
    logging.info(f"Removed {int(outside_2)} outside records from Data 2")
    logging.info(f"Data 1 clean: {len(df1_clean)} records")
    logging.info(f"Data 2 clean: {len(df2_clean)} records")

    # Log the difference
    diff_records = len(df2_clean) - len(df1_clean)
    logging.info(f"**RECORD DIFFERENCE: Dataset 2 has {diff_records} more records than Dataset 1**")

    # ----- Count occurrences per (person, mode)
    logging.info("Counting mode occurrences per person...")
    t_count = time.time()
    df1_counts = df1_clean.groupby(['person', 'mode'], observed=True).size().reset_index(name='count_1')
    df2_counts = df2_clean.groupby(['person', 'mode'], observed=True).size().reset_index(name='count_2')
    logging.info(f"Data 1: {len(df1_counts)} unique person-mode combinations")
    logging.info(f"Data 2: {len(df2_counts)} unique person-mode combinations")

    # Find common (person, mode) and compute to_drop = min(count_1, count_2)
    merged_counts = pd.merge(df1_counts, df2_counts, on=['person', 'mode'], how='inner')
    merged_counts['to_drop'] = merged_counts[['count_1', 'count_2']].min(axis=1)
    total_to_drop = int(merged_counts['to_drop'].sum())
    logging.info(f"Found {len(merged_counts)} common person-mode combinations")
    logging.info(f"Total records to drop (common modes): {total_to_drop}")
    logging.info(f"Counting completed in {time.time() - t_count:.2f} seconds")

    # ----- Filter datasets to keep only different modes (vectorized)
    logging.info("Filtering datasets to keep only different modes (vectorized)...")
    t_filter = time.time()

    # Rank entries within each (person, mode) group
    df1_clean = df1_clean.copy()
    df2_clean = df2_clean.copy()
    df1_clean['rank'] = df1_clean.groupby(['person', 'mode'], observed=True).cumcount()
    df2_clean['rank'] = df2_clean.groupby(['person', 'mode'], observed=True).cumcount()

    # Map to_drop to each row via merge (missing -> 0)
    drop_map = merged_counts[['person', 'mode', 'to_drop']]
    df1_f = df1_clean.merge(drop_map, on=['person', 'mode'], how='left')
    df2_f = df2_clean.merge(drop_map, on=['person', 'mode'], how='left')
    df1_f['to_drop'] = df1_f['to_drop'].fillna(0).astype('int64')
    df2_f['to_drop'] = df2_f['to_drop'].fillna(0).astype('int64')

    # Keep rows where rank >= to_drop
    df1_filtered = df1_f.loc[df1_f['rank'] >= df1_f['to_drop'], ['person', 'mode']].reset_index(drop=True)
    df2_filtered = df2_f.loc[df2_f['rank'] >= df2_f['to_drop'], ['person', 'mode']].reset_index(drop=True)

    logging.info(f"Final filtered datasets - Data 1: {len(df1_filtered)} records, Data 2: {len(df2_filtered)} records")
    logging.info(
        f"**FILTERED DIFFERENCE: {len(df2_filtered) - len(df1_filtered)} extra records in Dataset 2 filtered**")
    logging.info(f"Filtering completed in {time.time() - t_filter:.2f} seconds")

    # ----- Primary mode per person (before dropping equals)
    logging.info("Calculating primary modes for each person...")
    t_primary = time.time()

    def get_primary_mode(df: pd.DataFrame) -> pd.DataFrame:
        mode_counts = df.groupby(['person', 'mode'], observed=True).size().reset_index(name='count')
        idx = mode_counts.groupby('person')['count'].idxmax()
        primary = mode_counts.loc[idx, ['person', 'mode']].rename(columns={'mode': 'primary_mode'})
        return primary

    primary_modes_1 = get_primary_mode(df1_clean[['person', 'mode']])
    primary_modes_2 = get_primary_mode(df2_clean[['person', 'mode']])

    comparison = pd.merge(
        primary_modes_1, primary_modes_2, on='person',
        suffixes=('_first', '_second'), how='inner'
    )
    comparison['mode_changed'] = comparison['primary_mode_first'] != comparison['primary_mode_second']
    changed_count = int(comparison['mode_changed'].sum())
    unchanged_count = len(comparison) - changed_count
    logging.info(f"Primary mode comparison: {changed_count} persons changed mode, {unchanged_count} kept same mode")
    logging.info(f"Primary mode analysis completed in {time.time() - t_primary:.2f} seconds")

    # ----- Generate summary report
    generate_summary_file(
        df1_post_freight=df1_post_freight,
        df2_post_freight=df2_post_freight,
        merged_counts=merged_counts,
        df1_filtered=df1_filtered,
        df2_filtered=df2_filtered,
        detailed_expanded=detailed_expanded,
        output_path=output_path,
        first_file_name=first_file_name,
        second_file_name=second_file_name
    )

    return comparison


# main execution
if __name__ == "__main__":

    setup_logging(get_log_filename())

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_of_script = os.path.dirname(script_dir)
    config = configparser.ConfigParser()
    config.read(f'{parent_of_script}\\config\\config.ini')
    section = 'config_compare'

    try:
        doing_comparison = config.getboolean(section, 'doing_comparison')
        comparison_num_rows = config.getint(section, 'comparison_num_rows')
        sim_output_folder_1 = config.get(section, '1_sim_output_folder')
        sim_output_folder_2 = config.get(section, '2_sim_output_folder')
        clean_csv_folder = config.get('config', 'clean_csv_folder')
    except Exception as e:
        logging.error("Error reading config file: " + str(e))
        sys.exit(1)

    if not doing_comparison:
        logging.info("Comparison is disabled in the config file. Exiting.")
        sys.exit(0)

    overall_start_time = datetime.now()
    overall_start_ts = time.time()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_of_script = os.path.dirname(script_dir)
    compare_simulations_dir = os.path.join(parent_of_script, "plots//Compare_simulations")

    first_file_name = sim_output_folder_1.split('\\')[-1].split('.')[0]
    second_file_name = clean_csv_folder

    logging.info("=" * 60)
    logging.info("TRANSPORT MODE ANALYSIS - EXECUTION START (Corrected Version)")
    logging.info(f"Start Time: {overall_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

    try:
        results = analyze_transport_modes(
            sim_output_folder_1,
            sim_output_folder_2,
            detailed_expanded=False,
            nrows=comparison_num_rows,
            output_path=compare_simulations_dir,
            first_file_name=first_file_name,
            second_file_name=second_file_name
        )

        overall_end_time = datetime.now()
        total_secs = time.time() - overall_start_ts
        minutes, seconds = divmod(int(total_secs), 60)
        hours, minutes = divmod(minutes, 60)
        duration_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

        logging.info("=" * 60)
        logging.info("ANALYSIS COMPLETED SUCCESSFULLY (Corrected Version)")
        logging.info(f"End Time: {overall_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Total Processing Time: {duration_str} ({total_secs:.2f} seconds)")
        logging.info(f"Results: {len(results)} persons analyzed")
        logging.info("=" * 60)

    except FileNotFoundError as e:
        overall_end_time = datetime.now()
        logging.error(f"File not found: {e}")

    except Exception as e:
        overall_end_time = datetime.now()
        logging.error(f"An error occurred: {e}", exc_info=True)