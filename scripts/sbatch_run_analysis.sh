#!/bin/bash
#SBATCH --job-name=thurgau_analysis
#SBATCH --output=logs/analysis_%j.out
#SBATCH --error=logs/analysis_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --partition=standard

SCRIPTS_DIR="/home/comura/ThurgauPaperAnalysisAM/scripts"
CONFIG_FILE="/home/comura/ThurgauPaperAnalysisAM/config/config.ini"
# SIM_OUTPUT_FOLDER is passed via --export from sbatch_iterate_simulations.sh
# If not set, use $1 as fallback for manual runs
SIM_OUTPUT_FOLDER="${SIM_OUTPUT_FOLDER:-$1}"

mkdir -p "${SCRIPTS_DIR}/logs"

echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

if [ -n "$SIM_OUTPUT_FOLDER" ]; then
    echo "Updating config.ini with sim_output_folder = $SIM_OUTPUT_FOLDER"
    sed -i "s|^sim_output_folder = .*|sim_output_folder = ${SIM_OUTPUT_FOLDER}|" "$CONFIG_FILE"
fi

echo "Current sim_output_folder in config:"
grep "sim_output_folder" "$CONFIG_FILE"
echo ""

cd "$SCRIPTS_DIR"
bash run_all_scripts.sh

echo "Job finished at $(date)"
