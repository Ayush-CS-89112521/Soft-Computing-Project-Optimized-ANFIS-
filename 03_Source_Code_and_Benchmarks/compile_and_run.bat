@echo off
echo =========================================================================
echo Compiling Fast-LUT ANFIS C++ Benchmark with MinGW GCC 16.2 (-O3)...
echo =========================================================================
g++ -O3 -std=c++20 -I cpp/include cpp/src/main.cpp -o benchmark.exe
if %ERRORLEVEL% EQU 0 (
    echo Compilation successful! Executing native benchmark binary...
    echo.
    benchmark.exe
) else (
    echo [ERROR] Compilation failed.
)
