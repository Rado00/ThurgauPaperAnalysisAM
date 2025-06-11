@echo off
echo Starting the Python analysis pipeline...

REM Activate the Python environment
call "C:\Users\corra\Documents\1_GitHub\PythonEnvironments\ThurgauAnalysisEnv\Scripts\activate.bat"

REM Navigate to the directory containing your scripts
cd "C:\Users\corra\Documents\1_GitHub\ThurgauPaperAnalysisAM\scripts"

REM Run each script in sequence


REM echo Running 01_microcensus_population_filter.py...
REM python 01_microcensus_pre-process.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 02_microcensus_trips_filter.py...
REM python 02_microcensus_trips_filter.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 03_synPop_and_sim_create_csv_files.py...
REM python 03_synPop_and_sim_create_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 04_synPop_sim_trips.py...
REM python 04_synPop_sim_trips.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 05_generate_clean_csv_files.py...
REM python 05_generate_clean_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 06_synt_mode_share_by_time_distance.py...
REM python 06_synt_mode_share_by_time_distance.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 07_plot_mode_share.py...
REM python 07_plot_mode_share.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 08_plot_mode_share_target_area.py...
REM python 08_plot_mode_share_target_area.py
REM if %ERRORLEVEL% neq 0 goto :error

REM REM echo Running 09_plot_smaller_zones_modal_split.py...
REM REM python 09_plot_smaller_zones_modal_split.py
REM REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 10_plot_the_clean_csv_files.py...
REM python 10_plot_the_clean_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 11_CSVs_in_a_column.py...
REM python 11_CSVs_in_a_column.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 12_DRT_Data_Analysis.py...
REM python 12_DRT_Data_Analysis.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 13_DRT_Order_Ouputs.py...
python 13_DRT_Order_Ouputs.py
if %ERRORLEVEL% neq 0 goto :error

echo All scripts executed successfully!
exit /b 0

:error
echo A script failed with error level %ERRORLEVEL%. Exiting.
exit /b %ERRORLEVEL%
