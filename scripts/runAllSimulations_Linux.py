import configparser
import subprocess
import os

# Get current and parent directory
directory = os.getcwd()
parent_directory = os.path.dirname(directory)

# Define config path and simulation parameters
config_file = 'config.ini'
config_path = os.path.join(parent_directory, 'config', config_file)
shell_script = './run_all_scripts.sh'  # Your new .sh file
simulations_list = list(range(17, 25))  # Include 1 more than last value
base_sims_path = 'Paper2_SimsOutputs/1_ModalSplitCalibration/BaselineCalibration_NV_'

# Load the config file
config = configparser.ConfigParser()
config.read(config_path)

for i in simulations_list:
    try:
        if 'config' in config:
            # Update config parameter
            config['config']['sim_output_folder'] = f'{base_sims_path}{i}'

            # Write back to config file
            with open(config_path, 'w') as current_config:
                config.write(current_config)

            # Run the shell script
            print(f"\n🔁 Running simulation for folder {base_sims_path}{i}...")
            subprocess.run(['bash', shell_script], check=True)

        else:
            print("❌ Section 'config' not found in the config file.")

    except Exception as e:
        print(f"❌ Error during simulation {i}: {e}")
