Diagnostic notes kept from debugging the Phase 2 real-robot runs (2026-06-15).

Each file documents one failure seen during a run: the launch command, the symptom,
the relevant log lines (trimmed — the raw output had hundreds of duplicate lines), the
cause, and the fix. They are reference material, not part of the code.

Most issues were intermittent and centred on Nav2 / localization and the camera
pipeline on the real robot.