# 🎯 Semantic Web OWL Project - Status & Implementation Guide

**Project Date**: 27 March 2026  
**Team Deadline**: Before Wednesday Evening  
**Your Focus**: IIITH University Data  
**Status**: ⚠️ **CRITICAL PHASE** - Foundation issues need immediate fixing

---

## 📊 WHERE YOU CURRENTLY STAND

### ✅ What You Have
1. **Working Scrapers** for:
   - Courses (course_scraper_json.py)
   - Faculty (faculty_scraper_json.py)
   - URLs (web_scraper.py)

2. **Structured JSON Output**: Faculty data with ~117 records, properly formatted

3. **Team Infrastructure**: Common understanding that JSON→RDF→OWL is the pipeline

### ❌ What's Missing/Broken

| Issue | Current State | Why It Matters | Deadline Impact |
|-------|---------------|---------------|-----------------|
| **JSON→OWL Logic** | Undefined/unclear | Can't validate conversion | BLOCKING - Must fix |
| **Fallback Data** | Returns defaults on failure | Pollutes ontology | BLOCKING - Must fix |
| **MOWL-SOWL Mapping** | Manual/AI-dependent | Won't scale, no AI in production | HIGH PRIORITY |
| **Triplet Validation** | None | RDF quality unknown | BLOCKING - Must fix |

---

## 🔴 THE 3 CRITICAL ISSUES EXPLAINED

### Issue #1: JSON→OWL Conversion Logic Lacks Constraints

**What's Happening:**
```
Raw JSON Data → ??? (magic happens here) → OWL Ontology
```

**The Problem:**
```
Your scraped JSON:
{
  "name": "Dr. John Doe",
  "email": "john@iiit.ac.in",
  "department": "CSE"
}

After going through scraper → becomes:
Subject: ??? (Person? Faculty? Resource?)
Predicate: ??? (hasName? isNamed? name?)
Object: ??? (Literal? URI? Reference?)
```

**Why It Matters:**
- RDF triplets have **semantic meaning**: `(Subject, Predicate, Object)`
- Not all data can be any role: email ≠ subject, department ≠ object in all contexts
- Ontologies need **well-defined schema classes & properties**

**What You Need:**
Create a **JSON→RDF Mapping Schema** that defines:

```
RULE 1: Faculty Data Mapping
Input JSON Field          →  RDF Component    →  OWL Element
─────────────────────────────────────────────────────────────
{name}                   →  Object Literal   →  foaf:name
{email}                  →  Object Literal   →  foaf:mbox (or schema:email)
{department}             →  Object Reference →  schema:workLocation

RULE 2: Course Data Mapping
{course_code}            →  Object Literal   →  dc:identifier
{credits}                →  Object Literal   →  schema:creditPoints
{instructor}             →  Object Reference →  schema:instructor (LINKS to Faculty)
```

---

### Issue #2: Fallback/Default Data Corrupts Ontology

**What's Happening:**
```python
try:
    parse_webpage(url)
except:
    return {"name": "Unknown Faculty", "email": "unknown@iiit.ac.in"}  # ❌ BAD
```

**Why It's Critical:**
- Ontology is trained on data quality
- Default data = garbage in data out (GIGO)
- Makes debugging impossible: "Is this real faculty or default fallback?"

**Better Approach:**
```python
try:
    parse_webpage(url)
except Exception as e:
    # ✅ Option 1: Raise error (let user know it failed)
    raise ScraperError(f"Failed to parse {url}: {str(e)}")
    
    # ✅ Option 2: Return None with metadata
    return {
        "status": "PARSE_FAILED",
        "url": url,
        "error": str(e),
        "data": None  # No partial/default data
    }
    
    # ✅ Option 3: Partial data + confidence scores
    return {
        "name": extracted_name or None,
        "confidence": {"name": 0.8, "email": 0.0},
        "extraction_notes": ["Email not found on page"]
    }
```

---

### Issue #3: MOWL↔SOWL Mapping Automation

**Definitions:**
- **MOWL (Master OWL)**: Schema layer - defines classes, properties, constraints
  ```
  Example: Faculty (class), courses (property), email (datatype property)
  ```
- **SOWL (Schema OWL)**: Instance layer - actual data instances
  ```
  Example: "Dr. John Doe" is an instance of Faculty class
  ```

