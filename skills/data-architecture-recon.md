# data-architecture-recon

> Analyze an application's data layer and produce a sanitized report answering
> the questions that actually decide database design — before anyone argues
> about table sizes.

**Version:** v1
**Lineage:** distilled from years of entering large data-heavy enterprise
systems, where DB-design debates reliably collapse into storage-size
arguments — "N hundred million rows is pennies of disk" — a true number
answering the wrong question. The skill encodes the questions that are
usually missing from that debate: access patterns, mutation policy, growth
derivative, operational surface. Sibling of `recon-system-map` (that one
maps the whole system; this one goes deep on the data layer).
Sanitized-by-construction output comes from a career of working under NDA:
the report must be shareable without leaking anything.
**Use with:** any agent with read access to the repo (Claude Code, Codex,
Cursor); degrades gracefully to docs-only input.
**Strength:** the evidence rule and the sanitized output format are MUST.
The classification taxonomy and report section order are SHOULD — adapt to
the system's shape.

## Prompt

```
You are performing a read-only reconnaissance of this application's DATA
LAYER. Your goal: answer the questions that decide database design. You make
NO changes. Every claim must cite where it was observed (file / pattern
class); anything not derivable from code goes to the final section as an open
question — never as a guess.

PROCEDURE

1. Inventory the sources of truth.
   Locate: schema definitions (migrations, DDL, ORM models), data-loading
   code (batch jobs, ETL, ingestion endpoints), query layer (repositories,
   API handlers, report builders), infra config (DB engine, storage,
   replicas). List what exists and what is conspicuously absent.

2. Classify the data into three kinds. For every major table/collection:
   - REFERENCE / universe data — shared facts the app doesn't own
     (instruments, catalogs, calendars): one copy, versioned, slowly
     changing.
   - FACT / event data — what the business produces (positions,
     transactions, measurements): high-volume, time-keyed.
   - DERIVED / serving data — aggregates, caches, projections: rebuildable
     from the above.
   Flag any table that mixes kinds — that is usually where the pain lives.

3. Volumes and growth — ORDERS OF MAGNITUDE ONLY.
   Largest tables: row-count magnitude class (1M / 100M / 1B), row-width
   class (narrow ids+numbers vs wide JSON/text). Growth per day/load.
   Accumulated time horizon. State the DERIVATIVE, not just the snapshot:
   "at current rate, table X doubles in N months."

4. Write model.
   How data arrives: batch / stream / interactive. Mutation policy per major
   table: append-only vs update-in-place. How corrections/restatements are
   performed (UPDATE? compensating rows? reload?). Are loads idempotent and
   atomic — can a bad batch be rolled back as a unit? Is "what did we know
   on date D" answerable (versioning/snapshots) — YES / NO / partial?

5. Read model.
   From API/UI code, enumerate the top query shapes: point lookups,
   entity-slice reads (one parent + children on a date), time series,
   cross-entity aggregations, full scans. Which are latency-critical?
   Compare against physical layout: does clustering/index order serve the
   MAJORITY shape, and what serves the minority shape (second index?
   projection? nothing)?

6. Operational surface.
   Partitioning: present, by what key, prunable? Retention/archival: policy
   or infinite accumulation? Migration history: long/locking ALTERs on big
   tables? Index count vs write amplification on hot tables. Backup/restore
   and replication behavior under bulk loads. Data-quality observability:
   does anyone find out when a load is wrong, and how fast?

7. Findings → design levers. Map each finding to its standard lever:
   update-in-place corrections → append-only + load versions;
   mixed reference+fact table → split, version reference separately;
   on-the-fly aggregation in UI path → materialized serving projection;
   unbounded accumulation → date partitioning + retention via partition
   drop; long ALTERs → additive schema evolution on partitions;
   "what changed?" unanswerable → bitemporal keys (as_of + load_version).

OUTPUT FORMAT — SANITIZED BY CONSTRUCTION

Use GENERIC ROLE NAMES ("portfolio-like aggregate root", "instrument-like
reference entity", "daily fact table F1"). Keep a private glossary mapping
real names in a SEPARATE local file, never in the report. Orders of magnitude
only. No business identifiers, no client names, no actual values.

# Data Architecture Recon — <app codename>
## 1. Data inventory (kinds: reference / fact / derived)
## 2. Volume & growth (magnitude class, growth rate, doubling time)
## 3. Write model (arrival, mutation policy, corrections, atomicity,
     versioning: YES/NO/partial)
## 4. Read model (top-5 query shapes, latency-critical ones,
     layout match/mismatch)
## 5. Operational surface (partitioning, retention, migration pains,
     observability)
## 6. Top-5 risks, ranked (what breaks first as data grows)
## 7. Design levers (finding → standard lever, effort class S/M/L)
## 8. Open questions for system owners (what code could not answer)
```

## Notes & known limits

- NOT a performance audit: it reads code and schema, it does not run
  benchmarks. Magnitude classes come from migrations/configs/comments, and
  belong in section 8 when the code doesn't say.
- The sanitized format is a feature, not a constraint: the report is designed
  to be discussable outside the project (design reviews, consulting, chats
  with your own advisors) without leaking anything. Resist the urge to
  "just add the real names" — that property is the point.
- Section 8 doubles as the agenda for the design meeting: the questions code
  cannot answer are exactly the ones the room must.
- On systems with several stores (OLTP + warehouse + caches), run per store,
  then write a one-page "flow between stores" preamble.

## Changelog

- v1 (2026-08) — initial form: questions-before-architecture discipline,
  standard-levers mapping, sanitized output contract.
