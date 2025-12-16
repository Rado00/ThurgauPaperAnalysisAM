@echo off
echo Starting the Python analysis pipeline...

REM Activate the Python environment
call "C:\Users\corra\Documents\1_GitHub\PythonEnvironments\ThurgauAnalysisEnv\Scripts\activate.bat"

REM Navigate to the directory containing your scripts
cd "C:\Users\corra\Documents\1_GitHub\ThurgauPaperAnalysisAM\scripts"

REM Run each script in sequence

echo Running 01_microcensus_pre-process.py...
python 01_microcensus_pre-process.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 02_microcensus_trips_filter.py...
python 02_microcensus_trips_filter.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 03_synPop_and_sim_create_csv_files.py...
python 03_synPop_and_sim_create_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

REM Note: Scripts 04 and 05_1 have been merged into a single script for better performance
REM (avoids writing/reading intermediate CSV files)
echo Running 04_05_synPop_sim_trips_and_clean.py...
python 04_05_synPop_sim_trips_and_clean.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 05_2_compare_outputs.py...
python 05_2_compare_outputs.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 06_synt_mode_share_by_time_distance.py...
python 06_synt_mode_share_by_time_distance.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 07_plot_mode_share.py...
python 07_plot_mode_share.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 08_plot_mode_share_target_area.py...
python 08_plot_mode_share_target_area.py
if %ERRORLEVEL% neq 0 goto :error

REM echo Running 09_plot_smaller_zones_modal_split.py...
REM python 09_plot_smaller_zones_modal_split.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 10_plot_the_clean_csv_files.py...
python 10_plot_the_clean_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 11_DRT_Order_Ouputs.py...
python 11_DRT_Order_Ouputs.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 12_CSVs_in_a_column.py...
python 12_CSVs_in_a_column.py
if %ERRORLEVEL% neq 0 goto :error

echo 13_transform_output_format.py...
python 13_transform_output_format.py
if %ERRORLEVEL% neq 0 goto :error



echo All scripts executed successfully!
exit /b 0

:error
echo A script failed with error level %ERRORLEVEL%. Exiting.
exit /b %ERRORLEVEL%