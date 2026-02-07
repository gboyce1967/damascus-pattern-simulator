"""
Steel Database Module for Damascus Pattern Simulator

Contains physical properties, heat treatment specs, forging characteristics,
and material loss data for various steels used in Damascus pattern welding.

Supports both built-in steels and user-defined custom steels.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_CUSTOM_STEELS_PATH = MODULE_DIR / "custom_steels.json"


class Steel:
    """
    Represents a steel type with all its physical and forging properties.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize steel from dictionary.
        
        Args:
            data: Dictionary containing steel properties
        """
        # Basic info
        self.name = data.get('name', 'Unknown Steel')
        self.category = data.get('category', 'Custom')
        self.is_custom = data.get('is_custom', False)
        
        # Physical properties
        self.density = data.get('density', 0.284)  # lb/in³
        self.thermal_expansion = data.get('thermal_expansion', 7.0e-6)  # in/in/°F
        self.thermal_conductivity = data.get('thermal_conductivity', 20.0)  # BTU/hr/ft/F
        self.modulus_elasticity = data.get('modulus_elasticity', 30)  # psi x 10^6
        
        # Heat treatment
        self.austenitizing_temp = data.get('austenitizing_temp', (1500, 1500))  # °F (min, max)
        self.quench_method = data.get('quench_method', 'Oil')
        self.tempering_data = data.get('tempering_data', [])  # List of (temp, hardness) tuples
        
        # Forging properties
        self.forging_range = data.get('forging_range', (1650, 2150))  # °F (min, max)
        self.movement_level = data.get('movement_level', 5)  # 1-10 scale
        
        # Material losses
        self.scale_loss = data.get('scale_loss', (2.0, 5.0))  # % per hour (min, max)
        self.decarb_depth = data.get('decarb_depth', (0.020, 0.040))  # inches (min, max)
        
        # Visual properties
        self.etch_color = data.get('etch_color', 'medium')  # 'bright', 'medium', 'dark'
        
        # Optional notes
        self.notes = data.get('notes', '')
        
        # Metadata
        self.created_date = data.get('created_date', datetime.now().isoformat())
        self.created_by = data.get('created_by', 'Built-in')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert steel to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'category': self.category,
            'is_custom': self.is_custom,
            'density': self.density,
            'thermal_expansion': self.thermal_expansion,
            'thermal_conductivity': self.thermal_conductivity,
            'modulus_elasticity': self.modulus_elasticity,
            'austenitizing_temp': self.austenitizing_temp,
            'quench_method': self.quench_method,
            'tempering_data': self.tempering_data,
            'forging_range': self.forging_range,
            'movement_level': self.movement_level,
            'scale_loss': self.scale_loss,
            'decarb_depth': self.decarb_depth,
            'etch_color': self.etch_color,
            'notes': self.notes,
            'created_date': self.created_date,
            'created_by': self.created_by
        }
    
    def get_display_text(self) -> str:
        """Get formatted text for display in reference viewer."""
        # Note: We'll format bold in the GUI using tags, so we return tuples of (text, tag)
        # For now, return plain text with special markers that GUI will parse
        text = f"━━━ {self.name} ━━━\n\n"
        
        text += f"Category: {self.category}\n"
        if self.is_custom:
            text += f"[Custom Steel - Added by: {self.created_by}]\n"
        text += "\n"
        
        text += "═══ PHYSICAL PROPERTIES ═══\n\n"
        text += f"  Density:\n    {self.density:.3f} lb/in³\n\n"
        text += f"  Thermal Expansion:\n    {self.thermal_expansion:.2e} in/in/°F\n\n"
        text += f"  Thermal Conductivity:\n    {self.thermal_conductivity:.1f} BTU/hr/ft/F\n\n"
        text += f"  Modulus of Elasticity:\n    {self.modulus_elasticity} psi x 10^6\n\n"
        
        text += "\n═══ HEAT TREATMENT ═══\n\n"
        text += f"  Austenitizing Temperature:\n    {self.austenitizing_temp[0]}-{self.austenitizing_temp[1]}°F\n\n"
        text += f"  Quench Method:\n    {self.quench_method}\n\n"
        if self.tempering_data:
            text += "  Tempering (Double temper 2 hours each):\n"
            for temp, hardness in self.tempering_data:
                text += f"    {temp}°F → {hardness} HRC\n"
            text += "\n"
        
        text += "\n═══ FORGING CHARACTERISTICS ═══\n\n"
        text += f"  Forging Temperature Range:\n    {self.forging_range[0]}-{self.forging_range[1]}°F\n\n"
        text += f"  Movement Level:\n    {self.movement_level}/10 (1=easy, 10=very stiff)\n\n"
        text += f"  Scale Loss:\n    {self.scale_loss[0]:.1f}-{self.scale_loss[1]:.1f}% per hour of soak time\n\n"
        text += f"  Decarburization Depth:\n    {self.decarb_depth[0]:.3f}\"-{self.decarb_depth[1]:.3f}\" per session\n\n"
        text += f"  Etch Appearance:\n    {self.etch_color.capitalize()} (in Damascus patterns)\n\n"
        
        if self.notes:
            text += "\n═══ ADDITIONAL NOTES ═══\n\n"
            text += f"{self.notes}\n"
        
        return text


class SteelDatabase:
    """
    Manages built-in and custom steels.
    """
    
    def __init__(self, custom_steels_file: Optional[str] = None):
        """
        Initialize database with built-in steels and load custom steels.
        
        Args:
            custom_steels_file: Optional custom JSON path. Defaults to data/custom_steels.json.
        """
        if custom_steels_file:
            custom_path = Path(custom_steels_file)
            if not custom_path.is_absolute():
                custom_path = MODULE_DIR / custom_path
            self.custom_steels_file = custom_path
        else:
            self.custom_steels_file = DEFAULT_CUSTOM_STEELS_PATH
        self.steels: Dict[str, Steel] = {}
        
        # Load built-in steels
        self._load_builtin_steels()
        
        # Load custom steels
        self._load_custom_steels()
    
    def _load_builtin_steels(self):
        """Load built-in steel definitions."""
        builtin = {
            '1084': {
                'name': '1084 High Carbon Steel',
                'category': 'High Carbon',
                'density': 0.284,
                'thermal_expansion': 7.2e-6,
                'thermal_conductivity': 28.0,
                'modulus_elasticity': 30,
                'austenitizing_temp': (1500, 1500),
                'quench_method': 'Oil (Parks 50 or preheated Canola)',
                'tempering_data': [(350, 61.5), (400, 59.5), (450, 57.5)],
                'forging_range': (1650, 2150),
                'movement_level': 2,
                'scale_loss': (2.0, 5.0),
                'decarb_depth': (0.020, 0.040),
                'etch_color': 'dark',
                'notes': 'Normalizing: 1600F, hold 10 mins, air cool before hardening.',
                'is_custom': False
            },
            '15N20': {
                'name': '15N20 High Nickel Alloy Steel',
                'category': 'High Carbon / Nickel Alloy',
                'density': 0.284,
                'thermal_expansion': 7.1e-6,
                'thermal_conductivity': 26.5,
                'modulus_elasticity': 30,
                'austenitizing_temp': (1475, 1525),
                'quench_method': 'Oil',
                'tempering_data': [(350, 60), (400, 58), (450, 56)],
                'forging_range': (1650, 2100),
                'movement_level': 3,
                'scale_loss': (1.5, 3.0),
                'decarb_depth': (0.015, 0.025),
                'etch_color': 'bright',
                'notes': 'Composition: 0.75% C, 2.0% Ni. Provides bright layers in Damascus due to nickel resisting etchant.',
                'is_custom': False
            },
            'O1': {
                'name': 'O1 Oil-Hardening Tool Steel',
                'category': 'Low Alloy Tool Steel',
                'density': 0.283,
                'thermal_expansion': 7.7e-6,
                'thermal_conductivity': 19.0,
                'modulus_elasticity': 30,
                'austenitizing_temp': (1450, 1500),
                'quench_method': 'Warm oil (125-150°F)',
                'tempering_data': [(300, 64), (400, 62), (500, 59)],
                'forging_range': (1800, 2100),
                'movement_level': 5,
                'scale_loss': (1.5, 3.0),
                'decarb_depth': (0.015, 0.025),
                'etch_color': 'medium-dark',
                'notes': 'Annealing: 1450F, cool 20F/hr to 900F. Stress relief: 1200-1250F, 1 hour.',
                'is_custom': False
            },
            'A2': {
                'name': 'A2 Air-Hardening Tool Steel',
                'category': 'High Alloy Tool Steel',
                'density': 0.284,
                'thermal_expansion': 7.5e-6,
                'thermal_conductivity': 15.1,
                'modulus_elasticity': 29,
                'austenitizing_temp': (1750, 1800),
                'quench_method': 'Still air or positive pressure air to 150F',
                'tempering_data': [(350, 61), (400, 59.5), (500, 57.5)],
                'forging_range': (1850, 2150),
                'movement_level': 8,
                'scale_loss': (0.5, 2.0),
                'decarb_depth': (0.010, 0.020),
                'etch_color': 'medium',
                'notes': 'Preheat to 1100-1200F. Impact toughness: 40 ft-lbs at 60 HRC. High chromium provides dimensional stability.',
                'is_custom': False
            },
            'D2': {
                'name': 'D2 High-Carbon High-Chromium Tool Steel',
                'category': 'High Alloy Tool Steel',
                'density': 0.284,
                'thermal_expansion': 7.3e-6,
                'thermal_conductivity': 14.0,
                'modulus_elasticity': 29,
                'austenitizing_temp': (1825, 1875),
                'quench_method': 'Air or oil',
                'tempering_data': [(400, 61), (500, 59), (600, 57)],
                'forging_range': (1850, 2150),
                'movement_level': 9,
                'scale_loss': (0.5, 2.0),
                'decarb_depth': (0.010, 0.020),
                'etch_color': 'medium',
                'notes': '12% Chromium. Very stiff during forging. Requires heavy equipment.',
                'is_custom': False
            },
            'MagnaCut': {
                'name': 'CPM MagnaCut',
                'category': 'Powder Metallurgy',
                'density': 0.280,
                'thermal_expansion': 6.4e-6,
                'thermal_conductivity': 11.2,
                'modulus_elasticity': 31,
                'austenitizing_temp': (2050, 2050),
                'quench_method': 'Plate quench or fast air',
                'tempering_data': [(300, 62), (350, 61)],
                'forging_range': (1900, 2100),
                'movement_level': 10,
                'scale_loss': (0.5, 1.5),
                'decarb_depth': (0.005, 0.015),
                'etch_color': 'medium-bright',
                'notes': 'Must use foil wrap or vacuum. Requires cryogenic treatment after quench. Impact toughness: 16 ft-lbs at 62 HRC.',
                'is_custom': False
            },
            'CruWear': {
                'name': 'CPM CruWear',
                'category': 'Powder Metallurgy',
                'density': 0.282,
                'thermal_expansion': 7.0e-6,
                'thermal_conductivity': 10.5,
                'modulus_elasticity': 30,
                'austenitizing_temp': (1950, 2050),
                'quench_method': 'Air or plate quench',
                'tempering_data': [(1000, 62)],  # Triple temper
                'forging_range': (1900, 2100),
                'movement_level': 10,
                'scale_loss': (0.5, 1.5),
                'decarb_depth': (0.005, 0.015),
                'etch_color': 'medium',
                'notes': 'Preheat to 1550F. Triple temper at 1000F for max stability. Impact: 25-30 ft-lbs at 62 HRC.',
                'is_custom': False
            },
            '52100': {
                'name': '52100 Bearing Steel',
                'category': 'High Carbon / Low Chrome',
                'density': 0.284,
                'thermal_expansion': 7.0e-6,
                'thermal_conductivity': 24.0,
                'modulus_elasticity': 30,
                'austenitizing_temp': (1475, 1550),
                'quench_method': 'Oil',
                'tempering_data': [(350, 61), (400, 59), (450, 57)],
                'forging_range': (1700, 2100),
                'movement_level': 4,
                'scale_loss': (1.5, 3.5),
                'decarb_depth': (0.015, 0.030),
                'etch_color': 'dark',
                'notes': '~1.5% Chromium. Sensitive to overheating above 2150F (red shortness).',
                'is_custom': False
            }
        }
        
        for key, data in builtin.items():
            self.steels[key] = Steel(data)
    
    def _load_custom_steels(self):
        """Load custom steels from JSON file."""
        if self.custom_steels_file.exists():
            try:
                with self.custom_steels_file.open('r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                
                for key, data in custom_data.items():
                    data['is_custom'] = True
                    self.steels[key] = Steel(data)
                
                print(f"Loaded {len(custom_data)} custom steels from {self.custom_steels_file}")
            except Exception as e:
                print(f"Error loading custom steels: {e}")
    
    def save_custom_steels(self):
        """Save all custom steels to JSON file."""
        custom_data = {}
        
        for key, steel in self.steels.items():
            if steel.is_custom:
                custom_data[key] = steel.to_dict()
        
        self.custom_steels_file.parent.mkdir(parents=True, exist_ok=True)
        with self.custom_steels_file.open('w', encoding='utf-8') as f:
            json.dump(custom_data, f, indent=2)
        
        print(f"Saved {len(custom_data)} custom steels to {self.custom_steels_file}")
    
    def add_custom_steel(self, key: str, data: Dict[str, Any]) -> Steel:
        """
        Add a new custom steel.
        
        Args:
            key: Unique identifier for the steel
            data: Dictionary with steel properties
            
        Returns:
            The created Steel object
        """
        data['is_custom'] = True
        steel = Steel(data)
        self.steels[key] = steel
        self.save_custom_steels()
        return steel
    
    def get_steel(self, key: str) -> Optional[Steel]:
        """Get steel by key."""
        return self.steels.get(key)
    
    def get_all_steels(self) -> Dict[str, Steel]:
        """Get all steels (built-in and custom)."""
        return self.steels
    
    def get_steel_names(self) -> list:
        """Get list of all steel names."""
        return [steel.name for steel in self.steels.values()]
    
    def get_steels_by_category(self, category: str) -> Dict[str, Steel]:
        """Get all steels in a category."""
        return {k: v for k, v in self.steels.items() if v.category == category}
    
    def export_steel_for_github(self, steel: Steel) -> str:
        """
        Export steel data formatted for GitHub issue.
        
        Args:
            steel: Steel object to export
            
        Returns:
            Markdown-formatted text for GitHub issue
        """
        md = f"### New Steel Submission: {steel.name}\n\n"
        md += f"**Category:** {steel.category}\n"
        md += f"**Submitted by:** {steel.created_by}\n"
        md += f"**Date:** {steel.created_date}\n\n"
        
        md += "#### Physical Properties\n"
        md += f"- Density: {steel.density:.3f} lb/in³\n"
        md += f"- Thermal Expansion: {steel.thermal_expansion:.2e} in/in/°F\n"
        md += f"- Thermal Conductivity: {steel.thermal_conductivity:.1f} BTU/hr/ft/F\n"
        md += f"- Modulus of Elasticity: {steel.modulus_elasticity} psi x 10^6\n\n"
        
        md += "#### Heat Treatment\n"
        md += f"- Austenitizing: {steel.austenitizing_temp[0]}-{steel.austenitizing_temp[1]}°F\n"
        md += f"- Quench: {steel.quench_method}\n"
        if steel.tempering_data:
            md += "- Tempering:\n"
            for temp, hardness in steel.tempering_data:
                md += f"  - {temp}°F: {hardness} HRC\n"
        md += "\n"
        
        md += "#### Forging Characteristics\n"
        md += f"- Forging Range: {steel.forging_range[0]}-{steel.forging_range[1]}°F\n"
        md += f"- Movement Level: {steel.movement_level}/10\n"
        md += f"- Scale Loss: {steel.scale_loss[0]:.1f}-{steel.scale_loss[1]:.1f}% per hour\n"
        md += f"- Decarburization: {steel.decarb_depth[0]:.3f}\"-{steel.decarb_depth[1]:.3f}\"\n"
        md += f"- Etch Color: {steel.etch_color}\n\n"
        
        if steel.notes:
            md += "#### Notes\n"
            md += f"{steel.notes}\n\n"
        
        md += "---\n"
        md += "Please review this submission and consider adding it to the built-in steel database.\n"
        
        return md


# Global database instance
_database = None

def get_database() -> SteelDatabase:
    """Get or create the global steel database instance."""
    global _database
    if _database is None:
        _database = SteelDatabase()
    return _database
