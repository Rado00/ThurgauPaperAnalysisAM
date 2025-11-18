import configparser
import subprocess
import os

parent_folder = os.path.dirname(os.getcwd())
config_path = os.path.join(parent_folder, 'config', 'config.ini')

# Path to the bash script to run
script_to_run = "run_all_scripts.sh"

# Generate shapefile names from 01 to 25
for i in range(1, 26):
    # Create shapefile name with zero-padding
    shapefile_name = f"{i:02d}_ShapeFile.shp"
    
    print(f"\n{'='*50}")
    print(f"Processing: {shapefile_name}")
    print(f"{'='*50}")
    
    # Read the config.ini file
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Update the target_area value
    config['config']['target_area'] = shapefile_name
    
    # Write the updated config back to the file
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"Updated config.ini with target_area = {shapefile_name}")
    
    # Run the bash script
    try:
        print(f"Running script: {script_to_run}")
        result = subprocess.run(
            ['bash', script_to_run],  # Changed from 'python' to 'bash'
            capture_output=True,
            text=True,
            check=True
        )
        print("Script executed successfully!")
        if result.stdout:
            print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running script for {shapefile_name}")
        print(f"Error message: {e.stderr}")
        # You can choose to continue or break here
        # break  # Uncomment to stop on first error
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

print(f"\n{'='*50}")
print("All iterations completed!")
print(f"{'='*50}")