// DWI-RESIDENT-0.1 resident definition-selection and epoch transaction runtime.
// Existing N1/D1 State, Operator, Config and checkpoint ABIs are unchanged.
#include "resident.inc"
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <map>
#include <set>
#include <chrono>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif

namespace {
using Clock=std::chrono::steady_clock;
static_assert(sizeof(float)==4&&sizeof(uint)==4,"XIR requires FP32 and uint32");
static_assert(std::numeric_limits<float>::is_iec559,"XIR requires IEEE-754 float");
constexpr char residentMagic[8]={'D','W','R','D','0','0','0','1'};
constexpr uint exactLimit=16777215u,targetSelector=UINT32_MAX;
struct Function {uint code,outputs,instructions,inputs,width,signature;};
struct Program {
 std::vector<uint> config,images;
 std::vector<Function> functions;
 std::map<uint,std::pair<uint,uint>> signatures;
 uint count=0,records=0,stateWidth=0,heapWords=0,mutationSteps=0,actionSteps=0;
 uint heapOffset=0,mutationOffset=0,actionOffset=0,stride=0;
};
struct Result {
 std::vector<uint> images;
 std::string device="CPU",deviceType="cpu";
 uint vendorId=0,deviceId=0,driverVersion=0,apiVersion=0;
 bool validationEnabled=false,allBuffersDeviceLocal=false;
 uint validationErrors=0,validationWarnings=0;
 uint64_t uploadBytes=0,downloadBytes=0,dispatches=0,submissions=0;
 double executionSeconds=0;
};
double elapsed(Clock::time_point start){return std::chrono::duration<double>(Clock::now()-start).count();}
bool finite(float value){return (dw_float_bits(value)&0x7f800000u)!=0x7f800000u;}
std::string lower(std::string value){for(char& c:value)c=char(std::tolower(static_cast<unsigned char>(c)));return value;}
std::string json_string(const std::string& value){
 std::ostringstream out;out<<'"';
 for(unsigned char c:value){
  if(c=='"'||c=='\\')out<<'\\'<<char(c);
  else if(c<32)out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;
  else out<<char(c);
 }
 out<<'"';return out.str();
}
void read_exact(std::ifstream& in,void* data,uint64_t bytes){
 if(bytes>uint64_t(std::numeric_limits<std::streamsize>::max()))throw std::runtime_error("Input exceeds stream size limit");
 if(bytes&&!in.read(static_cast<char*>(data),std::streamsize(bytes)))throw std::runtime_error("Truncated input payload");
}
void write_exact(std::ofstream& out,const void* data,uint64_t bytes){
 if(bytes>uint64_t(std::numeric_limits<std::streamsize>::max()))throw std::runtime_error("Output exceeds stream size limit");
 if(bytes&&!out.write(static_cast<const char*>(data),std::streamsize(bytes)))throw std::runtime_error("Could not write output payload");
}

void ensure(bool condition,const std::string& message){if(!condition)throw std::runtime_error(message);}
void range(uint begin,uint width,uint limit,const std::string& where,bool allowEmpty=false){ensure((allowEmpty||width>0)&&uint64_t(begin)+width<=limit,where+": range outside bounds");}
void validate_function(const Program& p,const Function& f,uint ordinal){
 const std::string where="Function "+std::to_string(ordinal);
 ensure(f.instructions>=1&&f.instructions<=256,where+": instruction count must be 1..256");
 ensure(f.inputs<=64&&f.width>=1&&f.width<=32,where+": invalid input/output width");
 ensure(f.signature!=0,where+": signature must be positive");
 ensure(uint64_t(f.code)+uint64_t(f.instructions)*4u<=p.heapWords,where+": code range outside heap");
 ensure(uint64_t(f.outputs)+f.width<=p.heapWords,where+": output registers outside heap");
 for(uint i=0;i<f.instructions;++i){
  const uint* words=p.config.data()+p.heapOffset+f.code+4u*i;uint op=words[0],a=words[1],b=words[2],c=words[3];
  const std::string at=where+" instruction "+std::to_string(i);ensure(op<=17,at+": unknown XIR opcode");
  if(op==0){ensure(finite(dw_bits_float(a)),at+": nonfinite constant");ensure(!b&&!c,at+": unused operands must be zero");}
  else if(op==1){ensure(a<f.inputs,at+": invalid input column");ensure(!b&&!c,at+": unused operands must be zero");}
  else {
   ensure(a<i,at+": operand a is not a back-reference");bool binary=op==2||op==3||op==4||op==5||op==11||op==12||op==15;
   if(binary||op==16)ensure(b<i,at+": operand b is not a back-reference");else ensure(!b,at+": unused b must be zero");
   if(op==16)ensure(c<i,at+": operand c is not a back-reference");else ensure(!c,at+": unused c must be zero");
  }
 }
 for(uint i=0;i<f.width;++i)ensure(p.config[p.heapOffset+f.outputs+i]<f.instructions,where+": output register outside program");
}
void validate_plan(const Program& p,bool mutation){
 uint steps=mutation?p.mutationSteps:p.actionSteps,offset=mutation?p.mutationOffset:p.actionOffset;
 std::array<bool,256> initialized{};std::array<bool,64> written{};
 auto read=[&](uint first,uint width,const std::string& at,bool empty=false){range(first,width,256,at,empty);for(uint j=0;j<width;++j)ensure(initialized[first+j],at+": uninitialized frame read at "+std::to_string(first+j));};
 auto write=[&](uint first,uint width,const std::string& at){range(first,width,256,at);for(uint j=0;j<width;++j)initialized[first+j]=true;};
 for(uint step=0;step<steps;++step){
  const uint* w=p.config.data()+offset+8u*step;uint op=w[0];std::string at=std::string(mutation?"Mutation":"Action")+" plan step "+std::to_string(step);
  ensure(op<=10,at+": unknown opcode");uint used=0;
  auto selector=[&](uint record){ensure(record<p.records||(mutation&&record==targetSelector),at+": invalid record selector");};
  auto call=[&](uint inputs,uint outputs,uint inputBase,uint outputBase){read(inputBase,inputs,at,true);write(outputBase,outputs,at);};
  if(op==0){used=3;ensure(finite(dw_bits_float(w[2])),at+": nonfinite constant");write(w[1],1,at);}
  else if(op==1){used=4;range(w[2],w[3],p.stateWidth,at);write(w[1],w[3],at);}
  else if(op==2){used=6;selector(w[2]);range(w[3],w[4],24,at);ensure(w[5]<=1&&(!mutation||w[5]==0),at+": forbidden record read bank");write(w[1],w[4],at);}
  else if(op==3){used=4;ensure(w[1]<p.functions.size(),at+": invalid fixed function handle");const auto& f=p.functions[w[1]];call(f.inputs,f.width,w[2],w[3]);}
  else if(op==4){
   used=8;selector(w[1]);ensure(w[2]<3,at+": invalid record slot");ensure(w[3]==(mutation?0u:1u),at+": forbidden record call bank");
   auto signature=p.signatures.find(w[6]);ensure(signature!=p.signatures.end(),at+": unknown call signature");
   if(w[1]==targetSelector){for(uint record=0;record<p.records;++record)ensure(p.config[8u+4u*record+1u+w[2]]==w[6],at+": target slot has incompatible immutable signature");}
   else ensure(p.config[8u+4u*w[1]+1u+w[2]]==w[6],at+": selected slot has incompatible immutable signature");
   ensure(w[7]==0,at+": reserved word must be zero");call(signature->second.first,signature->second.second,w[4],w[5]);
  }
  else if(op==5||op==6){
   used=4;ensure((op==5)==mutation,at+": write opcode used in the wrong plan");uint limit=mutation?24u:p.stateWidth;
   range(w[1],w[3],limit,at);read(w[2],w[3],at);for(uint j=0;j<w[3];++j){ensure(!written[w[1]+j],at+": duplicate destination write");written[w[1]+j]=true;}
  }
  else if(op==7){used=2;read(w[1],1,at);}
  else if(op==8){used=2;write(w[1],1,at);}
  else if(op==9){used=2;ensure(mutation,at+": target source index is mutation-only");write(w[1],1,at);}
  else {used=4;read(w[2],w[3],at);write(w[1],w[3],at);}
  for(uint j=used;j<8;++j)ensure(w[j]==0,at+": unused words must be zero");
 }
 uint required=mutation?24u:p.stateWidth;for(uint i=0;i<required;++i)ensure(written[i],std::string(mutation?"Mutation":"Action")+" plan leaves output word "+std::to_string(i)+" unwritten");
}
bool possible_xir_failure(const Program& p,const uint* image,const uint* step,uint phase,uint target,uint detail){
 uint ordinal=detail>>16u,reason=detail&65535u;if(!ordinal||reason<1||reason>4)return false;
 auto possible=[&](const Function& f){if(ordinal>f.instructions)return false;uint opcode=p.config[p.heapOffset+f.code+4u*(ordinal-1u)];return reason==3||(reason==1&&opcode==5)||(reason==2&&opcode==9)||(reason==4&&opcode==17);};
 if(step[0]==3)return possible(p.functions[step[1]]);
 if(step[0]!=4)return false;
 if(phase==1){uint record=step[1]==targetSelector?target:step[1];uint handle=image[6u+p.stateWidth+24u*record+step[2]];return handle<p.functions.size()&&possible(p.functions[handle]);}
 // An action failure rolls candidate handles back. Its declared signature
 // bounds the possible functions; the discarded candidate cannot be recovered.
 for(const auto& f:p.functions)if(f.signature==step[6]&&possible(f))return true;return false;
}
void validate_failure(const Program& p,const uint* image,const std::string& where){
 uint epoch=image[0],status=image[1],phase=image[2],target=image[3],step=image[4],detail=image[5];
 ensure(epoch<=exactLimit,where+": epoch exceeds exact integer bound");ensure(status<=8,where+": unknown failure status");
 if(!status){ensure(!phase&&!target&&!step&&!detail,where+": successful image has nonzero failure header");return;}
 if(status==8){ensure(phase==3&&target==UINT32_MAX&&step==0&&epoch==exactLimit&&detail==epoch,where+": inconsistent epoch-limit failure");return;}
 ensure(phase==1||phase==2,where+": invalid failure phase");ensure(phase==1?target<p.records:target==UINT32_MAX,where+": invalid failure target");
 uint count=phase==1?p.mutationSteps:p.actionSteps;ensure(step<count,where+": failure step outside plan");const uint* w=p.config.data()+(phase==1?p.mutationOffset:p.actionOffset)+8u*step;
 bool post=phase==1&&step==p.mutationSteps-1u;
 if(status==1)ensure(possible_xir_failure(p,image,w,phase,target,detail),where+": inconsistent XIR failure detail");
 else if(status==2)ensure((post&&detail<3u)||(w[0]==4u&&detail>=p.functions.size()),where+": inconsistent invalid-handle detail");
 else if(status==3)ensure(phase==1&&w[0]==5&&detail>=w[1]&&detail<uint64_t(w[1])+w[3]&&detail<4,where+": inconsistent integer-conversion failure");
 else if(status==4)ensure((post&&detail<3)||(w[0]==4&&detail==w[2]),where+": inconsistent signature failure");
 else if(status==5)ensure(post&&detail==3,where+": inconsistent generation failure");
 else if(status==6){
  bool recordWrite=phase==1&&w[0]==5&&detail>=w[1]&&detail<uint64_t(w[1])+w[3];
  bool stateWrite=phase==2&&w[0]==6&&detail>=w[1]&&detail<uint64_t(w[1])+w[3];
  ensure((post&&detail>=4&&detail<24)||recordWrite||stateWrite||(w[0]==7&&detail==w[1]),where+": inconsistent nonfinite-value detail");
 }else if(status==7)ensure(w[0]==7&&detail==w[1],where+": inconsistent plan-require failure");
}
void validate_images(const Program& p,const std::vector<uint>& images){
 ensure(images.size()==uint64_t(p.count)*p.stride,"Instance payload size mismatch");
 for(uint lane=0;lane<p.count;++lane){
  const uint* image=images.data()+size_t(lane)*p.stride;std::string where="Instance "+std::to_string(lane);
  for(uint i=0;i<p.stateWidth;++i)ensure(finite(dw_bits_float(image[6u+i])),where+": nonfinite state word "+std::to_string(i));
  for(uint record=0;record<p.records;++record){const uint* words=image+6u+p.stateWidth+24u*record;
   for(uint slot=0;slot<3;++slot){ensure(words[slot]<p.functions.size(),where+": unresolved record handle");ensure(p.functions[words[slot]].signature==p.config[8u+4u*record+1u+slot],where+": record handle signature mismatch");}
   ensure(words[3]<=exactLimit,where+": generation exceeds exact integer bound");for(uint i=4;i<24;++i)ensure(finite(dw_bits_float(words[i])),where+": nonfinite record parameter");
  }
  validate_failure(p,image,where);
 }
}
Program read_program(const std::filesystem::path& path){
 uint endian=1;ensure(*reinterpret_cast<unsigned char*>(&endian)==1,"Resident host requires little-endian storage");
 std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)throw std::runtime_error("Cannot open input: "+path.string());auto end=in.tellg();ensure(end>=std::streamoff(40),"Input shorter than DWRD0001 header");uint64_t bytes=uint64_t(end);in.seekg(0);
 char magic[8];uint h[8];read_exact(in,magic,8);read_exact(in,h,sizeof(h));ensure(!std::memcmp(magic,residentMagic,8),"Expected DWRD0001 magic");
 Program p;p.count=h[0];p.records=h[1];p.stateWidth=h[2];p.heapWords=h[4];p.mutationSteps=h[5];p.actionSteps=h[6];
 ensure(p.count>0,"count must be positive");ensure(p.records>=1&&p.records<=32,"recordCount must be 1..32");ensure(p.stateWidth>=1&&p.stateWidth<=64,"stateWidth must be 1..64");ensure(h[3]>=1&&h[3]<=256,"functionCount must be 1..256");ensure(p.mutationSteps>=1&&p.mutationSteps<=4096&&p.actionSteps>=1&&p.actionSteps<=4096,"Plan lengths must be 1..4096");ensure(h[7]==0,"Reserved header word must be zero");
 uint64_t heap=8u+4u*p.records+6u*h[3],mutation=heap+p.heapWords,action=mutation+8u*p.mutationSteps,configWords=action+8u*p.actionSteps;
 p.stride=6u+p.stateWidth+24u*p.records;uint64_t instanceWords=uint64_t(p.count)*p.stride;
 ensure(configWords<=UINT32_MAX&&instanceWords<=UINT32_MAX,"Buffer word indices exceed uint32 ABI");uint64_t expected=8u+4u*(configWords+instanceWords);ensure(bytes==expected,"Input size mismatch: expected "+std::to_string(expected)+", received "+std::to_string(bytes));ensure(expected<=SIZE_MAX&&expected<=uint64_t(std::numeric_limits<std::streamsize>::max()),"Payload exceeds host address/stream limits");
 p.heapOffset=uint(heap);p.mutationOffset=uint(mutation);p.actionOffset=uint(action);p.config.resize(size_t(configWords));std::copy(h,h+8,p.config.begin());read_exact(in,p.config.data()+8,(configWords-8u)*4u);p.images.resize(size_t(instanceWords));read_exact(in,p.images.data(),instanceWords*4u);
 for(uint i=0;i<h[3];++i){const uint* f=p.config.data()+8u+4u*p.records+6u*i;Function function{f[0],f[1],f[2],f[3],f[4],f[5]};validate_function(p,function,i);auto entry=p.signatures.emplace(function.signature,std::make_pair(function.inputs,function.width));ensure(entry.second||entry.first->second==std::make_pair(function.inputs,function.width),"Functions sharing a signature have different widths");p.functions.push_back(function);}
 std::set<uint> identities;for(uint i=0;i<p.records;++i){const uint* meta=p.config.data()+8u+4u*i;ensure(identities.insert(meta[0]).second,"Duplicate source index");ensure(double(float(meta[0]))==double(meta[0]),"Source index is not exactly representable as FP32");for(uint slot=1;slot<4;++slot)ensure(meta[slot]!=0&&p.signatures.count(meta[slot]),"Immutable record signature has no matching bank function");}
 validate_plan(p,true);validate_plan(p,false);validate_images(p,p.images);return p;
}
void write_result(const std::filesystem::path& path,const Program& p,const Result& r){
 validate_images(p,r.images);std::ofstream out(path,std::ios::binary|std::ios::trunc);if(!out)throw std::runtime_error("Cannot create output: "+path.string());write_exact(out,residentMagic,8);write_exact(out,p.config.data(),p.config.size()*4u);write_exact(out,r.images.data(),r.images.size()*4u);out.flush();ensure(bool(out),"Could not flush checkpoint");
}
Result run_cpu(const Program& p,uint epochs,bool reverse){
 Result r;r.images=p.images;std::vector<uint> next(p.images.size());auto start=Clock::now();
 for(uint epoch=0;epoch<epochs;++epoch){for(uint lane=0;lane<p.count;++lane)dw_resident_step(p.config.data(),r.images.data(),next.data(),lane,reverse?1u:0u);r.images.swap(next);}
 r.executionSeconds=elapsed(start);return r;
}
void vk_check(VkResult result,const char* operation){if(result!=VK_SUCCESS)throw std::runtime_error(std::string(operation)+" failed (VkResult "+std::to_string(int(result))+")");}
struct Buffer {VkBuffer handle=VK_NULL_HANDLE;VkDeviceMemory memory=VK_NULL_HANDLE;VkDeviceSize size=0;bool coherent=false,deviceLocal=false;};
struct Vulkan {
 VkInstance instance=VK_NULL_HANDLE;VkPhysicalDevice physical=VK_NULL_HANDLE;VkDevice device=VK_NULL_HANDLE;VkQueue queue=VK_NULL_HANDLE;
 VkDescriptorSetLayout descriptorLayout=VK_NULL_HANDLE;VkDescriptorPool descriptorPool=VK_NULL_HANDLE;
 VkPipelineLayout pipelineLayout=VK_NULL_HANDLE;VkPipeline pipeline=VK_NULL_HANDLE;
 VkCommandPool commandPool=VK_NULL_HANDLE;VkFence fence=VK_NULL_HANDLE;
 VkDebugUtilsMessengerEXT messenger=VK_NULL_HANDLE;
 VkPhysicalDeviceProperties properties{};VkPhysicalDeviceMemoryProperties memory{};
 std::array<Buffer,3> buffers{};uint queueFamily=0;std::atomic<uint> validationErrors{0},validationWarnings{0};bool validationEnabled=false;
 ~Vulkan(){
  if(device){vkDeviceWaitIdle(device);if(fence)vkDestroyFence(device,fence,nullptr);if(commandPool)vkDestroyCommandPool(device,commandPool,nullptr);
   if(pipeline)vkDestroyPipeline(device,pipeline,nullptr);if(pipelineLayout)vkDestroyPipelineLayout(device,pipelineLayout,nullptr);
   if(descriptorPool)vkDestroyDescriptorPool(device,descriptorPool,nullptr);if(descriptorLayout)vkDestroyDescriptorSetLayout(device,descriptorLayout,nullptr);
   for(auto& b:buffers){if(b.handle)vkDestroyBuffer(device,b.handle,nullptr);if(b.memory)vkFreeMemory(device,b.memory,nullptr);}vkDestroyDevice(device,nullptr);
  }
  if(messenger){auto fn=reinterpret_cast<PFN_vkDestroyDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT"));if(fn)fn(instance,messenger,nullptr);}
  if(instance)vkDestroyInstance(instance,nullptr);
 }
 static VKAPI_ATTR VkBool32 VKAPI_CALL debug(VkDebugUtilsMessageSeverityFlagBitsEXT severity,VkDebugUtilsMessageTypeFlagsEXT,const VkDebugUtilsMessengerCallbackDataEXT* data,void* context){
  auto& self=*static_cast<Vulkan*>(context);if(severity&VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT)++self.validationErrors;else if(severity&VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT)++self.validationWarnings;
  std::cerr<<"Vulkan validation: "<<(data&&data->pMessage?data->pMessage:"(no message)")<<'\n';return VK_FALSE;
 }
 void initialize(const std::string& wanted){
  const char* layer="VK_LAYER_KHRONOS_validation";const char* extension=VK_EXT_DEBUG_UTILS_EXTENSION_NAME;
  validationEnabled=std::getenv("DAWNWOOD_VALIDATION")!=nullptr;
  if(validationEnabled){uint n=0;vk_check(vkEnumerateInstanceLayerProperties(&n,nullptr),"Enumerate layers");std::vector<VkLayerProperties> layers(n);vk_check(vkEnumerateInstanceLayerProperties(&n,layers.data()),"Enumerate layers");bool found=false;for(const auto& l:layers)if(std::string(l.layerName)==layer)found=true;if(!found)throw std::runtime_error("DAWNWOOD_VALIDATION requested but Khronos validation layer is unavailable");}
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.pApplicationName="Dawnwood DWI-RESIDENT-0.1";app.applicationVersion=VK_MAKE_VERSION(0,1,0);app.apiVersion=VK_API_VERSION_1_1;
  VkInstanceCreateInfo create{};create.sType=VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;create.pApplicationInfo=&app;
  VkDebugUtilsMessengerCreateInfoEXT debugInfo{};debugInfo.sType=VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT;debugInfo.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;debugInfo.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT;debugInfo.pfnUserCallback=&debug;debugInfo.pUserData=this;
  if(validationEnabled){create.enabledLayerCount=1;create.ppEnabledLayerNames=&layer;create.enabledExtensionCount=1;create.ppEnabledExtensionNames=&extension;create.pNext=&debugInfo;}
  vk_check(vkCreateInstance(&create,nullptr,&instance),"vkCreateInstance");
  if(validationEnabled){auto fn=reinterpret_cast<PFN_vkCreateDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT"));if(!fn)throw std::runtime_error("Vulkan debug messenger entry point unavailable");vk_check(fn(instance,&debugInfo,nullptr,&messenger),"Create debug messenger");}
  uint count=0;vk_check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"Enumerate devices");if(!count)throw std::runtime_error("No Vulkan device");
  std::vector<VkPhysicalDevice> devices(count);vk_check(vkEnumeratePhysicalDevices(instance,&count,devices.data()),"Enumerate devices");
  int best=-1;std::string selection=lower(wanted);
  for(auto candidate:devices){
   VkPhysicalDeviceProperties props{};vkGetPhysicalDeviceProperties(candidate,&props);if(!selection.empty()&&lower(props.deviceName).find(selection)==std::string::npos)continue;
   uint n=0;vkGetPhysicalDeviceQueueFamilyProperties(candidate,&n,nullptr);std::vector<VkQueueFamilyProperties> families(n);vkGetPhysicalDeviceQueueFamilyProperties(candidate,&n,families.data());
   for(uint i=0;i<n;++i)if(families[i].queueCount&&(families[i].queueFlags&VK_QUEUE_COMPUTE_BIT)){
    int score=props.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU?4:props.deviceType==VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU?3:props.deviceType==VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU?2:1;
    if(score>best){best=score;physical=candidate;properties=props;queueFamily=i;}break;
   }
  }
  if(!physical)throw std::runtime_error("No compute-capable Vulkan device matches: "+wanted);
  const auto& limits=properties.limits;
  if(limits.maxComputeWorkGroupInvocations<64||limits.maxComputeWorkGroupSize[0]<64||limits.maxPerStageDescriptorStorageBuffers<3||limits.maxDescriptorSetStorageBuffers<3||limits.maxPushConstantsSize<16)throw std::runtime_error("Device lacks required resident compute limits");
  float priority=1.0f;VkDeviceQueueCreateInfo queueInfo{};queueInfo.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;queueInfo.queueFamilyIndex=queueFamily;queueInfo.queueCount=1;queueInfo.pQueuePriorities=&priority;
  VkDeviceCreateInfo deviceInfo{};deviceInfo.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;deviceInfo.queueCreateInfoCount=1;deviceInfo.pQueueCreateInfos=&queueInfo;
  vk_check(vkCreateDevice(physical,&deviceInfo,nullptr,&device),"vkCreateDevice");vkGetDeviceQueue(device,queueFamily,0,&queue);vkGetPhysicalDeviceMemoryProperties(physical,&memory);
 }
 void make_buffer(Buffer& b,VkDeviceSize bytes){
  b.size=std::max<VkDeviceSize>(4,bytes);if(b.size>properties.limits.maxStorageBufferRange)throw std::runtime_error("resident buffer exceeds device maxStorageBufferRange");
  VkBufferCreateInfo info{};info.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;info.size=b.size;info.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;info.sharingMode=VK_SHARING_MODE_EXCLUSIVE;vk_check(vkCreateBuffer(device,&info,nullptr,&b.handle),"vkCreateBuffer");
  VkMemoryRequirements required{};vkGetBufferMemoryRequirements(device,b.handle,&required);uint selected=UINT32_MAX;int score=-1;
  for(uint i=0;i<memory.memoryTypeCount;++i){auto flags=memory.memoryTypes[i].propertyFlags;uint heap=memory.memoryTypes[i].heapIndex;if((required.memoryTypeBits&(1u<<i))&&(flags&VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)&&required.size<=memory.memoryHeaps[heap].size){int current=((flags&VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)?8:0)+((flags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)?2:0)+((flags&VK_MEMORY_PROPERTY_HOST_CACHED_BIT)?1:0);if(current>score){selected=i;score=current;}}}
  if(selected==UINT32_MAX)throw std::runtime_error("No host-visible memory type for resident buffer");
  b.coherent=(memory.memoryTypes[selected].propertyFlags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)!=0;
  b.deviceLocal=(memory.memoryTypes[selected].propertyFlags&VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT)!=0;
  VkMemoryAllocateInfo allocation{};allocation.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;allocation.allocationSize=required.size;allocation.memoryTypeIndex=selected;vk_check(vkAllocateMemory(device,&allocation,nullptr,&b.memory),"vkAllocateMemory");vk_check(vkBindBufferMemory(device,b.handle,b.memory,0),"vkBindBufferMemory");
 }
 void transfer(Buffer& b,void* data,size_t bytes,bool upload){
  if(!bytes)return;if(bytes>b.size)throw std::runtime_error("Internal resident buffer transfer overflow");
  void* mapped=nullptr;vk_check(vkMapMemory(device,b.memory,0,VK_WHOLE_SIZE,0,&mapped),"vkMapMemory");
  VkMappedMemoryRange range{};range.sType=VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;range.memory=b.memory;range.offset=0;range.size=VK_WHOLE_SIZE;
  VkResult result=VK_SUCCESS;
  if(upload){std::memcpy(mapped,data,bytes);if(!b.coherent)result=vkFlushMappedMemoryRanges(device,1,&range);}
  else {if(!b.coherent)result=vkInvalidateMappedMemoryRanges(device,1,&range);if(result==VK_SUCCESS)std::memcpy(data,mapped,bytes);}
  vkUnmapMemory(device,b.memory);vk_check(result,upload?"Flush memory":"Invalidate memory");
 }

 Result run(const Program& p,const std::filesystem::path& shader,uint epochs,bool reverse){
  Result result;result.device=properties.deviceName;result.vendorId=properties.vendorID;result.deviceId=properties.deviceID;result.driverVersion=properties.driverVersion;result.apiVersion=properties.apiVersion;result.validationEnabled=validationEnabled;
  result.deviceType=properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU?"discrete_gpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU?"integrated_gpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_CPU?"software_cpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU?"virtual_gpu":"other";
  result.images.resize(p.images.size());make_buffer(buffers[0],p.config.size()*4u);make_buffer(buffers[1],p.images.size()*4u);make_buffer(buffers[2],p.images.size()*4u);result.allBuffersDeviceLocal=std::all_of(buffers.begin(),buffers.end(),[](const Buffer& b){return b.deviceLocal;});
  transfer(buffers[0],const_cast<uint*>(p.config.data()),p.config.size()*4u,true);transfer(buffers[1],const_cast<uint*>(p.images.data()),p.images.size()*4u,true);result.uploadBytes=(p.config.size()+p.images.size())*4u;
  std::array<VkDescriptorSetLayoutBinding,3> bindings{};for(uint i=0;i<3;++i){bindings[i].binding=i;bindings[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;bindings[i].descriptorCount=1;bindings[i].stageFlags=VK_SHADER_STAGE_COMPUTE_BIT;}
  VkDescriptorSetLayoutCreateInfo layoutInfo{};layoutInfo.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;layoutInfo.bindingCount=3;layoutInfo.pBindings=bindings.data();vk_check(vkCreateDescriptorSetLayout(device,&layoutInfo,nullptr,&descriptorLayout),"Create descriptor layout");
  VkPushConstantRange push{VK_SHADER_STAGE_COMPUTE_BIT,0,16};VkPipelineLayoutCreateInfo pipelineInfo{};pipelineInfo.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;pipelineInfo.setLayoutCount=1;pipelineInfo.pSetLayouts=&descriptorLayout;pipelineInfo.pushConstantRangeCount=1;pipelineInfo.pPushConstantRanges=&push;vk_check(vkCreatePipelineLayout(device,&pipelineInfo,nullptr,&pipelineLayout),"Create pipeline layout");
  std::ifstream shaderFile(shader,std::ios::binary|std::ios::ate);if(!shaderFile)throw std::runtime_error("Cannot open shader beside executable: "+shader.string());auto shaderBytes=shaderFile.tellg();ensure(shaderBytes>=std::streamoff(20)&&uint64_t(shaderBytes)%4u==0&&uint64_t(shaderBytes)<=64u*1024u*1024u,"Invalid SPIR-V file size");
  std::vector<uint> spirv(size_t(shaderBytes)/4u);shaderFile.seekg(0);read_exact(shaderFile,spirv.data(),uint64_t(shaderBytes));ensure(spirv[0]==0x07230203u,"Invalid SPIR-V magic");
  VkShaderModuleCreateInfo moduleInfo{};moduleInfo.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;moduleInfo.codeSize=spirv.size()*4u;moduleInfo.pCode=spirv.data();VkShaderModule module=VK_NULL_HANDLE;vk_check(vkCreateShaderModule(device,&moduleInfo,nullptr,&module),"Create shader module");
  VkComputePipelineCreateInfo compute{};compute.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;compute.stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;compute.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;compute.stage.module=module;compute.stage.pName="main";compute.layout=pipelineLayout;VkResult pipelineResult=vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&compute,nullptr,&pipeline);vkDestroyShaderModule(device,module,nullptr);vk_check(pipelineResult,"Create resident pipeline");
  VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,6};VkDescriptorPoolCreateInfo poolInfo{};poolInfo.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;poolInfo.maxSets=2;poolInfo.poolSizeCount=1;poolInfo.pPoolSizes=&poolSize;vk_check(vkCreateDescriptorPool(device,&poolInfo,nullptr,&descriptorPool),"Create descriptor pool");
  VkDescriptorSetLayout layouts[2]={descriptorLayout,descriptorLayout};VkDescriptorSet sets[2]{};VkDescriptorSetAllocateInfo allocation{};allocation.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;allocation.descriptorPool=descriptorPool;allocation.descriptorSetCount=2;allocation.pSetLayouts=layouts;vk_check(vkAllocateDescriptorSets(device,&allocation,sets),"Allocate descriptor sets");
  for(uint parity=0;parity<2;++parity){std::array<VkDescriptorBufferInfo,3> infos{{{buffers[0].handle,0,buffers[0].size},{buffers[1u+parity].handle,0,buffers[1u+parity].size},{buffers[2u-parity].handle,0,buffers[2u-parity].size}}};std::array<VkWriteDescriptorSet,3> writes{};
   for(uint i=0;i<3;++i){writes[i].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;writes[i].dstSet=sets[parity];writes[i].dstBinding=i;writes[i].descriptorCount=1;writes[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;writes[i].pBufferInfo=&infos[i];}vkUpdateDescriptorSets(device,3,writes.data(),0,nullptr);
  }
  VkCommandPoolCreateInfo commandInfo{};commandInfo.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;commandInfo.queueFamilyIndex=queueFamily;commandInfo.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;vk_check(vkCreateCommandPool(device,&commandInfo,nullptr,&commandPool),"Create command pool");
  VkCommandBufferAllocateInfo commandAllocation{};commandAllocation.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;commandAllocation.commandPool=commandPool;commandAllocation.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;commandAllocation.commandBufferCount=1;VkCommandBuffer command=VK_NULL_HANDLE;vk_check(vkAllocateCommandBuffers(device,&commandAllocation,&command),"Allocate command buffer");
  VkFenceCreateInfo fenceInfo{};fenceInfo.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;vk_check(vkCreateFence(device,&fenceInfo,nullptr,&fence),"Create fence");
  uint64_t laneBatch=std::min<uint64_t>(uint64_t(properties.limits.maxComputeWorkGroupCount[0])*64u,1048576u);ensure(laneBatch>0,"Device reports no X workgroups");uint parity=0;
  // Bounded command batches need fence synchronization, but never read or
  // upload state/programs between epochs. Both instance images stay resident.
  for(uint64_t done=0;done<epochs;){
   uint batch=uint(std::min<uint64_t>(64u,uint64_t(epochs)-done));vk_check(vkResetCommandBuffer(command,0),"Reset command buffer");VkCommandBufferBeginInfo begin{};begin.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;vk_check(vkBeginCommandBuffer(command,&begin),"Begin command buffer");
   VkMemoryBarrier before{};before.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;before.srcAccessMask=done?VK_ACCESS_SHADER_WRITE_BIT:VK_ACCESS_HOST_WRITE_BIT;before.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;vkCmdPipelineBarrier(command,done?VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT:VK_PIPELINE_STAGE_HOST_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&before,0,nullptr,0,nullptr);
   vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);
   for(uint epoch=0;epoch<batch;++epoch){
    vkCmdBindDescriptorSets(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipelineLayout,0,1,&sets[parity],0,nullptr);
    for(uint64_t base=0;base<p.count;base+=laneBatch){uint lanes=uint(std::min<uint64_t>(laneBatch,uint64_t(p.count)-base));uint parameters[4]={p.count,uint(base),reverse?1u:0u,0u};vkCmdPushConstants(command,pipelineLayout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(parameters),parameters);vkCmdDispatch(command,(lanes+63u)/64u,1,1);++result.dispatches;}
    VkMemoryBarrier dependency{};dependency.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;dependency.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;dependency.dstAccessMask=VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT;vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&dependency,0,nullptr,0,nullptr);parity^=1u;
   }
   if(done+batch==epochs){VkMemoryBarrier download{};download.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;download.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;download.dstAccessMask=VK_ACCESS_HOST_READ_BIT;vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&download,0,nullptr,0,nullptr);}
   vk_check(vkEndCommandBuffer(command),"End command buffer");vk_check(vkResetFences(device,1,&fence),"Reset fence");VkSubmitInfo submit{};submit.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;submit.commandBufferCount=1;submit.pCommandBuffers=&command;auto start=Clock::now();vk_check(vkQueueSubmit(queue,1,&submit,fence),"Queue submit");vk_check(vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX),"Wait for resident epochs");result.executionSeconds+=elapsed(start);++result.submissions;done+=batch;
  }
  transfer(buffers[1u+parity],result.images.data(),result.images.size()*4u,false);result.downloadBytes=result.images.size()*4u;
  result.validationErrors=validationErrors.load();result.validationWarnings=validationWarnings.load();ensure(!result.validationErrors,"Vulkan validation reported "+std::to_string(result.validationErrors)+" errors");return result;
 }
};
std::filesystem::path executable_directory(const char* argv0){
#ifdef _WIN32
 (void)argv0;
 std::vector<wchar_t> buffer(32768);DWORD length=GetModuleFileNameW(nullptr,buffer.data(),DWORD(buffer.size()));if(!length||length>=buffer.size())throw std::runtime_error("Cannot resolve executable path");return std::filesystem::path(std::wstring(buffer.data(),length)).parent_path();
#else
 std::error_code error;auto path=std::filesystem::read_symlink("/proc/self/exe",error);if(!error)return path.parent_path();return std::filesystem::absolute(argv0).parent_path();
#endif
}
}


