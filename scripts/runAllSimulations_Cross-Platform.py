import configparser
import subprocess
import os
import platform

# Detect OS
is_windows = platform.system() == 'Windows'

# Directories and config
directory = os.getcwd()
parent_directory = os.path.dirname(directory)
config_file = 'config.ini'
config_path = os.path.join(parent_directory, 'config', config_file)

# Script to run
script_to_run = 'allScripts.bat' if is_windows else './run_all_scripts.sh'

# Simulation parameters
simulations_list = list(range(17, 25))  # Adjust range as needed
base_sims_path = os.path.join('Paper2_SimsOutputs', '2_Fleet', 'Aaa_')

# Load the config
config = configparser.ConfigParser()
config.read(config_path)

for i in simulations_list:
    try:
        if 'config' in config:
            # Update the sim_output_folder path
            sim_path = f'{base_sims_path}{i}'  # This becomes a string like '.../BaselineCalibration_NV_17'
            config['config']['sim_output_folder'] = sim_path

            # Save the modified config
            with open(config_path, 'w') as current_config:
                config.write(current_config)

            # Run the appropriate script
            print(f"\n🔁 Running simulation for: {sim_path}")
            if is_windows:
                subprocess.run([script_to_run], shell=True, check=True)
            else:
                subprocess.run(['bash', script_to_run], check=True)

        else:
            print("❌ Section 'config' not found in the config file.")

    except Exception as e:
        print(f"❌ Error in simulation {i}: {e}")
