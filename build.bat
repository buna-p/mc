@echo off
chcp 65001 >nul
echo ====================================
echo   Сборка ExcelProcessor.exe
echo ====================================
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "ExcelProcessor" ^
    --add-data "file_dialogs.py;." ^
    --add-data "excel_processor.py;." ^
    --add-data "address_parser.py;." ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    main.py

echo.
echo Готово! Ищи ExcelProcessor.exe в папке dist\
pause