uint parse_uint(const std::string& value,const std::string& where){
 ensure(!value.empty()&&std::all_of(value.begin(),value.end(),[](unsigned char c){return c>='0'&&c<='9';}),where+": expected an unsigned decimal integer");size_t used=0;uint64_t parsed=0;try{parsed=std::stoull(value,&used,10);}catch(...){throw std::runtime_error(where+": integer outside uint32 range");}ensure(used==value.size()&&parsed<=UINT32_MAX,where+": integer outside uint32 range");return uint(parsed);
}
int main(int argc,char** argv){
 auto totalStart=Clock::now();
 try{
  ensure(argc>=2&&std::string(argv[1])=="run","Usage: dawnwood-resident run --input file --output file --backend cpu|vulkan --epochs N [--device substring] [--reverse-targets]");
  std::string input,output,backend,wanted,epochText;bool reverse=false;std::set<std::string> seen;
  for(int i=2;i<argc;++i){std::string option=argv[i];ensure(seen.insert(option).second,"Duplicate option: "+option);if(option=="--reverse-targets"){reverse=true;continue;}std::string* target=option=="--input"?&input:option=="--output"?&output:option=="--backend"?&backend:option=="--epochs"?&epochText:option=="--device"?&wanted:nullptr;ensure(target!=nullptr,"Unknown option: "+option);ensure(i+1<argc,"Missing value for "+option);*target=argv[++i];ensure(!target->empty(),"Empty value for "+option);}
  ensure(!input.empty()&&!output.empty()&&!epochText.empty(),"--input, --output and --epochs are required");ensure(backend=="cpu"||backend=="vulkan","--backend must be cpu or vulkan");ensure(backend=="vulkan"||wanted.empty(),"--device is valid only with --backend vulkan");uint epochs=parse_uint(epochText,"--epochs");
  Program p=read_program(input);Result r;if(backend=="cpu")r=run_cpu(p,epochs,reverse);else {Vulkan runtime;runtime.initialize(wanted);r=runtime.run(p,executable_directory(argv[0])/"resident.spv",epochs,reverse);}
  write_result(output,p,r);uint64_t failures=0,previousFailures=0,commits=0;uint minimumEpoch=UINT32_MAX,maximumEpoch=0;std::array<uint64_t,9> statuses{};
  for(uint lane=0;lane<p.count;++lane){size_t base=size_t(lane)*p.stride;uint epoch=r.images[base],status=r.images[base+1u];failures+=status!=0;previousFailures+=p.images[base+1u]!=0;++statuses[status];ensure(epoch>=p.images[base],"Runtime regressed an instance epoch");commits+=epoch-p.images[base];minimumEpoch=std::min(minimumEpoch,epoch);maximumEpoch=std::max(maximumEpoch,epoch);}
  std::cout<<std::setprecision(10)<<"{\"profile\":\"DWI-RESIDENT-0.1\",\"backend\":"<<json_string(backend)<<",\"device\":"<<json_string(r.device)<<",\"device_type\":"<<json_string(r.deviceType)<<",\"vendor_id\":"<<r.vendorId<<",\"device_id\":"<<r.deviceId<<",\"driver_version\":"<<r.driverVersion<<",\"api_version\":"<<r.apiVersion<<",\"count\":"<<p.count<<",\"record_count\":"<<p.records<<",\"state_width\":"<<p.stateWidth<<",\"function_count\":"<<p.functions.size()<<",\"mutation_steps\":"<<p.mutationSteps<<",\"action_steps\":"<<p.actionSteps<<",\"epochs_requested\":"<<epochs<<",\"committed_instance_epochs\":"<<commits<<",\"minimum_final_epoch\":"<<minimumEpoch<<",\"maximum_final_epoch\":"<<maximumEpoch<<",\"reverse_targets\":"<<(reverse?"true":"false")<<",\"status\":"<<json_string(failures?"lane_failure":"ok")<<",\"failed_lanes\":"<<failures<<",\"previously_failed_lanes\":"<<previousFailures<<",\"status_counts\":[";
  for(size_t i=0;i<statuses.size();++i){if(i)std::cout<<',';std::cout<<statuses[i];}
  std::cout<<"],\"execution_seconds\":"<<r.executionSeconds<<",\"total_seconds\":"<<elapsed(totalStart)<<",\"timing_scope\":"<<json_string(backend=="cpu"?"CPU epoch evaluation loop":"sum of host submit-to-fence waits; excludes setup, command recording and readback")<<",\"validation_enabled\":"<<(r.validationEnabled?"true":"false")<<",\"validation_errors\":"<<r.validationErrors<<",\"validation_warnings\":"<<r.validationWarnings<<",\"upload_bytes\":"<<r.uploadBytes<<",\"download_bytes\":"<<r.downloadBytes<<",\"dispatches\":"<<r.dispatches<<",\"submissions\":"<<r.submissions<<",\"all_buffers_device_local\":"<<(r.allBuffersDeviceLocal?"true":"false")<<",\"per_epoch_host_reads\":0,\"per_epoch_host_uploads\":0,\"transfer_counter_scope\":\"explicit host/device buffer uploads and readbacks; not CPU memory accesses or device bus traffic\",\"instance_model\":\"independent substrate per lane\",\"failure_policy\":\"rollback full epoch; retain first failure and freeze instance\",\"checkpoint_format\":\"DWRD0001\"}\n";
  return failures?3:0;
 }catch(const std::exception& error){std::cerr<<"DWI-RESIDENT-0.1: "<<error.what()<<'\n';std::cout<<"{\"profile\":\"DWI-RESIDENT-0.1\",\"status\":\"error\",\"error\":"<<json_string(error.what())<<"}\n";return 2;}
}
