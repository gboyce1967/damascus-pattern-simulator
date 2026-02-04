# Steel Database & Custom Steel Feature - Development Notes
**Date:** February 4, 2026  
**Project:** Damascus Pattern Simulator 3D  
**Feature:** Steel Metallurgical Properties Reference System

## Overview
Successfully implemented a comprehensive steel database system with built-in reference data and support for user-defined custom steels. This system allows users to:
- View detailed metallurgical properties for 8 built-in steels
- Add their own custom steel specifications
- Export custom steels as GitHub issues for sharing with the project
- Search through steel specifications with highlighting

## Implementation Summary

### Files Created
1. **`steel_database.py`** (413 lines)
   - `Steel` class: Represents a steel with all physical and forging properties
   - `SteelDatabase` class: Manages both built-in and custom steels
   - Singleton pattern with `get_database()` function
   - JSON-based persistence for custom steels (`custom_steels.json`)

2. **`test_custom_steel.py`** (181 lines)
   - Automated test suite for steel database functionality
   - Tests: creation, database operations, display formatting, GitHub export

### Files Modified
**`damascus_3d_gui.py`**
- Added "Reference" menu with 4 options:
  - Hardening & Tempering Guide
  - Steel Properties Database (with custom steel management)
  - Forging Losses Reference
  - Plasticity Guide
- Implemented comprehensive "Add Custom Steel" dialog (lines 2261-2491)
- Added helper methods for database UI operations

## Steel Data Structure

### Built-in Steels (8 total)
1. **1084** - High Carbon Steel
2. **15N20** - High Nickel Alloy Steel (bright etch layer)
3. **O1** - Oil-Hardening Tool Steel
4. **A2** - Air-Hardening Tool Steel
5. **D2** - High-Carbon High-Chromium Tool Steel
6. **MagnaCut** - Modern Stainless PM Steel
7. **CruWear** - Wear-Resistant Tool Steel
8. **52100** - Bearing Steel

### Properties Tracked
Each steel contains:

**Physical Properties:**
- Density (lb/in³)
- Thermal expansion coefficient (in/in/°F)
- Thermal conductivity (BTU/hr/ft/F)
- Modulus of elasticity (psi × 10⁶)

**Heat Treatment:**
- Austenitizing temperature range (°F)
- Quench method (oil/water/air/plate)
- Tempering data (temperature → hardness curves)

**Forging Characteristics:**
- Safe forging temperature range (°F)
- Movement level (1-10 scale: 1=easy, 10=very stiff)
- Scale loss percentage range per hour
- Decarburization depth range per session (inches)
- Etch color (dark/light/gray/mixed for Damascus contrast)

**Metadata:**
- Notes (normalizing procedures, special handling)
- Creation date
- Created by (Built-in vs User)
- Custom flag

## Custom Steel System

### Add Custom Steel Dialog Features
**Organized into 6 sections:**
1. Basic Information (name*, category*)
2. Physical Properties (4 fields)
3. Heat Treatment (austenitizing, quench, tempering data)
4. Forging Characteristics (6 fields)
5. Etching & Appearance
6. Additional Notes (free-form text)

**UI Features:**
- Scrollable canvas for all fields
- Inline tooltips with typical value ranges
- Dropdown menus for categorical data
- Input validation with error messages
- Tempering data parsed from semicolon-separated format
- Smart key generation from steel name (ensures uniqueness)

### Data Persistence
- Custom steels saved to `custom_steels.json` in project directory
- JSON format with full property dictionary
- Automatically loaded on application startup
- Separate from built-in steels (allows easy reset)

### GitHub Export Feature
Users can export custom steels as formatted markdown for GitHub issues:
- Structured markdown with clear sections
- All properties formatted for review
- Copy-to-clipboard functionality
- Direct link to create new issue
- Encourages community contributions

## Key Design Decisions

### 1. Dictionary-Based Constructor
Steel class uses dictionary constructor for flexibility:
```python
steel = Steel({
    'name': 'Custom Steel',
    'category': 'Tool Steel',
    # ... other properties
})
```
**Rationale:** Allows optional properties without complex parameter lists

### 2. Separate Custom Storage
Custom steels stored separately from code to avoid:
- Modifying source files during runtime
- Git conflicts with user data
- Loss of custom data on updates

### 3. Key Generation
Automatic key generation from steel name:
- Converts to lowercase
- Replaces spaces and hyphens with underscores
- Adds numeric suffix if key already exists
- Example: "1095 High Carbon" → "1095_high_carbon"

### 4. Validation Strategy
Minimal required fields (name + category) to lower barrier:
- Only 2 required fields
- All physical properties optional
- Allows partial data entry (e.g., just forging temps)
- User can expand data later

## User Workflow

### Adding a Custom Steel
1. Reference → Steel Properties Database
2. Click "➕ Add Custom Steel"
3. Fill in desired fields (minimum: name + category)
4. Click "✅ Save Steel"
5. Steel immediately available in database

### Exporting to GitHub
1. Reference → Steel Properties Database
2. Select custom steel from list (marked with ⭐)
3. Click "📤 Export to GitHub"
4. Markdown copied to clipboard
5. Paste into GitHub issue at provided URL

