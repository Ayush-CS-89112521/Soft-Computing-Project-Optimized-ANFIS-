import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
import os

# Set high resolution and clean font family
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['mathtext.fontset'] = 'dejavusans'

# Create wide landscape figure
fig, ax = plt.subplots(figsize=(15.5, 9.2), dpi=350)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color Palette (Top-tier academic pastel palette)
c_bg_main   = "#F8FAFC"
c_bg_sub    = "#F1F5F9"
c_hit       = "#DCFCE7" # Soft Mint
c_hit_edge  = "#16A34A"
c_proc      = "#EFF6FF" # Soft Blue
c_proc_edge = "#2563EB"
c_infer     = "#FEF3C7" # Soft Amber
c_infer_edge= "#D97706"
c_adapt     = "#FEE2E2" # Soft Coral
c_adapt_edge= "#DC2626"
c_meta      = "#F3E8FF" # Soft Purple
c_meta_edge = "#7C3AED"
c_diamond   = "#E0E7FF" # Indigo tint
c_diamond_e = "#4338CA"
c_arrow     = "#334155" # Slate 700

# Helper function to draw rounded boxes
def draw_box(ax, x, y, w, h, text, title="", bg="#FFFFFF", edge="#000000", lw=1.4, fontsize=9.5, title_fs=10.5):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0.5,rounding_size=1.2",
                       ec=edge, fc=bg, lw=lw, zorder=3)
    ax.add_patch(p)
    cx = x + w / 2.0
    if title:
        cy_title = y + h - (h * 0.28)
        cy_text  = y + (h * 0.38)
        ax.text(cx, cy_title, title, ha='center', va='center', fontsize=title_fs, fontweight='bold', color=edge, zorder=4)
        ax.text(cx, cy_text, text, ha='center', va='center', fontsize=fontsize, color='#1E293B', zorder=4)
    else:
        cy = y + h / 2.0
        ax.text(cx, cy, text, ha='center', va='center', fontsize=fontsize, color='#1E293B', zorder=4)
    return p

# Helper function to draw diamond decision boxes
def draw_diamond(ax, cx, cy, w, h, text, bg=c_diamond, edge=c_diamond_e, lw=1.5, fontsize=9):
    pts = np.array([
        [cx, cy + h/2.0],
        [cx + w/2.0, cy],
        [cx, cy - h/2.0],
        [cx - w/2.0, cy]
    ])
    p = Polygon(pts, closed=True, ec=edge, fc=bg, lw=lw, zorder=3)
    ax.add_patch(p)
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fontsize, fontweight='bold', color=edge, zorder=4)
    return p

# Helper function to draw orthogonal arrows with clear styling
def draw_arrow(ax, x1, y1, x2, y2, label="", label_pos=None, color=c_arrow, lw=1.6, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->,head_width=0.35,head_length=0.45",
                                color=color, lw=lw, linestyle=ls),
                zorder=2)
    if label:
        lx = (x1 + x2)/2.0 if label_pos is None else label_pos[0]
        ly = (y1 + y2)/2.0 if label_pos is None else label_pos[1]
        ax.text(lx, ly, label, fontsize=9, fontweight='bold', color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec="none", alpha=0.85),
                ha='center', va='center', zorder=5)

# Background Subsystem Regions (Dotted/Dashed Enclosures)
# 1. Critical Path Container
box_crit = FancyBboxPatch((1.5, 3.0), 97.0, 93.0,
                          boxstyle="round,pad=1.0,rounding_size=2.0",
                          ec="#CBD5E1", fc="#F8FAFC", lw=1.5, ls="--", zorder=1)
ax.add_patch(box_crit)
ax.text(4.0, 93.5, "OPTIMIZED ANFIS RUNTIME ARCHITECTURE & PIPELINE FLOW (C = 64)",
        fontsize=12, fontweight='bold', color="#0F172A", zorder=2)

# Sub-regions:
# Sub-region A: Fast-Path Hit & Lookup (Top Left)
box_lookup = FancyBboxPatch((3.0, 68.0), 45.0, 23.0,
                            boxstyle="round,pad=0.8,rounding_size=1.5",
                            ec="#93C5FD", fc="#F0F7FF", lw=1.2, ls=":", zorder=1)
ax.add_patch(box_lookup)
ax.text(4.5, 88.8, "Stage 1: Memory Access Ingestion & Fast Hit Path",
        fontsize=10, fontweight='bold', color="#1E40AF", zorder=2)

# Sub-region B: Online Adaptation via Ghost Cache (Top Right)
box_adapt = FancyBboxPatch((51.0, 68.0), 46.0, 23.0,
                           boxstyle="round,pad=0.8,rounding_size=1.5",
                           ec="#FCA5A5", fc="#FFF5F5", lw=1.2, ls=":", zorder=1)
