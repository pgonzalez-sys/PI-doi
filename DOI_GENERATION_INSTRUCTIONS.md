# Psychopharmacology Institute - DOI Generation Instructions

## Overview

This document contains all instructions for generating Crossref DOI XML files for the Psychopharmacology Institute. Use this prompt when you need to generate new DOIs or update existing batches.

---

## Quick Start Command

To generate DOIs for all new publications (excluding already submitted):

```bash
cd "C:\Users\yello\Projects\psychopharmacology-doi"
python -m src.cli --output output/production/ --no-validate
```

---

## Publication Types That Need DOIs

| Type | Code Pattern | DOI Format | Example |
|------|--------------|------------|---------|
| **Video Lectures** | Numeric only (no letters) | `PI-VL{code}` | `57` → `10.64239/PI-VL57` |
| **Expert Consultations** | Starts with `EC` | `PI-{code}` | `EC088` → `10.64239/PI-EC088` |
| **Quick Takes** | Starts with `QT` | `PI-{code}` | `QT52` → `10.64239/PI-QT52` |
| **Brain Guides** | Starts with `BG` or `SBG` | `PI-{code}` | `BG014` → `10.64239/PI-BG014` |
| **CAPSmart Takes** | Starts with `CAP`, `CAPS`, or `CAPST` | `PI-{code}` | `CAPST01` → `10.64239/PI-CAPST01` |

### Section DOIs (for publications with sections)

Sections append the section number directly to the parent code:
- Parent: `10.64239/PI-VL57`
- Section 1: `10.64239/PI-VL5701`
- Section 2: `10.64239/PI-VL5702`
- etc.

---

## Publication Types to EXCLUDE (No DOI)

| Type | Code Pattern | Reason |
|------|--------------|--------|
| **Newsletter** | `NL...` | Not scholarly content |
| **Open Access** | `OA...` | Different content type |
| **Open Podcast** | `OPC...` | Podcast episodes |
| **Activities/Essays** | `SA...` | Activities, not publications |

---

## DOI Format Requirements

1. **All DOIs must be UPPERCASE**: `10.64239/PI-VL57` (not `pi-vl57`)
2. **Prefix**: Always `10.64239/PI-`
3. **Video Lectures**: Add `VL` prefix to numeric codes
4. **Remove hyphens**: `OPC-031` becomes `OPC031`
5. **Section numbers**: Append directly as 2 digits (`01`, `02`, etc.)

---

## Already Submitted DOIs (EXCLUDE FROM NEW BATCHES)

Update this list after each successful Crossref submission.

### Batch 1 - Submitted 2026-03-11
| Publication Code | DOI | Type | Sections |
|------------------|-----|------|----------|
| `EC088` | `10.64239/PI-EC088` | Expert Consultation | 0 |
| `102` | `10.64239/PI-VL102` | Video Lecture | 10 (VL10201-VL10210) |

**Total DOIs in Batch 1:** 12 (2 publications + 10 sections)

### Batch 2 - Submitted 2026-03-27
| Type | Code Range | Count | Sections |
|------|------------|-------|----------|
| Video Lectures | `VL000` - `VL101` (excluding VL102) | 101 | 994 |
| Expert Consultations | `EC001` - `EC086` (excluding EC088) | 81 | 0 |
| Quick Takes | `QT01` - `QT85` | 85 | 425 |
| Brain Guides | `BG001` - `BG021` | 21 | 105 |
| Special Brain Guides | `SBG2024`, `SBG2025` | 2 | 0 |
| CAPSmart Takes | `CAPST01` - `CAPST20` | 20 | 26 |

**Total DOIs in Batch 2:** 1,860 (310 publications + 1,550 sections)

#### Last Submitted Codes (Start from here for next batch)
| Type | Last Code | Notes |
|------|-----------|-------|
| Video Lectures | `VL101` | VL102 was in Batch 1 |
| Expert Consultations | `EC086` | EC088 was in Batch 1; EC082, EC087 not found |
| Quick Takes | `QT85` | |
| Brain Guides | `BG021` | |
| Special Brain Guides | `SBG2025` | |
| CAPSmart Takes | `CAPST20` | |

#### Missing/Gap Codes (not in WordPress)
- **EC**: EC004, EC009, EC011, EC067, EC082, EC087
- **VL**: VL11, VL19, VL28, VL33, VL55, VL64, VL88, VL99

