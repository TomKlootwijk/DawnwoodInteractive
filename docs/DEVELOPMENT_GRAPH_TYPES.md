# Development source-graph contracts

This compiler extension connects explicit nominal declarations to the [resident-v3 capacity](RESIDENT_V3_ABI.md). It is a foundation for the ongoing SDF-construction application.

`source_graph.apply_graph(..., resident_backend=source_resident_v3)` selects this capacity when lowering a definition. The public `Dawnwood-Graph.cmd` wrapper still targets v2; callers using v3 must explicitly declare its definition profile and compiler. This is a new compilation, not automatic checkpoint migration.

`DWI-GRAPH-TYPES-0.2` adds nominal program-opcode/index/size/revision and resource-coordinate/distance/area types. A definition may declare `source.graph_type_contracts` with `profile`, `states` and `functions`. State entries name additional real state slots. Function entries provide ordered `inputs` and `outputs` type maps matching actual numerical bindings. Existing state meanings and established source-role contracts cannot be overridden. Graphs using these declarations must explicitly select the extended type profile; every added state still needs one return.

The [direct compilation experiment](../output/source_development_2026-09-25/graph_contracts/REPORT.json) reproduces four earlier v2 program files byte for byte, recompiles their payloads unchanged under v3, lowers a 128-state extension with an explicitly typed helper, and rejects 11 invalid contract/capacity cases without modifying the caller's definition. These checks cover capacity and type integration. The complete resident SDF application remains pending.
