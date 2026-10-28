#include <iostream>
#include <vector>
#include <fstream>
#include <string>
#include <iomanip>
#include <algorithm>
#include "fast_lut_anfis.hpp"

using namespace Caching;

struct Trial {
    std::string name;
    std::vector<uint64_t> requests;
};

std::vector<uint64_t> read_trace_slice(const std::string& path, size_t start_idx, size_t count) {
    std::vector<uint64_t> res;
    std::ifstream infile(path);
    if (!infile.is_open()) {
        std::string alt = "cpp/" + path;
        infile.open(alt);
        if (!infile.is_open()) {
            std::cerr << "Cannot open " << path << "\n";
            return res;
        }
    }
    uint64_t val;
    size_t idx = 0;
    while (infile >> val) {
        if (idx >= start_idx && idx < start_idx + count) {
            res.push_back(val);
        }
        idx++;
        if (idx >= start_idx + count) break;
    }
    return res;
}

int main() {
    const uint64_t C = 256;
    const size_t CHUNK = 20000;

    std::vector<Trial> trials = {
        {"CloudPhysics_w01_P1", read_trace_slice("traces/cloudphysics_w01.trace", 0, CHUNK)},
        {"CloudPhysics_w01_P2", read_trace_slice("traces/cloudphysics_w01.trace", 25000, CHUNK)},
        {"CloudPhysics_w02_P1", read_trace_slice("traces/cloudphysics_w02.trace", 0, CHUNK)},
        {"CloudPhysics_w02_P2", read_trace_slice("traces/cloudphysics_w02.trace", 25000, CHUNK)},
        {"CloudPhysics_w05_P1", read_trace_slice("traces/cloudphysics_w05.trace", 0, CHUNK)},
        {"SNIA_MSR_hm0_P1",    read_trace_slice("traces/snia_msr_hm0.trace", 0, CHUNK)},
        {"SNIA_MSR_hm0_P2",    read_trace_slice("traces/snia_msr_hm0.trace", 25000, CHUNK)},
        {"UMass_Financial1_P1", read_trace_slice("traces/umass_financial1.trace", 0, CHUNK)},
        {"UMass_Financial1_P2", read_trace_slice("traces/umass_financial1.trace", 25000, CHUNK)},
        {"UMass_WebSearch1_P1", read_trace_slice("traces/umass_websearch1.trace", 0, CHUNK)}
    };

    std::ofstream out("wilcoxon_trials.csv");
    out << "trial,workload,requests,LRU,FIFO,LFU,ARC,TwoQueue,StaticFuzzy,FastLUT_ANFIS\n";

    std::cout << "Running 10 paired trials across production traces (Capacity C=" << C << ")...\n";

    for (size_t t = 0; t < trials.size(); ++t) {
        const auto& tr = trials[t];
        if (tr.requests.empty()) {
            std::cerr << "Empty trace for " << tr.name << "\n";
            continue;
        }

        LRUCache lru(C);
        FIFOCache fifo(C);
        LFUCache lfu(C);
        ARCCache arc(C);
        TwoQueueCache tq(C);
        StaticFuzzyCache sf(C);
        FastLutAnfisCache anfis(C);

        for (uint64_t req : tr.requests) {
            lru.access(req);
            fifo.access(req);
            lfu.access(req);
            arc.access(req);
            tq.access(req);
            sf.access(req);
            anfis.access(req);
        }

        double hr_lru = lru.get_stats().hit_rate_pct;
        double hr_fifo = fifo.get_stats().hit_rate_pct;
        double hr_lfu = lfu.get_stats().hit_rate_pct;
        double hr_arc = arc.get_stats().hit_rate_pct;
        double hr_tq = tq.get_stats().hit_rate_pct;
        double hr_sf = sf.get_stats().hit_rate_pct;
        double hr_anfis = anfis.get_stats().hit_rate_pct;

        out << (t + 1) << "," << tr.name << "," << tr.requests.size() << ","
            << std::fixed << std::setprecision(4)
            << hr_lru << "," << hr_fifo << "," << hr_lfu << "," << hr_arc << ","
            << hr_tq << "," << hr_sf << "," << hr_anfis << "\n";

        std::cout << "Trial " << (t + 1) << " [" << tr.name << "]: ANFIS=" << hr_anfis 
                  << "%, ARC=" << hr_arc << "%, LRU=" << hr_lru << "%, LFU=" << hr_lfu << "%\n";
    }

    out.close();
    std::cout << "Trial execution complete. Saved to wilcoxon_trials.csv\n";
    return 0;
}
