# Refactored: Mode Share Analysis Extended Comparison
import os
import logging
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from datetime import datetime
from functions.commonFunctions import *
from functools import reduce

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')

def load_population_data(file_path):
    df = pd.read_csv(file_path)
    df['sex'] = df['sex'].replace({0: 'Male', 1: 'Female', 'male': 'Male', 'female': 'Female'})
    if 'number_of_cars' in df.columns:
        df['number_of_cars'] = df['number_of_cars'].astype(str)
        df['number_of_cars'] = df['number_of_cars'].replace({'3': '3+', '4': '3+', '5': '3+'})
    return df

def plot_gender_distribution(df_mic, df_sim, plots_directory):
    mic_gender = df_mic[df_mic['sex'].isin(['Male', 'Female'])].groupby('sex')['household_weight'].sum().reset_index()
    mic_gender.columns = ['Gender', 'Count']

    if 'sex' in df_sim.columns:
        df_sim['sex'] = df_sim['sex'].replace({0: 'Male', 1: 'Female', 'male': 'Male', 'female': 'Female'})
        sim_gender = df_sim[df_sim['sex'].isin(['Male', 'Female'])]['sex'].value_counts().reset_index()
        sim_gender.columns = ['Gender', 'Count']
    else:
        sim_gender = pd.DataFrame({'Gender': ['Male', 'Female'], 'Count': [0, 0]})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
    ax1.pie(sim_gender['Count'], labels=sim_gender['Gender'], autopct='%1.1f%%', startangle=90)
    ax1.set_title('Gender Distribution Synthetic Population')
    ax2.pie(mic_gender['Count'], labels=mic_gender['Gender'], autopct='%1.1f%%', startangle=90)
    ax2.set_title('Gender Distribution - Microcensus')
    fig.suptitle("Comparative Gender Distribution With Household Weight")
    plt.tight_layout()
    fig.subplots_adjust(top=0.85)
    plt.savefig(f"{plots_directory}/gender_distribution.png", dpi=300)
    plt.close()

def plot_car_ownership(df_mic, df_households_sim, plots_directory):
    df_mic['car_availability'] = df_mic['car_availability'].astype(str)
    mic = df_mic.groupby('car_availability')['household_weight'].sum().reset_index()
    mic.columns = ['Number of Cars', 'Microcensus']
    mic_total = mic['Microcensus'].sum()
    mic['Microcensus'] = (mic['Microcensus'] / mic_total) * 100

    if 'numberOfCars' in df_households_sim.columns:
        sim = df_households_sim['numberOfCars'].astype(str).replace({'3': '3+', '4': '3+', '5': '3+'})
        sim = sim.value_counts(normalize=True).reset_index()
        sim.columns = ['Number of Cars', 'Simulation']
        sim['Simulation'] *= 100
    else:
        sim = pd.DataFrame(columns=['Number of Cars', 'Simulation'])

    merged = pd.merge(mic, sim, on='Number of Cars', how='outer').fillna(0)
    merged = merged.sort_values('Number of Cars')

    fig, ax = plt.subplots(figsize=(8, 6))
    x = range(len(merged['Number of Cars']))
    ax.bar([i - 0.2 for i in x], merged['Microcensus'], width=0.4, label='Microcensus - Car Ownership', color='blue')
    ax.bar([i + 0.2 for i in x], merged['Simulation'], width=0.4, label='Synthetic - Car Ownership', color='red')
    ax.set_xticks(x)
    ax.set_xticklabels(merged['Number of Cars'])
    ax.set_title('Comparison of Car Ownership Distribution - Percentage With Household Weight')
    ax.set_ylabel('Percentage (%)')

    for i, (m, s) in enumerate(zip(merged['Microcensus'], merged['Simulation'])):
        ax.text(i - 0.2, m + 0.5, f'{m:.1f}', ha='center', color='white', fontsize=8)
        ax.text(i + 0.2, s + 0.5, f'{s:.1f}', ha='center', color='white', fontsize=8)

    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{plots_directory}/car_ownership_distribution.png", dpi=300)
    plt.close()