ax.add_patch(box_adapt)
ax.text(52.5, 88.8, "Stage 2: Ghost-Cache Online Learning (Widrow-Hoff LMS)",
        fontsize=10, fontweight='bold', color="#991B1B", zorder=2)

# Sub-region C: Out-of-Band Workload Meta-Controller (Middle Right)
box_meta = FancyBboxPatch((51.0, 39.0), 46.0, 26.0,
                          boxstyle="round,pad=0.8,rounding_size=1.5",
                          ec="#D8B4FE", fc="#FAF5FF", lw=1.2, ls=":", zorder=1)
ax.add_patch(box_meta)
ax.text(52.5, 62.8, "Stage 3: Out-of-Band CART Meta-Controller (Amortized N = 250)",
        fontsize=10, fontweight='bold', color="#6B21A8", zorder=2)

# Sub-region D: 5-Layer L1-Resident ANFIS Engine (Bottom Area)
box_infer = FancyBboxPatch((3.0, 5.5), 94.0, 30.5,
                           boxstyle="round,pad=0.8,rounding_size=1.5",
                           ec="#FCD34D", fc="#FFFDF5", lw=1.2, ls=":", zorder=1)
ax.add_patch(box_infer)
ax.text(4.5, 33.8, "Stage 4: L1-Cache-Resident Neuro-Fuzzy Inference Engine & Tournament Eviction (240.3 ns)",
        fontsize=10, fontweight='bold', color="#B45309", zorder=2)

# --- STAGE 1: INGESTION & FAST HIT PATH ---
# Input Access
draw_box(ax, 5.0, 75.0, 12.0, 9.0,
         "$x_t$ at timestamp $t_{\\mathrm{curr}}$\n(Address & Op)",
         title="Incoming Access",
         bg=c_proc, edge=c_proc_edge, fontsize=8.5, title_fs=9.5)

# Directory Lookup Diamond
draw_diamond(ax, 24.5, 79.5, 11.0, 10.0,
             "Hit in\nCache $\\mathcal{C}$?",
             bg=c_diamond, edge=c_diamond_e, fontsize=8.5)

# Hit Servicing Box
draw_box(ax, 34.0, 74.5, 12.5, 10.0,
         "- Update $t_{\\mathrm{last}} \\leftarrow t_{\\mathrm{curr}}$\n- $F \\leftarrow \\min(F+1, 20)$\n- Deliver Data to CPU",
         title="Fast-Path Hit (5-15 ns)",
         bg=c_hit, edge=c_hit_edge, fontsize=8.0, title_fs=9.0)

# Connectors for Stage 1
draw_arrow(ax, 17.0, 79.5, 19.0, 79.5)
draw_arrow(ax, 30.0, 79.5, 34.0, 79.5, label="YES", label_pos=(32.0, 81.3), color=c_hit_edge)
draw_arrow(ax, 24.5, 74.5, 24.5, 59.0, label="NO (Miss)", label_pos=(24.5, 67.0), color=c_adapt_edge)

# Capacity Diamond
draw_diamond(ax, 24.5, 53.5, 11.0, 9.0,
             "Cache Full?\n($|\\mathcal{C}| = 64$)",
             bg=c_diamond, edge=c_diamond_e, fontsize=8.5)

# Cold insertion box
draw_box(ax, 5.0, 48.5, 12.0, 10.0,
         "- Allocate free slot\n- $t_{\\mathrm{arrival}} \\leftarrow t_{\\mathrm{curr}}$\n- Fetch from DRAM/SSD",
         title="Direct Insertion",
         bg=c_hit, edge=c_hit_edge, fontsize=8.0, title_fs=9.0)

draw_arrow(ax, 19.0, 53.5, 17.0, 53.5, label="NO", label_pos=(18.0, 55.2), color=c_hit_edge)

# --- STAGE 2: GHOST CACHE & ONLINE ADAPTATION ---
# From Capacity Diamond to Ghost Query & Eviction Path
draw_arrow(ax, 30.0, 53.5, 36.0, 53.5)
draw_arrow(ax, 36.0, 53.5, 36.0, 79.5)
draw_arrow(ax, 36.0, 79.5, 53.5, 79.5, label="Enter Eviction Pipeline", label_pos=(44.5, 81.2))

# Ghost Cache Diamond
draw_diamond(ax, 59.0, 79.5, 11.0, 10.0,
             "Key $x_t$ in\nGhost $\\mathcal{B}$?",
             bg=c_diamond, edge=c_diamond_e, fontsize=8.5)

