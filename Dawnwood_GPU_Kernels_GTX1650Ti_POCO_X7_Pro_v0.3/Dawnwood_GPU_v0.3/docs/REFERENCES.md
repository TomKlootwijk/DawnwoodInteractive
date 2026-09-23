# Source and implementation references

**User-confirmed formalization baseline:** `source/Dawnwood_Interactive_Unified_v0.2.pdf`, 18 pages. Its bytes and the original discussion are unchanged; the historical `source/formalization_lineage_v0.4.json` records both hashes. The current full numerical definition is `FORMALIZATION_v0.5.md`, developed through the preserved v0.4 edition.

Arithmetic control reference: [Khronos GLSL specification, precise qualification](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html). Portable validation tooling was extracted from the [official LunarG Vulkan SDK](https://vulkan.lunarg.com/sdk/home); the downloaded archive matched its published checksum. `results/v0.4/layers_provenance.json` records the exact archive URL, version and file hashes. No SDK installer or system registration was needed for these desktop validation runs.

**Controlling project source:** `source/double-slit-theory.pdf`, supplied 24-page discussion. Technical requirements are mapped by page in `CLAIMS.md`. The owner's current device correction—GTX 1650 Ti laptop, 4 GB—is recorded in the laptop profile rather than retaining the older RTX laptop target from the source.

Primary technical references for the implementation and test protocols:

- Khronos, Vulkan synchronization examples: https://docs.vulkan.org/guide/latest/synchronization_examples.html
- Khronos, Vulkan specification (storage buffers, memory dependencies, format queries, limits): https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html
- Khronos, Android compute implementation tutorial: https://docs.vulkan.org/tutorial/latest/Advanced_Vulkan_Compute/12_Mobile_and_Embedded_Compute/02_android_compute.html
- Android Developers, Vulkan in the NDK: https://developer.android.com/ndk/guides/graphics/getting-started
- Android Developers, ADB: https://developer.android.com/tools/adb
- Android Developers, Android Gradle Plugin 8.7 release notes: https://developer.android.com/build/releases/past-releases/agp-8-7-0-release-notes
- Microsoft, block-compression definitions including BC4 and BC5: https://learn.microsoft.com/en-us/windows/win32/direct3d10/d3d10-graphics-programming-guide-resources-block-compression
- Xiaomi, POCO X7 Pro specification: https://www.mi.com/global/product/poco-x7-pro/specs/
- NVIDIA, Vulkan driver information: https://developer.nvidia.com/vulkan-driver
- Gradle, wrapper integrity verification: https://docs.gradle.org/current/userguide/gradle_wrapper.html

The new equations and record/ABI choices are described in `NUMERICAL_PROFILE.md`. External API/format documentation does not validate the source's stronger physics or universality assertions; those have their own evidence rows.
