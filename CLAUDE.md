## Claude Preamble
<!-- VERSION: 2026-06-04-v51 -->
<!-- SYNC-SOURCE: ~/.claude/conventions/universal-claudemd.md -->

**Universal laws (§1–§55) load via user-level `~/.claude/conventions/` and are ALWAYS in context** — `universal-claudemd.summary.md` (≤50-line salient view, read FIRST) → `universal-claudemd.md` (full) + `project-hygiene.md`. Do **NOT** assume their content from memory; consult + verify before asserting (§34 / §43.6 / §43.7). The `## Active Cluster Playbooks` block below names this repo's situational playbooks **read-on-demand** (§49.10): Read the named playbook when its trigger fires — never guess its contents; always-load guardrails are inline. Sync: `~/.claude/scripts/sync-preambles.py` (manual cadence; run after any source edit).

## Active Cluster Playbooks (read-on-demand — §49.10; bodies at ~/.claude/conventions/playbooks/)
<!-- BEGIN PLAYBOOKS BLOCK (managed by sync-preambles.py — read-on-demand pointers per §49.10; bodies at ~/.claude/conventions/playbooks/) -->

These cluster playbooks apply to this repo. You do NOT know their contents from memory —
**Read the named file when its trigger fires; never assume** (§49.10, §34, §43.6). Bodies are
NOT inlined and NOT @-imported; the always-load GUARDRAILs below are the only parts that must
hold without a Read.

- `commercial-bound.md` — when: license / sponsor-readiness / graph-tool-output / white-label work. GUARDRAIL: never commit/ship GitNexus (PolyForm-NC) graph output from a commercial-bound repo — CGC is the canonical graph source.
- `brand-registry.md` — when: brand / positioning / brand-canon / cross-repo brand work.

<!-- END PLAYBOOKS BLOCK -->

---

# blob-pdf-exporter
Chrome MV3 browser extension (Cramraika public OSS) — combines `blob:` images on the current page into a single PDF, for document viewers that render pages as blob URLs.

## Stack
- Chrome **Manifest V3** extension, vanilla JS. Build via `Makefile`; packaged output in `dist/`. No backend.

## Status / Tier
- **Tier C** (OSS utility — no design system). Vagary Labs OSS surface; sponsor-ready.

## License classification: commercial-bound
Public OSS (permissive). Per `commercial-bound.md`: GitNexus (PolyForm-NC) graph output MUST NOT be committed/shipped; use CGC for any shippable graph artefact.

## Cross-references
- `~/.claude/conventions/repo-inventory.md` (fleet inventory; this repo added 2026-05-14)
- Sibling OSS utilities: `bulk`, `tldv_downloader`, `pulseboard`
