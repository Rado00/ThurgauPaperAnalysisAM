#!/bin/bash
set -e

echo "Starting the Python analysis pipeline..."

# Detect user and OS
USER_NAME=$(whoami)
OS_TYPE=$(uname)

# -------------------------------
# ENVIRONMENT SETUP
# -------------------------------
if [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "gsangiovanni" ]]; then
    echo "Running on Terastat cluster as gsangiovanni"
    
    module load anaconda/2022.10
    source /lustre/software/anaconda/2022.10_all/etc/profile.d/conda.sh
    conda activate ThurgauAnalysisEnv
    
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
    conda activate ThurgauAnalysisEnv

elif [[ "$OS_TYPE" == "Linux" && "$USER_NAME" == "root" ]]; then
    echo "Running on Linux as root"
    
    source /root/local/python/lib/python3.11/venv/scripts/common/activate
    SCRIPTS_PATH="/project/corrado_paper/ThurgauPaperAnalysisAM/scripts/"

else
    echo "Unsupported system configuration"
    exit 1
fi

# -------------------------------
# FILE PATHS
# -------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TXT_FILE="$SCRIPT_DIR/run_analysis_all_zones.txt"
CONFIG_FILE="/project/corrado_paper/ThurgauPaperAnalysisAM/config/config.ini"

# -------------------------------
# CHECK INPUT FILE
# -------------------------------
if [[ ! -f "$TXT_FILE" ]]; then
    echo "? Error: run_analysis_all_zones.txt does not exist"
    exit 1
fi

echo "Reading input file: $TXT_FILE"

# -------------------------------
# MAIN LOOP
# -------------------------------
while IFS=',' read -r clean_csv_folder target_area; do

    # Skip empty lines
    [[ -z "$clean_csv_folder" ]] && continue

    # Trim whitespace
    clean_csv_folder=$(echo "$clean_csv_folder" | xargs)
    target_area=$(echo "$target_area" | xargs)

    echo "----------------------------------------"
    echo "Processing:"
    echo "clean_csv_folder = $clean_csv_folder"
    echo "target_area      = $target_area"

    # -------------------------------
    # UPDATE CONFIG.INI
    # -------------------------------
    sed -i "s|^clean_csv_folder = .*|clean_csv_folder = $clean_csv_folder|" "$CONFIG_FILE"
    sed -i "s|^target_area = .*|target_area = $target_area|" "$CONFIG_FILE"

    # -------------------------------
    # RUN PYTHON SCRIPTS
    # -------------------------------
    cd "$SCRIPTS_PATH" || exit 1

    echo "Running 07_plot_mode_share.py..."
    python3 07_plot_mode_share.py

    echo "Running 08_plot_mode_share_target_area.py..."
    python3 08_plot_mode_share_target_area.py

    echo "Running 11_DRT_Order_Ouputs.py..."
    python3 11_DRT_Order_Ouputs.py

    echo "Running 12_CSVs_in_a_column.py..."
    python3 12_CSVs_in_a_column.py

    echo "Running 13_transform_output_format.py..."
    python3 13_transform_output_format.py

    echo "? Finished iteration for:"
    echo "   $clean_csv_folder / $target_area"

done < "$TXT_FILE"

echo "?? All scripts executed successfully!"