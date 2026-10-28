#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <random>
#include <map>
#include <chrono>

#include "fast_lut_anfis.hpp"

using namespace Caching;

struct ScanManifestEntry {
    int trace_id;
    std::string filename;
    int target_capacity;
    std::string archetype;
    int hot_size;
    double scan_pct;
    int total_requests;
    int unique_blocks;
};

std::vector<ScanManifestEntry> load_scan_manifest(const std::string& path) {
    std::vector<ScanManifestEntry> entries;
    std::ifstream file(path);
    if (!file.is_open()) return entries;

    std::string line;
    std::getline(file, line); // skip header
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string token;
        ScanManifestEntry e;

        if (std::getline(ss, token, ',')) e.trace_id = std::stoi(token);
        if (std::getline(ss, token, ',')) e.filename = token;
        if (std::getline(ss, token, ',')) e.target_capacity = std::stoi(token);
        if (std::getline(ss, token, ',')) e.archetype = token;
        if (std::getline(ss, token, ',')) e.hot_size = std::stoi(token);
        if (std::getline(ss, token, ',')) e.scan_pct = std::stod(token);
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
    int samples_per_capacity = 20; // default 20 randomly chosen files per capacity
    if (argc > 1) {
        samples_per_capacity = std::max(1, std::stoi(argv[1]));
    }

    std::string bank_dir = "cpp/traces/scan_bank/";
    std::string manifest_file = bank_dir + "scan_manifest.csv";

    auto manifest = load_scan_manifest(manifest_file);
    if (manifest.empty()) {
        bank_dir = "traces/scan_bank/";
        manifest_file = bank_dir + "scan_manifest.csv";
        manifest = load_scan_manifest(manifest_file);
    }

    if (manifest.empty()) {
        std::cerr << "Could not open scan_manifest.csv in " << bank_dir << "\n";
        return 1;
    }

    std::cout << "=========================================================================================\n";
    std::cout << "  MASS SCAN-DOMINATED BENCHMARK: 1,000 DIVERSE TRACES (25,000 REQUESTS EACH)\n";
    std::cout << "  Randomly sampling " << samples_per_capacity << " traces per capacity for C in {32, 64, 128, 256, 512}\n";
    std::cout << "=========================================================================================\n\n";

    std::vector<uint64_t> capacities = {32, 64, 128, 256, 512};
    std::mt19937 g(20261027);

    std::ofstream out_csv("scan_mass_results.csv");
    out_csv << "trace_id,filename,capacity,archetype,hot_size,scan_pct,policy,hit_rate_pct,hits,misses,avg_latency_ns\n";

    for (uint64_t C : capacities) {
        std::vector<ScanManifestEntry> cap_entries;
        for (const auto& m : manifest) {
            if (m.target_capacity == static_cast<int>(C)) {
                cap_entries.push_back(m);
            }
        }

        if (cap_entries.empty()) {
            cap_entries = manifest;
        }

        std::shuffle(cap_entries.begin(), cap_entries.end(), g);
        size_t num_to_test = std::min(cap_entries.size(), static_cast<size_t>(samples_per_capacity));

        std::cout << ">>> Running Evaluation for Capacity C = " << C 
                  << " across " << num_to_test << " randomly chosen traces (" 
                  << (num_to_test * 25000) << " requests per policy)...\n";

        std::map<std::string, std::vector<double>> policy_hit_rates;
        std::map<std::string, std::vector<double>> policy_latencies;

        for (size_t i = 0; i < num_to_test; ++i) {
            const auto& entry = cap_entries[i];
            std::string full_path = bank_dir + entry.filename;
            auto requests = load_trace(full_path);
            if (requests.empty()) {
                std::cerr << "Warning: empty trace " << full_path << "\n";
                continue;
            }

            LRUCache lru(C);
            FIFOCache fifo(C);
            LFUCache lfu(C);
            ARCCache arc(C);
            TwoQueueCache tq(C);
            StaticFuzzyCache sf(C, 12);
            FastLutAnfisCache anfis(C, 12);

            std::vector<BaseCache*> policies = {&lru, &fifo, &lfu, &arc, &tq, &sf, &anfis};

            for (uint64_t req : requests) {
                for (auto* p : policies) {
                    p->access(req);
                }
            }

            for (auto* p : policies) {
                auto s = p->get_stats();
                policy_hit_rates[s.name].push_back(s.hit_rate_pct);
                policy_latencies[s.name].push_back(s.avg_latency_nanoseconds);

                out_csv << entry.trace_id << ","
                        << entry.filename << ","
                        << C << ","
                        << entry.archetype << ","
                        << entry.hot_size << ","
                        << entry.scan_pct << ","
                        << s.name << ","
                        << std::fixed << std::setprecision(4) << s.hit_rate_pct << ","
                        << s.hit_count << ","
                        << s.miss_count << ","
                        << std::setprecision(1) << s.avg_latency_nanoseconds << "\n";
            }
        }

        std::cout << "\n-----------------------------------------------------------------------------------------\n";
        std::cout << " SUMMARY TELEMETRY FOR CAPACITY C = " << C << " (Across " << num_to_test << " Random Traces)\n";
        std::cout << "-----------------------------------------------------------------------------------------\n";
        std::cout << std::left 
                  << std::setw(22) << "Policy"
                  << std::setw(18) << "Mean Hit Rate (%)"
                  << std::setw(16) << "Median (%)"
                  << std::setw(16) << "Min (%)"
                  << std::setw(16) << "Max (%)"
                  << std::setw(16) << "Avg Latency (ns)"
                  << "\n";
        std::cout << "-----------------------------------------------------------------------------------------\n";

        for (const auto& pair : policy_hit_rates) {
            auto v = pair.second;
            std::sort(v.begin(), v.end());
            double mean = 0.0;
            for (double x : v) mean += x;
            mean /= v.size();
            double median = v[v.size() / 2];
            double min_v = v.front();
            double max_v = v.back();

            const auto& lats = policy_latencies[pair.first];
            double avg_lat = 0.0;
            for (double l : lats) avg_lat += l;
            avg_lat /= lats.size();

            std::cout << std::left 
                      << std::setw(22) << pair.first
                      << std::setw(18) << std::fixed << std::setprecision(2) << mean
                      << std::setw(16) << std::fixed << std::setprecision(2) << median
                      << std::setw(16) << std::fixed << std::setprecision(2) << min_v
                      << std::setw(16) << std::fixed << std::setprecision(2) << max_v
                      << std::setw(16) << std::fixed << std::setprecision(1) << avg_lat
                      << "\n";
        }
        std::cout << "-----------------------------------------------------------------------------------------\n\n";
    }

    out_csv.close();
    std::cout << "Evaluation complete. All individual trial rows saved to scan_mass_results.csv\n";
    return 0;
}
