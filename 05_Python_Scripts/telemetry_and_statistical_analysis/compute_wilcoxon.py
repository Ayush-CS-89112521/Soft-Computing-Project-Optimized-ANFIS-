import csv
import numpy as np
from scipy import stats

def compute_statistics():
    filepath = "c:/Users/Asus/OneDrive/Desktop/Soft computing Project/new ideas/Optimized Standard ANFIS/wilcoxon_trials.csv"
    
    trials = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trials.append(row)
            
    policies = ["LRU", "FIFO", "LFU", "ARC", "TwoQueue", "StaticFuzzy", "FastLUT_ANFIS"]
    data = {p: np.array([float(r[p]) for r in trials]) for p in policies}
    
    print("=" * 80)
    print("STATISTICAL EVALUATION ACROSS 10 PRODUCTION TRIALS (N = 10)")
    print("=" * 80)
    
    print(f"\n{'Policy':<18} {'Mean Hit Rate (%)':<20} {'Std Dev (%)':<15} {'Median (%)':<15}")
    print("-" * 70)
    for p in policies:
        mean_v = np.mean(data[p])
        std_v = np.std(data[p], ddof=1)
        med_v = np.median(data[p])
        print(f"{p:<18} {mean_v:<20.3f} {std_v:<15.3f} {med_v:<15.3f}")
        
    anfis_hr = data["FastLUT_ANFIS"]
    
    print("\n" + "=" * 90)
    print("PAIRED HYPOTHESIS TESTING: Fast-LUT ANFIS (Ours) vs Baselines (Alpha = 0.05)")
    print("=" * 90)
    print(f"{'Comparison':<22} {'Mean Diff':<12} {'Std Diff':<10} {'t-stat':<10} {'t p-val':<12} {'Wilcoxon W':<12} {'W p-val':<12} {'Cohen d':<10} {'Decision':<15}")
    print("-" * 115)
    
    baselines = ["LFU", "StaticFuzzy", "FIFO", "TwoQueue", "LRU", "ARC"]
    results = {}
    
    for b in baselines:
        b_hr = data[b]
        diff = anfis_hr - b_hr
        mean_d = np.mean(diff)
        std_d = np.std(diff, ddof=1)
        
        # Paired t-test
        t_stat, p_ttest = stats.ttest_rel(anfis_hr, b_hr)
        
        # Wilcoxon signed-rank test
        # zero_method='pratt' or 'wilcox'
        try:
            # Note: when diff has non-zero elements
            non_zero_diff = diff[diff != 0]
            if len(non_zero_diff) > 0:
                res_w = stats.wilcoxon(anfis_hr, b_hr)
                w_stat = res_w.statistic
                p_wilcoxon = res_w.pvalue
            else:
                w_stat, p_wilcoxon = 0.0, 1.0
        except Exception as e:
            w_stat, p_wilcoxon = float('nan'), float('nan')
            
        # Cohen's d for paired samples: mean(diff) / std(diff)
        cohen_d = mean_d / std_d if std_d > 0 else 0.0
        
        if p_wilcoxon < 0.05 and mean_d > 0:
            decision = "Reject H0 (Win)"
        elif p_wilcoxon < 0.05 and mean_d < 0:
            decision = "Reject H0 (Loss)"
        else:
            decision = "Fail to Reject (Parity)"
            
        results[b] = {
            "mean_diff": mean_d,
            "std_diff": std_d,
            "t_stat": t_stat,
            "p_ttest": p_ttest,
            "w_stat": w_stat,
            "p_wilcoxon": p_wilcoxon,
            "cohen_d": cohen_d,
            "decision": decision
        }
        
        print(f"ANFIS vs {b:<13} {mean_d:>+8.3f}%   {std_d:<10.3f} {t_stat:>8.3f}  {p_ttest:<12.4e} {w_stat:>8.1f}     {p_wilcoxon:<12.4e} {cohen_d:>7.3f}    {decision}")

    return results

if __name__ == "__main__":
    compute_statistics()
