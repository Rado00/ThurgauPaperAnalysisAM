#!/bin/bash
set -e

echo "Starting the Python analysis pipeline..."

# Detect user and OS
USER_NAME=$(whoami)
OS_TYPE=$(uname)

# Set up conda and paths
if [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "gsangiovanni" ]]; then
    echo "Running on Terastat cluster as gsangiovanni"
    
    # Load Anaconda module
    module load anaconda/2022.10
    
    # Initialize conda for this script
    source /lustre/software/anaconda/2022.10_all/etc/profile.d/conda.sh
    
    # Activate environment
    conda activate ThurgauAnalysisEnv
    
    # Set scripts path
    SCRIPTS_PATH="/lustre/home/gsangiovanni/Rado/ThurgauPaperAnalysisAM/scripts"
    
elif [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "muaa" ]]; then
    echo "Running on ZHAW or local Linux as muaa"
    source /home/muaa/miniconda3/etc/profile.d/conda.sh
    conda activate ThurgauAnalysisEnv
    SCRIPTS_PATH="/home/muaa/ThurgauPaperAnalysisAM/scripts"

elif [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "comura" ]]; then
    echo "Running on UZH Linux as comura"
    eval "$(~/miniconda3/bin/conda shell.bash hook)"
    conda activate ThurgauAnalysisEnv
    SCRIPTS_PATH="/home/comura/ThurgauPaperAnalysisAM/scripts"

elif [[ "$OS_TYPE" == "MINGW"* || "$OS_TYPE" == "CYGWIN"* || "$OS_TYPE" == "MSYS"* ]] && [[ "$USER_NAME" == "muaa" ]]; then
    echo "Running on Windows as muaa"
    SCRIPTS_PATH="C:/Users/${USER_NAME}/Documents/3_MIEI/ThurgauPaperAnalysisAM/scripts"
    # Windows: Activate manually if needed or ensure conda is in PATH
    conda activate ThurgauAnalysisEnv
elif [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "sarf" ]]; then
    echo "Running on Linux as sarf"
    source /home/sarf/projects/corrado_paper/ThurgauAnalysisEnv/bin/activate
    SCRIPTS_PATH="/home/sarf/projects/corrado_paper/ThurgauPaperAnalysisAM/scripts"

else
    echo "Unsupported system configuration"
    exit 1
fi

cd "$SCRIPTS_PATH"

# Run each script
# echo "Running 01_microcensus_pre-process.py..."
# python 01_microcensus_pre-process.py

# echo "Running 02_microcensus_trips_filter.py..."
# python 02_microcensus_trips_filter.py

# echo "Running 03_synPop_and_sim_create_csv_files.py..."
# python 03_synPop_and_sim_create_csv_files.py

# Note: Scripts 04 and 05_1 have been merged into a single script for better performance
# (avoids writing/reading intermediate CSV files)
# echo "Running 04_05_synPop_sim_trips_and_clean.py..."
# python 04_05_synPop_sim_trips_and_clean.py

# echo "Running 05_2_compare_outputs.py..."
# python 05_2_compare_outputs.py

# echo "Running 06_synt_mode_share_by_time_distance.py..."
# python 06_synt_mode_share_by_time_distance.py

echo "Running 07_plot_mode_share.py..."
python 07_plot_mode_share.py

echo "Running 08_plot_mode_share_target_area.py..."
python 08_plot_mode_share_target_area.py

# Optional scripts (uncomment to enable)
# echo "Running 09_plot_smaller_zones_modal_split.py..."
# python 09_plot_smaller_zones_modal_split.py

echo "Running 10_plot_the_clean_csv_files.py..."
python 10_plot_the_clean_csv_files.py

echo "Running 11_DRT_Order_Ouputs.py..."
python 11_DRT_Order_Ouputs.py

echo "Running 12_CSVs_in_a_column.py..."
python 12_CSVs_in_a_column.py

echo "Running 13_transform_output_format.py"
python 13_transform_output_format.py

echo "All scripts executed successfully!"