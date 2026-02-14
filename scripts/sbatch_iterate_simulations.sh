#!/bin/bash
SCRIPTS_DIR="/home/comura/ThurgauPaperAnalysisAM/scripts"
SIMULATIONS_FILE="${SCRIPTS_DIR}/simulationsToBeAnalysed.txt"
SBATCH_SCRIPT="${SCRIPTS_DIR}/sbatch_run_analysis.sh"

mkdir -p "${SCRIPTS_DIR}/logs"

if [ ! -f "$SIMULATIONS_FILE" ]; then
    echo "Error: $SIMULATIONS_FILE not found!"
    exit 1
fi

echo "========================================"
echo "BATCH SUBMISSION - $(date)"
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
    SIM_NAME=$(basename "$line")

    echo "[$COUNT/$TOTAL] Submitting: $SIM_NAME"

    if [ -z "$PREV_JOB_ID" ]; then
        SUBMIT_OUTPUT=$(sbatch --export=SIM_OUTPUT_FOLDER="$line" --job-name="analysis_${SIM_NAME}" "$SBATCH_SCRIPT")
    else
        SUBMIT_OUTPUT=$(sbatch --dependency=afterany:${PREV_JOB_ID} --export=SIM_OUTPUT_FOLDER="$line" --job-name="analysis_${SIM_NAME}" "$SBATCH_SCRIPT")
    fi


    PREV_JOB_ID=$(echo "$SUBMIT_OUTPUT" | awk '{print $NF}')
    echo "  $SUBMIT_OUTPUT"
    echo ""

done < "$SIMULATIONS_FILE"

echo "========================================"
echo "All $COUNT job(s) submitted."
echo "Use 'squeue -u comura' to check job status."
echo "========================================"
