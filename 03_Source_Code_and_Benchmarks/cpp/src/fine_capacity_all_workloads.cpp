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

std::vector<uint64_t> load_trace_file(const std::string& path, size_t max_reqs = 25000) {
    std::vector<uint64_t> reqs;
    std::vector<std::string> candidates = {path, "cpp/traces/" + path, "traces/" + path};
    std::ifstream in;
    for (const auto& c : candidates) {
        in.open(c);
        if (in.is_open()) break;
    }
    if (!in.is_open()) return reqs;

    uint64_t val;
    size_t count = 0;
    while (in >> val) {
        reqs.push_back(val);
        count++;
        if (max_reqs > 0 && count >= max_reqs) break;
    }
    return reqs;
}

std::vector<std::string> get_manifest_traces(const std::string& manifest_path, int target_cap, size_t num_samples) {
    std::vector<std::string> files;
    std::ifstream in(manifest_path);
    if (!in.is_open()) return files;

    std::string line;
    std::getline(in, line); // header
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string token;
        std::string fname;
        int tcap = 0;
        if (std::getline(ss, token, ',')) {} // id
        if (std::getline(ss, fname, ',')) {}
        if (std::getline(ss, token, ',')) tcap = std::stoi(token);

        if (tcap == target_cap || tcap == 32 || tcap == 64) {
            files.push_back(fname);
        }
    }
    std::mt19937 g(20261027);
    std::shuffle(files.begin(), files.end(), g);
    if (files.size() > num_samples) files.resize(num_samples);
    return files;
}

struct WorkloadCategory {
    std::string name;
    std::string csv_filename;
    std::vector<std::pair<std::string, std::vector<uint64_t>>> traces;
};

void run_suite_for_category(WorkloadCategory& suite, const std::vector<uint64_t>& capacities) {
    std::cout << "\n=========================================================================================\n";
    std::cout << " WORKLOAD SUITE: " << suite.name << "\n";
    std::cout << " Traces evaluated: " << suite.traces.size() << " distinct traces (including static files)\n";
    std::cout << " Capacities: C = 2 to 64 (17 discrete evaluation points)\n";
    std::cout << " Policies: Clean 5 Core Baselines (LFU, FIFO, LRU, ARC, Fast-LUT-ANFIS)\n";
    std::cout << "=========================================================================================\n\n";

    std::cout << std::left << std::setw(12) << "Capacity"
              << std::setw(11) << "LFU"
              << std::setw(11) << "FIFO"
              << std::setw(11) << "LRU"
              << std::setw(11) << "ARC"
              << std::setw(16) << "Fast-LUT-ANFIS"
              << std::setw(15) << "Adv vs ARC"
              << std::setw(15) << "Adv vs LRU"
              << "\n";
    std::cout << std::string(96, '-') << "\n";

    std::ofstream out_csv(suite.csv_filename);
    out_csv << "capacity,LFU,FIFO,LRU,ARC,FastLUT_ANFIS,Gain_vs_ARC,Gain_vs_LRU\n";

    std::vector<std::string> policy_names = {"LFU", "FIFO", "LRU", "IBM-ARC", "Fast-LUT-ANFIS"};

    for (uint64_t C : capacities) {
        std::map<std::string, double> sum_hit_rates;

        for (const auto& trace_pair : suite.traces) {
            const auto& reqs = trace_pair.second;

            LFUCache lfu(C);
            FIFOCache fifo(C);
            LRUCache lru(C);
            ARCCache arc(C);
            FastLutAnfisCache anfis(C, std::min<uint32_t>(C, 12));

            std::vector<BaseCache*> policies = {&lfu, &fifo, &lru, &arc, &anfis};
            for (uint64_t req : reqs) {
                for (auto* p : policies) p->access(req);
            }

            for (auto* p : policies) {
                sum_hit_rates[p->get_stats().name] += p->get_stats().hit_rate_pct;
            }
        }

        size_t N = suite.traces.size();
        double lfu_mean = sum_hit_rates["LFU"] / N;
        double fifo_mean = sum_hit_rates["FIFO"] / N;
        double lru_mean = sum_hit_rates["LRU"] / N;
        double arc_mean = sum_hit_rates["IBM-ARC"] / N;
        double anfis_mean = sum_hit_rates["Fast-LUT-ANFIS"] / N;

        double gain_arc = anfis_mean - arc_mean;
        double gain_lru = anfis_mean - lru_mean;

        std::cout << "C = " << std::left << std::setw(8) << C
                  << std::right << std::setw(8) << std::fixed << std::setprecision(2) << lfu_mean << "%  "
                  << std::setw(8) << fifo_mean << "%  "
                  << std::setw(8) << lru_mean << "%  "
                  << std::setw(8) << arc_mean << "%  "
                  << std::setw(12) << anfis_mean << "%  "
                  << std::setw(11) << (gain_arc >= 0 ? "+" : "") << gain_arc << "%  "
                  << std::setw(11) << (gain_lru >= 0 ? "+" : "") << gain_lru << "%\n";

        out_csv << C << ","
                << std::fixed << std::setprecision(4)
                << lfu_mean << ","
                << fifo_mean << ","
                << lru_mean << ","
                << arc_mean << ","
                << anfis_mean << ","
                << gain_arc << ","
                << gain_lru << "\n";
    }

    out_csv.close();
    std::cout << std::string(96, '-') << "\n";
    std::cout << "Saved: " << suite.csv_filename << "\n";
}

