# DWI-RESIDENT-0.1 implementation contract

This is an explicit finite numerical execution binding, not a recovered source equation or a completed eight-stage application. Source record identities, body/field/placement programs, recurrent anchors and returned state remain connected. An immutable validated function bank supplies executable expressions; resident handles choose which definition actually acts. This supports selection among authored programs, not synthesis of new instructions.

Each lane is an independent substrate instance with its own record table and state. It is not a population of wavefronts sharing one common LUT. The first component implements old-snapshot mutation, publication, explicit action calls and whole-instance continuation. Full catalogue and cycle integration remain required.

## Binary and buffers

Little endian `DWRD0001`, followed by eight uint32 words:
`count, recordCount, stateWidth, functionCount, heapWords, mutationSteps, actionSteps, reserved=0`.

Limits: count>0; 1..32 records; 1..64 state floats; 1..256 functions; 1..4096 steps in each plan; all computed sizes fit uint32 indices and host/device limits. XIR limits remain 256 instructions, 64 inputs, 32 outputs per function. Frame has 256 FP32 registers. Signature IDs are positive uint32 values; every function with the same signature has identical input/output widths.

Following the header are:

1. `recordCount` immutable four-word records: source index, body signature, field signature, placement signature. Source indices are unique. Ordinals address storage; source indices retain the source catalogue identity.
2. `functionCount` six-word descriptors: code offset, output-register offset, instruction count, input width, output width, signature. Offsets address the following uint32 heap. All expressions are validated before execution.
3. `heapWords` uint32 words containing XIR instructions and output-register lists.
4. `mutationSteps` eight-word instructions, then `actionSteps` eight-word instructions.
5. `count` instance images, each of `6+stateWidth+24*recordCount` words.

Image header: epoch, status, failure phase, failure target ordinal, failure step, failure detail. Initial success has the last five words zero. Epoch is at most 16777215. State floats follow, then live records. Each record has 24 words: body handle, field handle, placement handle, generation (uint32), then 20 finite FP32 values. The binding names those values, including recurrent anchor u/v/orientation. Handles are zero-based function indices and must match the immutable slot signature. Generation is at most 16777215. No unresolved handle is executable or accepted in this profile.

The configuration GPU buffer contains the eight header words plus all static metadata, heap and plans. Two instance buffers alternate as old and next images. Configuration and instances upload once; epochs dispatch and synchronize without host program edits/uploads. The checkpoint uses the identical file format and includes every program, plan, handle, parameter and state word.

## Explicit call plans

Every instruction is eight uint32 words. Unused words must be zero. `TARGET=0xffffffff` denotes the current mutation target; it is forbidden in action. Record-bank selector 0 means the old snapshot and 1 the complete candidate table. Mutation may only read/call bank0. Action record calls use bank1; explicit record reads may use either bank. All reads must refer to initialized frame registers; the frame resets before each target and before action.

| Opcode | Eight words, with trailing zero padding | Meaning |
|---|---|---|
| 0 | `0,dst,floatBits` | Finite constant into frame. |
| 1 | `1,dst,stateIndex,width` | Read consecutive old-state floats. |
| 2 | `2,dst,recordSelector,word,width,bank` | Read consecutive record words into floats. The first four words convert exact integers to FP32; later words preserve float bits. |
| 3 | `3,functionHandle,inputBase,outputBase` | Call fixed bank helper over consecutive frame inputs/outputs. |
| 4 | `4,recordSelector,slot,bank,inputBase,outputBase,signature` | Resolve current record slot (0body,1field,2placement), require the stated signature and execute its bank function. |
| 5 | `5,recordWord,frameSource,width` | Mutation only: write consecutive words of the current candidate record. |
| 6 | `6,stateIndex,frameSource,width` | Action only: write consecutive next-state floats. |
| 7 | `7,frameSource` | Require finite nonzero value. |
| 8 | `8,dst` | Read the old epoch as FP32. |
| 9 | `9,dst` | Mutation only: read current target's immutable source index as exact FP32. |
| 10 | `10,dst,src,width` | Copy initialized frame values with snapshot/memmove overlap semantics. |

Each mutation plan must write all 24 target words exactly once. Each action plan must write every state word exactly once. Helper and record call inputs must all be initialized; outputs may overwrite frame slots after inputs are copied. Opcode9 requires source indices exactly representable as FP32. Signature checking uses current handles, not frozen compile-time programs. Plans contain memory moves/calls; numerical laws live in the explicit bank programs.

## Epoch transaction

Copy the previous image to the candidate. If the old image already has a failure status, preserve it without advancing. Otherwise check epoch<16777215. For each target, execute mutation using the same immutable old state/table. All record writes are provisional. Validate each proposed handle, signature, finite parameter and exact integer; require generation=old generation+1. No candidate record is read during mutation. An optional reverse target traversal is a diagnostic and must preserve results.

After every record succeeds, action resolves the complete new record table and writes the next state. Commit by incrementing epoch only after action succeeds. Any failure restores every old state/record word, then writes the failure header. Thus even an action failure rolls back the preceding provisional mutation. Failures are instance-local. No partially published record or XIR failure's zero row becomes valid state.

Status codes: 1=XIR failure (detail retains XIR status); 2=invalid handle; 3=invalid integer; 4=signature mismatch; 5=generation mismatch; 6=nonfinite value; 7=plan require failure; 8=epoch limit. Failure phase is 1mutation, 2action or 3epoch control; target is ordinal for mutation and UINT32_MAX otherwise; step is the plan index (zero for epoch control). Detail is XIR status or the implicated word/index. The host must validate checkpoint headers consistently and reject malformed or nonfinite payloads before dispatch.

## Source obligations beyond the generic machine

The authored mutation plan must call the OLD mutation record and OLD pinion; transport must consume old anchors. Field rebinding must depend on old field plus new body and anchor. The mutator is one of the targets. A self-changed mutator governs the next epoch's mutation; new ordinary action definitions act after publication in this epoch. Generic memory/call validity alone does not prove these source dependencies: the selected binding and numerical intervention evidence must establish them.

The complete source cycle still needs PHI, split/parity, typed selection, dependent four-slot RK4 with two fourth-slot Y-up actions, primitive/divergence/coupling, RGBA/history/inverse and surface return. Do not rename this mutation/action component as that completed cycle.
