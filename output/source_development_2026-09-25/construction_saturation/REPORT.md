# Bounded load of the resident construction profile

The laptop reached **100% reported GPU utilization** while executing the source-connected construction profile. The final bounded continuation ran 16,384 instances for 1,024 additional epochs, preserving their existing state and reaching epoch **1,152**. Its recorded host submit-to-fence sum was **18.2902397 seconds**; the complete native process took about **22.49 seconds**.

All **14,319,616 returned mutable words** matched the corresponding CPU reference images exactly. Vulkan validation reported **0 errors and 0 warnings**, with no failed lanes. The independent domain reader passed every distinct template class.

## Two retained observations

The first fixed run used 16,384 instances and 128 epochs. It reached 100% utilization but completed its submit-to-fence waits in only 2.3259571 seconds, below the intended 10–30-second interval. That result remains in [the first summary](summary.json), with its raw checkpoint and telemetry.

The [continuation decision](continued_1024/protocol.json) was recorded before the longer run. It selected exactly 1,024 additional epochs from the existing GPU128 and CPU128 checkpoints. The eightfold duration estimate was based on the observed short interval, not on choosing favorable numerical results. No state was reset, no tolerance changed, and no further extension followed.

| Observation | First run | Fixed continuation |
|---|---:|---:|
| Instances |16,384 |16,384 |
| Requested epochs in this run |128 |1,024 |
| Final epoch |128 |1,152 |
| Committed GPU instance-epochs |2,097,152 |16,777,216 |
| Host submit-to-fence sum |2.3259571 s |18.2902397 s |
| Public native-process wall time |6.28 s |22.49 s |
| Native-window samples reporting 100% GPU |2 of 7 |16 of 23 |
| Maximum observed temperature |54°C |61°C |
| Maximum observed power |117.67 W |119.61 W |
| Maximum observed GPU memory used |305 MiB |305 MiB |
| Differing mutable words versus CPU |0 |0 |

The device was **NVIDIA GeForce RTX 5070 Ti Laptop GPU**, reporting 12,227 MiB total memory. Telemetry was sampled once per second around each native process, including setup and readback. The continuation's 16 samples at 100% are observations, not a proof of uninterrupted 100% activity between samples. This is a bounded compute-load check; 305 MiB use does not demonstrate full memory capacity, and the short campaign does not establish thermal equilibrium.

## What the comparison covers

The public compiler reproduced the default three-instance program SHA256 `c3af6851c99c3d1fb4285fedf14d6f45bfb18c096822d8ea92b09981c4daab90`. Each large-population lane is an exact copy of source template `lane modulo 3`, giving multiplicities 5,462, 5,461 and 5,461. The first three population images were mechanically extracted before GPU execution and used as the CPU inputs. The initial static bytes changed only at the count word.

CPU evaluation ran all three distinct initial classes for the same epoch counts. Every GPU lane was then compared byte for byte with its matching CPU result: complete instance header, state and all 32 live records. This checks the entire population through repeated classes; it is not a claim of 16,384 independently varied input cases. The configuration bytes remained unchanged during each native run, and the three extracted final GPU templates also matched the complete CPU checkpoint.

For continuation, both backends resumed their retained epoch 128 images. Every GPU input class already matched its CPU128 image before the run. The native output reports epoch 1,152 for all lanes. Thus the longer run also checks prolonged checkpoint continuation of the constructed definitions and their resident records.

## Domain state after the load

All three template programs contain five active nodes, three leaves and revision 2, with training coverage 9. They pass the exact packed-constant geometric admission check and separate boundary-oracle readout. Maximum observed query-distance error is 0 for these particular template queries. Maximum score error is approximately `8.3703e-7`, below the predeclared `2e-5` score threshold. These checks retain the declared resource metric, quota and objective; they do not convert a resource-preference region into an allocator guarantee.

The full source recurrence and normal resident record mutation run in every epoch. Construction is enabled in this profile. Once the nine declared training requests are covered, it keeps the accepted three-leaf programs while continuing the source recurrence. GPU execution used 1,024 dispatches and 16 submissions in the longer run, with device-local buffers and no per-epoch host read or upload reported by the native backend.

The CPU reference executes three templates while the GPU executes the whole repeated population. Their timings are therefore not a speedup comparison. The result establishes bounded load, exact parity for the tested classes, and continuation consistency for this numerical profile.

## Retained evidence

- [Final continuation summary](continued_1024/summary.json), [commands](continued_1024/commands.json) and [telemetry](continued_1024/telemetry.json).
- [Final raw GPU checkpoint](continued_1024/gpu.bin), [CPU reference](continued_1024/cpu_reference.bin), [extracted GPU templates](continued_1024/gpu_templates.bin) and [independent template results](continued_1024/gpu_template_results.json).
- [Initial protocol](protocol.json), [mechanical population preparation](preparation_receipt.json), [source compilation](source_compilation/) and [runtime snapshots](runtime/).
- [First direct experiment](experiment.txt), [continuation experiment](continued_1024/experiment.txt) and its [metadata-only lineage annotation](continued_1024/manifest_lineage_step.txt).

Large definition JSON may be losslessly archived with original-byte hashes recorded in `archive_receipts.json`. Raw checkpoints and the manifests needed to inspect the reference templates remain directly usable. The final artifact index records all retained file hashes.