int main() {
    const std::vector<uint64_t> capacities = {2, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64};

    // 1. ZIPFIAN LOCALITY SUITE (Static websearch.trace + 10 Zipfian bank traces)
    WorkloadCategory zipf_suite;
    zipf_suite.name = "Zipfian Locality & WebSearch Suite";
    zipf_suite.csv_filename = "fine_capacity_zipfian.csv";
    zipf_suite.traces.push_back({"static_websearch.trace", load_trace_file("websearch.trace", 25000)});
    zipf_suite.traces.push_back({"static_umass_websearch1.trace", load_trace_file("umass_websearch1.trace", 25000)});
    auto zipf_files = get_manifest_traces("cpp/traces/zipfian_bank/zipfian_manifest.csv", 32, 8);
    for (const auto& f : zipf_files) {
        zipf_suite.traces.push_back({f, load_trace_file("cpp/traces/zipfian_bank/" + f, 25000)});
    }

    // 2. DYNAMIC PHASE SHIFTING SUITE (Static phase_shift.trace + 10 Phase-shift bank traces)
    WorkloadCategory phase_suite;
    phase_suite.name = "Dynamic Phase-Shifting Suite";
    phase_suite.csv_filename = "fine_capacity_phaseshift.csv";
    phase_suite.traces.push_back({"static_phase_shift.trace", load_trace_file("phase_shift.trace", 25000)});
    auto phase_files = get_manifest_traces("cpp/traces/phase_shift_bank/phase_shift_manifest.csv", 32, 9);
    for (const auto& f : phase_files) {
        phase_suite.traces.push_back({f, load_trace_file("cpp/traces/phase_shift_bank/" + f, 25000)});
    }

    // 3. SCAN-DOMINATED SUITE (Static scan.trace + 10 Scan bank traces)
    WorkloadCategory scan_suite;
    scan_suite.name = "Scan-Dominated Sequential Suite";
    scan_suite.csv_filename = "fine_capacity_scandominated.csv";
    scan_suite.traces.push_back({"static_scan.trace", load_trace_file("scan.trace", 25000)});
    auto scan_files = get_manifest_traces("cpp/traces/scan_bank/scan_manifest.csv", 32, 9);
    for (const auto& f : scan_files) {
        scan_suite.traces.push_back({f, load_trace_file("cpp/traces/scan_bank/" + f, 25000)});
    }

    // 4. REAL FINANCIAL OLTP SUITE (Static financial.trace + Real UMass Financial1)
    WorkloadCategory fin_suite;
    fin_suite.name = "Real Financial OLTP Database Suite";
    fin_suite.csv_filename = "fine_capacity_financial.csv";
    fin_suite.traces.push_back({"static_financial.trace", load_trace_file("financial.trace", 25000)});
    fin_suite.traces.push_back({"static_umass_financial1_chunk1.trace", load_trace_file("umass_financial1.trace", 25000)});

    run_suite_for_category(zipf_suite, capacities);
    run_suite_for_category(phase_suite, capacities);
    run_suite_for_category(scan_suite, capacities);
    run_suite_for_category(fin_suite, capacities);

    return 0;
}
