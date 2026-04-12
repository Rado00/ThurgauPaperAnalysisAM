#!/bin/bash
# ------------------------------------------------------------------
# Iterator script: reads simulationsToBeAnalysed.txt line by line
# and submits ONE analysis job per line.
#
# Each line has the format:
#   <sim_output_folder>[, <shapefile_name>]
#
# For SLURM users the per-simulation job is submitted via sbatch to
# scripts/sbatch_run_analysis.sh, with SIM_OUTPUT_FOLDER and TARGET_AREA
# exported to the job environment. Jobs are chained with
# --dependency=afterany so they run sequentially and each one rewrites
# config.ini at its own start time (avoiding race conditions on the
# shared config).
#
# For root (non-SLURM) the per-simulation job is invoked directly via
# bash, again with SIM_OUTPUT_FOLDER and TARGET_AREA exported.
# ------------------------------------------------------------------

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
if [ ! -f "$SBATCH_SCRIPT" ]; then
    echo "Error: $SBATCH_SCRIPT not found!"
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

    # Parse: check if line contains a comma (shapefile specified)
    if [[ "$line" == *","* ]]; then
        SIM_FOLDER=$(echo "$line" | cut -d',' -f1 | xargs)
        SHAPEFILE=$(echo "$line" | cut -d',' -f2 | xargs)
    else
        SIM_FOLDER="$line"
        SHAPEFILE=""
    fi
    SIM_NAME=$(basename "$SIM_FOLDER")

    echo "[$COUNT/$TOTAL] Submitting: $SIM_NAME"
    echo "  sim_output_folder: $SIM_FOLDER"
    if [ -n "$SHAPEFILE" ]; then
        echo "  target_area:       $SHAPEFILE"
    fi

    if [ "$USE_SLURM" = true ]; then
        # Build --export list. Include TARGET_AREA only if a shapefile was
        # specified so we don't overwrite the existing value with empty.
        if [ -n "$SHAPEFILE" ]; then
            EXPORT_VARS="SIM_OUTPUT_FOLDER=${SIM_FOLDER},TARGET_AREA=${SHAPEFILE}"
        else
            EXPORT_VARS="SIM_OUTPUT_FOLDER=${SIM_FOLDER}"
        fi

        if [ -z "$PREV_JOB_ID" ]; then
            SUBMIT_OUTPUT=$(sbatch \
                --partition="$PARTITION" \
                --export="$EXPORT_VARS" \
                --job-name="analysis_${SIM_NAME}" \
                "$SBATCH_SCRIPT")
        else
            SUBMIT_OUTPUT=$(sbatch \
                --partition="$PARTITION" \
                --dependency=afterany:${PREV_JOB_ID} \
                --export="$EXPORT_VARS" \
                --job-name="analysis_${SIM_NAME}" \
                "$SBATCH_SCRIPT")
        fi
        PREV_JOB_ID=$(echo "$SUBMIT_OUTPUT" | awk '{print $NF}')
        echo "  $SUBMIT_OUTPUT"
    else
        # Non-SLURM: run the per-job script serially in the foreground.
        LOG_FILE="${SCRIPTS_DIR}/logs/analysis_${SIM_NAME}_${COUNT}_$(date +%Y%m%d_%H%M%S).log"
        echo "  Log file: $LOG_FILE"
        SIM_OUTPUT_FOLDER="$SIM_FOLDER" TARGET_AREA="$SHAPEFILE" \
            bash "$SBATCH_SCRIPT" > "$LOG_FILE" 2>&1
        echo "  Finished with exit code: $?"
    fi
    echo ""
done < "$SIMULATIONS_FILE"

echo "========================================"
echo "All $COUNT job(s) submitted."
if [ "$USE_SLURM" = true ]; then
    echo "Use 'squeue -u $USER_NAME' to check job status."
fi
echo "========================================"
