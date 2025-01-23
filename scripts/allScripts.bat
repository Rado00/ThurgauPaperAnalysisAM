@echo off
echo Starting the Python analysis pipeline...

REM Activate the Python environment
call "C:\Users\muaa\Documents\3_MIEI\PythonEnvironments\ThurgauAnalysisEnv\Scripts\activate.bat"

REM Navigate to the directory containing your scripts
cd "C:\Users\muaa\Documents\3_MIEI\ThurgauPaperAnalysisAM\scripts"

REM Run each script in sequence
REM echo Running 01_microcensus_population_filter.py...
REM python 01_microcensus_population_filter.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 02_microcensus_trips_filter.py...
REM python 02_microcensus_trips_filter.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 03_synPop_and_sim_create_csv_files.py...
REM python 03_synPop_and_sim_create_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 03_synt_and_sim_mode_share_by_time_distance.py...
REM python 03_synt_and_sim_mode_share_by_time_distance.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 04_generate_clean_csv_files.py...
REM python 04_generate_clean_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 04_plot_mode_share_time_distance_synt.py...
REM python 04_plot_mode_share_time_distance_synt.py
REM if %ERRORLEVEL% neq 0 goto :error

REM NOT USING THIS
REM echo Running 04_2_synPop_sim_analysis.py...
REM python 04_2_synPop_sim_analysis.py
REM if %ERRORLEVEL% neq 0 goto :error

REM echo Running 05_plot_the_clean_csv_files.py...
REM python 05_plot_the_clean_csv_files.py
REM if %ERRORLEVEL% neq 0 goto :error

echo Running 05_2_CSVs_in_a_column.py...
python 05_2_CSVs_in_a_column.py
if %ERRORLEVEL% neq 0 goto :error

echo All scripts executed successfully!
pause
exit /b 0

:error
echo A script failed with error level %ERRORLEVEL%. Exiting.
pause
exit /b %ERRORLEVEL%
