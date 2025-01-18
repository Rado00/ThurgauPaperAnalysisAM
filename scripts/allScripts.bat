@echo off
echo Starting the Python analysis pipeline...

REM Activate the Python environment
call "C:\Users\muaa\Documents\3_MIEI\PythonEnvironments\ThurgauAnalysisEnv\Scripts\activate.bat"

REM Navigate to the directory containing your scripts
cd "C:\Users\muaa\Documents\3_MIEI\ThurgauPaperAnalysisAM\scripts"

REM Run each script in sequence
echo Running 01_microcensus_population_filter.py...
python 01_microcensus_population_filter.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 02_microcensus_trips_filter.py...
python 02_microcensus_trips_filter.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 03_synPop_&_sim_create_csv_files.py...
python 03_synPop_&_sim_create_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 04_generate_clean_csv_files.py...
python 04_generate_clean_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

echo Running 05_plot_the_clean_csv_files.py...
python 05_plot_the_clean_csv_files.py
if %ERRORLEVEL% neq 0 goto :error

echo All scripts executed successfully!
pause
exit /b 0

:error
echo A script failed with error level %ERRORLEVEL%. Exiting.
pause
exit /b %ERRORLEVEL%
