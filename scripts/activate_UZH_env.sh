#!/bin/bash

# Load Anaconda module
module load anaconda3/2024.02-1

# Set up conda shell support
eval "$(/apps/opt/spack/linux-ubuntu20.04-x86_64/gcc-9.3.0/anaconda3-2024.02-1-whphrx3ledrvyrcnibu7lezfvvqltgt5/bin/conda shell.bash hook)"
# eval "$(/apps/opt/spack/linux-ubuntu20.04-x86_64/gcc-9.3.0/anaconda3-2024.02-1/bin/conda shell.bash hook)"

# Activate your environment
conda activate ThurgauAnalysisEnv
