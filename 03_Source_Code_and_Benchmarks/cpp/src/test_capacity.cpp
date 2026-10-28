#include <iostream>
#include <vector>
#include <fstream>
#include <iomanip>
#include "fast_lut_anfis.hpp"

using namespace Caching;

int main() {
    std::string path = "traces/cloudphysics_w02.trace";
    std::ifstream infile(path);
    if (!infile.is_open()) {
        infile.open("cpp/" + path);
    }
    std::vector<uint64_t> requests;
    uint64_t val;
    while (infile >> val) requests.push_back(val);
    
    std::cout << "========================================================================================\n";
    std::cout << "  CLOUDPHYSICS VMWARE (w02) CAPACITY SCALING EVALUATION (50,000 REQUESTS)\n";
    std::cout << "========================================================================================\n\n";
    
    std::vector<uint64_t> capacities = {32, 64, 128, 256, 512};
    
    std::cout << std::left 
              << std::setw(12) << "Capacity"
              << std::setw(14) << "LRU (%)"
              << std::setw(14) << "FIFO (%)"
              << std::setw(14) << "LFU (%)"
              << std::setw(14) << "ARC (%)"
              << std::setw(14) << "2Q (%)"
              << std::setw(16) << "ANFIS (Ours %)"
              << std::setw(16) << "ANFIS Lat (ns)"
              << "\n";
    std::cout << "----------------------------------------------------------------------------------------\n";
    
    for (uint64_t C : capacities) {
        LRUCache lru(C);
        FIFOCache fifo(C);
        LFUCache lfu(C);
        ARCCache arc(C);
        TwoQueueCache twoq(C);
        FastLutAnfisCache anfis(C, 12, 0.25f, 0.65f, 0.10f, 0.04f, "Fast-LUT-ANFIS");
        
        for (uint64_t r : requests) {
            lru.access(r);
            fifo.access(r);
            lfu.access(r);
            arc.access(r);
            twoq.access(r);
            anfis.access(r);
        }
        
        std::cout << std::left
                  << std::setw(12) << C
                  << std::setw(14) << std::fixed << std::setprecision(2) << lru.get_stats().hit_rate_pct
                  << std::setw(14) << std::fixed << std::setprecision(2) << fifo.get_stats().hit_rate_pct
                  << std::setw(14) << std::fixed << std::setprecision(2) << lfu.get_stats().hit_rate_pct
                  << std::setw(14) << std::fixed << std::setprecision(2) << arc.get_stats().hit_rate_pct
                  << std::setw(14) << std::fixed << std::setprecision(2) << twoq.get_stats().hit_rate_pct
                  << std::setw(16) << std::fixed << std::setprecision(2) << anfis.get_stats().hit_rate_pct
                  << std::setw(16) << std::fixed << std::setprecision(1) << anfis.get_stats().avg_latency_nanoseconds
                  << "\n";
    }
    return 0;
}
