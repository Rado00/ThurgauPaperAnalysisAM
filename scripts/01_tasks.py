"""
This is the main script to do the tasks.

Author: Corrado Muratori
Date: 2024-05-28
"""

# Import necessary libraries
import warnings
from common import *
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option('display.width', 1000)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
warnings.filterwarnings("ignore")


if __name__ == '__main__':
    setup_logging("01_tasks.log")

    data_path, zone_name, scenario, csv_folder, output_folder, percentile, clean_csv_folder = read_config()
    cvs_path = os.path.join(data_path, zone_name, csv_folder, percentile)

    directory = os.getcwd()
    parent_directory = os.path.dirname(directory)
    plots_directory = os.path.join(parent_directory, 'plots')

    # Read persons data
    persons_sim = pd.read_csv(os.path.join(cvs_path, 'df_persons_sim.csv'))
    person_synthetic = pd.read_csv(os.path.join(cvs_path, 'df_persons_synt.csv'))

    # Print the first 5 rows of the data
    print(persons_sim.head())
    print(person_synthetic.head())

    # Print the shape of the data
    print(persons_sim.shape)
    print(person_synthetic.shape)

    # Plot the sum of null
    # Counting null values in each DataFrame
    null_values_df1 = persons_sim.isnull().sum()
    null_values_df2 = person_synthetic.isnull().sum()

    # Plotting null values for DataFrame 1
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    null_values_df1.plot(kind='bar', color='blue', alpha=0.7)
    plt.title('Null Values in DataFrame 1')
    plt.xlabel('Columns')
    plt.ylabel('Count')

    # Plotting null values for DataFrame 2
    plt.subplot(1, 2, 2)
    null_values_df2.plot(kind='bar', color='red', alpha=0.7)
    plt.title('Null Values in DataFrame 2')
    plt.xlabel('Columns')
    plt.ylabel('Count')

    plt.tight_layout()
    plt.savefig(os.path.join(plots_directory, 'null_values.png'))
    # plt.show()

    # Task 1: Plot age distribution of synthetic and simulated persons
    # Plotting the age distribution
    plt.figure(figsize=(10, 6))
    plt.hist(persons_sim['age'], bins=10, alpha=0.5, label='DataFrame 1')
    plt.hist(person_synthetic['age'], bins=10, alpha=0.5, label='DataFrame 2')

    plt.xlabel('Age')
    plt.ylabel('Frequency')
    plt.title('Age Distribution')
    plt.legend(loc='upper right')
    plt.savefig(os.path.join(plots_directory, 'age_distribution.png'))
    # plt.show()


