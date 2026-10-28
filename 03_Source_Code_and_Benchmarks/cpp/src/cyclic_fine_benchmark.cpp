#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <random>
#include <map>

#include "fast_lut_anfis.hpp"

using namespace Caching;

struct ManifestEntry {
    int trace_id;
    std::string filename;
    int target_capacity;
    std::string archetype;
    int loop_length;
    double noise_pct;
    int total_requests;
    int unique_blocks;
};

std::vector<ManifestEntry> load_manifest(const std::string& path) {
    std::vector<ManifestEntry> entries;
    std::ifstream file(path);
    if (!file.is_open()) return entries;

    std::string line;
    std::getline(file, line); // header
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string token;
        ManifestEntry e;

        if (std::getline(ss, token, ',')) e.trace_id = std::stoi(token);
        if (std::getline(ss, token, ',')) e.filename = token;
        if (std::getline(ss, token, ',')) e.target_capacity = std::stoi(token);
        if (std::getline(ss, token, ',')) e.archetype = token;
        if (std::getline(ss, token, ',')) e.loop_length = std::stoi(token);
        if (std::getline(ss, token, ',')) e.noise_pct = std::stod(token);
        if (std::getline(ss, token, ',')) e.total_requests = std::stoi(token);
        if (std::getline(ss, token, ',')) e.unique_blocks = std::stoi(token);

        entries.push_back(e);
    }
    return entries;
}

std::vector<uint64_t> load_trace(const std::string& filepath) {
    std::vector<uint64_t> reqs;
    std::ifstream in(filepath);
    if (!in.is_open()) return reqs;
    uint64_t val;
    while (in >> val) reqs.push_back(val);
    return reqs;
}

int main(int argc, char* argv[]) {
    int num_traces_to_sample = 20; // 20 generated traces from bank
    if (argc > 1) {
        num_traces_to_sample = std::max(1, std::stoi(argv[1]));
    }

    std::string bank_dir = "cpp/traces/cyclic_bank/";
    std::string manifest_file = bank_dir + "cyclic_manifest.csv";

    auto manifest = load_manifest(manifest_file);
    if (manifest.empty()) {
        bank_dir = "traces/cyclic_bank/";
        manifest_file = bank_dir + "cyclic_manifest.csv";
        manifest = load_manifest(manifest_file);
    }

    if (manifest.empty()) {
        std::cerr << "Could not open manifest: " << manifest_file << "\n";
        return 1;
    }

    // Filter traces that have loop lengths relevant to C in [2, 64] (e.g., target_capacity 32 and 64)
    std::vector<ManifestEntry> candidates;
    for (const auto& m : manifest) {
        if (m.target_capacity == 32 || m.target_capacity == 64) {
            candidates.push_back(m);
        }
    }
    if (candidates.empty()) candidates = manifest;

    std::mt19937 g(20261027);
    std::shuffle(candidates.begin(), candidates.end(), g);
    size_t actual_samples = std::min(candidates.size(), static_cast<size_t>(num_traces_to_sample));
    candidates.resize(actual_samples);

    // Preload traces
    std::vector<std::pair<ManifestEntry, std::vector<uint64_t>>> traces_loaded;
    for (const auto& c : candidates) {
        std::string full_path = bank_dir + c.filename;
        auto reqs = load_trace(full_path);
        if (!reqs.empty()) {
            traces_loaded.push_back({c, std::move(reqs)});
        }
    }

    std::cout << "=========================================================================================\n";
    std::cout << "  FINE-GRAINED CAPACITY SCALING BENCHMARK FOR CYCLIC WORKLOADS (C = 2 to 64)\n";
    std::cout << "  Testing " << traces_loaded.size() << " generated cyclic trace files (25,000 requests each)\n";
    std::cout << "  Total access requests evaluated per capacity: " << (traces_loaded.size() * 25000) << "\n";
    std::cout << "=========================================================================================\n\n";

    // Fine-grained capacities from 2 to 64
    std::vector<uint64_t> capacities = {2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64};

    std::ofstream out_csv("cyclic_capacity_2_to_64.csv");
    out_csv << "capacity,policy,mean_hit_rate_pct,median_hit_rate_pct,min_hit_rate_pct,max_hit_rate_pct,avg_latency_ns\n";

    std::vector<std::string> policy_order = {"LFU", "Static-Fuzzy (Bengar '20)", "FIFO", "2Q (VLDB '94)", "LRU", "IBM-ARC", "Fast-LUT-ANFIS"};

    // Print Header
    std::cout << std::left << std::setw(12) << "Capacity (C)"
              << std::setw(12) << "LFU"
              << std::setw(14) << "StaticFuzzy"
              << std::setw(12) << "FIFO"
              << std::setw(12) << "2Q"
              << std::setw(12) << "LRU"
              << std::setw(12) << "ARC"
              << std::setw(16) << "Fast-LUT-ANFIS"
              << "\n";
    std::cout << std::string(96, '-') << "\n";

    for (uint64_t C : capacities) {
        std::map<std::string, std::vector<double>> hit_rates;
        std::map<std::string, std::vector<double>> latencies;

        for (const auto& pair : traces_loaded) {
            const auto& reqs = pair.second;

            LRUCache lru(C);
            FIFOCache fifo(C);
            LFUCache lfu(C);
            ARCCache arc(C);
            TwoQueueCache tq(C);
            StaticFuzzyCache sf(C, std::min<uint32_t>(C, 12));
            FastLutAnfisCache anfis(C, std::min<uint32_t>(C, 12));

            std::vector<BaseCache*> policies = {&lru, &fifo, &lfu, &arc, &tq, &sf, &anfis};

            for (uint64_t req : reqs) {
                for (auto* p : policies) {
                    p->access(req);
                }
            }

            for (auto* p : policies) {
                auto s = p->get_stats();
                hit_rates[s.name].push_back(s.hit_rate_pct);
                latencies[s.name].push_back(s.avg_latency_nanoseconds);
            }
        }

        std::cout << "C = " << std::left << std::setw(8) << C;

        for (const auto& pname : policy_order) {
            auto v = hit_rates[pname];
            std::sort(v.begin(), v.end());
            double mean = 0.0;
            for (double x : v) mean += x;
            mean /= v.size();
            double median = v[v.size() / 2];
            double min_v = v.front();
            double max_v = v.back();

            const auto& lats = latencies[pname];
            double avg_lat = 0.0;
            for (double l : lats) avg_lat += l;
            avg_lat /= lats.size();

            std::cout << std::right << std::setw(9) << std::fixed << std::setprecision(2) << mean << "%  ";

            out_csv << C << ","
                    << pname << ","
                    << std::fixed << std::setprecision(4) << mean << ","
                    << median << ","
                    << min_v << ","
                    << max_v << ","
                    << std::setprecision(1) << avg_lat << "\n";
        }
        std::cout << "\n";
    }

    out_csv.close();
    std::cout << std::string(96, '-') << "\n";
    std::cout << "Fine-grained sweep complete! Full telemetry saved to cyclic_capacity_2_to_64.csv\n";
    return 0;
}
