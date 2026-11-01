#pragma once

#include <iostream>
#include <vector>
#include <unordered_map>
#include <list>
#include <deque>
#include <cmath>
#include <chrono>
#include <random>
#include <algorithm>
#include <numeric>
#include <iomanip>
#include <string>
#include <cstdint>

namespace Caching {

// Cache Telemetry Statistics
struct CacheStats {
    std::string name;
    uint64_t capacity{0};
    uint64_t access_count{0};
    uint64_t hit_count{0};
    uint64_t miss_count{0};
    double hit_rate_pct{0.0};
    double total_time_microseconds{0.0};
    double avg_latency_nanoseconds{0.0};
    uint64_t ghost_hits{0};
};

// Base Cache Interface
class BaseCache {
public:
    uint64_t capacity;
    std::string name;
    uint64_t access_count{0};
    uint64_t hit_count{0};
    uint64_t miss_count{0};
    uint64_t total_decision_time_ns{0};

    BaseCache(uint64_t cap, const std::string& policy_name)
        : capacity(cap), name(policy_name) {}

    virtual ~BaseCache() = default;
    virtual bool access(uint64_t key) = 0;

    virtual CacheStats get_stats() const {
        CacheStats s;
        s.name = name;
        s.capacity = capacity;
        s.access_count = access_count;
        s.hit_count = hit_count;
        s.miss_count = miss_count;
        s.hit_rate_pct = access_count > 0 ? (100.0 * hit_count / access_count) : 0.0;
        s.total_time_microseconds = total_decision_time_ns / 1000.0;
        s.avg_latency_nanoseconds = access_count > 0 ? (static_cast<double>(total_decision_time_ns) / access_count) : 0.0;
        s.ghost_hits = 0;
        return s;
    }
};

// =========================================================================
// 1. Classical LRU Cache (Doubly Linked List + Hash Map, True O(1))
// =========================================================================
class LRUCache : public BaseCache {
private:
    std::list<uint64_t> lru_list;
    std::unordered_map<uint64_t, std::list<uint64_t>::iterator> table;

public:
    LRUCache(uint64_t cap, const std::string& policy_name = "LRU")
        : BaseCache(cap, policy_name) {}

    bool access(uint64_t key) override {
        auto t0 = std::chrono::high_resolution_clock::now();
        access_count++;

        auto it = table.find(key);
        bool is_hit = false;

        if (it != table.end()) {
            lru_list.erase(it->second);
            lru_list.push_front(key);
            table[key] = lru_list.begin();
            hit_count++;
            is_hit = true;
        } else {
            if (table.size() >= capacity) {
                uint64_t evict_key = lru_list.back();
                lru_list.pop_back();
                table.erase(evict_key);
            }
            lru_list.push_front(key);
            table[key] = lru_list.begin();
            miss_count++;
            is_hit = false;
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        total_decision_time_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
        return is_hit;
    }
};

// =========================================================================
// 2. Classical FIFO Cache (First-In First-Out, True O(1))
// =========================================================================
class FIFOCache : public BaseCache {
private:
    std::deque<uint64_t> fifo_queue;
    std::unordered_map<uint64_t, bool> in_cache;

public:
    FIFOCache(uint64_t cap, const std::string& policy_name = "FIFO")
        : BaseCache(cap, policy_name) {}

    bool access(uint64_t key) override {
        auto t0 = std::chrono::high_resolution_clock::now();
        access_count++;
        bool is_hit = (in_cache.find(key) != in_cache.end());

        if (is_hit) {
            hit_count++;
        } else {
            miss_count++;
            if (in_cache.size() >= capacity) {
                uint64_t evict = fifo_queue.front();
                fifo_queue.pop_front();
                in_cache.erase(evict);
            }
            fifo_queue.push_back(key);
            in_cache[key] = true;
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        total_decision_time_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
        return is_hit;
    }
};

// =========================================================================
// 3. Classical LFU Cache (Least Frequently Used, True O(1) via Frequency Buckets)
// =========================================================================
class LFUCache : public BaseCache {
private:
    struct LfuItem {
        uint64_t key;
        uint64_t freq;
        std::list<uint64_t>::iterator iter;
    };
    uint64_t min_freq{0};
    std::unordered_map<uint64_t, LfuItem> key_map;
    std::unordered_map<uint64_t, std::list<uint64_t>> freq_map;

public:
    LFUCache(uint64_t cap, const std::string& policy_name = "LFU")
        : BaseCache(cap, policy_name) {}

