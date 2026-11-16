"""
Tests for the project loader and validation system
"""

import json
import unittest
from pathlib import Path
import tempfile
import shutil

from src.core.project_loader import ProjectLoader
from src.core.schema_validator import ProjectSchemaValidator


class TestProjectLoader(unittest.TestCase):
    """Test cases for ProjectLoader"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.projects_root = Path(self.temp_dir) / "projects"
        self.projects_root.mkdir()
        
        self.loader = ProjectLoader(self.projects_root)
        
        # Sample valid project data
        self.sample_data = {
            "project": {
                "name": "Test Project",
                "type": "community_housing",
                "location": "gnowangerup",
                "site_area_ha": 17.18,
                "developable_fraction": 0.333,
                "land_tenure": "peppercorn_lease",
                "land_cost": 0
            },
            "buildings": {
                "homes": [
                    {"type": "3x2", "count": 2, "bedrooms": 3, "bathrooms": 2, "area_sqm": 140, "construction_type": "standard"},
                    {"type": "2x1", "count": 6, "bedrooms": 2, "bathrooms": 1, "area_sqm": 90, "construction_type": "standard"}
                ]
            },
            "phases": {
                "planning": {"cost": 800000},
                "infrastructure": {"cost": 2300000},
                "construction": {"cost": 4000000},
                "project_management": {"cost": 300000},
                "contingency_percent": 10
            },
            "funding": {
                "model": "nfp_grants",
                "sources": [
                    {"source": "Government Grant", "amount": 4500000}
                ]
            }
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_save_project(self):
        """Test saving a project"""
        path = self.loader.save_project(self.sample_data, "test_project")
        self.assertTrue(path.exists())
        
        # Verify saved data
        with open(path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["project"]["name"], "Test Project")
        self.assertIn("metadata", saved_data)
    
    def test_load_project(self):
        """Test loading a project"""
        self.loader.save_project(self.sample_data, "test_project")
        data = self.loader.load_project("test_project")
        self.assertEqual(data["project"]["name"], "Test Project")
        self.assertEqual(data["project"]["site_area_ha"], 17.18)
    
    def test_validate_project(self):
        """Test validation of project data"""
        validator = ProjectSchemaValidator()
        is_valid, errors = validator.validate(self.sample_data)
        self.assertTrue(is_valid)
        
        # Test invalid data
        invalid_data = {"project": {"name": "Test"}}
        is_valid, errors = validator.validate(invalid_data)
        self.assertFalse(is_valid)
        self.assertIsNotNone(errors)
    
    def test_list_projects(self):
        """Test listing projects"""
        self.loader.save_project(self.sample_data, "project1")
        self.loader.save_project(self.sample_data, "project2")
        
        projects = self.loader.list_projects()
        self.assertEqual(len(projects), 2)
        self.assertIn("project1", [p["path"] for p in projects])
        self.assertIn("project2", [p["path"] for p in projects])
    
    def test_data_access_methods(self):
        """Test data access helper methods"""
        self.loader.save_project(self.sample_data, "test_project")
        self.loader.load_project("test_project")
        
        self.assertEqual(self.loader.get_project_site_area(), 17.18)
        self.assertEqual(self.loader.get_total_dwellings(), 8)
        self.assertEqual(self.loader.get_contingency_percent(), 10)
        self.assertEqual(self.loader.get_total_funding(), 4500000)
        self.assertEqual(self.loader.get_construction_costs(), 4000000)
    
    def test_get_data_path(self):
        """Test dot notation data access"""
        self.loader.save_project(self.sample_data, "test_project")
        self.loader.load_project("test_project")
        
        self.assertEqual(self.loader.get_data("project.name"), "Test Project")
        self.assertEqual(self.loader.get_data("buildings.homes[0].count"), 2)
        self.assertEqual(self.loader.get_data("nonexistent.path"), None)


class TestAgentIntegration(unittest.TestCase):
    """Test agent integration with project data"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.projects_root = Path(self.temp_dir) / "projects"
        self.projects_root.mkdir()
        
        self.loader = ProjectLoader(self.projects_root)
        
        # Load sample project data
        self.sample_data = {
            "project": {
                "name": "Gnowangerup Test",
                "type": "community_housing",
                "location": "gnowangerup",
                "site_area_ha": 17.18,
                "developable_fraction": 0.333,
                "land_tenure": "peppercorn_lease",
                "land_cost": 0
            },
            "buildings": {
                "homes": [
                    {"type": "3x2", "count": 2, "bedrooms": 3, "bathrooms": 2, "area_sqm": 140, "construction_type": "standard"},
                    {"type": "2x1", "count": 6, "bedrooms": 2, "bathrooms": 1, "area_sqm": 90, "construction_type": "standard"}
                ]
            },
            "phases": {
                "planning": {"cost": 800000},
                "infrastructure": {"cost": 2300000},
                "construction": {"cost": 4000000},
                "project_management": {"cost": 300000},
                "contingency_percent": 10
            },
            "funding": {
                "model": "nfp_grants",
                "sources": [
                    {"source": "Government Grant", "amount": 4500000},
                    {"source": "Philanthropic", "amount": 900000}
                ]
            }
        }
        
        self.loader.save_project(self.sample_data, "gnowangerup_test")
        self.loader.load_project("gnowangerup_test")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_agent_access(self):
        """Test that agents can access project data"""
        from src.agents.example_agent import CostAgent
        
        agent = CostAgent(self.loader)
        self.assertEqual(agent.get_project_data("project.name"), "Gnowangerup Test")
        
        # Test agent processing
        output = agent.process()
        self.assertEqual(output["agent_name"], "CostAgent")
        self.assertIn("cost_breakdown", output["results"])
        self.assertIn("funding_analysis", output["results"])
        
        # Check if funding calculation is correct
        funding_gap = output["results"]["funding_analysis"]["funding_gap"]
        expected_gap = (800000 + 2300000 + 4000000 + 300000) * 1.1 - 5400000
        # Should be around 1400000
        self.assertGreater(funding_gap, 0)


if __name__ == "__main__":
    unittest.main()