#include "fast_lut_anfis.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <random>
#include <sstream>
#include <string>
#include <vector>
#include <filesystem>

using namespace Caching;
using Clock = std::chrono::steady_clock;

struct Workload {
    std::string name;
    uint64_t seed;
    std::vector<uint64_t> requests;
    bool synthetic;
};

static std::string csvQuote(const std::string& s) {
    std::string out = "\"";
    for (char c : s) {
        if (c == '"') out += "\"\"";
        else out += c;
    }
    out += '"';
    return out;
}

static bool loadTrace(const std::string& filename, std::vector<uint64_t>& requests, size_t maxRequests = 0) {
    std::vector<std::string> candidatePaths = {
        filename,
        "cpp/traces/" + filename,
        "traces/" + filename,
        "../cpp/traces/" + filename,
        "/mnt/data/" + filename
    };
    std::ifstream in;
    for (const auto& p : candidatePaths) {
        in.open(p);
        if (in.is_open()) break;
    }
    if (!in.is_open()) return false;
    uint64_t x;
    size_t count = 0;
    while (in >> x) {
        requests.push_back(x);
        count++;
        if (maxRequests > 0 && count >= maxRequests) break;
    }
    return !requests.empty();
}

static uint64_t sampleZipf(const std::vector<double>& cdf, std::mt19937_64& rng) {
    const double u = std::generate_canonical<double, 53>(rng);
    auto it = std::lower_bound(cdf.begin(), cdf.end(), u);
    size_t idx = static_cast<size_t>(it - cdf.begin());
    if (idx >= cdf.size()) idx = cdf.size() - 1;
    return static_cast<uint64_t>(idx);
}

static std::vector<uint64_t> generateTrace(const std::string& type,
                                           uint64_t seed,
                                           size_t n,
                                           uint64_t universe = 2000) {
    std::mt19937_64 rng(seed);
    std::vector<uint64_t> out;
    out.reserve(n);
    std::uniform_int_distribution<uint64_t> uniformBlock(0, universe - 1);

    if (type == "zipfian") {
        std::vector<double> cdf(universe);
        double total = 0.0;
        for (uint64_t i = 1; i <= universe; ++i) total += 1.0 / std::pow(static_cast<double>(i), 1.05);
        double cumulative = 0.0;
        for (uint64_t i = 1; i <= universe; ++i) {
            cumulative += (1.0 / std::pow(static_cast<double>(i), 1.05)) / total;
            cdf[i - 1] = cumulative;
        }
        cdf.back() = 1.0;
        for (size_t i = 0; i < n; ++i) out.push_back(sampleZipf(cdf, rng));
    } else if (type == "uniform") {
        for (size_t i = 0; i < n; ++i) out.push_back(uniformBlock(rng));
    } else if (type == "cyclic") {
        // Repeated working set, with a small amount of deterministic-seed noise.
        const uint64_t workingSet = 128;
        std::uniform_int_distribution<int> noiseChance(0, 99);
        for (size_t i = 0; i < n; ++i) {
            if (noiseChance(rng) < 5) out.push_back(uniformBlock(rng));
            else out.push_back(static_cast<uint64_t>(i % workingSet));
        }
    } else if (type == "scan") {
        // Sequential scan through a large address range; each full pass repeats.
        for (size_t i = 0; i < n; ++i) out.push_back(static_cast<uint64_t>(i % universe));
    } else if (type == "phase_shift") {
        // Hot set changes every 2,000 requests. Some requests still hit the background.
        const size_t phaseLength = 2000;
        const uint64_t hotSize = 120;
        std::uniform_int_distribution<int> hotChance(0, 99);
        for (size_t i = 0; i < n; ++i) {
            uint64_t phase = static_cast<uint64_t>(i / phaseLength);
            uint64_t hotStart = (phase * 257) % (universe - hotSize);
            if (hotChance(rng) < 85) {
                std::uniform_int_distribution<uint64_t> hotOffset(0, hotSize - 1);
                out.push_back(hotStart + hotOffset(rng));
            } else {
                out.push_back(uniformBlock(rng));
            }
        }
    }
    return out;
}

static std::vector<std::unique_ptr<BaseCache>> makePolicies(uint64_t capacity) {
    std::vector<std::unique_ptr<BaseCache>> policies;
    policies.emplace_back(std::make_unique<LRUCache>(capacity, "LRU"));
    policies.emplace_back(std::make_unique<FIFOCache>(capacity, "FIFO"));
    policies.emplace_back(std::make_unique<LFUCache>(capacity, "LFU"));
    policies.emplace_back(std::make_unique<ARCCache>(capacity, "ARC"));
    policies.emplace_back(std::make_unique<TwoQueueCache>(capacity, "2Q"));
    policies.emplace_back(std::make_unique<StaticFuzzyCache>(capacity, 12, "StaticFuzzy"));
    policies.emplace_back(std::make_unique<FastLutAnfisCache>(capacity, 12, 0.25f, 0.65f, 0.10f, 0.04f, "FastLutAnfis"));
    return policies;
}