    bool access(uint64_t key) override {
        auto t0 = std::chrono::high_resolution_clock::now();
        access_count++;
        auto it = key_map.find(key);
        bool is_hit = (it != key_map.end());

        if (is_hit) {
            hit_count++;
            uint64_t f = it->second.freq;
            freq_map[f].erase(it->second.iter);
            if (freq_map[f].empty()) {
                freq_map.erase(f);
                if (min_freq == f) min_freq = f + 1;
            }
            it->second.freq = f + 1;
            freq_map[f + 1].push_front(key);
            it->second.iter = freq_map[f + 1].begin();
        } else {
            miss_count++;
            if (key_map.size() >= capacity) {
                uint64_t evict = freq_map[min_freq].back();
                freq_map[min_freq].pop_back();
                if (freq_map[min_freq].empty()) {
                    freq_map.erase(min_freq);
                }
                key_map.erase(evict);
            }
            min_freq = 1;
            freq_map[1].push_front(key);
            key_map[key] = {key, 1, freq_map[1].begin()};
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        total_decision_time_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
        return is_hit;
    }
};

// =========================================================================
// 4. IBM ARC Cache (Megiddo & Modha, USENIX FAST 2003)
// =========================================================================
class ARCCache : public BaseCache {
private:
    double p{0.0};
    std::list<uint64_t> t1_list, t2_list, b1_list, b2_list;
    std::unordered_map<uint64_t, std::list<uint64_t>::iterator> t1_map, t2_map, b1_map, b2_map;

    void replace(bool in_b2) {
        size_t len_t1 = t1_map.size();
        if (len_t1 > 0 && (len_t1 > static_cast<size_t>(p) || (in_b2 && len_t1 == static_cast<size_t>(p)))) {
            uint64_t k = t1_list.back();
            t1_list.pop_back();
            t1_map.erase(k);
            b1_list.push_front(k);
            b1_map[k] = b1_list.begin();
        } else {
            if (!t2_map.empty()) {
                uint64_t k = t2_list.back();
                t2_list.pop_back();
                t2_map.erase(k);
                b2_list.push_front(k);
                b2_map[k] = b2_list.begin();
            }
        }
    }

public:
    ARCCache(uint64_t cap, const std::string& policy_name = "IBM-ARC")
        : BaseCache(cap, policy_name) {}

    bool access(uint64_t key) override {
        auto t0 = std::chrono::high_resolution_clock::now();
        access_count++;
        bool is_hit = false;

        auto it_t1 = t1_map.find(key);
        if (it_t1 != t1_map.end()) {
            t1_list.erase(it_t1->second);
            t1_map.erase(it_t1);
            t2_list.push_front(key);
            t2_map[key] = t2_list.begin();
            hit_count++;
            is_hit = true;
        } else {
            auto it_t2 = t2_map.find(key);
            if (it_t2 != t2_map.end()) {
                t2_list.erase(it_t2->second);
                t2_list.push_front(key);
                t2_map[key] = t2_list.begin();
                hit_count++;
                is_hit = true;
            } else {
                auto it_b1 = b1_map.find(key);
                if (it_b1 != b1_map.end()) {
                    double len_b1 = static_cast<double>(b1_map.size());
                    double len_b2 = static_cast<double>(b2_map.size());
                    double delta = len_b1 == 0.0 ? 1.0 : std::max(1.0, len_b2 / len_b1);
                    p = std::min(static_cast<double>(capacity), p + delta);
                    replace(false);

                    b1_list.erase(it_b1->second);
                    b1_map.erase(it_b1);
                    t2_list.push_front(key);
                    t2_map[key] = t2_list.begin();
                    miss_count++;
                    is_hit = false;
                } else {
                    auto it_b2 = b2_map.find(key);
                    if (it_b2 != b2_map.end()) {
                        double len_b1 = static_cast<double>(b1_map.size());
                        double len_b2 = static_cast<double>(b2_map.size());
                        double delta = len_b2 == 0.0 ? 1.0 : std::max(1.0, len_b1 / len_b2);
                        p = std::max(0.0, p - delta);
                        replace(true);

                        b2_list.erase(it_b2->second);
                        b2_map.erase(it_b2);
                        t2_list.push_front(key);
                        t2_map[key] = t2_list.begin();
                        miss_count++;
                        is_hit = false;
                    } else {
                        size_t len_l1 = t1_map.size() + b1_map.size();
                        size_t len_l2 = t2_map.size() + b2_map.size();

                        if (len_l1 == capacity) {
                            if (t1_map.size() < capacity) {
                                if (!b1_list.empty()) {
                                    uint64_t b1_k = b1_list.back();
                                    b1_list.pop_back();
                                    b1_map.erase(b1_k);
                                }
                                replace(false);
                            } else {
                                if (!t1_list.empty()) {
                                    uint64_t t1_k = t1_list.back();
                                    t1_list.pop_back();
                                    t1_map.erase(t1_k);
                                }
                            }
                        } else if (len_l1 < capacity && (len_l1 + len_l2) >= capacity) {
                            if ((len_l1 + len_l2) == 2 * capacity) {
                                if (!b2_list.empty()) {
                                    uint64_t b2_k = b2_list.back();
                                    b2_list.pop_back();
                                    b2_map.erase(b2_k);
                                }
                            }
                            replace(false);
                        }

                        t1_list.push_front(key);
                        t1_map[key] = t1_list.begin();
                        miss_count++;
                        is_hit = false;
                    }
                }
            }
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        total_decision_time_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
        return is_hit;
    }
};

// =========================================================================
// 5. Exact CART Decision Tree Classifier in C++
// =========================================================================
class WorkloadClassifier {
public:
    enum Regime {
        ZIPFIAN = 0,
        SCAN = 1,
        CYCLIC = 2,
        MIXED = 3
    };

