# Content Type Structure

## Overview

The system handles **two types of content structures** automatically:

### 1. Hierarchical (Parent + Child)
Publications with multiple sections that need parent-child DOI relationships.

**Content Types:**
- **Video Lectures** - Course with multiple video sections
- **Quick Takes** - Series with multiple episodes
- **CAPS/CAPS MARTEX** - Course with multiple sections
- **Expert Consultations** (future) - Will have multiple sections

**DOI Generation:**
- Publication DOI: `10.64239/pi-{code}`
- Section DOIs: `10.64239/pi-{code}-s01`, `s02`, `s03`, etc.
- Sections link to parent using Crossref relations

**Example:**
```
Publication: Antidepressant Withdrawal Effects (Code: 98)
├─ DOI: 10.64239/pi-98
├─ Section 1: Current Trends...
│  └─ DOI: 10.64239/pi-98-s01 (isPartOf: 10.64239/pi-98)
├─ Section 2: Neurobiological Mechanisms...
│  └─ DOI: 10.64239/pi-98-s02 (isPartOf: 10.64239/pi-98)
└─ ... (9 more sections)

Total: 12 DOIs (1 publication + 11 sections)
```

### 2. Single Level (No Sections)
Standalone publications without sections.

**Content Types:**
- **Brain Guides** - Comprehensive standalone guides
- **Open Access Publications** - Single article/paper
- **Expert Consultations** (current) - Single consultation

**DOI Generation:**
- Publication DOI only: `10.64239/pi-{code}`
- No section DOIs needed

**Example:**
```
Publication: "New" Antidepressants? A Quick Takes Episode (Code: OPC-031)
└─ DOI: 10.64239/pi-opc-031

Total: 1 DOI (publication only)
```

## How Detection Works

The system automatically detects content structure:

1. **Fetch publication** from WordPress
2. **Check for sections** using LearnDash API endpoint:
   - `GET /ldlms/v2/sfwd-courses/{id}/steps`
   - Extracts lesson IDs from response
3. **If sections found**:
   - Generate publication DOI
   - Generate section DOIs for each lesson
   - Link sections to parent with relations
4. **If no sections**:
   - Generate publication DOI only
   - Done

## Example Output

### Sample Batch with Mixed Content

**Input:** 3 publications
- 1 Brain Guide (no sections)
- 1 Quick Take (no sections)
- 1 Video Lecture (11 sections)

**Output:** 13 DOIs
- 3 publication DOIs
- 11 section DOIs (from video lecture only)

### DOI Report Format

The generated CSV shows the structure clearly:

```csv
Type,DOI,Title,Report Number,URL,Parent DOI,WordPress ID
Publication,10.64239/pi-bg-01,Brain Guide Title,BG-01,https://...,1200100
Publication,10.64239/pi-opc-031,Quick Take Episode,OPC-031,https://...,1200285
Publication,10.64239/pi-98,Antidepressant Withdrawal,98,https://...,1201848
Section,10.64239/pi-98-s01,Current Trends...,9801,https://...,10.64239/pi-98,1625317
Section,10.64239/pi-98-s02,Neurobiological...,9802,https://...,10.64239/pi-98,1625318
...
```

## Crossref Submission

Both types are included in the **same XML batch file**:

```xml
<doi_batch>
  <body>
    <!-- Standalone publication (no sections) -->
    <report-paper>
      <report-paper_metadata>
        <doi_data>
          <doi>10.64239/pi-opc-031</doi>
        </doi_data>
      </report-paper_metadata>
    </report-paper>

    <!-- Hierarchical publication (parent) -->
    <report-paper>
      <report-paper_metadata>
        <doi_data>
          <doi>10.64239/pi-98</doi>
        </doi_data>
      </report-paper_metadata>
    </report-paper>

    <!-- Hierarchical publication (child section) -->
    <report-paper>
      <report-paper_metadata>
        <rel:program>
          <rel:related_item>
            <rel:intra_work_relation relationship-type="isPartOf">
              10.64239/pi-98
            </rel:intra_work_relation>
          </rel:related_item>
        </rel:program>
        <doi_data>
          <doi>10.64239/pi-98-s01</doi>
        </doi_data>
      </report-paper_metadata>
    </report-paper>

    <!-- More sections... -->
  </body>
</doi_batch>
```

## Expected Scale

Based on your content mix (~300 publications):

### Breakdown by Type
- **~150 hierarchical** (video lectures, quick takes, CAPS)
  - Average 3-5 sections each
  - Publication DOIs: 150
  - Section DOIs: ~450-750

- **~150 standalone** (brain guides, open access)
  - Publication DOIs: 150
  - Section DOIs: 0

### Total Estimate
- **Publication DOIs: ~300**
- **Section DOIs: ~450-750**
- **Total DOIs: ~750-1050**

All within Crossref's single batch limit of 10,000 DOIs.

## Display Requirements

### For Hierarchical Publications

**Sidebar** (visible on all sections):
```
Antidepressant Withdrawal Effects and Safe Deprescribing

📄 Publication DOI: 10.64239/pi-98
   [Cite this course]
```

**Content Area** (section-specific):
```
Section 1: Current Trends in Antidepressant Use

Published: September 1, 2025
📄 Section DOI: 10.64239/pi-98-s01
```

### For Standalone Publications

**Content Area** (single DOI):
```
Brain Guide: Comprehensive Psychopharmacology

Published: September 1, 2025
📄 DOI: 10.64239/pi-bg-01
```

## Summary

✅ **Automatic detection** - no manual configuration needed
✅ **Handles both structures** - hierarchical and standalone
✅ **Single XML batch** - all DOIs in one submission
✅ **Clear reporting** - CSV shows structure for easy integration
✅ **Crossref compliant** - proper relations for hierarchical content

The system is fully ready for your mixed content types!
