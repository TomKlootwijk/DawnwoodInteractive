#include <stdexcept>
#include <jni.h>
#include "runtime.hpp"
extern "C" JNIEXPORT jstring JNICALL Java_nl_dawnwood_kernel_MainActivity_nativeRun(JNIEnv* env,jclass,jobjectArray input){
 std::vector<std::string> args;
 try{jsize n=env->GetArrayLength(input);for(jsize i=0;i<n;++i){auto item=static_cast<jstring>(env->GetObjectArrayElement(input,i));const char* text=env->GetStringUTFChars(item,nullptr);if(!text)throw std::runtime_error("JNI string allocation failed");args.emplace_back(text);env->ReleaseStringUTFChars(item,text);env->DeleteLocalRef(item);}auto report=execute(args);return env->NewStringUTF(report.c_str());}
 catch(const std::exception& e){auto result=std::string("{\"error\":")+json_escape(e.what())+"}";return env->NewStringUTF(result.c_str());}
}