def plot_license_availability(df_mic, df_sim, plots_directory):
    mic = df_mic[(df_mic['car_availability'] == False) & (df_mic['driving_license'] >= 1)]
    sim = df_sim[(df_sim['carAvail'].str.lower() != 'never') & (df_sim['hasLicense'].str.lower() == 'yes')]

    mic_count = len(mic)
    sim_count = len(sim)

    fig, ax = plt.subplots()
    ax.bar(['Microcensus', 'Simulation'], [mic_count, sim_count], color=['blue', 'orange'])
    ax.set_title('License Holders With Car Access')
    ax.set_ylabel('Count')
    plt.tight_layout()
    plt.savefig(f"{plots_directory}/car_license_availability.png", dpi=300)
    plt.close()

def plot_income_distribution(df_mic, df_sim, plots_directory):
    income_class_labels = {
        0: 'Under CHF 2000', 1: 'CHF 2000–4000', 2: 'CHF 4001–6000', 3: 'CHF 6001–8000',
        4: 'CHF 8001–10000', 5: 'CHF 10001–12000', 6: 'CHF 12001–14000',
        7: 'CHF 14001–16000', 8: 'More than CHF 16000'
    }
    df_mic = df_mic[df_mic['income_class'].isin(income_class_labels.keys())]
    mic = df_mic.groupby('income_class')['household_weight'].sum().reset_index()
    mic['Income Class'] = mic['income_class'].map(income_class_labels)
    mic = mic[['Income Class', 'household_weight']].rename(columns={'household_weight': 'Microcensus'})

    if 'income_class' in df_sim.columns:
        sim = df_sim['income_class'].value_counts().reset_index()
        sim.columns = ['income_class', 'Simulation']
        sim['Income Class'] = sim['income_class'].map(income_class_labels)
        sim = sim[['Income Class', 'Simulation']]
    else:
        sim = pd.DataFrame(columns=['Income Class', 'Simulation'])

    merged = pd.merge(mic, sim, on='Income Class', how='outer').fillna(0)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(merged['Income Class']))
    ax.bar([i - 0.2 for i in x], merged['Microcensus'], width=0.4, label='Microcensus', alpha=0.7)
    ax.bar([i + 0.2 for i in x], merged['Simulation'], width=0.4, label='Simulation', alpha=0.7)
    ax.set_title('Income Class Distribution')
    ax.set_ylabel('Count')
    ax.set_xticks(x)
    ax.set_xticklabels(merged['Income Class'], rotation=45, ha='right')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{plots_directory}/income_distribution.png", dpi=300)
    plt.close()

def main():
    setup_logging(get_log_filename())
    logging.info("Starting main execution...")
    config = read_config()
    (data_path, simulation_zone_name, scenario, sim_output_folder, percentile, analysis_zone_name,
     csv_folder, clean_csv_folder, shapeFileName, read_SynPop, read_microcensus, sample_for_debugging) = config

    data_path_clean = os.path.join(data_path, analysis_zone_name, clean_csv_folder, percentile)
    plots_directory = os.path.join(os.path.dirname(os.getcwd()), "plots",
                                   f"plots_{os.path.basename(sim_output_folder)}")
    os.makedirs(plots_directory, exist_ok=True)

    df_population_mic = load_population_data(os.path.join(data_path, analysis_zone_name,clean_csv_folder,percentile, "population_at_least_one_activity_inside_mic.csv"))
    df_population_sim = load_population_data(os.path.join(data_path_clean, "population_all_activities_inside_sim.csv"))
    df_households_sim = pd.read_csv(os.path.join(data_path_clean, "households_sim.csv"))

    plot_gender_distribution(df_population_mic, df_population_sim, plots_directory)
    plot_car_ownership(df_population_mic, df_households_sim, plots_directory)
    plot_license_availability(df_population_mic, df_population_sim, plots_directory)
    plot_income_distribution(df_population_mic, df_population_sim, plots_directory)

if __name__ == '__main__':
    main()