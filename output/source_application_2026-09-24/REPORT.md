# Original source application: reproduction and live definition edits

24 September 2026. All commands ran on the local laptop using the installed
Python with UTF-8 mode. This campaign executes the original v0.2 **symbolic**
application. It makes no GPU, numerical SDF evaluation or biochemical claim.

The original archive SHA-256 is
`4d2a178334b3532166e3873c0f8ebeca78b9dad41d66b347a53e85b42c9393be`.
All 40 extracted files are preserved. The archive's own manifest verifies its
39 listed files; the manifest itself is additionally covered by the extraction
[provenance](../../source_workbench/PROVENANCE.json).

| Direct observation | Result |
|---|---|
| Original existing check suite | 36 passed; no new tests written |
| 16-cycle reproduction | Complete snapshot equals the original shipped snapshot |
| Eight cycles, save, resume for eight | Complete snapshot equals uninterrupted 16 cycles |
| Edit `double_dot` at cycle eight, continue eight | Returned state identity changes; edited literal belongs to returned-state ancestry and all 31 resulting body ancestries |
| Edit `mutation` at the same saved cycle, continue eight | Returned state identity changes; the metarule edit belongs to returned-state ancestry and all 31 resulting body ancestries |
| Source integrity after execution | Original archive members remain byte-identical |

The unchanged final state identity is
`8962b81354a8af8e9dd63a779177ffbe1dd67cbb50f2b6cad7e213e08c2f0a57`.
The `double_dot` branch returns
`31d4c1e11eea5a4327d511599d8f48d1c05207e0e52ba143955ce81464bfe28a`;
the mutation-definition branch returns
`2f043f8b5f9ea5937b4523c63573a8f704d7f596c00043c5ad88e17cec11f707`.

These differences establish expression dependency propagation. A new symbol or
changed hash is not evidence of a numerically executed new coupling or mutation
law. The restored application's `Apply_SDF_operator` and mutation operations
construct graph nodes. Its nine numerical binding entries remain `null`.

## Reproduce and inspect

[commands.json](commands.json) contains every executed command, working directory
and exit code. Each command has separate stdout/stderr files. The original
checks' detailed output is [existing_checks.stderr.txt](existing_checks.stderr.txt).
[comparison.json](comparison.json) records snapshot comparisons and graph ancestry.

The saved [full](full16/snapshot.json), [continued](resume8/snapshot.json),
[body-edited](edited8/snapshot.json) and
[metarule-edited](mutation_edited8/snapshot.json) snapshots retain complete
graphs. The two edited branches start from the same
[epoch-eight snapshot](split8/snapshot.json), with the same session inputs.

The `double_dot` branch uses the source's own example edit. The metarule branch
uses [mutation_body_edit.json](mutation_body_edit.json), explicitly labelled a
symbolic dependency probe. Both use the original CLI's `--body-edit` facility.

The [literal application contract](../../docs/LITERAL_APPLICATION_CONTRACT.md)
sets the separate acceptance conditions for connecting this model to numerical
GPU execution. This restoration does not complete that integration.
