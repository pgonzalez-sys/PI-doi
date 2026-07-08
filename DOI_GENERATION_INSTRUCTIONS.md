# Psychopharmacology Institute - DOI Generation Instructions

## Overview

This document contains all instructions for generating Crossref DOI XML files for the Psychopharmacology Institute. **Read this file fully before running a new batch** — it is the single source of truth for what's already been submitted and what to do next.

This is the **active** repository. A second repo, `psychopharmacology-doi`, is an earlier version of this same tool and has been superseded — do not use it.

---

## Quick Start Command

```bash
cd ~/path/to/PI-doi   # wherever you've cloned this repo locally
python -m src.cli --output output/production/ --no-validate
```

The tool automatically excludes anything already registered at Crossref (see "Safety net" below), so you can always just run this and it will only produce DOIs for genuinely new content.

---

## File Naming Convention

Every batch submitted to Crossref follows this pattern (matches what shows in the Crossref admin portal's submission history):

```
Psychopharmacology Institute-{batch number, 3 digits}-{MMDDYY}.xml
```

Example: `Psychopharmacology Institute-007-070826.xml` = batch 007, generated July 8, 2026.

Save the generated file locally under `DOI/Files to export to Crossref/` (in the Projects folder) using this name **before** uploading it to Crossref, and keep the `doi_report.csv` alongside it (same name + `-doi_report.csv` suffix) as a readable record of what's in the batch.

---

## Publication Types That Need DOIs

| Type | Code Pattern | DOI Format | Example |
|------|--------------|------------|---------|
| **Video Lectures** | Numeric (`57`) **or** `VL`-prefixed (`VL57`) — WordPress started storing the `VL` prefix directly in the code field around May 2026; both formats must be recognized | `PI-VL{code}` | `57` or `VL57` → `10.64239/PI-VL57` |
| **Expert Consultations** | Starts with `EC` | `PI-{code}` | `EC088` → `10.64239/PI-EC088` |
| **Quick Takes** | Starts with `QT` | `PI-{code}` | `QT52` → `10.64239/PI-QT52` |
| **Brain Guides** | Starts with `BG` or `SBG` | `PI-{code}` | `BG014` → `10.64239/PI-BG014` |
| **CAPSmart Takes** | Starts with `CAP`, `CAPS`, or `CAPST` | `PI-{code}` | `CAPST01` → `10.64239/PI-CAPST01` |

### Section DOIs (for publications with sections)

Sections append the section number directly to the parent code: `10.64239/PI-VL5701`, `10.64239/PI-VL5702`, etc.

**Any publication type can have sections, including Expert Consultations** (confirmed 2026-07-08 with `EC101`, which has 2 sections) — do not assume ECs or Brain Guides never have sections. The code fetches sections for every publication type automatically; there's nothing type-specific to configure.

---

## Publication Types to EXCLUDE (No DOI)

| Type | Code Pattern | Reason |
|------|--------------|--------|
| **Newsletter** | `NL...` | Not scholarly content |
| **Open Access** | `OA...` | Different content type |
| **Open Podcast** | `OPC...` | Podcast episodes |
| **Activities/Essays** | `SA...` | Activities, not publications |
| **VLX codes** | `VLX01`, `VLX02`, etc. | Old video lectures that are **not** DOI-eligible products (confirmed by Pamela 2026-07-08) — distinct from normal `VL##` codes |

---

## DOI Format Requirements

1. **All DOIs must be UPPERCASE**: `10.64239/PI-VL57` (not `pi-vl57`)
2. **Prefix**: Always `10.64239/PI-`
3. **Video Lectures**: `VL` prefix is added automatically if the WordPress code is bare numeric; left as-is if WordPress already includes it
4. **Remove hyphens**: `OPC-031` becomes `OPC031`
5. **Section numbers**: Append directly as 2 digits (`01`, `02`, etc.)

---

## Safety net: live Crossref check (added 2026-07-08)

`src/fetchers/publications.py` keeps a hardcoded `EXCLUDED_CODES` set as a historical record, but **that list is not the only thing preventing duplicates.** Every run of `fetch_all()` also queries Crossref's public API directly (`src/fetchers/crossref_registry.py`) for every DOI already registered under prefix `10.64239`, and excludes those too — live, every time, no maintenance required.

**Why this exists:** on 2026-07-08 we discovered `EXCLUDED_CODES` was badly out of date. Two manual batches (003, 004 — see history below) had been submitted to Crossref between March and May 2026 but were never added to this file, and the tool would have silently tried to re-generate DOIs for content that already had them. The live check makes that class of bug impossible going forward — if this list is ever forgotten again, Crossref's own record still catches it.

If Crossref's API can't be reached, the live check silently falls back to `EXCLUDED_CODES` alone (a warning is logged) — so it's still worth keeping that list reasonably current.

---

## Already Submitted DOIs — Batch History

**This table is the process record. After every successful Crossref submission, add a row here with the batch's actual contents** (grab the code list from the `doi_report.csv` generated alongside the XML). Don't rely on memory or the live check alone — future sessions need this written down.

| Batch | Filename | Submitted | Crossref ID | Publications | Sections | Total DOIs | Codes / Notes |
|-------|----------|-----------|--------------|---------------|----------|------------|----------------|
| 001 | `Psychopharmacology Institute-001-031126.xml` | 2026-03-11 | 1736825252 | 2 | 10 | 12 | `EC088`, `102`/`VL102` (+ 10 sections VL10201–10) |
| 002 | `Psychopharmacology Institute-002-032726.xml` | 2026-03-27 | 1739137244 | 310 | 1,550 | 1,860 | VL000–VL101 (excl. VL102), EC001–EC086 (excl. EC088), QT01–QT85, BG001–BG021, SBG2024/2025, CAPST01–20 |
| 003 | `Psychopharmacology Institute-003-042426.xml` | 2026-04-24 | 1743108910 | — | — | — | **Content not on file** — submitted directly, no local record kept. Covered by the live Crossref check regardless. |
| 004 | `Psychopharmacology Institute-004-051126.xml` | 2026-05-11 | 1746429999 | — | — | — | **Content not on file** — same as above. |
| 005 | `Psychopharmacology Institute-005-052926.xml` | 2026-05-29 | 1749852925 | 5 | 5 | 10 | `EC100` (+2 sections), `BG028`, `QT87` (+5 sections) |
| 006 | `Psychopharmacology Institute-006-052926.xml` | 2026-05-29 | 1749856057 | 2 | 10 | 12 | `VL102` (resubmitted with corrected metadata), `VL104` (+10 sections) |
| 007 | `Psychopharmacology Institute-007-070826.xml` | 2026-07-08 | 1755140916 | 5 | 18 | 23 | `EC101` (+2 sections), `BG023`, `BGCONGRESS2026`, `VL107` (+11 sections), `QT88` (+5 sections) — 23/23 succeeded, 0 failures |

**As of 2026-07-08, the total registered at Crossref (confirmed via live API query) is 1,951 DOIs** (1,928 through Batch 006, +23 from Batch 007). All 23 Batch 007 DOIs have also been written back into WordPress (see "Writing DOIs back into WordPress" below) and confirmed live.

### Excluded / not DOI-eligible (confirmed, do not include in future batches)
- `VLX01`, `VLX02` — old video lectures, not real products (Pamela, 2026-07-08)

---

## Writing DOIs back into WordPress (final step, after Crossref confirms)

Crossref registering a DOI does NOT put it on the website automatically. There's a WordPress ACF field, `pi_doi`, on both publications (`sfwd-courses`) and sections (`sfwd-lessons`), which is what actually displays the DOI on the page. This has to be written back manually via the WordPress REST API after each Crossref submission succeeds:

```
POST /wp-json/wp/v2/sfwd-courses/{id}   body: {"acf": {"pi_doi": "10.64239/PI-{CODE}"}}   (publications)
POST /wp-json/wp/v2/sfwd-lessons/{id}   body: {"acf": {"pi_doi": "10.64239/PI-{CODE}"}}   (sections)
```

The `doi_report.csv` generated alongside each batch's XML has the WordPress ID for every publication and section in that batch (`WordPress ID` column) — use it directly, don't look codes up again.

**Audit performed 2026-07-08:** checked every one of the 318 then-registered publications and their ~1,570 sections by walking each course's actual ordered step list (`ldlms/v2/sfwd-courses/{id}/steps`) and comparing the expected DOI (parent code + position) against what's live in `pi_doi`. Result: only ONE gap found — publication `EC088` (Batch 1, 2026-03-11) had never gotten its `pi_doi` written back. Fixed same day. Every section already matched correctly — the write-back process has otherwise been done reliably for every prior batch.

**Do NOT derive a section's code from its raw `pi_section_code` ACF field alone** — for older content that field is sometimes just a bare 1-2 digit position number (e.g. `"08"`) with no indication of its parent lecture, and guessing "bare number → add VL prefix" can collide with an unrelated publication's real code (this happened during the 2026-07-08 audit: a section with code `"08"` was nearly mismatched against the real, unrelated publication `VL08`). Always resolve a section's true code via its parent course's ordered step list, exactly as the generator itself does it.

---

## WordPress Configuration

### API Credentials (.env file)
Not committed to the repo. See `Accesses/PI_IP_Access_Reference.md` in the Projects folder for the current WordPress Application Password.

### WordPress Fields Used
- `acf.pi_publication_code` — Publication code (e.g., `EC088`, `VL57`)
- `acf.pi_section_code` — Section code (if available)
- `acf.pi_key_points` — Used for abstract
- `acf.pi_learning_objectives` — Used for abstract (fallback)
- `coauthors` — Faculty/authors (via Co-Authors Plus plugin)

---

## Crossref Configuration

- **Depositor**: Psychopharmacology Institute / services@psychcampus.com
- **Publisher**: Psychopharmacology Institute, United States
- **Schema**: Crossref 5.4.0, Content Type: Report (`report-paper`)

---

## Step-by-Step Process for a New DOI Batch

1. **Run the CLI** (see Quick Start above). It fetches WordPress, filters to valid/not-yet-registered codes (both via `EXCLUDED_CODES` and the live Crossref check), and writes `output/production/crossref_batch_<timestamp>.xml` + `doi_report.csv`.
2. **Review `doi_report.csv`** — sanity-check the codes and titles found. Watch for anything with an unfamiliar code pattern (like the `VLX` case) and flag it before including it.
3. **Rename** the XML to `Psychopharmacology Institute-{next batch #}-{MMDDYY}.xml` and save both it and the CSV into `DOI/Files to export to Crossref/` in the Projects folder.
4. **Submit to Crossref**: upload the XML via the Crossref admin portal.
5. **Update this document**: add a row to the Batch History table above with the real submission date/ID and the codes covered. This is required — it's what lets the next session pick up exactly where this one left off, instead of reconstructing it from Crossref or WordPress from scratch.
6. **Push to GitHub**: commit any code changes plus this file, push to `pgonzalez-sys/PI-doi`.

---

## Troubleshooting

### Authentication Error (401)
Check `.env` has the current WordPress Application Password (see `Accesses/PI_IP_Access_Reference.md`).

### Live Crossref check returns nothing / warning logged
Crossref's API may be briefly unreachable — the tool falls back to `EXCLUDED_CODES` only. Re-run once connectivity is confirmed before trusting the output as complete.

### Unfamiliar code prefix / format
Don't guess — ask before including it in a batch. This is exactly what happened with `VLX01`/`VLX02` and the `VL`-prefix format change; both needed a human call, not an assumption.

---

## Code Reference

- `src/cli.py` — CLI entry point
- `src/fetchers/publications.py` — WordPress fetch + code validation + exclusion filtering
- `src/fetchers/crossref_registry.py` — live Crossref registry check (safety net, added 2026-07-08)
- `src/transformers/doi_generator.py` — DOI pattern generation
- `src/transformers/wp_to_crossref.py` — data transformation
- `src/generators/xml_builder.py` — XML generation

---

## Contact

- Crossref documentation: https://www.crossref.org/documentation/
- Repository: https://github.com/pgonzalez-sys/PI-doi