    static Regime classify(const std::deque<uint64_t>& window) {
        size_t n = window.size();
        if (n < 60) return MIXED;

        // 1. Frequency histogram and unique counts
        std::unordered_map<uint64_t, uint32_t> counts;
        counts.reserve(n);
        for (uint64_t k : window) {
            counts[k]++;
        }
        size_t unique_count = counts.size();
        double u_ratio = static_cast<double>(unique_count) / n;

        // 2. Normalized Shannon Entropy (Feat[1])
        double entropy = 0.0;
        for (const auto& pair : counts) {
            double p = static_cast<double>(pair.second) / n;
            entropy -= p * std::log2(p + 1e-12);
        }
        double max_entropy = std::log2(std::max(2.0, static_cast<double>(unique_count)));
        double f2_entropy = max_entropy > 0.0 ? (entropy / max_entropy) : 0.0;

        // 3. Autocorrelation (Feat[2])
        double mean = 0.0;
        for (uint64_t k : window) mean += k;
        mean /= n;
        double denom = 1e-9;
        for (uint64_t k : window) {
            double d = static_cast<double>(k) - mean;
            denom += d * d;
        }
        double max_corr = 0.0;
        const size_t lags[] = {10, 20, 40, 80};
        for (size_t lag : lags) {
            if (lag < n / 2) {
                double num = 0.0;
                for (size_t i = 0; i < n - lag; ++i) {
                    num += (static_cast<double>(window[i]) - mean) * (static_cast<double>(window[i + lag]) - mean);
                }
                double corr = num / denom;
                if (corr > max_corr) max_corr = corr;
            }
        }
        double f3_autocorr = std::clamp(max_corr, 0.0, 1.0);

        if (f2_entropy <= 0.8356) {
            return ZIPFIAN; // Class 0 (Heavy temporal locality)
        } else {
            if (f2_entropy <= 0.9496) {
                if (f3_autocorr <= 0.0734) {
                    return SCAN; // Class 1 (Sequential scans)
                } else {
                    return (f2_entropy <= 0.9095) ? MIXED : SCAN;
                }
            } else {
                // High entropy: check unique ratio hedge
                if (u_ratio <= 0.50) {
                    return CYCLIC; // Class 2 (Repeating cyclic loop with capacity thrashing)
                } else {
                    return ZIPFIAN; // High-entropy random access
                }
            }
        }
    }
};

// =========================================================================
// =========================================================================
// =========================================================================
// 6. Tri-Input Fast-LUT ANFIS Cache in High-Performance C++
// =========================================================================
class FastLutAnfisCache : public BaseCache {
public:
    struct Entry {
        uint64_t last_access{0};
        uint32_t frequency{0};
        uint64_t arrival_time{0};
    };

    struct GhostEntry {
        float score{0.0f};
    };

private:
    uint32_t candidate_sample_size{12};
    float w_lru{0.25f};
    float w_lfu{0.65f};
    float w_fifo{0.10f};
    float lr{0.04f};
    float W{200.0f};
    float inv_W{0.005f};