### Viewing Reference Data
1. Reference → Hardening & Tempering Guide
2. Select steel from tabs
3. Use Ctrl+F to search within viewer
4. Search highlights matches in yellow and scrolls to first match

## Testing

### Automated Test Coverage
✅ Custom steel creation  
✅ Database add/save/load operations  
✅ Display text formatting  
✅ GitHub export markdown generation  
✅ Unique key generation  
✅ JSON persistence  

**Test command:**
```bash
python3 test_custom_steel.py
```

### Manual Testing Checklist
- [ ] GUI launches without errors
- [ ] Reference menu opens all 4 viewers
- [ ] Steel Properties Database lists 8 built-in steels
- [ ] Add Custom Steel dialog scrolls properly
- [ ] Custom steel saves and appears in list with ⭐
- [ ] Export to GitHub copies markdown to clipboard
- [ ] custom_steels.json created in project directory
- [ ] Custom steels persist across application restarts

## Future Enhancements (Not Yet Implemented)

### Phase B: Steel Selection in Layer Configuration
- Replace hardcoded steel types in billet creation
- Multi-steel layer support (beyond 2 types)
- "+" button to add additional steel layers
- Steel property-based simulation adjustments

### Phase C: Property-Based Simulation
- Use movement_level to adjust forging simulation
- Scale loss affects billet dimensions over time
- Decarburization affects edge properties
- Different etch colors in pattern preview

### Phase D: Steel Recommendations
- Suggest steel combinations for specific patterns
- Warning for incompatible steel pairings
- Temperature range validation (ensure overlap)

## Known Limitations

1. **No Edit Function:** Can't modify custom steels after creation (must delete and re-add)
2. **No Delete Function:** Can manually edit `custom_steels.json` to remove
3. **No Import Function:** Can't import steels from GitHub issues (one-way export only)
4. **No Validation of Ranges:** Doesn't check if min < max for temperature ranges
5. **Not Yet Integrated:** Steel properties not used in actual simulation yet

## Code Architecture Notes

### Singleton Pattern for Database
```python
_database = None

def get_database() -> SteelDatabase:
    global _database
    if _database is None:
        _database = SteelDatabase()
    return _database
```
**Rationale:** Ensures single source of truth, avoids multiple file reads

### GUI Dialog Structure
- Uses Toplevel window with transient + grab_set for modal behavior
- Canvas + Scrollbar for scrollable content
- LabelFrame sections for visual grouping
- Helper function `create_entry()` reduces boilerplate
- Nested `save_custom_steel()` closure accesses entries dict

### Display Text Formatting
- Unicode box characters for visual hierarchy
- Property names followed by indented values
- Contextual help text (e.g., "1=easy, 10=very stiff")
- Consistent spacing for readability

## Data Sources

Original reference documents (content now embedded in code):
- `Hardening-tempering.txt` → 8 built-in steels
- `steel-plasticity.txt` → Movement level data
- `steel-losses-during-forging.txt` → Scale loss and decarb data

All data validated against:
- Steel manufacturer datasheets
- Knifemaker reference guides
- Forging community best practices

## Debugging Capabilities

### Logging
All steel operations logged:
```python
logger.info(f"Added custom steel: {name} with key: {key}")
logger.error(f"Error saving custom steel: {e}")
```

### Error Handling
- Try/except blocks around file I/O
- Validation error dialogs with specific messages
- Graceful handling of missing/malformed JSON
- Traceback logging for debugging

## Performance Considerations

- Database loaded once at startup (singleton pattern)
- JSON file operations only on add/delete (not on read)
- Display text computed on-demand (not cached)
- Search uses simple string matching (adequate for small datasets)

## Accessibility Features

- Keyboard navigation (Tab between fields)
- Mousewheel scrolling in dialog
- High contrast text in viewers (dark gray on white)
- Clear error messages
- Tooltips with example values

## Version Control Notes

**Git tracking:**
- `steel_database.py` ✓
- `damascus_3d_gui.py` (modified) ✓
- `test_custom_steel.py` ✓
- `DEVELOPMENT_NOTES_STEEL_DATABASE.md` ✓

**Git ignore:**
- `custom_steels.json` (user data, should be in .gitignore)

## Next Session TODO

Based on original plan, continue with:
1. **Option B Complete:** Finish custom steel dialog features
   - ✅ Add Custom Steel dialog (DONE)
   - ✅ Save/load functionality (DONE)
   - ✅ Export to GitHub (DONE)
   - ⬜ Edit existing custom steels (NOT YET)
   - ⬜ Delete custom steels (NOT YET)

2. **Option C:** Steel selection in layer configuration
   - Allow user to select steels from database for billet layers
   - Support >2 steel types in a billet
   - Update layer creation UI

3. **Option D:** Integrate properties into simulation
   - Use movement_level in forging calculations
   - Apply scale_loss to dimensions
   - Show etch_color in pattern preview

---

**End of Development Notes**  
*These notes should be kept in the project folder for reference during future development sessions.*
