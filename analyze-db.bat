@echo off
:: ========================================================================
:: MCP Servers Database Analysis Script
:: ========================================================================
:: This script analyzes the SQLite database and generates comprehensive
:: reports on MCP servers, GitHub metrics, configurations, and more.
::
:: Outputs:
::   - Console: Colored report with tables
::   - Markdown: reports/db-analysis-YYYY-MM-DD.md
:: ========================================================================

title MCP Database Analysis

echo.
echo ===============================================================================
echo    MCP SERVERS DATABASE ANALYSIS
echo ===============================================================================
echo.
echo Analyzing database: data\mcp_servers.db
echo.

:: Compile TypeScript to JavaScript if needed
if not exist "scripts\analyze-database.js" (
    echo [1/2] Compiling TypeScript...
    call npx tsc scripts/analyze-database.ts --target ES2020 --module commonjs --lib ES2020 --esModuleInterop --skipLibCheck --resolveJsonModule --moduleResolution node
    if errorlevel 1 (
        echo.
        echo ERROR: TypeScript compilation failed!
        echo Please check your TypeScript installation and script syntax.
        pause
        exit /b 1
    )
    echo.
)

:: Run the analysis
echo [2/2] Running analysis...
echo.
node scripts\analyze-database.js

if errorlevel 1 (
    echo.
    echo ERROR: Analysis failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo    Analysis complete! Check the reports folder for Markdown output.
echo ===============================================================================
echo.
pause
