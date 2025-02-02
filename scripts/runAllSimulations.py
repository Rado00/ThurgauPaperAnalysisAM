import configparser
import subprocess
import os

directory = os.getcwd()
parent_directory = os.path.dirname(directory)
config_file = 'config.ini'
config_path = os.path.join(parent_directory, f'config/{config_file}')
# File path to the .bat file
bat_file = 'allScripts.bat'  # Replace with your .bat file's name or path
# Create a ConfigParser instance
config = configparser.ConfigParser()
# Read the existing config file
config.read(config_path)
simulations_list = list(range(63, 76)) #Mettere 1 in + a fine range
base_sims_path = r'Paper2_SimsOutputs\1_ModalSplitCalibration\BaselineCalibration'
for i in simulations_list:
    try:
        # Check if the section exists
        if 'config' in config:
            # Modify the port number
            config['config']['sim_output_folder'] = f'{base_sims_path}{i}'  # New port number
            # Save the changes back to the config file
            with open(config_path, 'w') as current_config:
                config.write(current_config)

            # Run the .bat file
            print(f"Running the .bat file for port {i}...")
            subprocess.run(bat_file, shell=True)
        else:
            print("Section 'config' not found in the config file.")
    except Exception as e:
        print(f"An error occurred: {e}")
