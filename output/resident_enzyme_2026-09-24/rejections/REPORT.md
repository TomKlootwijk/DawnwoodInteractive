# Enzyme authoring rejection checks

Direct validation rejected all 58/58 designated malformed cases; the valid eight-observation application compiled successfully.

Source SHA-256: `2875592287d4905881422da819e55068cab9b4b2b20e985a1b673168a6419911`. It was unchanged at the end of the check.

The checks ran directly from an ephemeral shell-provided Python program. No GPU execution, numerical edits or persistent test implementation was used. The exact case descriptions and observed exceptions are in [summary.json](summary.json).

| Category | Cases | Rejected |
|---|---:|---:|
| application_inputs | 31 | 31 |
| json_reader | 3 | 3 |
| inherited_source_binding_guards | 13 | 13 |
| protected_law_identity | 7 | 7 |
| extension_source_plan_shape | 4 | 4 |

The valid control includes finite negative observations and uses the full application and generic resident compiler. The plan-shape cases exercise explicit extension guards; this report does not claim that all source-cycle checks were repeated. It also checks that an identical acceptance AST under a different function handle is rejected when substituted into one same-interface strategy family.

Only representative malformed cases were covered. Runtime behavior, mathematical accuracy and biochemical model validity are separate evidence.
