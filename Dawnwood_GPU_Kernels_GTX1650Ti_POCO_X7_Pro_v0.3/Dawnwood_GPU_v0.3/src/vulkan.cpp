#include "runtime.hpp"
#include "spirv.hpp"
#include <vulkan/vulkan.h>
#include <algorithm>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <sstream>
#include <stdexcept>
#include <cctype>
#include <array>
#include <atomic>
#include <iostream>
namespace {
void check(VkResult r,const char* where){if(r!=VK_SUCCESS)throw std::runtime_error(std::string(where)+" (VkResult "+std::to_string(int(r))+")");}
std::string lower(std::string x){for(char& c:x)c=char(std::tolower(static_cast<unsigned char>(c)));return x;}
uint tuning_value(const char* name,uint fallback){const char* value=std::getenv(name);if(!value)return fallback;std::string text=value;size_t used=0;uint64_t parsed=0;try{parsed=std::stoull(text,&used);}catch(...){throw std::runtime_error(std::string(name)+" requires a positive uint32");}if(text.empty()||text[0]<'0'||text[0]>'9'||used!=text.size()||!parsed||parsed>UINT32_MAX)throw std::runtime_error(std::string(name)+" requires a positive uint32");return uint(parsed);}
struct Buffer {VkBuffer handle=VK_NULL_HANDLE;VkDeviceMemory memory=VK_NULL_HANDLE;VkDeviceSize size=0,allocated=0;uint heapIndex=0;bool coherent=false;};
struct Image {VkImage handle=VK_NULL_HANDLE;VkImageView view=VK_NULL_HANDLE;VkDeviceMemory memory=VK_NULL_HANDLE;VkDeviceSize allocated=0;uint heapIndex=0,width=0,height=0;};
}
struct VulkanRuntime::Impl {
 VkInstance instance=VK_NULL_HANDLE;VkPhysicalDevice physical=VK_NULL_HANDLE;VkDevice device=VK_NULL_HANDLE;VkQueue queue=VK_NULL_HANDLE;
 VkPhysicalDeviceProperties props{};VkPhysicalDeviceMemoryProperties memory{};VkPhysicalDeviceMemoryBudgetPropertiesEXT budget{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_BUDGET_PROPERTIES_EXT};
 VkCommandPool commandPool=VK_NULL_HANDLE;VkCommandBuffer command=VK_NULL_HANDLE;VkFence fence=VK_NULL_HANDLE;
 VkDescriptorSetLayout descriptorLayout=VK_NULL_HANDLE;VkDescriptorPool descriptorPool=VK_NULL_HANDLE;VkDescriptorSet sets[2]{};
 VkPipelineLayout pipelineLayout=VK_NULL_HANDLE;VkPipeline mutatePipeline=VK_NULL_HANDLE,evolvePipeline=VK_NULL_HANDLE;VkPipeline splitPipelines[5]{};VkQueryPool queries=VK_NULL_HANDLE;
 Buffer states[2],staging,evolutionWork;Image operators[2];VkSampler lutSampler=VK_NULL_HANDLE;Config cfg{};uint parity=0,queueFamily=0,timestampBits=0,lutWidth=0,lutHeight=0,allocationCount=0;bool splitEvolution=false;
 std::array<VkDeviceSize,VK_MAX_MEMORY_HEAPS> heapAllocated{};
 VkDebugUtilsMessengerEXT messenger=VK_NULL_HANDLE;
 std::atomic<uint64_t> validationErrors{0},validationWarnings{0};
 static VKAPI_ATTR VkBool32 VKAPI_CALL validation_message(VkDebugUtilsMessageSeverityFlagBitsEXT severity,VkDebugUtilsMessageTypeFlagsEXT,const VkDebugUtilsMessengerCallbackDataEXT* data,void* context){auto& self=*static_cast<Impl*>(context);if(severity&VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT)++self.validationErrors;else if(severity&VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT)++self.validationWarnings;std::cerr<<"Vulkan validation: "<<(data&&data->pMessage?data->pMessage:"(no message)")<<'\n';return VK_FALSE;}
 void check_validation()const{if(validationErrors.load())throw std::runtime_error("Vulkan validation reported "+std::to_string(validationErrors.load())+" error(s); see stderr");}
 bool budgetAvailable=false,validationEnabled=false;float budgetFraction=0.8f;double seconds=0,wallSeconds=0,maxSubmissionSeconds=0;uint64_t uploadBytes=0,downloadBytes=0,totalEpochs=0,computeSubmissions=0;uint stateDispatchLimit=65536,workgroupSize=64;
 ~Impl(){if(device){vkDeviceWaitIdle(device);if(queries)vkDestroyQueryPool(device,queries,nullptr);if(mutatePipeline)vkDestroyPipeline(device,mutatePipeline,nullptr);if(evolvePipeline)vkDestroyPipeline(device,evolvePipeline,nullptr);for(auto pipeline:splitPipelines)if(pipeline)vkDestroyPipeline(device,pipeline,nullptr);if(descriptorPool)vkDestroyDescriptorPool(device,descriptorPool,nullptr);if(pipelineLayout)vkDestroyPipelineLayout(device,pipelineLayout,nullptr);if(descriptorLayout)vkDestroyDescriptorSetLayout(device,descriptorLayout,nullptr);if(lutSampler)vkDestroySampler(device,lutSampler,nullptr);if(fence)vkDestroyFence(device,fence,nullptr);if(commandPool)vkDestroyCommandPool(device,commandPool,nullptr);for(auto& b:states)destroy(b);for(auto& b:operators)destroy(b);destroy(staging);destroy(evolutionWork);vkDestroyDevice(device,nullptr);}if(instance){if(messenger){auto destroyMessenger=reinterpret_cast<PFN_vkDestroyDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkDestroyDebugUtilsMessengerEXT"));if(destroyMessenger)destroyMessenger(instance,messenger,nullptr);}vkDestroyInstance(instance,nullptr);}}
 void destroy(Buffer& b){if(b.handle)vkDestroyBuffer(device,b.handle,nullptr);if(b.memory)vkFreeMemory(device,b.memory,nullptr);b={};}
 void destroy(Image& b){if(b.view)vkDestroyImageView(device,b.view,nullptr);if(b.handle)vkDestroyImage(device,b.handle,nullptr);if(b.memory)vkFreeMemory(device,b.memory,nullptr);b={};}
 uint memory_type(const VkMemoryRequirements& req,VkMemoryPropertyFlags required){
  uint type=UINT32_MAX;int score=-1;
  if(allocationCount>=props.limits.maxMemoryAllocationCount)throw std::runtime_error("Device memory allocation-count limit reached");
  for(uint i=0;i<memory.memoryTypeCount;++i){auto flags=memory.memoryTypes[i].propertyFlags;if((req.memoryTypeBits&(1u<<i))&&(flags&required)==required){uint heap=memory.memoryTypes[i].heapIndex;VkDeviceSize available=memory.memoryHeaps[heap].size;if(budgetAvailable)available=budget.heapBudget[heap]>budget.heapUsage[heap]?budget.heapBudget[heap]-budget.heapUsage[heap]:0;VkDeviceSize limit=std::min(available,VkDeviceSize(double(available)*budgetFraction));if(heapAllocated[heap]>limit||req.size>limit-heapAllocated[heap])continue;int candidate=(required&VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT)?((flags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)?2:1):((props.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU&&!(flags&VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT))?2:1);if(candidate>score){type=i;score=candidate;}}}
  if(type==UINT32_MAX)throw std::runtime_error("No suitable Vulkan memory type with sufficient reported heap budget for the padded allocation");return type;
 }
 void make_buffer(Buffer& b,VkDeviceSize size,VkBufferUsageFlags usage,VkMemoryPropertyFlags required){
  b.size=size;VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};ci.size=size;ci.usage=usage;ci.sharingMode=VK_SHARING_MODE_EXCLUSIVE;check(vkCreateBuffer(device,&ci,nullptr,&b.handle),"vkCreateBuffer");
  VkMemoryRequirements req{};vkGetBufferMemoryRequirements(device,b.handle,&req);uint type=memory_type(req,required);
  VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=req.size;ai.memoryTypeIndex=type;check(vkAllocateMemory(device,&ai,nullptr,&b.memory),"vkAllocateMemory");++allocationCount;b.allocated=req.size;b.heapIndex=memory.memoryTypes[type].heapIndex;heapAllocated[b.heapIndex]+=req.size;b.coherent=(memory.memoryTypes[type].propertyFlags&VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)!=0;check(vkBindBufferMemory(device,b.handle,b.memory,0),"vkBindBufferMemory");
 }
 void make_image(Image& b){
  b.width=lutWidth;b.height=lutHeight;VkImageCreateInfo ci{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};ci.imageType=VK_IMAGE_TYPE_2D;ci.format=VK_FORMAT_R32G32B32A32_UINT;ci.extent={lutWidth,lutHeight,1};ci.mipLevels=1;ci.arrayLayers=1;ci.samples=VK_SAMPLE_COUNT_1_BIT;ci.tiling=VK_IMAGE_TILING_OPTIMAL;ci.usage=VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT;ci.sharingMode=VK_SHARING_MODE_EXCLUSIVE;ci.initialLayout=VK_IMAGE_LAYOUT_UNDEFINED;check(vkCreateImage(device,&ci,nullptr,&b.handle),"vkCreateImage operator LUT");
  VkMemoryRequirements req{};vkGetImageMemoryRequirements(device,b.handle,&req);uint type=memory_type(req,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=req.size;ai.memoryTypeIndex=type;check(vkAllocateMemory(device,&ai,nullptr,&b.memory),"vkAllocateMemory operator LUT");++allocationCount;b.allocated=req.size;b.heapIndex=memory.memoryTypes[type].heapIndex;heapAllocated[b.heapIndex]+=req.size;check(vkBindImageMemory(device,b.handle,b.memory,0),"vkBindImageMemory operator LUT");
  VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};vi.image=b.handle;vi.viewType=VK_IMAGE_VIEW_TYPE_2D;vi.format=ci.format;vi.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};check(vkCreateImageView(device,&vi,nullptr,&b.view),"vkCreateImageView operator LUT");
 }
 void begin(){check(vkResetCommandBuffer(command,0),"vkResetCommandBuffer");VkCommandBufferBeginInfo info{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};info.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;check(vkBeginCommandBuffer(command,&info),"vkBeginCommandBuffer");}
 void finish(){check(vkEndCommandBuffer(command),"vkEndCommandBuffer");check(vkResetFences(device,1,&fence),"vkResetFences");VkSubmitInfo s{VK_STRUCTURE_TYPE_SUBMIT_INFO};s.commandBufferCount=1;s.pCommandBuffers=&command;check(vkQueueSubmit(queue,1,&s,fence),"vkQueueSubmit");check(vkWaitForFences(device,1,&fence,VK_TRUE,UINT64_MAX),"vkWaitForFences");check_validation();}
 void barrier(VkPipelineStageFlags from,VkPipelineStageFlags to,VkAccessFlags src,VkAccessFlags dst){VkMemoryBarrier b{VK_STRUCTURE_TYPE_MEMORY_BARRIER};b.srcAccessMask=src;b.dstAccessMask=dst;vkCmdPipelineBarrier(command,from,to,0,1,&b,0,nullptr,0,nullptr);}
 void stage_upload(const void* data,size_t payload,size_t transferred){void* map=nullptr;check(vkMapMemory(device,staging.memory,0,VK_WHOLE_SIZE,0,&map),"vkMapMemory upload");std::memcpy(map,data,payload);if(transferred>payload)std::memset(static_cast<char*>(map)+payload,0,transferred-payload);if(!staging.coherent){VkMappedMemoryRange r{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};r.memory=staging.memory;r.size=VK_WHOLE_SIZE;check(vkFlushMappedMemoryRanges(device,1,&r),"vkFlushMappedMemoryRanges");}vkUnmapMemory(device,staging.memory);}
 void stage_read(void* data,size_t bytes){void* map=nullptr;check(vkMapMemory(device,staging.memory,0,VK_WHOLE_SIZE,0,&map),"vkMapMemory read");if(!staging.coherent){VkMappedMemoryRange r{VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE};r.memory=staging.memory;r.size=VK_WHOLE_SIZE;check(vkInvalidateMappedMemoryRanges(device,1,&r),"vkInvalidateMappedMemoryRanges");}std::memcpy(data,map,bytes);vkUnmapMemory(device,staging.memory);}
 void image_barrier(Image& image,VkImageLayout oldLayout,VkImageLayout newLayout,VkPipelineStageFlags from,VkPipelineStageFlags to,VkAccessFlags src,VkAccessFlags dst){VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};b.srcAccessMask=src;b.dstAccessMask=dst;b.oldLayout=oldLayout;b.newLayout=newLayout;b.srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;b.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;b.image=image.handle;b.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};vkCmdPipelineBarrier(command,from,to,0,0,nullptr,0,nullptr,1,&b);}
 void upload(Buffer& target,const void* data,size_t bytes){for(size_t offset=0;offset<bytes;){size_t chunk=size_t(std::min<VkDeviceSize>(bytes-offset,staging.size));stage_upload(static_cast<const char*>(data)+offset,chunk,chunk);begin();VkBufferCopy copy{0,offset,chunk};vkCmdCopyBuffer(command,staging.handle,target.handle,1,&copy);barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT);finish();uploadBytes+=chunk;offset+=chunk;}}
 void read(Buffer& source,void* data,size_t bytes){for(size_t offset=0;offset<bytes;){size_t chunk=size_t(std::min<VkDeviceSize>(bytes-offset,staging.size));begin();barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT|VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_SHADER_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT);VkBufferCopy copy{offset,0,chunk};vkCmdCopyBuffer(command,source.handle,staging.handle,1,&copy);barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT);finish();stage_read(static_cast<char*>(data)+offset,chunk);downloadBytes+=chunk;offset+=chunk;}}
 void upload(Image& target,const void* data,size_t bytes){
  size_t rowBytes=size_t(target.width)*16,rowsPerChunk=size_t(staging.size)/rowBytes;if(!rowsPerChunk)throw std::runtime_error("Staging buffer cannot hold a LUT row");
  for(uint row=0;row<target.height;){uint rows=uint(std::min<size_t>(target.height-row,rowsPerChunk));size_t offset=size_t(row)*rowBytes,chunk=size_t(rows)*rowBytes,payload=std::min(chunk,bytes-offset);stage_upload(static_cast<const char*>(data)+offset,payload,chunk);begin();image_barrier(target,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_MEMORY_WRITE_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);VkBufferImageCopy copy{};copy.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};copy.imageOffset={0,int32_t(row),0};copy.imageExtent={target.width,rows,1};vkCmdCopyBufferToImage(command,staging.handle,target.handle,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&copy);image_barrier(target,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT);finish();uploadBytes+=chunk;row+=rows;}
 }
 void read(Image& source,void* data,size_t bytes){
  size_t rowBytes=size_t(source.width)*16,rowsPerChunk=size_t(staging.size)/rowBytes;if(!rowsPerChunk)throw std::runtime_error("Staging buffer cannot hold a LUT row");
  for(uint row=0;row<source.height;){uint rows=uint(std::min<size_t>(source.height-row,rowsPerChunk));size_t offset=size_t(row)*rowBytes,chunk=size_t(rows)*rowBytes,payload=std::min(chunk,bytes-offset);begin();image_barrier(source,VK_IMAGE_LAYOUT_GENERAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_MEMORY_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT);VkBufferImageCopy copy{};copy.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};copy.imageOffset={0,int32_t(row),0};copy.imageExtent={source.width,rows,1};vkCmdCopyImageToBuffer(command,source.handle,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,staging.handle,1,&copy);barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_HOST_READ_BIT);image_barrier(source,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_GENERAL,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT);finish();stage_read(static_cast<char*>(data)+offset,payload);downloadBytes+=chunk;row+=rows;}
 }
 VkPipeline pipeline(const uint32_t* words,size_t bytes,const char* passName){VkShaderModule module=VK_NULL_HANDLE;VkShaderModuleCreateInfo mi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};mi.codeSize=bytes;mi.pCode=words;check(vkCreateShaderModule(device,&mi,nullptr,&module),"vkCreateShaderModule");VkComputePipelineCreateInfo pi{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};pi.layout=pipelineLayout;pi.stage.sType=VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;pi.stage.stage=VK_SHADER_STAGE_COMPUTE_BIT;pi.stage.module=module;pi.stage.pName="main";VkSpecializationMapEntry entry{0,0,sizeof(uint)};VkSpecializationInfo specialization{1,&entry,sizeof(uint),&workgroupSize};pi.stage.pSpecializationInfo=&specialization;VkPipeline result=VK_NULL_HANDLE;auto status=vkCreateComputePipelines(device,VK_NULL_HANDLE,1,&pi,nullptr,&result);vkDestroyShaderModule(device,module,nullptr);std::string context=std::string(passName)+" on "+props.deviceName;check(status,context.c_str());return result;}
 void setup(const Snapshot& initial,const std::string& wanted,bool allowSoftware,float requestedBudgetFraction){validate_snapshot(initial);cfg=initial.cfg;if(!(requestedBudgetFraction>0.0f&&requestedBudgetFraction<=0.98f))throw std::runtime_error("Budget fraction must be >0 and <=0.98");budgetFraction=requestedBudgetFraction;
  VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};app.pApplicationName="Dawnwood Interactive DWI-N1";app.applicationVersion=VK_MAKE_VERSION(0,5,0);app.apiVersion=VK_API_VERSION_1_1;
  VkInstanceCreateInfo ci{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};ci.pApplicationInfo=&app;const char* validation="VK_LAYER_KHRONOS_validation";
  if(std::getenv("DAWNWOOD_VALIDATION")){uint n=0;check(vkEnumerateInstanceLayerProperties(&n,nullptr),"enumerate layers");std::vector<VkLayerProperties> layers(n);check(vkEnumerateInstanceLayerProperties(&n,layers.data()),"enumerate layers");for(auto& l:layers)if(std::string(l.layerName)==validation)validationEnabled=true;if(!validationEnabled)throw std::runtime_error("Validation requested but VK_LAYER_KHRONOS_validation is unavailable");ci.enabledLayerCount=1;ci.ppEnabledLayerNames=&validation;}
  VkDebugUtilsMessengerCreateInfoEXT debugInfo{VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT};
  const char* debugExtension=VK_EXT_DEBUG_UTILS_EXTENSION_NAME;
  if(validationEnabled){debugInfo.messageSeverity=VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;debugInfo.messageType=VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT|VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT;debugInfo.pfnUserCallback=validation_message;debugInfo.pUserData=this;ci.enabledExtensionCount=1;ci.ppEnabledExtensionNames=&debugExtension;ci.pNext=&debugInfo;}
  check(vkCreateInstance(&ci,nullptr,&instance),"vkCreateInstance Vulkan 1.1");
  if(validationEnabled){auto createMessenger=reinterpret_cast<PFN_vkCreateDebugUtilsMessengerEXT>(vkGetInstanceProcAddr(instance,"vkCreateDebugUtilsMessengerEXT"));if(!createMessenger)throw std::runtime_error("Validation requires VK_EXT_debug_utils callback support");check(createMessenger(instance,&debugInfo,nullptr,&messenger),"vkCreateDebugUtilsMessengerEXT");}
  uint n=0;check(vkEnumeratePhysicalDevices(instance,&n,nullptr),"enumerate devices");std::vector<VkPhysicalDevice> devices(n);check(vkEnumeratePhysicalDevices(instance,&n,devices.data()),"enumerate devices");
  std::string available;int best=-1;for(auto d:devices){VkPhysicalDeviceProperties prop;vkGetPhysicalDeviceProperties(d,&prop);available+=std::string(prop.deviceName)+"; ";if(!wanted.empty()&&lower(prop.deviceName).find(lower(wanted))==std::string::npos)continue;if(prop.apiVersion<VK_API_VERSION_1_1)continue;if(prop.deviceType==VK_PHYSICAL_DEVICE_TYPE_CPU&&!allowSoftware)continue;int rank=prop.deviceType==VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU?3:(prop.deviceType==VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU?2:1);if(rank>best){physical=d;props=prop;best=rank;}}
  if(!physical)throw std::runtime_error("No matching Vulkan 1.1 GPU. Available: "+available+". CPU ICDs require --allow-software.");
  uint qn=0;vkGetPhysicalDeviceQueueFamilyProperties(physical,&qn,nullptr);std::vector<VkQueueFamilyProperties> qs(qn);vkGetPhysicalDeviceQueueFamilyProperties(physical,&qn,qs.data());queueFamily=UINT32_MAX;for(uint i=0;i<qn;++i)if(qs[i].queueCount&&(qs[i].queueFlags&VK_QUEUE_COMPUTE_BIT)){queueFamily=i;timestampBits=qs[i].timestampValidBits;if(!(qs[i].queueFlags&VK_QUEUE_GRAPHICS_BIT))break;}
  if(queueFamily==UINT32_MAX)throw std::runtime_error("No compute queue");
  VkDeviceSize sb=VkDeviceSize(cfg.count)*sizeof(State),ob=VkDeviceSize(cfg.opCount)*sizeof(Operator);
  if(sb>props.limits.maxStorageBufferRange)throw std::runtime_error("Requested state buffer exceeds maxStorageBufferRange; reduce count or partition workload");
  workgroupSize=tuning_value("DAWNWOOD_WORKGROUP_SIZE",64);if(workgroupSize!=32&&workgroupSize!=64&&workgroupSize!=128&&workgroupSize!=256)throw std::runtime_error("Workgroup size must be 32, 64, 128 or 256");
  if((uint64_t(cfg.opCount)+workgroupSize-1)/workgroupSize>props.limits.maxComputeWorkGroupCount[0])throw std::runtime_error("Operator mutation dispatch exceeds device workgroup limit");
  stateDispatchLimit=tuning_value("DAWNWOOD_DISPATCH_STATES",65536);
  if(stateDispatchLimit%workgroupSize||stateDispatchLimit>4194304||uint64_t(stateDispatchLimit)>uint64_t(props.limits.maxComputeWorkGroupCount[0])*workgroupSize)throw std::runtime_error("Dispatch states must be a multiple of the workgroup size, within the device limit and at most 4194304");
  if(props.limits.maxComputeWorkGroupInvocations<workgroupSize||props.limits.maxComputeWorkGroupSize[0]<workgroupSize||props.limits.maxComputeSharedMemorySize<31*sizeof(Operator)||props.limits.maxPushConstantsSize<sizeof(Config))throw std::runtime_error("Device cannot hold the selected workgroup, 31-operator shared LUT, or Config push constants");
  if(props.limits.maxPerStageDescriptorStorageBuffers<2||props.limits.maxPerStageDescriptorStorageImages<1||props.limits.maxPerStageDescriptorSampledImages<2||props.limits.maxPerStageDescriptorSamplers<2||props.limits.maxPerStageResources<5)throw std::runtime_error("Device descriptor limits cannot bind the state buffers and sampled/storage operator LUT images");
  uint perRow=std::min<uint>(256,props.limits.maxImageDimension2D/4);if(!perRow)throw std::runtime_error("Device image dimension cannot hold an operator");perRow=std::min(perRow,cfg.opCount);lutWidth=perRow*4;lutHeight=uint((uint64_t(cfg.opCount)+perRow-1)/perRow);if(lutHeight>props.limits.maxImageDimension2D)throw std::runtime_error("Operator LUT exceeds maxImageDimension2D");
  VkFormatProperties lutFormat{};vkGetPhysicalDeviceFormatProperties(physical,VK_FORMAT_R32G32B32A32_UINT,&lutFormat);VkFormatFeatureFlags lutRequired=VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT|VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT|VK_FORMAT_FEATURE_TRANSFER_SRC_BIT|VK_FORMAT_FEATURE_TRANSFER_DST_BIT;if((lutFormat.optimalTilingFeatures&lutRequired)!=lutRequired)throw std::runtime_error("RGBA32_UINT sampled/storage/transfer LUT format is unsupported");
  VkImageFormatProperties imageLimits{};check(vkGetPhysicalDeviceImageFormatProperties(physical,VK_FORMAT_R32G32B32A32_UINT,VK_IMAGE_TYPE_2D,VK_IMAGE_TILING_OPTIMAL,VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT|VK_IMAGE_USAGE_TRANSFER_DST_BIT,0,&imageLimits),"Operator LUT image format capabilities");if(lutWidth>imageLimits.maxExtent.width||lutHeight>imageLimits.maxExtent.height||VkDeviceSize(lutWidth)*lutHeight*16>imageLimits.maxResourceSize)throw std::runtime_error("Operator LUT exceeds format-specific image limits");
  uint en=0;check(vkEnumerateDeviceExtensionProperties(physical,nullptr,&en,nullptr),"device extensions");std::vector<VkExtensionProperties> exts(en);check(vkEnumerateDeviceExtensionProperties(physical,nullptr,&en,exts.data()),"device extensions");for(auto& e:exts)if(std::string(e.extensionName)==VK_EXT_MEMORY_BUDGET_EXTENSION_NAME)budgetAvailable=true;
  VkPhysicalDeviceMemoryProperties2 mem2{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2};if(budgetAvailable)mem2.pNext=&budget;vkGetPhysicalDeviceMemoryProperties2(physical,&mem2);memory=mem2.memoryProperties;
  float priority=1;VkDeviceQueueCreateInfo qi{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};qi.queueFamilyIndex=queueFamily;qi.queueCount=1;qi.pQueuePriorities=&priority;
  VkDeviceCreateInfo di{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};di.queueCreateInfoCount=1;di.pQueueCreateInfos=&qi;const char* be=VK_EXT_MEMORY_BUDGET_EXTENSION_NAME;if(budgetAvailable){di.enabledExtensionCount=1;di.ppEnabledExtensionNames=&be;}check(vkCreateDevice(physical,&di,nullptr,&device),"vkCreateDevice");vkGetDeviceQueue(device,queueFamily,0,&queue);
  VkCommandPoolCreateInfo cp{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};cp.queueFamilyIndex=queueFamily;cp.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;check(vkCreateCommandPool(device,&cp,nullptr,&commandPool),"vkCreateCommandPool");VkCommandBufferAllocateInfo ca{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};ca.commandPool=commandPool;ca.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;ca.commandBufferCount=1;check(vkAllocateCommandBuffers(device,&ca,&command),"vkAllocateCommandBuffers");VkFenceCreateInfo fi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};check(vkCreateFence(device,&fi,nullptr,&fence),"vkCreateFence");
  VkSamplerCreateInfo sampler{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};sampler.magFilter=VK_FILTER_NEAREST;sampler.minFilter=VK_FILTER_NEAREST;sampler.mipmapMode=VK_SAMPLER_MIPMAP_MODE_NEAREST;sampler.addressModeU=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;sampler.addressModeV=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;sampler.addressModeW=VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;sampler.maxLod=0;check(vkCreateSampler(device,&sampler,nullptr,&lutSampler),"vkCreateSampler integer operator LUT");
  // Mali compilation needs smaller entry points. The override exercises this
  // same schedule under desktop validation without changing stored state ABI.
  const char* splitOverride=std::getenv("DAWNWOOD_SPLIT_EVOLUTION");
  splitEvolution=props.vendorID==0x13b5u||(splitOverride&&std::string(splitOverride)=="1");
  uint bindingCount=splitEvolution?6u:5u;
  VkDescriptorType descriptorTypes[6]={VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,VK_DESCRIPTOR_TYPE_STORAGE_BUFFER};VkDescriptorSetLayoutBinding bindings[6]{};for(uint i=0;i<bindingCount;++i){bindings[i].binding=i;bindings[i].descriptorCount=1;bindings[i].descriptorType=descriptorTypes[i];bindings[i].stageFlags=VK_SHADER_STAGE_COMPUTE_BIT;}
  VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};li.bindingCount=bindingCount;li.pBindings=bindings;check(vkCreateDescriptorSetLayout(device,&li,nullptr,&descriptorLayout),"vkCreateDescriptorSetLayout");
  VkPushConstantRange push{VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(Config)};VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};pli.setLayoutCount=1;pli.pSetLayouts=&descriptorLayout;pli.pushConstantRangeCount=1;pli.pPushConstantRanges=&push;check(vkCreatePipelineLayout(device,&pli,nullptr,&pipelineLayout),"vkCreatePipelineLayout");
  // Finish the driver's potentially large temporary compiler allocations before
  // occupying near-capacity state storage, especially on unified-memory phones.
  mutatePipeline=pipeline(mutate_spv,sizeof(mutate_spv),"vkCreateComputePipelines mutate");
  if(splitEvolution){
   splitPipelines[0]=pipeline(prepare_spv,sizeof(prepare_spv),"vkCreateComputePipelines prepare");
   splitPipelines[1]=pipeline(slope_spv,sizeof(slope_spv),"vkCreateComputePipelines slope");
   splitPipelines[2]=pipeline(combine_spv,sizeof(combine_spv),"vkCreateComputePipelines combine");
   splitPipelines[3]=pipeline(geometry_spv,sizeof(geometry_spv),"vkCreateComputePipelines geometry");
   splitPipelines[4]=pipeline(finish_spv,sizeof(finish_spv),"vkCreateComputePipelines finish");
  }else evolvePipeline=pipeline(evolve_spv,sizeof(evolve_spv),"vkCreateComputePipelines evolve");
  vkGetPhysicalDeviceMemoryProperties2(physical,&mem2);memory=mem2.memoryProperties;
  for(auto& b:states)make_buffer(b,sb,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT|VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
  for(auto& b:operators)make_image(b);
  if(splitEvolution)make_buffer(evolutionWork,VkDeviceSize(std::min(cfg.count,stateDispatchLimit))*sizeof(EvolutionScratch),VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
  VkDeviceSize textureBytes=VkDeviceSize(lutWidth)*lutHeight*16;make_buffer(staging,std::min<VkDeviceSize>(16u*1024u*1024u,std::max(sb,textureBytes)),VK_BUFFER_USAGE_TRANSFER_SRC_BIT|VK_BUFFER_USAGE_TRANSFER_DST_BIT,VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT);
  VkDescriptorPoolSize ps[3]={{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,splitEvolution?6u:4u},{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,4},{VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,2}};VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};dpi.maxSets=2;dpi.poolSizeCount=3;dpi.pPoolSizes=ps;check(vkCreateDescriptorPool(device,&dpi,nullptr,&descriptorPool),"vkCreateDescriptorPool");VkDescriptorSetLayout layouts[2]={descriptorLayout,descriptorLayout};VkDescriptorSetAllocateInfo da{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};da.descriptorPool=descriptorPool;da.descriptorSetCount=2;da.pSetLayouts=layouts;check(vkAllocateDescriptorSets(device,&da,sets),"vkAllocateDescriptorSets");
  for(uint p=0;p<2;++p){VkDescriptorBufferInfo bi[3]={{states[p].handle,0,sb},{states[1-p].handle,0,sb},{evolutionWork.handle,0,evolutionWork.size}};VkDescriptorImageInfo ii[3]={{lutSampler,operators[p].view,VK_IMAGE_LAYOUT_GENERAL},{VK_NULL_HANDLE,operators[1-p].view,VK_IMAGE_LAYOUT_GENERAL},{lutSampler,operators[1-p].view,VK_IMAGE_LAYOUT_GENERAL}};VkWriteDescriptorSet writes[6]{};for(uint i=0;i<bindingCount;++i){writes[i].sType=VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;writes[i].dstSet=sets[p];writes[i].dstBinding=i;writes[i].descriptorCount=1;writes[i].descriptorType=descriptorTypes[i];if(i<2)writes[i].pBufferInfo=&bi[i];else if(i==5)writes[i].pBufferInfo=&bi[2];else writes[i].pImageInfo=&ii[i-2];}vkUpdateDescriptorSets(device,bindingCount,writes,0,nullptr);}
  if(timestampBits){VkQueryPoolCreateInfo qp{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};qp.queryType=VK_QUERY_TYPE_TIMESTAMP;qp.queryCount=2;check(vkCreateQueryPool(device,&qp,nullptr,&queries),"vkCreateQueryPool");}
  begin();for(auto& b:operators)image_barrier(b,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_GENERAL,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT|VK_PIPELINE_STAGE_TRANSFER_BIT,0,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT|VK_ACCESS_TRANSFER_WRITE_BIT);finish();
  upload(states[0],initial.states.data(),size_t(sb));upload(operators[0],initial.ops.data(),size_t(ob));
 }
 void begin_compute(){begin();if(queries){vkCmdResetQueryPool(command,queries,0,2);vkCmdWriteTimestamp(command,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,queries,0);}}
 double finish_compute(){
  if(queries)vkCmdWriteTimestamp(command,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,queries,1);
  auto start=std::chrono::steady_clock::now();finish();double measured=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  if(queries){uint64_t times[2]{};check(vkGetQueryPoolResults(device,queries,0,2,sizeof(times),times,sizeof(uint64_t),VK_QUERY_RESULT_64_BIT|VK_QUERY_RESULT_WAIT_BIT),"vkGetQueryPoolResults");uint64_t delta=times[1]-times[0];if(timestampBits<64)delta&=(uint64_t(1)<<timestampBits)-1;measured=double(delta)*double(props.limits.timestampPeriod)*1e-9;}
  ++computeSubmissions;maxSubmissionSeconds=std::max(maxSubmissionSeconds,measured);return measured;
 }
 void compute_dependency(){barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT);}
 void bind_epoch(){vkCmdBindDescriptorSets(command,VK_PIPELINE_BIND_POINT_COMPUTE,pipelineLayout,0,1,&sets[parity],0,nullptr);}
 void mutate(){Config dispatch=cfg;dispatch.reserved0=0;vkCmdPushConstants(command,pipelineLayout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(Config),&dispatch);vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,mutatePipeline);vkCmdDispatch(command,uint((uint64_t(cfg.opCount)+workgroupSize-1u)/workgroupSize),1,1);compute_dependency();}
 void evolve(uint base,uint count){
  Config dispatch=cfg;dispatch.reserved0=base;uint groups=uint((uint64_t(count)+workgroupSize-1u)/workgroupSize);
  auto pass=[&](VkPipeline selected){vkCmdPushConstants(command,pipelineLayout,VK_SHADER_STAGE_COMPUTE_BIT,0,sizeof(Config),&dispatch);vkCmdBindPipeline(command,VK_PIPELINE_BIND_POINT_COMPUTE,selected);vkCmdDispatch(command,groups,1,1);compute_dependency();};
  if(!splitEvolution){pass(evolvePipeline);return;}
  // Reuse bounded scratch only after every dependent pass finishes this chunk.
  pass(splitPipelines[0]);for(uint stage=0;stage<4;++stage){dispatch.reserved1=stage;pass(splitPipelines[1]);}
  dispatch.reserved1=cfg.reserved1;pass(splitPipelines[2]);pass(splitPipelines[3]);pass(splitPipelines[4]);
 }
 void advance(uint steps){
  seconds=wallSeconds=0;if(!steps)return;
  if(uint64_t(cfg.epoch)+steps>UINT32_MAX)throw std::runtime_error("This binary's epoch ABI is uint32; checkpoint before changing the epoch representation");
  auto start=std::chrono::steady_clock::now();
  if(cfg.count<=stateDispatchLimit){
   // Keep ordinary small workloads batched, bounded to eight complete epochs.
   for(uint done=0;done<steps;){uint batch=std::min(std::min(8u,std::max(1u,524288u/cfg.count)),steps-done);begin_compute();
    for(uint k=0;k<batch;++k){bind_epoch();mutate();evolve(0,cfg.count);parity=1u-parity;++cfg.epoch;}
    seconds+=finish_compute();done+=batch;
   }
  }else{
   // One shared mutation and old population per epoch. Partition only independent
   // evolution writers; offset is transient and never enters the checkpoint ABI.
   for(uint k=0;k<steps;++k){
    for(uint64_t base=0;base<cfg.count;base+=stateDispatchLimit){
     begin_compute();bind_epoch();if(base==0)mutate();else compute_dependency();
     evolve(uint(base),uint(std::min<uint64_t>(stateDispatchLimit,uint64_t(cfg.count)-base)));seconds+=finish_compute();
    }
    parity=1u-parity;++cfg.epoch;
   }
  }
  wallSeconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();if(!queries)seconds=wallSeconds;totalEpochs+=steps;
 }
};
VulkanRuntime::VulkanRuntime(const Snapshot& s,const std::string& name,bool allowSoftware,float budgetFraction):p(new Impl){p->setup(s,name,allowSoftware,budgetFraction);}
VulkanRuntime::~VulkanRuntime()=default;
void VulkanRuntime::advance(uint steps){p->advance(steps);}
Snapshot VulkanRuntime::download(){Snapshot s;s.cfg=p->cfg;s.states.resize(s.cfg.count);s.ops.resize(s.cfg.opCount);p->read(p->states[p->parity],s.states.data(),s.states.size()*sizeof(State));p->read(p->operators[p->parity],s.ops.data(),s.ops.size()*sizeof(Operator));return s;}
double VulkanRuntime::last_seconds()const{return p->seconds;}
bool VulkanRuntime::software()const{return p->props.deviceType==VK_PHYSICAL_DEVICE_TYPE_CPU;}
std::string VulkanRuntime::device_json()const{
 VkPhysicalDeviceFeatures features{};vkGetPhysicalDeviceFeatures(p->physical,&features);VkFormatProperties bc5{},eac{},astc{};
 vkGetPhysicalDeviceFormatProperties(p->physical,VK_FORMAT_BC5_UNORM_BLOCK,&bc5);vkGetPhysicalDeviceFormatProperties(p->physical,VK_FORMAT_EAC_R11G11_UNORM_BLOCK,&eac);vkGetPhysicalDeviceFormatProperties(p->physical,VK_FORMAT_ASTC_4x4_UNORM_BLOCK,&astc);
 uint64_t buffers=p->staging.allocated+p->evolutionWork.allocated,images=0;for(auto& b:p->states)buffers+=b.allocated;for(auto& b:p->operators)images+=b.allocated;
 std::ostringstream o;
 o<<"{\"name\":"<<json_escape(p->props.deviceName)<<",\"vendor_id\":"<<p->props.vendorID<<",\"device_id\":"<<p->props.deviceID<<",\"api_version\":"<<p->props.apiVersion<<",\"driver_version\":"<<p->props.driverVersion
  <<",\"software_device\":"<<(software()?"true":"false")<<",\"validation_layer_enabled\":"<<(p->validationEnabled?"true":"false")<<",\"validation_errors\":"<<p->validationErrors.load()<<",\"validation_warnings\":"<<p->validationWarnings.load()
  <<",\"memory_budget_extension\":"<<(p->budgetAvailable?"true":"false")<<",\"requested_budget_fraction\":"<<p->budgetFraction<<",\"device_type\":"<<uint(p->props.deviceType)
  <<",\"states_heap_index\":"<<p->states[0].heapIndex<<",\"state_buffer_heaps\":["<<p->states[0].heapIndex<<","<<p->states[1].heapIndex<<"]"
  <<",\"workgroup_size\":"<<p->workgroupSize<<",\"state_dispatch_limit\":"<<p->stateDispatchLimit<<",\"compute_submission_count\":"<<p->computeSubmissions<<",\"max_submission_seconds\":"<<p->maxSubmissionSeconds
  <<",\"split_evolution\":"<<(p->splitEvolution?"true":"false")<<",\"evolution_dispatches_per_chunk\":"<<(p->splitEvolution?8:1)<<",\"evolution_scratch_record_bytes\":"<<sizeof(EvolutionScratch)<<",\"evolution_scratch_bytes\":"<<p->evolutionWork.size<<",\"evolution_scratch_allocated_bytes\":"<<p->evolutionWork.allocated
  <<",\"texture_compression_BC\":"<<(features.textureCompressionBC?"true":"false")<<",\"BC5_sampled_image\":"<<((bc5.optimalTilingFeatures&VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)?"true":"false")
  <<",\"EAC_RG11_sampled_image\":"<<((eac.optimalTilingFeatures&VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)?"true":"false")<<",\"ASTC_4x4_sampled_image\":"<<((astc.optimalTilingFeatures&VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT)?"true":"false")
  <<",\"max_compute_shared_memory_bytes\":"<<p->props.limits.maxComputeSharedMemorySize<<",\"max_storage_buffer_range\":"<<p->props.limits.maxStorageBufferRange
  <<",\"max_compute_workgroup_count_x\":"<<p->props.limits.maxComputeWorkGroupCount[0]<<",\"max_image_dimension_2d\":"<<p->props.limits.maxImageDimension2D<<",\"max_memory_allocation_count\":"<<p->props.limits.maxMemoryAllocationCount<<",\"timestamp_valid_bits\":"<<p->timestampBits
  <<",\"allocated_buffer_bytes\":"<<buffers<<",\"allocated_image_bytes\":"<<images<<",\"allocated_total_bytes\":"<<buffers+images<<",\"staging_bytes\":"<<p->staging.size<<",\"allocation_count\":"<<p->allocationCount
  <<",\"state_ping_pong_payload_bytes\":"<<uint64_t(p->cfg.count)*sizeof(State)*2<<",\"operator_lut_payload_bytes\":"<<uint64_t(p->cfg.opCount)*sizeof(Operator)*2
  <<",\"operator_lut_format\":\"RGBA32_UINT\",\"operator_lut_storage\":\"sampled_and_storage_VkImage\",\"operator_lut_width\":"<<p->lutWidth<<",\"operator_lut_height\":"<<p->lutHeight
  <<",\"operator_lut_texels_per_record\":4,\"operator_lut_point_fetch\":true,\"operator_lut_filtering\":false,\"operator_lut_parameter_precision_bits\":32,\"operator_lut_flag_word_bits\":32,\"operator_lut_used_orientation_mask\":1,\"operator_bytecode_bits_per_instruction\":4"
  <<",\"evolve_shared_operator_records\":31,\"evolve_shared_operator_bytes\":1984,\"mutate_shared_operator_bytes\":128,\"permanent_texture_cache_residence_proven\":false"
  <<",\"upload_bytes\":"<<p->uploadBytes<<",\"download_bytes\":"<<p->downloadBytes<<",\"completed_epochs\":"<<p->totalEpochs<<",\"advance_buffer_copy_commands\":0,\"advance_image_copy_commands\":0"
  <<",\"timer\":"<<json_escape(p->queries?"Vulkan device timestamps":"host fence wall time")<<",\"last_dispatch_seconds\":"<<p->seconds<<",\"last_wall_seconds\":"<<p->wallSeconds<<",\"heaps\":[";
 for(uint i=0;i<p->memory.memoryHeapCount;++i){if(i)o<<",";uint64_t bufferHeap=0,imageHeap=0;if(p->staging.heapIndex==i)bufferHeap+=p->staging.allocated;if(p->evolutionWork.heapIndex==i)bufferHeap+=p->evolutionWork.allocated;for(auto& b:p->states)if(b.heapIndex==i)bufferHeap+=b.allocated;for(auto& b:p->operators)if(b.heapIndex==i)imageHeap+=b.allocated;
  o<<"{\"index\":"<<i<<",\"size\":"<<p->memory.memoryHeaps[i].size<<",\"runtime_buffer_allocation_bytes\":"<<bufferHeap<<",\"runtime_image_allocation_bytes\":"<<imageHeap<<",\"runtime_allocation_bytes\":"<<p->heapAllocated[i]<<",\"device_local\":"<<((p->memory.memoryHeaps[i].flags&VK_MEMORY_HEAP_DEVICE_LOCAL_BIT)?"true":"false");if(p->budgetAvailable)o<<",\"budget_at_start\":"<<p->budget.heapBudget[i]<<",\"usage_at_start\":"<<p->budget.heapUsage[i];o<<"}";
 }
 o<<"]}";return o.str();
}
