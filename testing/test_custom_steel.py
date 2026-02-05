#!/usr/bin/env python3
"""
Test script for custom steel database functionality.
Tests adding, loading, and exporting custom steels.
"""

from steel_database import Steel, get_database
import os
import json

def test_custom_steel_creation():
    """Test creating a custom steel."""
    print("=" * 60)
    print("TEST 1: Creating Custom Steel")
    print("=" * 60)
    
    # Create a custom steel
    custom_steel = Steel({
        'name': "1095 High Carbon Steel",
        'category': "High Carbon",
        'density': 0.283,
        'thermal_expansion': 7.5e-6,
        'thermal_conductivity': 29.0,
        'modulus_elasticity': 30,
        'austenitizing_temp': (1475, 1500),
        'quench_method': "Oil (Parks 50)",
        'tempering_data': [(400, 60.0), (450, 58.0), (500, 56.0)],
        'forging_range': (1700, 2200),
        'movement_level': 3,
        'scale_loss': (2.5, 5.5),
        'decarb_depth': (0.025, 0.045),
        'etch_color': "dark",
        'notes': "Excellent for Damascus. Very similar to 1084 but slightly higher carbon. Normalizing at 1600F recommended.",
        'is_custom': True
    })
    
    print(f"✓ Created custom steel: {custom_steel.name}")
    print(f"  Category: {custom_steel.category}")
    print(f"  Movement Level: {custom_steel.movement_level}")
    print(f"  Is Custom: {custom_steel.is_custom}")
    print()
    
    return custom_steel

def test_database_operations():
    """Test database add/save/load operations."""
    print("=" * 60)
    print("TEST 2: Database Operations")
    print("=" * 60)
    
    # Get database instance
    db = get_database()
    
    # Check built-in steels
    all_steels = db.get_all_steels()
    builtin_count = len([s for s in all_steels.values() if not s.is_custom])
    print(f"✓ Loaded {builtin_count} built-in steels")
    
    # Create and add custom steel
    custom_data = {
        'name': "Test Custom Steel XYZ",
        'category': "Tool Steel",
        'density': 0.285,
        'movement_level': 7,
        'etch_color': "light"
    }
    
    custom_steel = db.add_custom_steel('test_xyz', custom_data)
    print(f"✓ Added custom steel: {custom_steel.name}")
    
    # Verify it's in the database
    all_steels = db.get_all_steels()
    custom_count = len([s for s in all_steels.values() if s.is_custom])
    print(f"✓ Database now has {custom_count} custom steel(s)")
    
    # Check if custom_steels.json was created
    if os.path.exists('custom_steels.json'):
        with open('custom_steels.json', 'r') as f:
            data = json.load(f)
            print(f"✓ custom_steels.json created with {len(data)} steel(s)")
    
    print()
    return db

def test_steel_display():
    """Test steel display formatting."""
    print("=" * 60)
    print("TEST 3: Steel Display Text")
    print("=" * 60)
    
    db = get_database()
    
    # Get a built-in steel
    steel_1084 = db.get_steel('1084')
    if steel_1084:
        print("Display text for 1084:")
        print("-" * 60)
        display = steel_1084.get_display_text()
        # Show first 500 chars
        print(display[:500] + "..." if len(display) > 500 else display)
        print()
    
    return True

def test_github_export():
    """Test GitHub export formatting."""
    print("=" * 60)
    print("TEST 4: GitHub Export Format")
    print("=" * 60)
    
    # Create a sample custom steel
    custom_steel = Steel({
        'name': "SuperSteel 9000",
        'category': "Experimental",
        'density': 0.290,
        'thermal_conductivity': 32.0,
        'movement_level': 8,
        'forging_range': (1800, 2100),
        'etch_color': "mixed",
        'notes': "Fictional steel for testing export functionality.",
        'is_custom': True
    })
    
    db = get_database()
    markdown = db.export_steel_for_github(custom_steel)
    
    print("GitHub Issue Format:")
    print("-" * 60)
    print(markdown)
    print()
    
    return True

def cleanup():
    """Clean up test files."""
    print("=" * 60)
    print("CLEANUP")
    print("=" * 60)
    
    if os.path.exists('custom_steels.json'):
        os.remove('custom_steels.json')
        print("✓ Removed custom_steels.json")
    else:
        print("✓ No cleanup needed")
    print()

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "CUSTOM STEEL DATABASE TESTS" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    try:
        # Run tests
        test_custom_steel_creation()
        test_database_operations()
        test_steel_display()
        test_github_export()
        
        # Cleanup
        cleanup()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        cleanup()

if __name__ == "__main__":
    main()