**Current Manual Process:** 👤 Manually map IIITH SOWL to standard MOWL schema

**Why Manual Mapping Fails at Scale:**
- 100s of colleges × 1000s of records = millions of manual mappings
- Inconsistent mappings between colleges
- Time-consuming and error-prone

**Automation Approach:**

1. **Dictionary/Lookup Mapping** (Simple)
```python
FIELD_TO_OWL_MAPPING = {
    "faculty_name": "foaf:name",
    "faculty_email": "foaf:mbox",
    "dept_name": "schema:name",
    "course_code": "dc:identifier",
    # ...
}
```

2. **Similarity-Based Matching** (Smarter)
```python
import difflib
def auto_map_field_to_ontology(field_name, ontology_schema):
    """
    Match SOWL field names to MOWL classes/properties using similarity
    """
    best_match = max(
        ontology_schema.properties,
        key=lambda p: difflib.SequenceMatcher(None, field_name, p).ratio()
    )
    return best_match
```

3. **Rule-Based Mapping** (Most Reliable)
```python
def map_email_field(value):
    if is_valid_email(value):
        return ("foaf:mbox", "http://xmlns.com/foaf/0.1/mbox")
    else:
        return ("schema:text", "Unparseable")

def map_phone_field(value):
    if is_valid_phone(value):
        return ("schema:telephone", "http://schema.org/telephone")
```

---

## 🔧 SOLUTION FRAMEWORK: Improved Parser/Scraper

Here's the structure for your **NEW improved scraper** that addresses all 3 issues:

### Core Components

```
improved_scraper/
├── schema_mappings.py       # JSON → RDF conversion rules
├── triplet_validator.py     # Validates RDF triplets
├── error_handler.py         # Proper error handling (no defaults)
├── owl_converter.py         # Converts validated JSON to OWL
└── mowl_sowl_mapper.py      # Auto-maps instances to schema
```

### Key Features Required:

1. **Explicit Mapping Schema**
   - Define which JSON fields → which RDF properties
   - Document WHY each mapping makes semantic sense

2. **Triplet Validation**
   ```
   Before adding to ontology:
   ✓ Subject is valid resource/URI
   ✓ Predicate is defined in schema
   ✓ Object matches expected datatype
   ✓ No conflicting information
   ```

3. **Error Handling Strategy**
   ```
   Per Record:
   - Extract with validate()
   - If fails: Log error + skip (don't default)
   - If succeeds: Generate valid triplet
   
   Final Output:
   {
       "processed": 100,
       "successful": 92,
       "failed": 8,
       "errors": [...]
   }
   ```

4. **MOWL-SOWL Auto-Mapping**
   - Template-based or similarity-based matching
   - Configurable for different college schemas

---

## 📝 RECOMMENDED TASKS (Before Wednesday)

### Task 1: Create Mapping Schema (Priority: CRITICAL)
**Goal**: Document how IIITH JSON → RDF triplets

**Steps:**
1. Open [faculty_scrap/iiith_fac.json](faculty_scrap/iiith_fac.json)
2. For each field, define:
   - OWL class/property it maps to
   - Why this mapping makes sense semantically
   - Example triplet for 1-2 records
3. Create `schema_mappings.json` in faculty_scrap/

**Example Output:**
```json
{
  "mappings": [
    {
      "source_field": "name",
      "owl_property": "foaf:name",
      "owl_namespace": "http://xmlns.com/foaf/0.1/",
      "datatype": "xsd:string",
      "reasoning": "Person name matches FOAF vocabulary standard",
      "example_triplet": {
        "subject": "https://iiit.ac.in/faculty/john-doe",
        "predicate": "foaf:name",
        "object": "Dr. John Doe"
      }
    },
    ... more mappings
  ]
}
```

### Task 2: Build Error Handler (Priority: HIGH)
**Goal**: Stop returning default data

**Steps:**
1. Create `error_handler.py` in faculty_scrap/
2. Modify `faculty_scraper_json.py` to use it
3. Test: Try scraping failing URLs → should raise/log errors

**Example:**
```python
class FailureRecord:
    def __init__(self, url, error, stacktrace):
        self.url = url
        self.error_type = type(error).__name__
        self.error_msg = str(error)
        self.timestamp = datetime.now()
        self.data = None  # IMPORTANT: No partial data
```

