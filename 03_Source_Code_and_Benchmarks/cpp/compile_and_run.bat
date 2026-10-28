@echo off
echo Compiling Fast-LUT ANFIS C++ Benchmark with GCC 16.2 (-O3)...
g++ -O3 -std=c++20 -I include src/main.cpp -o benchmark.exe
if %ERRORLEVEL% EQU 0 (
    echo Compilation successful! Running benchmark...
    echo.
    benchmark.exe
) else (
    echo Compilation failed.
)