    // 6 Precomputed 256-Point Look-Up Tables (1 KB each = 6 KB L1 Data Cache)
    alignas(64) float lut_rl[256];
    alignas(64) float lut_rm[256];
    alignas(64) float lut_rh[256];
    alignas(64) float lut_fl[256];
    alignas(64) float lut_fm[256];
    alignas(64) float lut_fh[256];

    // 8 Takagi-Sugeno Consequents
    float consequents[8] = {0.05f, 0.30f, 0.60f, 0.40f, 0.55f, 0.75f, 0.70f, 0.95f};
    const float default_consequents[8] = {0.05f, 0.30f, 0.60f, 0.40f, 0.55f, 0.75f, 0.70f, 0.95f};

    // Cache Storage
    std::unordered_map<uint64_t, Entry> cache;
    std::vector<uint64_t> keys_list;
    std::vector<size_t> pool_indices;

    // FIFO Ghost Cache
    uint64_t ghost_capacity;
    std::list<uint64_t> ghost_list;
    std::unordered_map<uint64_t, std::pair<GhostEntry, std::list<uint64_t>::iterator>> ghost_map;
    uint64_t ghost_hits{0};

    // Sliding-window history for CART regime classification
    std::deque<uint64_t> history_trace;
    WorkloadClassifier::Regime current_regime{WorkloadClassifier::MIXED};

    std::mt19937 rng{42};

    // Phase 0: Precompute Gaussian Membership Functions at Boot-Up
    void init_luts() {
        for (int i = 0; i < 256; ++i) {
            float x = static_cast<float>(i) / 255.0f;
            auto gauss = [](float val, float m, float s) -> float {
                float diff = (val - m) / s;
                return std::exp(-0.5f * diff * diff);
            };
            lut_rl[i] = gauss(x, 0.15f, 0.15f);
            lut_rm[i] = gauss(x, 0.50f, 0.15f);
            lut_rh[i] = gauss(x, 0.85f, 0.15f);

            lut_fl[i] = gauss(x, 0.15f, 0.15f);
            lut_fm[i] = gauss(x, 0.50f, 0.15f);
            lut_fh[i] = gauss(x, 0.85f, 0.15f);
        }
    }

public:
    FastLutAnfisCache(
        uint64_t cap,
        uint32_t cand_size = 12,
        float wlru = 0.25f,
        float wlfu = 0.65f,
        float wfifo = 0.10f,
        float learning_rate = 0.04f,
        const std::string& policy_name = "Fast-LUT-ANFIS"
    ) : BaseCache(cap, policy_name),
        candidate_sample_size(std::min(static_cast<uint32_t>(cap), cand_size)),
        w_lru(wlru), w_lfu(wlfu), w_fifo(wfifo), lr(learning_rate),
        ghost_capacity(cap) {
        
        W = std::max(200.0f, static_cast<float>(cap) * 4.0f);
        inv_W = 1.0f / W;
        keys_list.reserve(cap);
        pool_indices.resize(cap);
        std::iota(pool_indices.begin(), pool_indices.end(), 0);
        cache.reserve(cap * 2);
        init_luts();
    }