### Task 3: Build Triplet Validator (Priority: HIGH)
**Goal**: Validate RDF triplets before storing

**Steps:**
1. Create `triplet_validator.py`
2. Define validation rules for IIITH schema
3. Use in parsing pipeline

**Minimal Validator:**
```python
class RDFTripletValidator:
    def validate(self, subject, predicate, obj):
        """
        Returns: (is_valid, error_msg)
        """
        # Subject must be URI
        if not is_uri(subject):
            return False, f"Subject {subject} not a valid URI"
        
        # Predicate must be known property
        known_predicates = load_ontology_schema()
        if predicate not in known_predicates:
            return False, f"Predicate {predicate} not in schema"
        
        # Object must match expected type
        expected_type = known_predicates[predicate]['range']
        if not is_compatible_datatype(obj, expected_type):
            return False, f"Object {obj} not {expected_type}"
        
        return True, None
```

### Task 4: Auto-Map MOWL-SOWL (Priority: MEDIUM)
**Goal**: Automate schema-instance mapping

**Steps:**
1. Create `mowl_sowl_mapper.py`
2. Implement dictionary-based mapping (simplest first)
3. Document IIITH field names → standard MOWL properties

**Simple Implementation:**
```python
class MOWLSOWLMapper:
    def __init__(self, mowl_schema):
        self.schema = mowl_schema
        self.field_mappings = {
            "faculty_name": "foaf:name",
            "faculty_email": "foaf:mbox",
            # ... define all IIITH fields
        }
    
    def map_instance(self, sowl_instance):
        """Convert IIITH SOWL instance to standard MOWL instance"""
        mowl_instance = {}
        for sowl_field, value in sowl_instance.items():
            if sowl_field in self.field_mappings:
                mowl_property = self.field_mappings[sowl_field]
                mowl_instance[mowl_property] = value
        return mowl_instance
```

---

## 📋 WHAT TO PRESENT TUESDAY EVENING

### Your Submission Should Include:

1. **Schema Mapping Document**
   - All IIITH JSON fields → OWL properties
   - Semantic reasoning for each mapping
   - Example triplets

2. **Improved Scraper Script**
   - Addresses all 3 issues
   - Clear code comments explaining triplet generation
   - Proper error handling (no defaults)

3. **Sample Output**
   - Show: X records processed, Y successful, Z failed
   - Failed records: logged with reasons, NO partial data

4. **MOWL-SOWL Mapping Prototype**
   - Even if simple, shows you tried

5. **Learnings Document**
   - What you learned about RDF/OWL structure
   - Why your mappings make semantic sense
   - Constraints for valid triplets

---

## 🎓 KEY CONCEPTS TO UNDERSTAND

### RDF Triplets (Subject, Predicate, Object)

```
Example 1 (Faculty):
Subject:   https://iiit.ac.in/faculty/john-doe  (unique resource)
Predicate: foaf:name                             (property)
Object:    "Dr. John Doe"                        (value)

Example 2 (Relationship):
Subject:   https://iiit.ac.in/faculty/john-doe
Predicate: schema:teaches                        (relationship property)
Object:    https://iiit.ac.in/course/CS101      (reference to another resource)

NOT VALID:
Subject:   "Dr. John Doe"                        ❌ (must be URI, not text)
Predicate: "teaches"                             ❌ (must be full property URI)
Object:    "some random text"                    ❌ (depends on predicate range)
```

### URIs Must Be Consistent
```
Faculty John Doe:
- MUST always be: https://iiit.ac.in/faculty/john-doe
- Never: https://iiit.ac.in/john-doe
- Never: john-doe
- Never: 123456

Why? Other entities link to this URI. Inconsistency breaks relationships.
```

### Properties Must Be From Schema
```
Valid properties (from FOAF, schema.org, Dublin Core):
✓ foaf:name
✓ schema:email  
✓ dc:identifier
✓ schema:teaches

Invalid (made up):
❌ hasName
❌ faculty_email
❌ custom_property

Every property must be defined in ontology schema.
```

---

## 🚀 QUICK START: Your First Improved Scraper

Create `faculty_scrap/improved_faculty_scraper.py`:

