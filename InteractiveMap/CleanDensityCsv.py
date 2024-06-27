import pandas as pd
import os

# Define the path to the CSV file
syntheticPersonsPath = "C:/Users/muaa/Documents/3_MIEI/2023_ABMT_Data/Thurgau/Thurgau_Baseline_100pct_1/output_persons.csv"

# Load the CSV file into a DataFrame with the correct delimiter
df = pd.read_csv(syntheticPersonsPath, delimiter=';')

# List of columns to keep (make sure these names match the actual column names)
columns_to_keep = [
    'person', 'ptHasHalbtax', 'ptHasGA', 'statpopPersonId',
    'statpopHouseholdId', 'age', 'home_x', 'home_y', 'isFreight',
    'carAvail', 'hasLicense'
]

# Filter the DataFrame to keep only the specified columns if they exist
existing_columns_to_keep = [col for col in columns_to_keep if col in df.columns]
df_filtered = df[existing_columns_to_keep]

# Filter out rows where isFreight is True or home_x is NaN
df_filtered = df_filtered[(df_filtered['isFreight'] == False) & (df_filtered['home_x'].notna())]

# Create the new column 'hasCarAndLicense'
df_filtered['hasCarAndLicense'] = (df_filtered['carAvail'].isin(['always', 'sometimes'])) & (df_filtered['hasLicense'] == True)

# Display the DataFrame
print("Filtered DataFrame:")
print(df_filtered.head())

# Optionally, save the filtered DataFrame to a new CSV file
filtered_csv_path = "filtered_output_persons.csv"
df_filtered.to_csv(filtered_csv_path, index=False)
print(f"Filtered data saved to {filtered_csv_path}")
