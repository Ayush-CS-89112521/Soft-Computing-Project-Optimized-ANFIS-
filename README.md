# Optimized ANFIS: Adaptive Neuro-Fuzzy Cache Replacement Engine

This repository contains the complete experimental infrastructure, native C++17 implementations, simulation trace suites, evaluation scripts, and LaTeX publication manuscripts for **Optimized ANFIS**.

Optimized ANFIS is an L1-cache-resident, line-rate Neuro-Fuzzy cache replacement policy evaluated across industrial workloads (CloudPhysics VMware, SNIA MSR Cambridge, UMass Financial1 OLTP) and adversarial stress benchmarks at the architecturally optimal operating point of Cache Capacity $C = 64$ blocks.

---

## Directory Organization

```
Soft Computing Optimized ANFIS/
|-- 01_Final_Manuscripts_PDF/             # Finalized, publication-ready PDF manuscripts
|   |-- FAST_LUT_ANFIS_C64_OPTIMAL_MANUSCRIPT.pdf   (IEEE Conference 2-Column Format)
|   |-- SPRINGER_ANFIS_MANUSCRIPT.pdf               (Springer Nature Journal Format)
|   |-- discussion_report.pdf                       (Extended Systems & Analysis Report)
|   `-- discussion.pdf                              (Technical Discussion Whitepaper)
|
|-- 02_LaTeX_Source/                      # Complete LaTeX source files and templates
|   |-- FAST_LUT_ANFIS_C64_OPTIMAL_MANUSCRIPT.tex   (IEEE Conference Manuscript source)
|   |-- SPRINGER_ANFIS_MANUSCRIPT.tex               (Springer Nature Manuscript source)
|   |-- ANFIS_RESEARCH_PAPER_OVERLEAF.tex           (Consolidated Overleaf submission)
|   |-- sn-jnl.cls, *.bst, *.sty                    (Springer and IEEE journal classes & styles)
|   |-- figures/                                    # High-resolution vector and raster charts
|   `-- package_documentation/                      # LaTeX package manuals and documentation
|
|-- 03_Source_Code_and_Benchmarks/        # Native C++17 replacement engine implementation
|   |-- cpp/                                        # Modular headers and policy source code
|   |   |-- anfis_cache.hpp                         # Optimized ANFIS controller implementation
|   |   |-- baseline_policies.hpp                   # MIN, LRU, LFU, FIFO, and ARC implementations
|   |   `-- workload_generators.hpp                 # Synthetic trace generation engines
|   |-- extended_cache_benchmark.cpp                # Comprehensive benchmarking harness
|   |-- compile_and_run.bat                         # GCC compilation and execution automation script
|   `-- binaries/                                   # Precompiled native benchmark executables (*.exe)
|
|-- 04_Experimental_Results_CSV/          # Empirical evaluation telemetry and trace datasets
|   |-- cache_results_results.csv                   # Primary multi-workload benchmark hit rates
|   |-- cache_results_synthetic_traces.csv          # High-volume synthetic trace performance
|   |-- fine_capacity_*.csv                         # Granular capacity scaling sweeps (C = 2 to 64)
|   |-- cyclic_mass_results.csv                     # Adversarial cyclic loop stress telemetry
|   |-- scan_mass_results.csv                       # Sequential scan resilience datasets
|   `-- wilcoxon_trials.csv                         # Paired statistical validation trials
|
|-- 05_Python_Scripts/                    # Data processing, statistical analysis, and plotting
|   |-- plotting_and_figures/                       # Publication figure generation scripts
|   |-- synthetic_trace_generators/                 # Reproducible synthetic workload bank generators
|   |-- workload_inspectors_and_downloaders/        # Storage trace acquisition and parser utilities
|   `-- telemetry_and_statistical_analysis/         # Wilcoxon hypothesis testing and Pareto sweeps
|
|-- 06_Documentation_and_Notes/           # Research methodology, trace guides, and notes
|   |-- dataset_and_test.md                         # Detailed storage trace specifications
|   |-- real world data testing.md                  # Trace download, parsing, and preprocessing notes
|   |-- discussion.md                               # Comprehensive comparative architectural analysis
|   |-- literature_matrix.md                        # Systematic baseline taxonomy and literature matrix
|   |-- OVERLEAF_INSTRUCTIONS.md                    # Overleaf compilation and upload guide
|   `-- old/                                        # Historical drafts and experimental iterations
|
`-- figures/                              # Root-level figures directory (mirrored for TeX paths)
```

---

## Key Performance Results at Operating Capacity $C = 64$

| Policy Architecture | Decision Latency | Background CPU Time | Cyclic Loop Hit Rate ($L > C$) | Overall Multi-Aspect Average |
| :--- | :---: | :---: | :---: | :---: |
| Classical LRU | $45.2\,\text{ns}$ | $0.0000\,\text{s}$ | $9.30\%$ | $48.76\%$ |
| Classical LFU | $48.1\,\text{ns}$ | $0.0000\,\text{s}$ | $55.17\%$ | $48.66\%$ |
| IBM ARC | $82.4\,\text{ns}$ | $0.0000\,\text{s}$ | $11.00\%$ | $52.36\%$ |
| Baseline Fuzzy (PSO / GA) | $119.6\text{--}144.1\,\mu\text{s}$ | $4.26\text{--}6.02\,\text{s}$ | $38.40\text{--}40.27\%$ | $52.36\%$ |
| **Optimized ANFIS (Ours)** | $\mathbf{240.3\,\text{ns}}$ | $\mathbf{0.0000\,\text{s}}$ | $\mathbf{65.63\%}$ | $\mathbf{58.73\%}$ |

---

## Compilation Instructions

### Compiling the Manuscripts Locally
To recompile either manuscript from source, navigate to `02_LaTeX_Source/` and execute `pdflatex`:

```bash
cd 02_LaTeX_Source

# Compile IEEE Conference Manuscript (8 pages)
pdflatex FAST_LUT_ANFIS_C64_OPTIMAL_MANUSCRIPT.tex
pdflatex FAST_LUT_ANFIS_C64_OPTIMAL_MANUSCRIPT.tex

# Compile Springer Nature Journal Manuscript (17 pages)
pdflatex SPRINGER_ANFIS_MANUSCRIPT.tex
pdflatex SPRINGER_ANFIS_MANUSCRIPT.tex
```

### Compiling and Running the Native C++ Benchmarks
To build and run the cache evaluation engine with MinGW GCC:

```bash
cd 03_Source_Code_and_Benchmarks
compile_and_run.bat
```
Alternatively, compile manually with maximum hardware optimizations:
```bash
g++ -O3 -march=native -std=c++17 extended_cache_benchmark.cpp -o binaries/extended_benchmark.exe
```

---

## Statistical Significance
Paired Wilcoxon signed-rank testing across all evaluation workloads confirms that Optimized ANFIS is statistically superior to IBM ARC ($W = 34.0, z = 2.38, p = 0.0173 < 0.05, d = 1.18$) and Classical LFU ($W = 0.0, p = 0.0156 < 0.05$).
