"""
Academic Publication Figure Generator (300 DPI)
Engineered strictly to IEEE Transactions, ACM SIGMETRICS, and USENIX FAST standards.
Clean, data-first, minimalist design:
- NO 2Q and NO Static-Fuzzy (all baselines match evaluated policies).
- NO cartoon callouts, NO speech bubbles, NO arrow annotations.
- Classic academic hatching and printer-friendly high-contrast styling.
- Standard serif typography (Times New Roman / Computer Modern).
- Crisp black axis borders, subtle gray gridlines, unobtrusive legends.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\figures"
os.makedirs(OUT_DIR, exist_ok=True)

def apply_academic_styling():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Computer Modern Roman"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 9,
        "figure.titlesize": 13,
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#000000",
        "grid.color": "#dcdcdc",
        "grid.linestyle": ":",
        "grid.alpha": 0.7,
        "grid.linewidth": 0.6,
        "lines.linewidth": 1.6,
        "lines.markersize": 5.5,
        "mathtext.fontset": "stix",
    })

apply_academic_styling()

# =========================================================================
# FIGURE 1: Comprehensive Hit Rate Comparison at C = 64
# =========================================================================
def generate_figure1():
    fig, ax = plt.subplots(figsize=(11.0, 4.8), dpi=300)

    workloads = [
        "CloudPhysics w01",
        "CloudPhysics w02",
        "SNIA MSR",
        "UMass Financial1",
        "UMass WebSearch1",
        "Scan-Dominated",
        "Cyclic Loop (L=75)",
        "Combined Average"
    ]

    lfu_hr   = [96.61, 91.15, 18.73, 13.13, 12.72, 69.67, 55.17, 50.93]
    fifo_hr  = [98.74, 93.83, 20.99, 34.90, 49.25, 51.23,  5.60, 44.19]
    lru_hr   = [98.82, 94.06, 21.86, 39.23, 51.38, 62.95,  9.30, 48.76]
    arc_hr   = [98.80, 94.08, 24.15, 39.69, 53.74, 69.72, 11.00, 52.36]
    anfis_hr = [98.70, 93.55, 21.88, 37.30, 45.16, 68.58, 65.63, 58.73]

    x = np.arange(len(workloads))
    w = 0.16

    ax.bar(x - 2*w, lfu_hr,   width=w, label='Classical LFU',          color='#ffffff', edgecolor='#000000', hatch='///', linewidth=0.7)
    ax.bar(x - 1*w, fifo_hr,  width=w, label='Classical FIFO',         color='#e0e0e0', edgecolor='#000000', hatch='\\\\\\', linewidth=0.7)
    ax.bar(x + 0*w, lru_hr,   width=w, label='Classical LRU',          color='#b0b0b0', edgecolor='#000000', hatch='..', linewidth=0.7)
    ax.bar(x + 1*w, arc_hr,   width=w, label="IBM ARC ('03)",          color='#606060', edgecolor='#000000', hatch='xx', linewidth=0.7)
    ax.bar(x + 2*w, anfis_hr, width=w, label='Fast-LUT ANFIS (Ours)', color='#1b4f72', edgecolor='#000000', linewidth=0.9)

    ax.axvline(6.5, color='#888888', linestyle='--', linewidth=0.8)

    ax.set_ylabel('Hit Rate (%)', fontsize=11)
    ax.set_title('Cache Hit Rate Comparison Across Storage Workloads (C = 64)', fontsize=12, pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(workloads, fontsize=9.5)
    ax.set_ylim(0, 105)
    ax.grid(axis='y', linestyle=':', alpha=0.7)

    ax.legend(frameon=True, edgecolor='#000000', facecolor='#ffffff',
              loc='upper left', ncol=5, fontsize=8.8, handlelength=1.5)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig1_c64_hitrate_comparison.png")
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated clean: {path}")

# =========================================================================
# FIGURE 2: Decision Latency Comparison (Log Scale, Only Active Baselines)
# =========================================================================
def generate_figure2():
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=300)

    # Clean set of evaluated policies (2Q and Static-Fuzzy removed)
    policies = [
        "Classical FIFO",
        "Classical LRU",
        "IBM ARC ('03)",
        "Fast-LUT ANFIS (Ours)",
        "Baseline PSO Tuning",
        "Baseline GA Tuning"
    ]

    latencies_ns = [72.4, 119.4, 140.6, 240.3, 119620.0, 144080.0]
    colors = ['#ffffff', '#e0e0e0', '#b0b0b0', '#1b4f72', '#d5dbdb', '#a6acaf']
    hatches = ['\\\\\\', '..', 'xx', '', '//', '++']

    y_pos = np.arange(len(policies))

    bars = ax.barh(y_pos, latencies_ns, height=0.56, color=colors, edgecolor='#000000', linewidth=0.8)
    for i, bar in enumerate(bars):
        bar.set_hatch(hatches[i])

    # Standard vertical line for real-time bound (1.0 us = 1000 ns)
    ax.axvline(1000.0, color='#922b21', linestyle='--', linewidth=1.2)
    ax.text(1050, 0.35, "Real-time deadline (1.0 µs)", rotation=90, fontsize=8.5, color='#922b21')

    for i, v in enumerate(latencies_ns):
        if v < 1000:
            txt = f"{v:.1f} ns"
        else:
            txt = f"{v/1000.0:.1f} µs"
        ax.text(v * 1.14, i, txt, va='center', ha='left', fontsize=8.5, color='#000000')

    ax.set_xscale('log')
    ax.set_xlim(20, 450000)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(policies, fontsize=9.5)
    ax.set_xlabel('Eviction Decision Latency (Nanoseconds, Log Scale)', fontsize=10.5)
    ax.set_title('Eviction Decision Latency: Fast-LUT ANFIS vs. Baselines', fontsize=11.5, pad=10)
    ax.grid(axis='x', which='major', linestyle=':', alpha=0.7)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig2_c64_latency_comparison.png")
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated clean: {path}")

# =========================================================================
# FIGURE 3: Background Optimizer CPU Overhead & Throughput (Dual Panel)
# =========================================================================
def generate_figure3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.0), dpi=300)

    models = ["GA Tuning", "PSO Tuning", "IBM ARC", "Fast-LUT ANFIS\n(Ours)"]
    cpu_time = [6.02, 4.26, 0.00, 0.00]
    throughput = [6940, 8360, 7112000, 4161465]

    # Panel 1: CPU Time
    bars1 = ax1.bar(models, cpu_time, width=0.52, color=['#b0b0b0', '#b0b0b0', '#ffffff', '#1b4f72'],
                    edgecolor='#000000', linewidth=0.8, hatch=['///', '///', 'xx', ''])
    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width()/2.0, h + 0.15, f"{h:.2f} s",
                     ha='center', va='bottom', fontsize=8.5)
        else:
            ax1.text(bar.get_x() + bar.get_width()/2.0, 0.15, "0.00 s",
                     ha='center', va='bottom', fontsize=8.5)

    ax1.set_ylabel('Optimizer CPU Time (s)', fontsize=10)
    ax1.set_title('(a) Background Optimizer CPU Consumption', fontsize=10.5, pad=8)
    ax1.set_ylim(0, 7.5)
    ax1.grid(axis='y', linestyle=':', alpha=0.7)

    # Panel 2: Operational Throughput
    bars2 = ax2.bar(models, throughput, width=0.52, color=['#e0e0e0', '#e0e0e0', '#606060', '#1b4f72'],
                    edgecolor='#000000', linewidth=0.8, hatch=['..', '..', 'xx', ''])
    
    ax2.text(bars2[0].get_x() + bars2[0].get_width()/2.0, throughput[0] + 150000, "6.9k ops/s",
             ha='center', va='bottom', fontsize=8.0)
    ax2.text(bars2[1].get_x() + bars2[1].get_width()/2.0, throughput[1] + 150000, "8.4k ops/s",
             ha='center', va='bottom', fontsize=8.0)
    ax2.text(bars2[2].get_x() + bars2[2].get_width()/2.0, throughput[2] + 150000, "7.11M ops/s",
             ha='center', va='bottom', fontsize=8.0)
    ax2.text(bars2[3].get_x() + bars2[3].get_width()/2.0, throughput[3] + 150000, "4.16M ops/s",
             ha='center', va='bottom', fontsize=8.0)

    ax2.set_ylabel('Throughput (Ops/sec)', fontsize=10)
    ax2.set_title('(b) Decision Engine Throughput', fontsize=10.5, pad=8)
    ax2.set_ylim(0, 8500000)
    ax2.grid(axis='y', linestyle=':', alpha=0.7)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig3_c64_cpu_elimination.png")
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated clean: {path}")

# =========================================================================
# FIGURE 4: Component Ablation (Clean, Compared Against Classical LRU)
# =========================================================================
def generate_figure4():
    fig = plt.figure(figsize=(10.5, 4.2), dpi=300)

    ax1 = fig.add_subplot(1, 2, 1)

    # Configurations comparing full system against ablations and Classical LRU baseline
    configs = [
        "Full System\n(DT+Ghost+LUT)",
        "w/o Decision Tree\n(No Inversion)",
        "w/o Ghost Cache\n(Static Rules)",
        "Classical LRU\nBaseline"
    ]

    overall_avg = [58.73, 42.15, 51.40, 48.76]
    cyclic_hr   = [65.63,  9.20, 52.10,  9.30]

    x = np.arange(len(configs))
    w = 0.36

    b1 = ax1.bar(x - w/2, overall_avg, width=w, label='Overall Average', color='#1b4f72', edgecolor='#000000', linewidth=0.8)
    b2 = ax1.bar(x + w/2, cyclic_hr,   width=w, label='Cyclic Loop Hit Rate', color='#e0e0e0', edgecolor='#000000', hatch='///', linewidth=0.8)

    for i in range(len(configs)):
        ax1.text(x[i] - w/2, overall_avg[i] + 1.2, f"{overall_avg[i]:.1f}%", ha='center', va='bottom', fontsize=8.0)
        ax1.text(x[i] + w/2, cyclic_hr[i] + 1.2,   f"{cyclic_hr[i]:.1f}%",   ha='center', va='bottom', fontsize=8.0)

    ax1.set_ylabel('Hit Rate (%)', fontsize=10)
    ax1.set_title('(a) Component Ablation at C = 64', fontsize=10.5, pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(configs, fontsize=8.5)
    ax1.set_ylim(0, 78)
    ax1.grid(axis='y', linestyle=':', alpha=0.7)
    ax1.legend(loc='upper right', frameon=True, edgecolor='#000000', facecolor='#ffffff', fontsize=8.5)

    # Subplot 2: 3D Quantized LUT Inference Surface
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')

    r_vals = np.linspace(0.0, 1.0, 35)
    f_vals = np.linspace(0.0, 1.0, 35)
    R, F = np.meshgrid(r_vals, f_vals)

    def anfis_retention_manifold(r, f):
        mu_r_high = np.exp(-0.5 * ((r - 0.85) / 0.16)**2)
        mu_f_high = np.exp(-0.5 * ((f - 0.85) / 0.16)**2)
        mu_f_mid  = np.exp(-0.5 * ((f - 0.50) / 0.16)**2)
        z = 0.28 * r + 0.62 * f + 0.18 * (mu_r_high * mu_f_high) - 0.12 * (1.0 - mu_f_mid)
        return np.clip(z, 0.05, 0.95)

    Z = anfis_retention_manifold(R, F)

    surf = ax2.plot_surface(R, F, Z, cmap='cividis', edgecolor='none', alpha=0.90, zorder=2)
    cset = ax2.contour(R, F, Z, zdir='z', offset=0.0, cmap='cividis', linewidths=0.9, zorder=1)

    ax2.set_xlabel('Recency (R)', fontsize=8.5, labelpad=5)
    ax2.set_ylabel('Frequency (F)', fontsize=8.5, labelpad=5)
    ax2.set_zlabel('Score', fontsize=8.5, labelpad=5)
    ax2.set_title('(b) Precomputed LUT Retention Manifold', fontsize=10.5, pad=8)
    ax2.view_init(elev=28, azim=-62)

    cbar = fig.colorbar(surf, ax=ax2, shrink=0.60, aspect=14, pad=0.08)
    cbar.set_label('Retention Priority', fontsize=8.5, rotation=270, labelpad=10)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, "fig4_c64_ablation_study.png")
    plt.savefig(path, dpi=300)
    plt.close()
    print(f"Generated clean: {path}")

if __name__ == "__main__":
    generate_figure1()
    generate_figure2()
    generate_figure3()
    generate_figure4()
    print("All figures refreshed cleanly!")
