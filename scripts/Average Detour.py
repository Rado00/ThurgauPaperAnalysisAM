import csv

def calculate_average_time_detour(file_path):
    total = 0
    count = 0

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            try:
                time_detour = float(row['timeDetour'])
                total += time_detour
                count += 1
            except ValueError:
                # Handle the case where the conversion to float fails
                print(f"Invalid data encountered: {row['timeDetour']}")

    if count > 0:
        average = total / count
        return average
    else:
        return None

# Replace 'your_file.csv' with the path to your CSV file
file_path = 'C:/Users/muaa/OneDrive - ZHAW/2_DB/2023_Rado_ABM_sims_10pct/Sim_29/ITERS/it.60/60.drt_detours_drt.csv'
average_time_detour = calculate_average_time_detour(file_path)
if average_time_detour is not None:
    print(f"Average of timeDetour: {average_time_detour}")
else:
    print("No valid data to calculate the average")
