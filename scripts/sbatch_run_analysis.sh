#!/bin/bash
#SBATCH --job-name=thurgau_analysis
#SBATCH --output=logs/analysis_%j.out
#SBATCH --error=logs/analysis_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4

# ------------------------------------------------------------------
# Per-job analysis script.
# Runs the full analysis pipeline (run_all_scripts.sh) exactly ONCE
# for the simulation and target area passed via environment variables:
#   SIM_OUTPUT_FOLDER : sim_output_folder to write into config.ini
#   TARGET_AREA       : target_area (shapefile) to write into config.ini
#                       (optional - only updated if non-empty)
#
# This script is invoked by sbatch_iterate_simulations.sh either via
# sbatch (on SLURM clusters) or directly via bash (non-SLURM, e.g. root).
# ------------------------------------------------------------------

USER_NAME=$(whoami)

if [[ "$USER_NAME" == "comura" ]]; then
    SCRIPTS_DIR="/home/comura/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/home/comura/ThurgauPaperAnalysisAM/config"
elif [[ "$USER_NAME" == "muaa" ]]; then
    SCRIPTS_DIR="/home/muaa/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/home/muaa/ThurgauPaperAnalysisAM/config"
elif [[ "$USER_NAME" == "gsangiovanni" ]]; then
    SCRIPTS_DIR="/lustre/home/gsangiovanni/Rado/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/lustre/home/gsangiovanni/Rado/ThurgauPaperAnalysisAM/config"
elif [[ "$USER_NAME" == "root" ]]; then
    SCRIPTS_DIR="/project/corrado_paper/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/project/corrado_paper/ThurgauPaperAnalysisAM/config"
else
    echo "Unsupported user: $USER_NAME"
    exit 1
fi

CONFIG_FILE="${CONFIG_DIR}/config.ini"
mkdir -p "${SCRIPTS_DIR}/logs"

# Allow first positional arg as fallback for SIM_OUTPUT_FOLDER
SIM_OUTPUT_FOLDER="${SIM_OUTPUT_FOLDER:-$1}"
# Allow second positional arg as fallback for TARGET_AREA
TARGET_AREA="${TARGET_AREA:-$2}"

echo "========================================"
echo "Job started at $(date)"
echo "Running on node: $(hostname)"
echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "User: $USER_NAME"
echo "SIM_OUTPUT_FOLDER: $SIM_OUTPUT_FOLDER"
echo "TARGET_AREA: $TARGET_AREA"
echo "========================================"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found!"
    exit 1
fi

if [ -n "$SIM_OUTPUT_FOLDER" ]; then
    echo "Updating sim_output_folder in config.ini to: $SIM_OUTPUT_FOLDER"
    sed -i "s|^sim_output_folder = .*|sim_output_folder = ${SIM_OUTPUT_FOLDER}|" "$CONFIG_FILE"
fi

if [ -n "$TARGET_AREA" ]; then
    echo "Updating target_area in config.ini to: $TARGET_AREA"
    sed -i "s|^target_area\s*=.*|target_area = ${TARGET_AREA}|" "$CONFIG_FILE"
fi

echo "Current config values:"
grep -E "^(sim_output_folder|target_area)\s*=" "$CONFIG_FILE"
echo ""

cd "$SCRIPTS_DIR"
bash run_all_scripts.sh

echo "Job finished at $(date)"