int main(int argc, char* argv[]) {
    // Usage: extended_cache_benchmark [seeds=20] [requests_per_synthetic_trace=10000] [output_prefix=cache_results]
    size_t seedCount = 20;
    size_t requestCount = 10000;
    std::string prefix = "cache_results";
    try {
        if (argc > 1) seedCount = std::max<size_t>(1, std::stoull(argv[1]));
        if (argc > 2) requestCount = std::max<size_t>(100, std::stoull(argv[2]));
        if (argc > 3) prefix = argv[3];
    } catch (...) {
        std::cerr << "Invalid argument. Usage: extended_cache_benchmark [seeds] [requests_per_trace] [output_prefix]\n";
        return 1;
    }

    const std::vector<uint64_t> capacities = {32, 64, 128, 256, 512};
    const std::vector<std::string> syntheticTypes = {"zipfian", "cyclic", "scan", "phase_shift"};

    struct TraceSpec {
        std::string displayName;
        std::string filename;
        size_t maxRequests;
    };

    const std::vector<TraceSpec> traceSpecs = {
        {"CloudPhysics_w01 (FAST '15)", "cloudphysics_w01.trace", 25000},
        {"CloudPhysics_w02 (FAST '15)", "cloudphysics_w02.trace", 25000},
        {"SNIA_MSR_hm0 (Enterprise)", "snia_msr_hm0.trace", 25000},
        {"UMass_Financial1 (OLTP)", "umass_financial1.trace", 25000},
        {"UMass_WebSearch1 (Search)", "umass_websearch1.trace", 25000},
        {"Cyclic_Loop (Stress)", "cyclic.trace", 0},
        {"Scan_Dominated (Sequential)", "scan.trace", 0}
    };

    std::vector<Workload> workloads;
    // Load official real-world and reference trace files
    for (const auto& spec : traceSpecs) {
        std::vector<uint64_t> trace;
        if (loadTrace(spec.filename, trace, spec.maxRequests)) {
            workloads.push_back({spec.displayName, 0, std::move(trace), false});
            std::cout << "Loaded trace: " << spec.displayName << " (" << workloads.back().requests.size() << " requests)\n";
        } else {
            std::cerr << "Warning: could not load " << spec.filename << "; skipping.\n";
        }
    }

    // Seeded synthetic workloads: independent generated sequences for paired comparisons.
    for (const auto& type : syntheticTypes) {
        for (size_t s = 0; s < seedCount; ++s) {
            const uint64_t seed = 20261027ULL + static_cast<uint64_t>(s) * 1009ULL
                                  + static_cast<uint64_t>(std::distance(syntheticTypes.begin(),
                                      std::find(syntheticTypes.begin(), syntheticTypes.end(), type))) * 1000003ULL;
            workloads.push_back({type, seed, generateTrace(type, seed, requestCount), true});
        }
    }

    const std::string resultsFile = prefix + "_results.csv";
    const std::string tracesFile = prefix + "_synthetic_traces.csv";
    std::ofstream results(resultsFile);
    std::ofstream tracesOut(tracesFile);
    if (!results || !tracesOut) {
        std::cerr << "Could not create output CSV files in the current directory.\n";
        return 1;
    }

    results << "workload,synthetic,seed,trace_length,capacity,policy,accesses,hits,misses,hit_rate_pct,avg_latency_ns,decision_time_us,wall_time_ms,unique_blocks\n";
    tracesOut << "workload,seed,request_index,block_id\n";

    const auto overallStart = Clock::now();
    size_t completed = 0;
    const size_t totalScenarios = workloads.size() * capacities.size();

    for (const auto& workload : workloads) {
        std::unordered_map<uint64_t, bool> unique;
        unique.reserve(workload.requests.size());
        for (uint64_t key : workload.requests) unique.emplace(key, true);

        if (workload.synthetic) {
            for (size_t i = 0; i < workload.requests.size(); ++i) {
                tracesOut << csvQuote(workload.name) << ',' << workload.seed << ',' << i << ',' << workload.requests[i] << '\n';
            }
        }

        for (uint64_t capacity : capacities) {
            auto policies = makePolicies(capacity);
            for (auto& policy : policies) {
                const auto wallStart = Clock::now();
                for (uint64_t key : workload.requests) policy->access(key);
                const auto wallEnd = Clock::now();
                const auto stats = policy->get_stats();
                const double wallMs = std::chrono::duration<double, std::milli>(wallEnd - wallStart).count();

                results << csvQuote(workload.name) << ','
                        << (workload.synthetic ? 1 : 0) << ','
                        << workload.seed << ','
                        << workload.requests.size() << ','
                        << capacity << ','
                        << csvQuote(stats.name) << ','
                        << stats.access_count << ','
                        << stats.hit_count << ','
                        << stats.miss_count << ','
                        << std::fixed << std::setprecision(6) << stats.hit_rate_pct << ','
                        << std::setprecision(3) << stats.avg_latency_nanoseconds << ','
                        << std::setprecision(6) << stats.total_time_microseconds << ','
                        << std::setprecision(6) << wallMs << ','
                        << unique.size() << '\n';
            }
            ++completed;
            if (completed % 10 == 0 || completed == totalScenarios) {
                std::cout << "Completed " << completed << "/" << totalScenarios
                          << " workload-capacity scenarios\r" << std::flush;
            }
        }
    }

    const double totalSeconds = std::chrono::duration<double>(Clock::now() - overallStart).count();
    std::cout << "\nFinished.\n"
              << "Workload sequences: " << workloads.size() << " ("
              << (workloads.size() - traceSpecs.size()) << " generated synthetic, "
              << traceSpecs.size() << " real/reference)\n"
              << "Capacities: 32, 64, 128, 256, 512\n"
              << "Policies: 7\n"
              << "Result rows: " << workloads.size() * capacities.size() * 7 << "\n"
              << "Elapsed time: " << std::fixed << std::setprecision(2) << totalSeconds << " seconds\n"
              << "Saved results: " << resultsFile << "\n"
              << "Saved generated request sequences: " << tracesFile << "\n"
              << "Use the results CSV for plots and paired statistical tests.\n";
    return 0;
}
