# Dawnwood GPU v0.4 - actual status

**Partially validated.** Both physical GPUs execute the final kernel. Existing desktop CPU (30), Python (17), 29 active-operator coverage and CPU checkpoint replay checks pass. The GTX short 128-state/16-epoch comparison passes. The 257-state GTX comparison fails at epoch 96; the 128-state POCO comparison fails at epoch 1, at unchanged tolerances. POCO GPU execution completes 4096 states for 64 epochs with valid finite records.

Read `v0.4/VALIDATION.md` and `v0.4/summary.json` for the full evidence and limitations. Historical v0.3 status is preserved as `STATUS_v0.3.md` and `release_status_v0.3.json`.