# Ghost Hit Box (Delta Rule)
draw_box(ax, 74.0, 72.0, 21.0, 15.0,
         "- Target $y^* = 1.0$ (Premature Eviction)\n- Compute Error: $e_t = 1.0 - \\mathrm{Score}_{\\mathrm{ghost}}$\n- Widrow-Hoff Delta Rule Update:\n  $c_i^{(t+1)} = \\mathrm{clamp}((1-\\lambda)c_i^{(t)} + \\lambda c_i^{(0)} + \\eta e_t \\bar{w}_i)$\n- 19 CPU Instructions (~15 ns, 0.0000 s CPU)",
         title="Instantaneous Online LMS Step",
         bg=c_adapt, edge=c_adapt_edge, fontsize=7.8, title_fs=8.8)

draw_arrow(ax, 64.5, 79.5, 74.0, 79.5, label="YES (Ghost Hit)", label_pos=(69.0, 81.5), color=c_adapt_edge)

# Downward arrow from ghost query to meta-controller / eviction
draw_arrow(ax, 59.0, 74.5, 59.0, 68.0, ls=":")

# --- STAGE 3: OUT-OF-BAND CART META-CONTROLLER ---
# Rolling Window Feature Extraction Box
draw_box(ax, 53.0, 44.0, 18.0, 16.0,
         "Sampled every $N = 250$ reqs:\n- $f_1 = U / N$ (Expansion)\n- $f_2 = H$ (Shannon Entropy)\n- $f_3 = \\mathrm{Corr}$ (Autocorr)\n- $f_4 = G$ (Gini Skew)\n- $f_5 = S$ (Stride Index)\nNormalized Feature: $\\mathbf{f} \\in [0, 1]^5$",
         title="5-D Telemetry Feature Extractor",
         bg=c_meta, edge=c_meta_edge, fontsize=7.6, title_fs=8.6)

# CART Decision Tree Engine
draw_box(ax, 74.5, 44.0, 20.5, 16.0,
         "Trained on balanced 4-regime bank:\n- If $H > 0.94$ and $u \\leq 0.50$ (Cyclic Loop):\n  $\\rightarrow$ Activate Recency Inversion ($1 - R$)\n- If $H \\leq 0.94$ and $\\rho \\leq 0.073$ (Scan):\n  $\\rightarrow$ Frequency Shielding ($1.5F, 0.5R$)\nLatency: 1.40 $\\mu$s (Amortized 5.6 ns/req)",
         title="CART Decision Tree Classifier",
         bg=c_meta, edge=c_meta_edge, fontsize=7.6, title_fs=8.6)

draw_arrow(ax, 71.0, 52.0, 74.5, 52.0)

# Connect from Capacity to Eviction Tournament
draw_arrow(ax, 24.5, 49.0, 24.5, 34.0, label="Cache Full", label_pos=(24.5, 42.0), color=c_infer_edge)

# --- STAGE 4: NEURO-FUZZY INFERENCE PIPELINE & TOURNAMENT ---
# Tournament Sampling Box
draw_box(ax, 5.0, 10.0, 15.0, 20.0,
         "When $|\\mathcal{C}| = 64$ is full:\n- Partial Fisher-Yates shuffle\n- Draw $K = 12$ candidates\n- Bounds scan to $O(1)$\n- Avoids full $O(C)$ sweeps\n- Read packed metadata:\n  $\\{t_{\\mathrm{last}}, \\mathrm{freq}, t_{\\mathrm{arrival}}\\}$",
         title="Eviction Tournament\n(K = 12 Candidates)",
         bg=c_infer, edge=c_infer_edge, fontsize=7.8, title_fs=8.8)

# Input Normalization & Blending Box
draw_box(ax, 23.0, 10.0, 16.0, 20.0,
         "For each candidate $k \\in \\mathcal{K}$:\n- $R = \\mathrm{clip}(1 - \\frac{\\Delta t}{4C}, 0, 1)$\n- $F = \\mathrm{clip}(\\frac{\\mathrm{freq}}{20}, 0, 1)$\n- $A = \\mathrm{clip}(1 - \\frac{\\Delta t_{\\mathrm{arr}}}{4C}, 0, 1)$\n- Composite Coordinates:\n  $R_{\\mathrm{eff}} = (0.25R + 0.10A)/0.35$\n  $F_{\\mathrm{eff}} = F$",
         title="Input Normalization &\nTri-Input Synthesis",
         bg=c_proc, edge=c_proc_edge, fontsize=7.8, title_fs=8.8)

draw_arrow(ax, 20.0, 20.0, 23.0, 20.0)

