@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Set the directory containing allScripts.bat
cd C:\Users\muaa\Documents\3_MIEI\ThurgauPaperAnalysisAM\scripts

REM Navigate to the directory containing config.ini
cd ..\config

REM Read simulation output path from config.ini
FOR /F "tokens=2 delims==" %%i IN ('findstr "sim_output_folder" config.ini') DO (
    SET "sim_output_folder=%%i"
)

REM Remove quotes from the path if present
SET sim_output_folder=%sim_output_folder:"=%

REM Correct backslashes and remove trailing space
SET sim_output_folder=%sim_output_folder:\=\\%
SET sim_output_folder=%sim_output_folder: =%

REM Loop through each folder in the simulation output directory
FOR /D %%G IN ("%sim_output_folder%\*") DO (
    ECHO Processing simulation folder: %%G

    REM Set the analysis_zone_name to the current directory name
    REM This assumes the folder name is the desired analysis_zone_name
    SET "folderName=%%~nG"
    REM Modify the config.ini with the new analysis_zone_name
    (echo analysis_zone_name=!folderName!) > temp.ini
    findstr /v "analysis_zone_name" config.ini >> temp.ini
    move /Y temp.ini config.ini

    REM Call allScripts.bat with the directory name
    CALL ..\scripts\allScripts.bat %%G
)

ECHO All simulations processed.
ENDLOCAL
