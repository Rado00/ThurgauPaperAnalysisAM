@echo off
echo Starting the Python analysis pipeline...

REM Activate the Python environment
call "C:\Users\muaa\Documents\3_MIEI\PythonEnvironments\ThurgauAnalysisEnv\Scripts\activate.bat"

REM Navigate to the directory containing your scripts
cd "C:\Users\muaa\Documents\3_MIEI\ThurgauPaperAnalysisAM\scripts"

REM Run each script in sequence


REM echo Running 01_microcensus_population_filter.py...
REM python 01_microcensus_pre-process.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 02_microcensus_trips_filter.py...
python 02_microcensus_trips_filter.py
if %ERRORLEVEL% neq 0 goto :error

REM echo Running 03_synPop_and_sim_create_csv_files.py...
REM python 03_synPop_and_sim_create_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 03_synPop_sim_trips.py...
python 03_synPop_sim_trips.py
if %ERRORLEVEL% neq 0 goto :error

REM echo Running 04_generate_clean_csv_files.py...
REM python 04_generate_clean_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 05_synt_and_sim_mode_share_by_time_distance.py...
REM python 05_synt_and_sim_mode_share_by_time_distance.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 06_plot_mode_share_time_distance_synt.py...
python 06_plot_mode_share_time_distance_synt.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 06_plot_mode_share_time_distance_synt.py...
python 06_plot_mode_share_time_distance_synt.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 07_plot_smaller_zones_modal_split.py...
python 07_plot_smaller_zones_modal_split.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 08_plot_the_clean_csv_files.py...
python 08_plot_the_clean_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 09_CSVs_in_a_column.py...
python 09_CSVs_in_a_column.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 10_DRT_Data_Analysis.py...
python 10_DRT_Data_Analysis.py
if %ERRORLEVEL% neq 0 goto :error

echo All scripts executed successfully!
exit /b 0

:error
echo A script failed with error level %ERRORLEVEL%. Exiting.
exit /b %ERRORLEVEL%

04_2_synPop_sim_analysis.py