    bool access(uint64_t key) override {
        auto t0 = std::chrono::high_resolution_clock::now();
        access_count++;

        // Phase 1: Request Registration & Sliding Window History (N=250)
        history_trace.push_back(key);
        if (history_trace.size() > 250) {
            history_trace.pop_front();
        }

        // Periodic CART Regime Classification (Every 250 accesses)
        if (access_count % 250 == 0 && history_trace.size() >= 120) {
            current_regime = WorkloadClassifier::classify(history_trace);
        }

        bool is_hit = false;
        auto it = cache.find(key);

        // Phase 2: Fast-Path Cache Hit Servicing (5-15 ns)
        if (it != cache.end()) {
            it->second.last_access = access_count;
            it->second.frequency++;
            hit_count++;
            is_hit = true;
        } else {
            // Phase 3: Ghost Cache Hit & Online Widrow-Hoff LMS Step (~15 ns)
            auto git = ghost_map.find(key);
            if (git != ghost_map.end()) {
                ghost_hits++;
                float ghost_score = git->second.first.score;
                ghost_list.erase(git->second.second);
                ghost_map.erase(git);

                float err = 1.0f - ghost_score;
                float step = lr * err * 0.125f;
                const float decay = 0.002f;

                for (int i = 0; i < 8; ++i) {
                    float c = (1.0f - decay) * consequents[i] + decay * default_consequents[i] + step;
                    consequents[i] = std::clamp(c, 0.05f, 0.95f);
                }
            }

            if (cache.size() >= capacity) {
                float curr_t = static_cast<float>(access_count);
                size_t n = keys_list.size();
                size_t num_cands = std::min(static_cast<size_t>(candidate_sample_size), n);

                size_t best_ci = 0;
                float min_score = 1e9f;
                bool is_cyclic = (current_regime == WorkloadClassifier::CYCLIC);
                bool is_scan = (current_regime == WorkloadClassifier::SCAN);

                // Phase 5: Eviction Tournament (Partial Fisher-Yates, K=12)
                for (size_t i = 0; i < num_cands; ++i) {
                    size_t j = i + (rng() % (n - i));
                    std::swap(pool_indices[i], pool_indices[j]);
                    size_t ci = pool_indices[i];

                    uint64_t cand_k = keys_list[ci];
                    const auto& meta = cache[cand_k];

                    // Phase 6: Tri-Input Metric Extraction & Normalization
                    float delta_r = curr_t - static_cast<float>(meta.last_access);
                    float r = std::clamp(1.0f - delta_r * inv_W, 0.0f, 1.0f);
                    float f = std::clamp(static_cast<float>(meta.frequency) * 0.05f, 0.0f, 1.0f);
                    float delta_fifo = curr_t - static_cast<float>(meta.arrival_time);
                    float fifo_age = std::clamp(1.0f - delta_fifo * inv_W, 0.0f, 1.0f);

                    // Phase 7: Linguistic Hedge Modulation (Cyclic / Scan Hedges)
                    if (is_cyclic) {
                        r = 1.0f - r;
                        fifo_age = 1.0f - fifo_age;
                    } else if (is_scan) {
                        f = std::min(1.0f, f * 1.5f);
                        r *= 0.5f;
                        fifo_age *= 0.5f;
                    }

                    // Phase 8: Signal Synthesis & Discrete Quantization ([0, 255])
                    float r_eff = w_lru * r + w_fifo * fifo_age;
                    float f_eff = w_lfu * f;

                    int ir = std::clamp(static_cast<int>((r_eff / 0.35f) * 255.0f), 0, 255);
                    int ifr = std::clamp(static_cast<int>((f_eff / 0.65f) * 255.0f), 0, 255);

                    // Phase 9: ANFIS Layer 1 - Fuzzification (6.0 KB LUT Lookup)
                    float rl = lut_rl[ir], rm = lut_rm[ir], rh = lut_rh[ir];
                    float fl = lut_fl[ifr], fm = lut_fm[ifr], fh = lut_fh[ifr];

                    // Phase 10: ANFIS Layer 2 - Rule Conjunctions (T-Norm Product)
                    float w0 = rl * fl, w1 = rl * fm, w2 = rl * fh;
                    float w3 = rm * fl, w4 = rm * fm, w5 = rm * fh;
                    float w6 = rh * fl, w7 = rh * fh;

                    // Phase 11: ANFIS Layers 3, 4 & 5 - Normalization & Defuzzification
                    float w_sum = w0 + w1 + w2 + w3 + w4 + w5 + w6 + w7 + 1e-6f;
                    float score = (
                        w0 * consequents[0] + w1 * consequents[1] + w2 * consequents[2] +
                        w3 * consequents[3] + w4 * consequents[4] + w5 * consequents[5] +
                        w6 * consequents[6] + w7 * consequents[7]
                    ) / w_sum;

                    if (score < min_score) {
                        min_score = score;
                        best_ci = ci;
                    }
                }

                // Phase 12: Victim Eviction & Ghost Migration
                uint64_t evict_key = keys_list[best_ci];

                if (ghost_map.size() >= ghost_capacity) {
                    uint64_t old_ghost = ghost_list.back();
                    ghost_list.pop_back();
                    ghost_map.erase(old_ghost);
                }
                ghost_list.push_front(evict_key);
                ghost_map[evict_key] = {{min_score}, ghost_list.begin()};

                cache.erase(evict_key);
                keys_list[best_ci] = key;
                cache[key] = {access_count, 1, access_count};
            } else {
                // Phase 4: Cold Direct Insertion (Cache Not Full)
                keys_list.push_back(key);
                cache[key] = {access_count, 1, access_count};
            }

            miss_count++;
            is_hit = false;
        }

        auto t1 = std::chrono::high_resolution_clock::now();
        total_decision_time_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
        return is_hit;
    }

    CacheStats get_stats() const override {
        CacheStats s = BaseCache::get_stats();
        s.ghost_hits = ghost_hits;
        return s;
    }
};

} // namespace FastCache
