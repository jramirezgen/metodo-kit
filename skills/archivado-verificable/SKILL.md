---
name: archivado-verificable
description: Archive and retire large local workspaces safely using one rsync exclusion set, SHA-256 manifests, explicit COMPLETE markers, dry-run deletion, and a mandatory negative gate test. Use for repository consolidation, historical workspace cleanup, or durable archival where partial copies must never authorize deletion.
---

# Archivado verificable

Use this skill when moving a large frozen directory to durable storage before
retiring the source. It is deliberately fail-closed.

## Invariants

- The source is never deleted by `archivar_210526.sh`.
- Use the same exclusions to measure and to copy.
- `COMPLETE.txt` exists only after source and destination SHA-256 manifests
  match.
- `retirar_certificados.sh` rechecks both manifests before deletion and exits
  nonzero on any blocked candidate.
- Run its negative test after changing either script.

## Procedure

1. Freeze the source and identify code, raw inputs, results, and regenerable
   intermediates. Do not treat a partial destination as an archive.
2. Measure with the project exclusion file. Preserve clone URL plus commit for
   any third-party tree excluded as re-clonable.
3. Archive using the project-local symlink or set `WORKSPACE` explicitly when
   calling the canonical script from this skill.
4. Confirm `COMPLETE.txt`; only then run `retirar_certificados.sh` in dry-run.
5. Review its list, then use `--aplicar` in one deliberate deletion batch.
6. Record the final state in the project handoff and persistent wiki.

## Scripts

- `scripts/archivar_210526.sh`: resumable archive plus manifest generation.
- `scripts/retirar_certificados.sh`: dry-run by default; validates source and
  destination SHA-256 before removal.

Project-specific exclusion files, triage tables, clinical data policy, and
retention decisions stay in the project. They are not copied into this skill.
