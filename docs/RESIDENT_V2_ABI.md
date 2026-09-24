# DWI-RESIDENT-0.2 execution contract

This version supplies typed body families and computed source-index lookup for the source application's heterogeneous calls. It is a finite evaluator, not by itself a completed application. Numerical source-cycle bindings and their evidence are separate. DWI-RESIDENT-0.1 and its artifacts remain unchanged.

## Layout

Little-endian magic `DWRD0002`; eight uint32 header words:
`count, recordCount, stateWidth, functionCount, heapWords, mutationSteps, actionSteps, familyCount`.
All v1 limits apply, plus 1..256 families and 1..32 methods per family.

Configuration follows this order:

1. `recordCount` four-word metadata entries: `[sourceIndex, bodyInterface, fieldSignature, placementSignature]`.
2. `functionCount` six-word XIR descriptors: `[codeOffset, outputsOffset, instructionCount, inputWidth, outputWidth, signature]`.
3. `familyCount` four-word family descriptors: `[interface, methodsOffset, methodCount, reservedZero]`.
4. `heapWords` words. Function offsets and method offsets are relative to this heap. Each method is a pair `[role, functionHandle]`, with roles strictly increasing; role zero is allowed. All families sharing an interface must have exactly the same ordered `(role, function signature)` pairs. Interfaces and signatures are positive uint32 IDs. Signature IDs retain identical input/output widths throughout the bank.
5. Mutation and action tapes, eight words per instruction.
6. Independent instance images, unchanged at `6+stateWidth+24*recordCount` words each.

Each live record's body handle now indexes a **family**, while its field and placement handles index functions. The immutable body interface constrains all permissible replacements. Thus one pinion body can contain anchor-transport and return roles, and one RK4 body can contain derivative and combination roles. Replacing that body replaces its complete method set atomically. Unused roles are never evaluated. Field/placement signatures, generation and finite parameter rules remain unchanged.

## Calls and lookup

All v1 tape opcodes retain their memory semantics. Opcode3 calls a fixed function. Opcode4 becomes:

`[4, ordinalOrTARGET, slot, bank, inputBase, outputBase, signature, role]`.

For body slot0, resolve the current family, then its requested role and exact signature. For slots1/2, role must be zero and the current function must match the signature. Static selectors must satisfy this contract during loading; TARGET must satisfy it for every mutation target.

Two additional opcodes take an initialized frame register containing a source index:

| Opcode | Words | Meaning |
|---|---|---|
| 11 | `[11, sourceIndexFrame, slot, bank, inputBase, outputBase, signature, role]` | Look up the actual source index and execute its current typed role. |
| 12 | `[12, dst, sourceIndexFrame, recordWord, width, bank, 0, 0]` | Look up the actual source index and read record words. |

Computed lookup requires a finite exact integer in `0..16777215`, then searches immutable source identities. Source indices are not ordinals and absent indices are never reduced modulo the table. A computed call may encounter an incompatible record; this is a lane failure, not a reason to require every heterogeneous record to have the same interface. The call signature must exist in the validated bank so the loader knows its input/output widths.

Mutation reads/calls only old records. Action calls new records; action reads may choose either table. Arguments are copied before results overwrite the frame. Body, field and placement handles are resolved when a call executes. All initialized-read, zero-padding and exactly-once destination-write checks remain mandatory.

## Arithmetic and failures

Opcodes0..17 retain v1 XIR meanings. Opcode18 is `log(x)` and opcode19 is `atan2(y,x)`, with the portable arithmetic and domains declared in [SOURCE_MATH_V2.md](SOURCE_MATH_V2.md). XIR reason5 is an invalid log domain; reason6 is an invalid atan2 domain. Reasons1..4 retain their v1 meanings.

Epoch transactions, common old snapshots, all-target publication, rollback and frozen failed images retain the [v1 contract](RESIDENT_ABI.md). Status1 carries the failing XIR instruction and reason. Status2 means an invalid family/function handle; status4 means a record slot's immutable interface/signature is violated. The new lookup failures are:

- status9: invalid computed source index; detail is the frame register index.
- status10: absent source index; detail is the requested exact integer.
- status11: computed-call role/signature mismatch; detail is the requested signature.

Static opcode4 incompatibility is rejected before execution. A runtime body-family method mismatch is status11 (validated static calls cannot reach it). Failure headers must be consistent with the stated tape step. After action rollback the discarded candidate body cannot be reconstructed; XIR failure validation bounds possible functions by the declared call signature. Computed mutation lookup likewise cannot reconstruct its transient frame, so validates against functions reachable through that role/signature in old records. Failure validation is structural validation, not a cryptographic execution proof.

The complete bank, families, tapes, current definitions, state and failure metadata survive checkpoints. A retained executable plan preserves its compiled cycle behavior; source JSON and stage names are retained alongside it by the compilation manifest. Execution validity alone does not establish source fidelity, domain validity, arbitrary expression synthesis, shared-LUT wavefront semantics or saturation.
