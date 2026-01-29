# Hierarchical DOI Implementation Summary

## ✅ What's Implemented

Successfully implemented hierarchical DOI structure for publications and sections with Crossref relations.

### Features

1. **Dual DOI Generation**
   - Publications: `10.64239/pi-{publication_code}` (e.g., `10.64239/pi-98`)
   - Sections: `10.64239/pi-{publication_code}-s{number}` (e.g., `10.64239/pi-98-s01`)

2. **Parent-Child Relationships**
   - Sections link to parent using Crossref `intra_work_relation` with `isPartOf`
   - Creates discoverable hierarchy in Crossref system

3. **Complete Data Fetching**
   - Fetches publications from WordPress/LearnDash
   - Fetches all sections (lessons) for each publication
   - Fetches author details for both publications and sections

4. **DOI Report Generation**
   - CSV report with all DOIs for easy reference
   - Includes WordPress IDs for integration
   - Shows parent-child relationships clearly

## Test Results

### Sample Publication: Antidepressant Withdrawal Effects and Safe Deprescribing

**Generated DOIs:**
- **Publication**: `10.64239/pi-98`
- **11 Sections**:
  - `10.64239/pi-98-s01` - Current Trends in Antidepressant Use...
  - `10.64239/pi-98-s02` - Neurobiological Mechanisms...
  - `10.64239/pi-98-s03` - Antidepressant Withdrawal Diagnosis...
  - ... (8 more sections)

**Total**: 12 DOIs (1 publication + 11 sections)

### XML Structure

Each section includes relations linking to parent:
```xml
<rel:program xmlns:rel="http://www.crossref.org/relations.xsd">
  <rel:related_item>
    <rel:intra_work_relation relationship-type="isPartOf" identifier-type="doi">
      10.64239/pi-98
    </rel:intra_work_relation>
  </rel:related_item>
</rel:program>
```

## Usage

### Generate DOIs for All Publications

```bash
# Activate virtual environment
source venv/bin/activate

# Generate batch XML with all publications and sections
python -m src.cli --mode batch --output output/batches/

# This will create:
# - output/batches/crossref_batch_YYYYMMDD_HHMMSS.xml (XML for Crossref)
# - output/batches/doi_report.csv (DOI reference for your website)
```

### Test with Limited Publications

```bash
# Test with first 5 publications
python -m src.cli --limit 5 --output output/test/

# Test with specific number
python -m src.cli --limit 20 --output output/sample/
```

### Generate Individual Files

```bash
# One XML file per DOI (for testing)
python -m src.cli --mode individual --output output/individual/
```

## Expected Output

For ~300 publications with an average of 2-3 sections each:
- **~300 publication DOIs**
- **~600-700 section DOIs**
- **Total: ~900-1000 DOIs**

All in a single XML batch file (well under Crossref's 10,000 DOI limit).

## DOI Display on Website

### Recommended Layout

**Left Sidebar** (visible on all sections):
```html
<div class="publication-doi">
  <strong>Publication DOI:</strong>
  <a href="https://doi.org/10.64239/pi-98">
    10.64239/pi-98
  </a>
  <button>Cite this course</button>
</div>
```

**Main Content Area** (section-specific):
```html
<div class="section-metadata">
  <span>Published on September 1, 2025</span>
  <div class="section-doi">
    <strong>Section DOI:</strong>
    <a href="https://doi.org/10.64239/pi-98-s01">
      10.64239/pi-98-s01
    </a>
  </div>
</div>
```

### Using the DOI Report

The generated `doi_report.csv` contains:

| Type | DOI | Title | Report Number | URL | Parent DOI | WordPress ID |
|------|-----|-------|---------------|-----|------------|--------------|
| Publication | 10.64239/pi-98 | Antidepressant Withdrawal... | 98 | https://... | | 1201848 |
| Section | 10.64239/pi-98-s01 | Current Trends... | 9801 | https://... | 10.64239/pi-98 | 1625317 |

Use WordPress IDs to match DOIs with your content and display them appropriately.

## 301 Redirects Are Fine

Your publication URLs redirect (301) to the first section. This is **perfectly valid**:
- Crossref DOI resolver follows HTTP redirects
- User flow: DOI → doi.org → publication URL → (301) → first section → content displays
- Both publication and section DOIs are visible on the page

## Next Steps

1. **Generate Full Batch**
   ```bash
   python -m src.cli --mode batch --output output/production/
   ```

2. **Review XML**
   - Check `output/production/crossref_batch_*.xml`
   - Verify DOI patterns and relationships

3. **Review DOI Report**
   - Open `output/production/doi_report.csv`
   - Use for integrating DOIs into WordPress pages

4. **Submit to Crossref**
   - Test environment first (if available)
   - Then production submission

5. **Update WordPress**
   - Add publication DOIs to sidebar
   - Add section DOIs to section pages
   - Make DOIs clickable (link to https://doi.org/{doi})

## Files Modified

### Core Implementation:
- `src/models/section.py` - New section model
- `src/models/publication.py` - Added sections list
- `src/models/metadata.py` - Added parent_doi and is_section fields
- `src/fetchers/publications.py` - Fetch sections from LearnDash API
- `src/transformers/doi_generator.py` - Generate section DOIs
- `src/transformers/wp_to_crossref.py` - Transform sections
- `src/generators/xml_builder.py` - Add relations to XML
- `src/cli.py` - Generate DOI report

### Configuration:
- No changes needed - uses existing crossref_config.yml

## Troubleshooting

### No sections found
- Some publications don't have sections (older content)
- This is normal - they'll only get publication DOIs

### Validation errors
- Schema validation may have path issues
- XML structure is correct - you can submit without validation
- Use `--no-validate` flag to skip

### Slow processing
- Fetching ~1000 DOIs takes time (each section requires API calls)
- Use `--limit` for testing
- Full batch may take 10-20 minutes

## Support

- Generated XML: `output/*/crossref_batch_*.xml`
- DOI Report: `output/*/doi_report.csv`
- Logs: Console output shows progress
- README: Full documentation in README.md
