// Standalone DWI-XIR-0.1 executable expression binding harness.
// Existing N1/D1 State, Operator, Config and checkpoint ABIs are unchanged.
#include "source_ir.inc"
#include <vulkan/vulkan.h>
#include <algorithm>
#include <array>
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
constexpr char inputMagic[8]={'D','W','I','R','0','0','0','1'};
constexpr char outputMagic[8]={'D','W','I','R','O','0','0','1'};
struct Program {
 uint count=0,instructionCount=0,inputWidth=0,outputWidth=0;
 std::vector<uint> words,outputRegisters;
 std::vector<float> inputs;
};
struct Result {
 std::vector<uint> statuses;
 std::vector<float> outputs;
 std::string device="CPU",deviceType="cpu";
 uint vendorId=0,deviceId=0,driverVersion=0,apiVersion=0;
 bool validationEnabled=false;
 uint validationErrors=0,validationWarnings=0;
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
void validate(const Program& p){
 auto invalid=[](uint i,const std::string& why){throw std::runtime_error("Instruction "+std::to_string(i)+": "+why);};
 for(uint i=0;i<p.instructionCount;++i){
  uint op=p.words[4u*i],a=p.words[4u*i+1u],b=p.words[4u*i+2u],c=p.words[4u*i+3u];
  if(op>17u)invalid(i,"unknown opcode "+std::to_string(op));
  if(op==0u){if(!finite(dw_bits_float(a)))invalid(i,"nonfinite constant");if(b||c)invalid(i,"unused operands must be zero");}
  else if(op==1u){if(a>=p.inputWidth)invalid(i,"input column outside inputWidth");if(b||c)invalid(i,"unused operands must be zero");}
  else {
   if(a>=i)invalid(i,"operand a is not a back-reference");
   bool binary=op==2u||op==3u||op==4u||op==5u||op==11u||op==12u||op==15u;
   if(binary||op==16u){if(b>=i)invalid(i,"operand b is not a back-reference");}
   else if(b)invalid(i,"unused operand b must be zero");
   if(op==16u){if(c>=i)invalid(i,"operand c is not a back-reference");}
   else if(c)invalid(i,"unused operand c must be zero");
  }
 }
 for(uint r:p.outputRegisters)if(r>=p.instructionCount)throw std::runtime_error("Output register outside instruction range");
 for(size_t i=0;i<p.inputs.size();++i)if(!finite(p.inputs[i]))throw std::runtime_error("Nonfinite input at scalar index "+std::to_string(i));
}
Program read_program(const std::filesystem::path& path){
 // The wire representation is explicitly little-endian, matching current targets.
 uint endian=1;if(*reinterpret_cast<unsigned char*>(&endian)!=1)throw std::runtime_error("This XIR host requires little-endian storage");
 std::ifstream in(path,std::ios::binary|std::ios::ate);if(!in)throw std::runtime_error("Cannot open input: "+path.string());
 auto end=in.tellg();if(end<std::streamoff(24))throw std::runtime_error("Input is shorter than the DWIR0001 header");
 uint64_t size=uint64_t(end);in.seekg(0);
 char magic[8];uint header[4];read_exact(in,magic,8);read_exact(in,header,16);
 if(std::memcmp(magic,inputMagic,8))throw std::runtime_error("Expected DWIR0001 input magic");
 Program p;p.count=header[0];p.instructionCount=header[1];p.inputWidth=header[2];p.outputWidth=header[3];
 if(!p.count)throw std::runtime_error("count must be positive");
 if(!p.instructionCount||p.instructionCount>256u)throw std::runtime_error("instructionCount must be in [1,256]");
 if(p.inputWidth>64u)throw std::runtime_error("inputWidth must be in [0,64]");
 if(!p.outputWidth||p.outputWidth>32u)throw std::runtime_error("outputWidth must be in [1,32]");
 uint64_t inputs=uint64_t(p.count)*p.inputWidth,outputs=uint64_t(p.count)*p.outputWidth;
 if(inputs>UINT32_MAX||outputs>UINT32_MAX)throw std::runtime_error("Scalar buffer index exceeds uint32 ABI");
 uint64_t expected=24u+16u*p.instructionCount+4u*p.outputWidth+4u*inputs;
 if(size!=expected)throw std::runtime_error("Input size mismatch: expected "+std::to_string(expected)+", received "+std::to_string(size));
 if(expected>SIZE_MAX||outputs>SIZE_MAX/sizeof(float))throw std::runtime_error("Payload exceeds host address space");
 p.words.resize(size_t(p.instructionCount)*4u);p.outputRegisters.resize(p.outputWidth);p.inputs.resize(size_t(inputs));
 read_exact(in,p.words.data(),p.words.size()*4u);read_exact(in,p.outputRegisters.data(),p.outputRegisters.size()*4u);read_exact(in,p.inputs.data(),p.inputs.size()*4u);
 validate(p);return p;
}
void write_result(const std::filesystem::path& path,const Program& p,const Result& result){
 std::ofstream out(path,std::ios::binary|std::ios::trunc);if(!out)throw std::runtime_error("Cannot create output: "+path.string());
 uint header[2]={p.count,p.outputWidth};write_exact(out,outputMagic,8);write_exact(out,header,sizeof(header));
 write_exact(out,result.statuses.data(),result.statuses.size()*4u);write_exact(out,result.outputs.data(),result.outputs.size()*4u);
 out.flush();if(!out)throw std::runtime_error("Could not flush output: "+path.string());
}
Result run_cpu(const Program& p){
 Result r;r.statuses.resize(p.count);r.outputs.resize(size_t(p.count)*p.outputWidth);
 const float dummy=0.0f;auto start=Clock::now();
 for(uint i=0;i<p.count;++i)r.statuses[i]=dw_ir_execute(p.words.data(),p.inputWidth?p.inputs.data()+size_t(i)*p.inputWidth:&dummy,p.outputRegisters.data(),r.outputs.data()+size_t(i)*p.outputWidth,p.instructionCount,p.outputWidth);
 r.executionSeconds=elapsed(start);return r;
}
void vk_check(VkResult result,const char* operation){if(result!=VK_SUCCESS)throw std::runtime_error(std::string(operation)+" failed (VkResult "+std::to_string(int(result))+")");}
struct Buffer {VkBuffer handle=VK_NULL_HANDLE;VkDeviceMemory memory=VK_NULL_HANDLE;VkDeviceSize size=0;bool coherent=false;};
struct Vulkan {
 VkInstance instance=VK_NULL_HANDLE;VkPhysicalDevice physical=VK_NULL_HANDLE;VkDevice device=VK_NULL_HANDLE;VkQueue queue=VK_NULL_HANDLE;
 VkDescriptorSetLayout descriptorLayout=VK_NULL_HANDLE;VkDescriptorPool descriptorPool=VK_NULL_HANDLE;
 VkPipelineLayout pipelineLayout=VK_NULL_HANDLE;VkPipeline pipeline=VK_NULL_HANDLE;
 VkCommandPool commandPool=VK_NULL_HANDLE;VkFence fence=VK_NULL_HANDLE;
 VkDebugUtilsMessengerEXT messenger=VK_NULL_HANDLE;
 VkPhysicalDeviceProperties properties{};VkPhysicalDeviceMemoryProperties memory{};
 std::array<Buffer,4> buffers{};uint queueFamily=0,validationErrors=0,validationWarnings=0;bool validationEnabled=false;
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
  VkApplicationInfo app{};app.sType=VK_STRUCTURE_TYPE_APPLICATION_INFO;app.pApplicationName="Dawnwood DWI-XIR-0.1";app.applicationVersion=VK_MAKE_VERSION(0,1,0);app.apiVersion=VK_API_VERSION_1_1;
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
  if(limits.maxComputeWorkGroupInvocations<64||limits.maxComputeWorkGroupSize[0]<64||limits.maxPerStageDescriptorStorageBuffers<4||limits.maxDescriptorSetStorageBuffers<4||limits.maxPushConstantsSize<20)throw std::runtime_error("Device lacks required XIR compute limits");
  float priority=1.0f;VkDeviceQueueCreateInfo queueInfo{};queueInfo.sType=VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;queueInfo.queueFamilyIndex=queueFamily;queueInfo.queueCount=1;queueInfo.pQueuePriorities=&priority;
  VkDeviceCreateInfo deviceInfo{};deviceInfo.sType=VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;deviceInfo.queueCreateInfoCount=1;deviceInfo.pQueueCreateInfos=&queueInfo;
  vk_check(vkCreateDevice(physical,&deviceInfo,nullptr,&device),"vkCreateDevice");vkGetDeviceQueue(device,queueFamily,0,&queue);vkGetPhysicalDeviceMemoryProperties(physical,&memory);
 }
 void make_buffer(Buffer& b,VkDeviceSize bytes){
  b.size=std::max<VkDeviceSize>(4,bytes);if(b.size>properties.limits.maxStorageBufferRange)throw std::runtime_error("XIR buffer exceeds device maxStorageBufferRange");
  VkBufferCreateInfo info{};info.sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;info.size=b.size;info.usage=VK_BUFFER_USAGE_STORAGE_BUFFER_BIT;info.sharingMode=VK_SHARING_MODE_EXCLUSIVE;vk_check(vkCreateBuffer(device,&info,nullptr,&b.handle),"vkCreateBuffer");
  VkMemoryRequirements required{};vkGetBufferMemoryRequirements(device,b.handle,&required);uint selected=UINT32_MAX;int score=-1;
  for(uint i=0;i<memory.memoryTypeCount;++i){auto flags=memory.memoryTypes[i].propertyFlags;uint heap=memory.memoryTypes[i].heapIndex;if((required.memoryTypeBits&(1u<<i))&&(flags&VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)&&required.size<=memory.memoryHeaps[heap].size){int current=(flags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)?2:1;if(current>score){selected=i;score=current;}}}
  if(selected==UINT32_MAX)throw std::runtime_error("No host-visible memory type for XIR buffer");
  b.coherent=(memory.memoryTypes[selected].propertyFlags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)!=0;
  VkMemoryAllocateInfo allocation{};allocation.sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;allocation.allocationSize=required.size;allocation.memoryTypeIndex=selected;vk_check(vkAllocateMemory(device,&allocation,nullptr,&b.memory),"vkAllocateMemory");vk_check(vkBindBufferMemory(device,b.handle,b.memory,0),"vkBindBufferMemory");
 }
 void transfer(Buffer& b,void* data,size_t bytes,bool upload){
  if(!bytes)return;if(bytes>b.size)throw std::runtime_error("Internal XIR buffer transfer overflow");
  void* mapped=nullptr;vk_check(vkMapMemory(device,b.memory,0,VK_WHOLE_SIZE,0,&mapped),"vkMapMemory");
  VkMappedMemoryRange range{};range.sType=VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;range.memory=b.memory;range.offset=0;range.size=VK_WHOLE_SIZE;
  VkResult result=VK_SUCCESS;
  if(upload){std::memcpy(mapped,data,bytes);if(!b.coherent)result=vkFlushMappedMemoryRanges(device,1,&range);}
  else {if(!b.coherent)result=vkInvalidateMappedMemoryRanges(device,1,&range);if(result==VK_SUCCESS)std::memcpy(data,mapped,bytes);}
  vkUnmapMemory(device,b.memory);vk_check(result,upload?"Flush memory":"Invalidate memory");
 }
 Result run(const Program& p,const std::filesystem::path& shader){
  Result result;result.device=properties.deviceName;result.vendorId=properties.vendorID;result.deviceId=properties.deviceID;result.driverVersion=properties.driverVersion;result.apiVersion=properties.apiVersion;result.validationEnabled=validationEnabled;
  result.deviceType=properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU?"discrete_gpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU?"integrated_gpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_CPU?"software_cpu":properties.deviceType==VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU?"virtual_gpu":"other";
  result.statuses.resize(p.count);result.outputs.resize(size_t(p.count)*p.outputWidth);
  std::vector<uint> program=p.words;program.insert(program.end(),p.outputRegisters.begin(),p.outputRegisters.end());
  make_buffer(buffers[0],program.size()*4u);make_buffer(buffers[1],p.inputs.size()*4u);make_buffer(buffers[2],result.statuses.size()*4u);make_buffer(buffers[3],result.outputs.size()*4u);
  transfer(buffers[0],program.data(),program.size()*4u,true);transfer(buffers[1],const_cast<float*>(p.inputs.data()),p.inputs.size()*4u,true);
  std::array<VkDescriptorSetLayoutBinding,4> bindings{};for(uint i=0;i<4;++i){bindings[i].binding=i;bindings[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;bindings[i].descriptorCount=1;bindings[i].stageFlags=VK_SHADER_STAGE_COMPUTE_BIT;}
  VkDescriptorSetLayoutCreateInfo layoutInfo{};layoutInfo.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;layoutInfo.bindingCount=4;layoutInfo.pBindings=bindings.data();vk_check(vkCreateDescriptorSetLayout(device,&layoutInfo,nullptr,&descriptorLayout),"Create descriptor layout");
  VkPushConstantRange push{VK_SHADER_STAGE_COMPUTE_BIT,0,20};VkPipelineLayoutCreateInfo pipelineInfo{};pipelineInfo.sType=VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;pipelineInfo.setLayoutCount=1;pipelineInfo.pSetLayouts=&descriptorLayout;pipelineInfo.pushConstantRangeCount=1;pipelineInfo.pPushConstantRanges=&push;vk_check(vkCreatePipelineLayout(device,&pipelineInfo,nullptr,&pipelineLayout),"Create pipeline layout");
  std::ifstream shaderFile(shader,std::ios::binary|std::ios::ate);if(!shaderFile)throw std::runtime_error("Cannot open shader beside executable: "+shader.string());
  auto shaderBytes=shaderFile.tellg();if(shaderBytes<std::streamoff(20)||uint64_t(shaderBytes)%4u||uint64_t(shaderBytes)>64u*1024u*1024u)throw std::runtime_error("Invalid SPIR-V file size");
  std::vector<uint> spirv(size_t(shaderBytes)/4u);shaderFile.seekg(0);read_exact(shaderFile,spirv.data(),uint64_t(shaderBytes));if(spirv[0]!=0x07230203u)throw std::runtime_error("Invalid SPIR-V magic");
  VkShaderModuleCreateInfo moduleInfo{};moduleInfo.sType=VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;moduleInfo.codeSize=spirv.size()*4u;moduleInfo.pCode=spirv.data();VkShaderModule module=VK_NULL_HANDLE;vk_check(vkCreateShaderModule(device,&moduleInfo,nullptr,&module),"Create shader module");
  VkComputePipelineCreateInfo compute{};compute.sType=VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;compute.stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;compute.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;compute.stage.module=module;compute.stage.pName="main";compute.layout=pipelineLayout;
  VkResult pipelineResult=vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&compute,nullptr,&pipeline);vkDestroyShaderModule(device,module,nullptr);vk_check(pipelineResult,"Create XIR compute pipeline");
  VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,4};VkDescriptorPoolCreateInfo poolInfo{};poolInfo.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;poolInfo.maxSets=1;poolInfo.poolSizeCount=1;poolInfo.pPoolSizes=&poolSize;vk_check(vkCreateDescriptorPool(device,&poolInfo,nullptr,&descriptorPool),"Create descriptor pool");
  VkDescriptorSetAllocateInfo allocation{};allocation.sType=VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;allocation.descriptorPool=descriptorPool;allocation.descriptorSetCount=1;allocation.pSetLayouts=&descriptorLayout;VkDescriptorSet set=VK_NULL_HANDLE;vk_check(vkAllocateDescriptorSets(device,&allocation,&set),"Allocate descriptor set");
  std::array<VkDescriptorBufferInfo,4> bufferInfos{};std::array<VkWriteDescriptorSet,4> writes{};
  for(uint i=0;i<4;++i){bufferInfos[i]={buffers[i].handle,0,buffers[i].size};writes[i].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;writes[i].dstSet=set;writes[i].dstBinding=i;writes[i].descriptorCount=1;writes[i].descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;writes[i].pBufferInfo=&bufferInfos[i];}vkUpdateDescriptorSets(device,4,writes.data(),0,nullptr);
  VkCommandPoolCreateInfo commandInfo{};commandInfo.sType=VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;commandInfo.queueFamilyIndex=queueFamily;vk_check(vkCreateCommandPool(device,&commandInfo,nullptr,&commandPool),"Create command pool");
  VkCommandBufferAllocateInfo commandAllocation{};commandAllocation.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;commandAllocation.commandPool=commandPool;commandAllocation.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;commandAllocation.commandBufferCount=1;VkCommandBuffer command=VK_NULL_HANDLE;vk_check(vkAllocateCommandBuffers(device,&commandAllocation,&command),"Allocate command buffer");
  VkCommandBufferBeginInfo begin{};begin.sType=VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;begin.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;vk_check(vkBeginCommandBuffer(command,&begin),"Begin command buffer");
  VkMemoryBarrier uploadBarrier{};uploadBarrier.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;uploadBarrier.srcAccessMask=VK_ACCESS_HOST_WRITE_BIT;uploadBarrier.dstAccessMask=VK_ACCESS_SHADER_READ_BIT;vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_HOST_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,0,1,&uploadBarrier,0,nullptr,0,nullptr);
  vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipeline);vkCmdBindDescriptorSets(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipelineLayout,0,1,&set,0,nullptr);
  // Partition only independent lanes. uint64 host arithmetic prevents overflow.
  uint64_t batch=std::min<uint64_t>(uint64_t(properties.limits.maxComputeWorkGroupCount[0])*64u,1048576u);
  if(!batch)throw std::runtime_error("Device reports no X workgroups");
  for(uint64_t base=0;base<p.count;base+=batch){uint n=uint(std::min<uint64_t>(batch,uint64_t(p.count)-base));uint parameters[5]={p.count,p.instructionCount,p.inputWidth,p.outputWidth,uint(base)};vkCmdPushConstants(command,pipelineLayout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(parameters),parameters);vkCmdDispatch(command,(n+63u)/64u,1,1);}
  VkMemoryBarrier downloadBarrier{};downloadBarrier.sType=VK_STRUCTURE_TYPE_MEMORY_BARRIER;downloadBarrier.srcAccessMask=VK_ACCESS_SHADER_WRITE_BIT;downloadBarrier.dstAccessMask=VK_ACCESS_HOST_READ_BIT;vkCmdPipelineBarrier(command,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&downloadBarrier,0,nullptr,0,nullptr);
  vk_check(vkEndCommandBuffer(command),"End command buffer");VkFenceCreateInfo fenceInfo{};fenceInfo.sType=VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;vk_check(vkCreateFence(device,&fenceInfo,nullptr,&fence),"Create fence");
  VkSubmitInfo submission{};submission.sType=VK_STRUCTURE_TYPE_SUBMIT_INFO;submission.commandBufferCount=1;submission.pCommandBuffers=&command;auto start=Clock::now();vk_check(vkQueueSubmit(queue,1,&submission,fence),"Queue submit");vk_check(vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX),"Wait for XIR execution");result.executionSeconds=elapsed(start);
  transfer(buffers[2],result.statuses.data(),result.statuses.size()*4u,false);transfer(buffers[3],result.outputs.data(),result.outputs.size()*4u,false);
  result.validationErrors=validationErrors;result.validationWarnings=validationWarnings;if(validationErrors)throw std::runtime_error("Vulkan validation reported "+std::to_string(validationErrors)+" errors");return result;
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