# Layer 1 L1-LUT Box
draw_box(ax, 42.0, 10.0, 16.0, 20.0,
         "Precomputed Gaussian curves:\n- Table Size: $6.0\\,\\mathrm{KB}$ (L1D Fit)\n- Discretization: 256 points\n- Quantized Integer Index:\n  $i_R = \\lfloor 255 R_{\\mathrm{eff}} \\rfloor, \\, i_F = \\lfloor 255 F_{\\mathrm{eff}} \\rfloor$\n- Direct $O(1)$ L1 Read:\n  $\\mu_L, \\mu_M, \\mu_H$ in 1-2 ns",
         title="Layer 1: Fuzzification via\nHardware L1 LUT (6 KB)",
         bg=c_infer, edge=c_infer_edge, fontsize=7.8, title_fs=8.8)

draw_arrow(ax, 39.0, 20.0, 42.0, 20.0)

# Layer 2, 3, 4 Firing & Defuzzification Box
draw_box(ax, 61.0, 10.0, 17.0, 20.0,
         "8-Rule Takagi-Sugeno Model:\n- L2 Product T-Norm:\n  $w_i = \\mu_{R, i} \\times \\mu_{F, i}$\n- L3 Firing Normalization:\n  $\\bar{w}_i = w_i / \\sum_{j=0}^7 w_j$\n- L4 Consequent Priorities: $c_i$\n- L5 Zero-Order Centroid:\n  $\\mathrm{Score} = \\sum_{i=0}^7 \\bar{w}_i c_i$",
         title="Layers 2-5: Rule Firing &\nDefuzzification Engine",
         bg=c_infer, edge=c_infer_edge, fontsize=7.8, title_fs=8.8)

draw_arrow(ax, 58.0, 20.0, 61.0, 20.0)

# Connect CART hedge influence into Normalization
draw_arrow(ax, 84.5, 44.0, 84.5, 33.0)
draw_arrow(ax, 84.5, 33.0, 31.0, 33.0)
draw_arrow(ax, 31.0, 33.0, 31.0, 30.0, label="Dynamic Hedge Modulation", label_pos=(55.0, 34.5), color=c_meta_edge, ls="--")

# Victim Selection Box
draw_box(ax, 81.0, 10.0, 14.5, 20.0,
         "Tournament Decision:\n- $\\mathrm{Victim} = \\arg\\min_{k} (\\mathrm{Score}_k)$\n- Evict victim from $\\mathcal{C}$\n- Record tag & score to\n  FIFO Ghost Cache $\\mathcal{B}$\n- Insert incoming block $x_t$\n- Line-Rate Latency: 240.3 ns",
         title="Victim Selection &\nCache Replacement",
         bg=c_hit, edge=c_hit_edge, fontsize=7.8, title_fs=8.8)

draw_arrow(ax, 78.0, 20.0, 81.0, 20.0)

# Output paths
out_dir = r"C:\Users\Asus\OneDrive\Desktop\Soft Computing Optimized ANFIS\figures"
os.makedirs(out_dir, exist_ok=True)
png_path = os.path.join(out_dir, "fig_system_architecture_flowchart.png")
pdf_path = os.path.join(out_dir, "fig_system_architecture_flowchart.pdf")

plt.tight_layout()
plt.savefig(png_path, dpi=350, bbox_inches='tight')
plt.savefig(pdf_path, bbox_inches='tight')
plt.close()

# Also copy to 02_LaTeX_Source/figures and project workspace
workspace_fig = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\02_LaTeX_Source\figures"
os.makedirs(workspace_fig, exist_ok=True)
import shutil
shutil.copy2(png_path, os.path.join(workspace_fig, "fig_system_architecture_flowchart.png"))
shutil.copy2(pdf_path, os.path.join(workspace_fig, "fig_system_architecture_flowchart.pdf"))

# Also copy to root figures in both locations
shutil.copy2(png_path, r"C:\Users\Asus\OneDrive\Desktop\Soft Computing Optimized ANFIS\02_LaTeX_Source\figures\fig_system_architecture_flowchart.png")
shutil.copy2(pdf_path, r"C:\Users\Asus\OneDrive\Desktop\Soft Computing Optimized ANFIS\02_LaTeX_Source\figures\fig_system_architecture_flowchart.pdf")

workspace_root_fig = r"c:\Users\Asus\OneDrive\Desktop\Soft computing Project\new ideas\Optimized Standard ANFIS\figures"
os.makedirs(workspace_root_fig, exist_ok=True)
shutil.copy2(png_path, os.path.join(workspace_root_fig, "fig_system_architecture_flowchart.png"))
shutil.copy2(pdf_path, os.path.join(workspace_root_fig, "fig_system_architecture_flowchart.pdf"))

print(f"Flowchart successfully generated at: {png_path}")
