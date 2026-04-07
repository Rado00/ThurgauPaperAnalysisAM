#!/bin/bash
USER_NAME=$(whoami)
if [[ "$USER_NAME" == "comura" ]]; then
    SCRIPTS_DIR="/home/comura/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/home/comura/ThurgauPaperAnalysisAM/config"
    PARTITION="standard"
    USE_SLURM=true
elif [[ "$USER_NAME" == "muaa" ]]; then
    SCRIPTS_DIR="/home/muaa/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/home/muaa/ThurgauPaperAnalysisAM/config"
    PARTITION="gpu"
    USE_SLURM=true
elif [[ "$USER_NAME" == "gsangiovanni" ]]; then
    SCRIPTS_DIR="/lustre/home/gsangiovanni/Rado/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/lustre/home/gsangiovanni/Rado/ThurgauPaperAnalysisAM/config"
    PARTITION="standard"
    USE_SLURM=true
elif [[ "$USER_NAME" == "root" ]]; then
    SCRIPTS_DIR="/project/corrado_paper/ThurgauPaperAnalysisAM/scripts"
    CONFIG_DIR="/project/corrado_paper/ThurgauPaperAnalysisAM/config"
    PARTITION="standard"
    USE_SLURM=false
else
    echo "Unsupported user: $USER_NAME"
    exit 1
fi
SIMULATIONS_FILE="${SCRIPTS_DIR}/simulationsToBeAnalysed.txt"
SBATCH_SCRIPT="${SCRIPTS_DIR}/sbatch_run_analysis.sh"
CONFIG_FILE="${CONFIG_DIR}/config.ini"
mkdir -p "${SCRIPTS_DIR}/logs"
if [ ! -f "$SIMULATIONS_FILE" ]; then
    echo "Error: $SIMULATIONS_FILE not found!"
    exit 1
fi
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found!"
    exit 1
fi
echo "========================================"
echo "BATCH SUBMISSION - $(date)"
echo "User: $USER_NAME"
echo "SLURM: $USE_SLURM"
echo "========================================"
COUNT=0
TOTAL=$(grep -cv '^\s*$\|^\s*#' "$SIMULATIONS_FILE")
PREV_JOB_ID=""
echo "Found $TOTAL simulation(s) to submit"
echo ""
while IFS= read -r line || [ -n "$line" ]; do
    line=$(echo "$line" | xargs)
    if [ -z "$line" ] || [[ "$line" == \#* ]]; then
        continue
    fi
    COUNT=$((COUNT + 1))
    if [[ "$line" == *","* ]]; then
        SIM_FOLDER=$(echo "$line" | cut -d',' -f1 | xargs)
        SHAPEFILE=$(echo "$line" | cut -d',' -f2 | xargs)
    else
        SIM_FOLDER="$line"
        SHAPEFILE=""
    fi
    SIM_NAME=$(basename "$SIM_FOLDER")
    if [ -n "$SHAPEFILE" ]; then
        echo "  Updating target_area in config.ini to: $SHAPEFILE"
        sed -i "s/^target_area\s*=.*/target_area = ${SHAPEFILE}/" "$CONFIG_FILE"
    fi
    echo "  Updating sim_output_folder in config.ini to: $SIM_FOLDER"
    sed -i "s|^sim_output_folder = .*|sim_output_folder = ${SIM_FOLDER}|" "$CONFIG_FILE"
    echo "[$COUNT/$TOTAL] Running: $SIM_NAME"
    if [ "$USE_SLURM" = true ]; then
        if [ -z "$PREV_JOB_ID" ]; then
            SUBMIT_OUTPUT=$(sbatch --export=SIM_OUTPUT_FOLDER="$SIM_FOLDER" --job-name="analysis_${SIM_NAME}" "$SBATCH_SCRIPT")
        else
            SUBMIT_OUTPUT=$(sbatch --dependency=afterany:${PREV_JOB_ID} --export=SIM_OUTPUT_FOLDER="$SIM_FOLDER" --job-name="analysis_${SIM_NAME}" "$SBATCH_SCRIPT")
        fi
        PREV_JOB_ID=$(echo "$SUBMIT_OUTPUT" | awk '{print $NF}')
        echo "  $SUBMIT_OUTPUT"
    else
        LOG_FILE="${SCRIPTS_DIR}/logs/analysis_${SIM_NAME}_${COUNT}_$(date +%Y%m%d_%H%M%S).log"
        echo "  Log file: $LOG_FILE"
        cd "$SCRIPTS_DIR"
        bash run_all_scripts.sh > "$LOG_FILE" 2>&1
        echo "  Finished with exit code: $?"
    fi
    echo ""
done < "$SIMULATIONS_FILE"
echo "========================================"
echo "All $COUNT job(s) completed."
if [ "$USE_SLURM" = true ]; then
    echo "Use 'squeue -u $USER_NAME' to check job status."
fi
echo "========================================"