```python
"""
Improved Faculty Scraper addressing TL's 3 issues:
1. Clear JSON→OWL mapping rules
2. Proper error handling (no defaults)
3. MOWL-SOWL auto-mapping preparation
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FacultyMappingSchema:
    """Defines JSON → RDF → OWL mapping rules"""
    
    MAPPINGS = {
        "url": {
            "owl_property": "dc:source",
            "datatype": "xsd:anyURI",
            "is_subject_key": True,  # Used to create subject URI
            "semantic_role": "Unique identifier in ontology"
        },
        "name": {
            "owl_property": "foaf:name",
            "datatype": "xsd:string",
            "is_subject_key": False,
            "semantic_role": "Faculty member's full name"
        },
        "email": {
            "owl_property": "foaf:mbox",
            "datatype": "xsd:string",
            "is_subject_key": False,
            "semantic_role": "Email contact information",
            "validation": lambda x: "@" in str(x) and "." in str(x)
        },
        "title": {
            "owl_property": "schema:jobTitle",
            "datatype": "xsd:string",
            "is_subject_key": False,
            "semantic_role": "Academic position/rank"
        },
        "department": {
            "owl_property": "schema:workLocation",
            "datatype": "xsd:string",
            "is_subject_key": False,
            "semantic_role": "Affiliated department/center"
        },
        "research_areas": {
            "owl_property": "schema:expertise",
            "datatype": "xsd:string",  # or reference to domain ontology
            "is_subject_key": False,
            "semantic_role": "Research interests/specializations"
        }
    }
    
    @staticmethod
    def get_mapping(field_name: str) -> Dict:
        """Get mapping for a field"""
        if field_name in FacultyMappingSchema.MAPPINGS:
            return FacultyMappingSchema.MAPPINGS[field_name]
        return None

class RDFTripletValidator:
    """Validates RDF triplets before adding to ontology"""
    
    def validate_subject(self, subject: str) -> Tuple[bool, Optional[str]]:
        """Subject must be a valid URI"""
        if not subject:
            return False, "Subject cannot be empty"
        if not subject.startswith(("http://", "https://")):
            return False, f"Subject must be URI, got: {subject}"
        return True, None
    
    def validate_triplet(self, subject: str, predicate: str, obj: any) -> Tuple[bool, Optional[str]]:
        """Validate complete triplet"""
        # Validate subject
        is_valid, error = self.validate_subject(subject)
        if not is_valid:
            return False, f"Subject validation: {error}"
        
        # Validate predicate
        if not predicate:
            return False, "Predicate cannot be empty"
        if not predicate.startswith(("foaf:", "schema:", "dc:", "xsd:")):
            return False, f"Predicate not from known ontology: {predicate}"
        
        # Validate object based on predicate
        # This is simplified; in production, check against schema
        if obj is None:
            return False, f"Object cannot be None for predicate {predicate}"
        
        return True, None

class ImprovedFacultyScraper:
    """
    Faculty scraper with:
    - Clear mapping rules (Issue #1)
    - Proper error handling (Issue #2)
    - MOWL-SOWL foundation (Issue #3)
    """
    
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.validator = RDFTripletValidator()
        self.schema = FacultyMappingSchema()
        
        # Statistics
        self.stats = {
            "total_records": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
    
    def create_subject_uri(self, faculty_record: Dict) -> str:
        """
        Create unique subject URI from faculty data
        
        Example: https://iiit.ac.in/faculty/john-doe
        """
        url = faculty_record.get('url', '')
        if url:
            # Extract meaningful part from URL
            faculty_slug = url.split('/')[-2] if url.endswith('/') else ''
            return f"https://iiit.ac.in/faculty/{faculty_slug}"
        
        raise ValueError("Cannot create subject URI: no URL field")
    
    def json_field_to_rdf_triplets(self, faculty_record: Dict) -> List[Tuple]:
        """
        Convert JSON faculty record to RDF triplets
        
        Issues Addressed:
        1. Clear mapping rules from schema
        2. Validates each triplet before creation
        3. Raises error on invalid data (no defaults)
        
        Returns: List of (subject, predicate, object) tuples
        """
        triplets = []
        
        # Create subject URI
        try:
            subject = self.create_subject_uri(faculty_record)
        except Exception as e:
            logger.error(f"Cannot create subject: {e}")
            raise
        
        # Process each field
        for field_name, value in faculty_record.items():
            if not value:
                continue  # Skip empty values (not partial defaults)
            
            # Get mapping for this field
            mapping = self.schema.get_mapping(field_name)
            if not mapping:
                logger.warning(f"No mapping for field '{field_name}', skipping")
                continue
            
            predicate = mapping['owl_property']
            
            # Validate field if validator exists
            if 'validation' in mapping:
                validator = mapping['validation']
                if not validator(value):
                    logger.warning(f"Field '{field_name}' failed validation: {value}")
                    continue
            
            # Create triplet
            triplet = (subject, predicate, value)
            
            # Validate triplet
            is_valid, error = self.validator.validate_triplet(subject, predicate, value)
            if not is_valid:
                logger.error(f"Invalid triplet: {error} - {triplet}")
                raise ValueError(f"Invalid triplet created: {error}")
            
            triplets.append(triplet)
            logger.debug(f"Created triplet: {subject} -> {predicate} -> {value}")
        
        return triplets
    
    def process_file(self) -> Dict:
        """
        Process JSON file and convert to RDF triplets
        
        Returns: Statistics about processing
        """
        logger.info(f"Starting processing of {self.input_file}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise
        
        faculty_records = data.get('faculty', [])
        self.stats['total_records'] = len(faculty_records)
        
        all_triplets = []
        
        for idx, record in enumerate(faculty_records, 1):
            try:
                triplets = self.json_field_to_rdf_triplets(record)
                all_triplets.extend(triplets)
                self.stats['successful'] += 1
                logger.info(f"Record {idx}/{len(faculty_records)}: SUCCESS - {len(triplets)} triplets")
                
            except Exception as e:
                self.stats['failed'] += 1
                error_entry = {
                    "record_index": idx,
                    "name": record.get('name', 'Unknown'),
                    "url": record.get('url', 'Unknown'),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
                self.stats['errors'].append(error_entry)
                logger.error(f"Record {idx}/{len(faculty_records)}: FAILED - {e}")
        
        # Save results
        output_data = {
            "metadata": {
                "source": "Improved Faculty Scraper v2",
                "created": datetime.now().isoformat(),
                "schema_version": "1.0",
                "addressing_issues": [
                    "Clear JSON->OWL mapping rules",
                    "Proper error handling (no defaults)",
                    "MOWL-SOWL mapping foundation"
                ]
            },
            "statistics": self.stats,
            "triplets": [
                {
                    "subject": s,
                    "predicate": p,
                    "object": o,
                }
                for s, p, o in all_triplets
            ]
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processing complete. Results saved to {self.output_file}")
        logger.info(f"Statistics: Processed={self.stats['total_records']}, "
                   f"Successful={self.stats['successful']}, "
                   f"Failed={self.stats['failed']}")
        
        return self.stats

if __name__ == "__main__":
    scraper = ImprovedFacultyScraper(
        input_file="iiith_fac.json",
        output_file="iiith_fac_improved_triplets.json"
    )
    
    stats = scraper.process_file()
    print("\n=== PROCESSING SUMMARY ===")
    print(f"Total Records: {stats['total_records']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    if stats['errors']:
        print(f"\nErrors:")
        for error in stats['errors']:
            print(f"  - Record {error['record_index']}: {error['error']}")
```

---

## 📚 RESOURCES FOR UNDERSTANDING

1. **RDF/OWL Concepts:**
   - RDF: https://www.w3.org/RDF/
   - OWL: https://www.w3.org/OWL/
   - FOAF Vocabulary: http://xmlns.com/foaf/spec/

2. **Standard Vocabularies:**
   - schema.org (good for general data)
   - FOAF (good for people)
   - Dublin Core (DC) (good for metadata)

3. **Testing Your Triplets:**
   - Use OWL validators online
   - Check for URI consistency
   - Verify predicates exist in schema

---

## ⏰ TIMELINE

| When | What | Deliverable |
|------|------|-------------|
| **Today (Mar 27)** | Understand issues, create mapper | Schema + validation |
| **Tomorrow** | Build improved scraper | Working code + output |
| **Tue Evening** | Team sync | Your implementation + learnings |
| **Wednesday** | Team selects best solution | Proceed with full migration |

---

**Good luck! Remember: Sir wants you to UNDERSTAND what you're doing, not just code it.**
