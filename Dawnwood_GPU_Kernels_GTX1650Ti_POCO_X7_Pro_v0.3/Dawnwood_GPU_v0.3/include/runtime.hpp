#pragma once
#include "numeric.hpp"
#include <memory>
#include <string>
#include <vector>
#include <functional>
struct Snapshot {Config cfg{};std::vector<State> states;std::vector<Operator> ops;};
Config default_config(uint count=256,uint operators=31);
void validate_config(const Config&);
void validate_snapshot(const Snapshot&,bool statesRequired=true);
void validate_state(const State&,uint,const Config&);
State initialize_state(Config,uint);
Snapshot initialize(Config,bool includeStates=true);
void cpu_step(Snapshot&);
class VulkanRuntime {
 struct Impl;std::unique_ptr<Impl> p;
public:
 explicit VulkanRuntime(const Snapshot&,const std::string& device="",bool allowSoftware=false,float budgetFraction=0.8f,bool streamInitialization=false);
 ~VulkanRuntime();VulkanRuntime(const VulkanRuntime&)=delete;VulkanRuntime& operator=(const VulkanRuntime&)=delete;
 void advance(uint steps);Snapshot download();std::string device_json()const;double last_seconds()const;bool software()const;
 Snapshot download_metadata();
 void visit_states(const std::function<void(const State*,uint,uint)>&);
};
std::string execute(const std::vector<std::string>& args);
std::string json_escape(const std::string&);