int main(int argc,char** argv){
 auto totalStart=Clock::now();
 try{
  if(argc<2||std::string(argv[1])!="run")throw std::runtime_error("Usage: source_ir run --backend cpu|vulkan --input file --output file [--device substring]");
  std::string backend,input,output,wanted;
  for(int i=2;i<argc;++i){std::string option=argv[i];if(i+1>=argc)throw std::runtime_error("Missing value for "+option);std::string value=argv[++i];std::string* target=option=="--backend"?&backend:option=="--input"?&input:option=="--output"?&output:option=="--device"?&wanted:nullptr;if(!target)throw std::runtime_error("Unknown option: "+option);if(!target->empty())throw std::runtime_error("Duplicate option: "+option);*target=value;}
  if(backend!="cpu"&&backend!="vulkan")throw std::runtime_error("--backend must be cpu or vulkan");if(input.empty()||output.empty())throw std::runtime_error("--input and --output are required");if(backend=="cpu"&&!wanted.empty())throw std::runtime_error("--device is valid only with --backend vulkan");
  Program program=read_program(input);Result result;
  if(backend=="cpu")result=run_cpu(program);else {Vulkan runtime;runtime.initialize(wanted);result=runtime.run(program,executable_directory(argv[0])/"source_ir.spv");}
  write_result(output,program,result);uint64_t failed=0;for(uint status:result.statuses)failed+=status!=0;
  std::cout<<std::setprecision(10)<<"{\"profile\":\"DWI-XIR-0.1\",\"backend\":"<<json_string(backend)<<",\"device\":"<<json_string(result.device)<<",\"device_type\":"<<json_string(result.deviceType)<<",\"vendor_id\":"<<result.vendorId<<",\"device_id\":"<<result.deviceId<<",\"driver_version\":"<<result.driverVersion<<",\"api_version\":"<<result.apiVersion<<",\"count\":"<<program.count<<",\"instruction_count\":"<<program.instructionCount<<",\"input_width\":"<<program.inputWidth<<",\"output_width\":"<<program.outputWidth<<",\"status\":"<<json_string(failed?"lane_failure":"ok")<<",\"failed_lanes\":"<<failed<<",\"execution_seconds\":"<<result.executionSeconds<<",\"total_seconds\":"<<elapsed(totalStart)<<",\"timing_scope\":"<<json_string(backend=="cpu"?"CPU evaluation loop":"host submit-to-fence wait; excludes setup and readback")<<",\"validation_enabled\":"<<(result.validationEnabled?"true":"false")<<",\"validation_errors\":"<<result.validationErrors<<",\"validation_warnings\":"<<result.validationWarnings<<",\"failure_outputs\":\"zero row; first failure status retained\"}\n";
  return failed?3:0;
 }catch(const std::exception& error){std::cerr<<"DWI-XIR-0.1: "<<error.what()<<'\n';std::cout<<"{\"profile\":\"DWI-XIR-0.1\",\"status\":\"error\",\"error\":"<<json_string(error.what())<<"}\n";return 2;}
}