---

## WordPress Configuration

### API Credentials (.env file)
Credentials are stored in the local `.env` file (not in repository for security).
Contact administrator for access.

### WordPress Fields Used
- `acf.pi_publication_code` - Publication code (e.g., "EC088", "57")
- `acf.pi_section_code` - Section code (if available)
- `acf.pi_key_points` - Used for abstract
- `acf.pi_learning_objectives` - Used for abstract (fallback)
- `coauthors` - Faculty/authors (via Co-Authors Plus plugin)

---

## Crossref Configuration

### Depositor Information
- **Name**: Psychopharmacology Institute
- **Email**: services@psychcampus.com
- **Registrant**: Psychopharmacology Institute

### Publisher Information
- **Name**: Psychopharmacology Institute
- **Place**: United States

### Schema
- **Version**: 5.4.0
- **Content Type**: Report (`report-paper`)

---

## File Locations

| File | Purpose |
|------|---------|
| `config/crossref_config.yml` | Crossref and publisher settings |
| `src/fetchers/publications.py` | Contains EXCLUDED_CODES list |
| `output/production/` | Production XML files |
| `output/production/doi_report.csv` | CSV report of generated DOIs |

---

## Step-by-Step Process for New DOI Batch

### 1. Verify Exclusions
Check that `src/fetchers/publications.py` has the correct `EXCLUDED_CODES`.

**Note:** All publications through 2026-03-27 have been submitted. The EXCLUDED_CODES set
contains all 312 submitted publication codes. For new publications, simply run the CLI -
it will automatically exclude already-submitted codes and only process new ones.

### 2. Test with One Publication
```bash
python -m src.cli --limit 1 --output output/test/ --no-validate
```
Review the generated XML to verify format.

### 3. Generate Full Batch
```bash
python -m src.cli --output output/production/ --no-validate
```

### 4. Review Output
- Check `output/production/crossref_batch_*.xml`
- Review `output/production/doi_report.csv`

### 5. Submit to Crossref
Upload XML file to Crossref admin portal.

### 6. Update This Document
After successful submission, add the new codes to the "Already Submitted DOIs" section above.

---

## Troubleshooting

### Authentication Error (401)
- Check `.env` file has correct credentials
- Verify WordPress Application Password is active

### No Publications Found
- Ensure `status=publish` filter is working
- Check WordPress has published courses

### Missing Sections
- Not all publications have sections
- Video Lectures, Quick Takes typically have sections
- Expert Consultations, Brain Guides typically don't

---

## Code Reference

### Key Files
- `src/cli.py` - Main CLI entry point
- `src/fetchers/publications.py` - WordPress data fetching + filtering
- `src/transformers/doi_generator.py` - DOI pattern generation
- `src/transformers/wp_to_crossref.py` - Data transformation
- `src/generators/xml_builder.py` - XML generation

### DOI Generation Logic (doi_generator.py)
```python
# Numeric codes get VL prefix (Video Lectures)
if code.isdigit():
    code = f"VL{code}"

# All codes uppercase, hyphens removed
code = code.upper().replace('-', '')

# Publication DOI: 10.64239/PI-{code}
# Section DOI: 10.64239/PI-{code}{section_number}
```

---

## Statistics (as of 2026-03-27)

| Metric | Count |
|--------|-------|
| Total publications in WordPress | 506 |
| Valid for DOI | 312 |
| Already submitted (Batch 1 + 2) | 312 |
| Remaining to process | 0 |
| Excluded (NL, OA, OPC, SA) | 194 |

### DOIs Registered
| Batch | Publications | Sections | Total DOIs |
|-------|--------------|----------|------------|
| Batch 1 (2026-03-11) | 2 | 10 | 12 |
| Batch 2 (2026-03-27) | 310 | 1,550 | 1,860 |
| **Total** | **312** | **1,560** | **1,872** |

### Breakdown by Type (All Submitted)
| Type | Count |
|------|-------|
| Video Lectures | 102 |
| Expert Consultations | 82 |
| Quick Takes | 85 |
| Brain Guides (BG) | 21 |
| Special Brain Guides (SBG) | 2 |
| CAPSmart Takes | 20 |

---

## Contact

For issues with this system, check:
- Generated logs for error details
- Crossref documentation: https://www.crossref.org/documentation/
- Repository: https://github.com/pgonzalez-sys/PI-doi
