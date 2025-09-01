#!/usr/bin/env python3
"""
Unit tests for the Entity Artifact Generation Script.

Tests the artifact generation logic with sample data to ensure
proper functionality without requiring Databricks connection.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from generate_entity_artifacts import EntityArtifactGenerator


class TestEntityArtifactGenerator(unittest.TestCase):
    """Test cases for EntityArtifactGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = EntityArtifactGenerator(dry_run=True, verbose=False)
        
        self.sample_entities = {
            "manufacturers": [
                {"id": "MFR_001", "name": "Cadbury", "type": "manufacturer", "display_name": "Cadbury"},
                {"id": "MFR_002", "name": "Mars", "type": "manufacturer", "display_name": "Mars"}
            ],
            "brands": [
                {"id": "BRD_001", "name": "Dairy Milk", "type": "brand", "display_name": "Dairy Milk"},
                {"id": "BRD_002", "name": "Galaxy", "type": "brand", "display_name": "Galaxy"}
            ],
            "categories": [
                {"id": "CAT_001", "name": "Chocolate Bars", "type": "category", "display_name": "Chocolate Bars"}
            ],
            "products": [
                {"id": "PRD_001", "name": "Milk Chocolate", "type": "product", "display_name": "Milk Chocolate"}
            ]
        }
    
    def test_initialization(self):
        """Test generator initialization."""
        self.assertTrue(self.generator.dry_run)
        self.assertFalse(self.generator.verbose)
        self.assertEqual(self.generator.catalog, "rgm_poc")
        self.assertEqual(self.generator.schema, "chocolate")
        self.assertEqual(self.generator.table, "master_product_hierarchy")
    
    def test_get_sample_entities(self):
        """Test sample entity generation."""
        entities = self.generator._get_sample_entities()
        
        self.assertIn("manufacturers", entities)
        self.assertIn("brands", entities)
        self.assertIn("categories", entities)
        self.assertIn("products", entities)
        
        # Check that each category has entities
        self.assertGreater(len(entities["manufacturers"]), 0)
        self.assertGreater(len(entities["brands"]), 0)
        self.assertGreater(len(entities["categories"]), 0)
        self.assertGreater(len(entities["products"]), 0)
        
        # Check entity structure
        manufacturer = entities["manufacturers"][0]
        self.assertIn("id", manufacturer)
        self.assertIn("name", manufacturer)
        self.assertIn("type", manufacturer)
        self.assertIn("display_name", manufacturer)
    
    def test_create_variations(self):
        """Test alias variation generation."""
        variations = self.generator._create_variations("Cadbury")
        
        # Should include basic variations
        self.assertIn("cadbury", variations)
        self.assertIn("cadburys", variations)
        self.assertIn("cadbury's", variations)
        self.assertIn("cad", variations)  # Abbreviation for names > 5 chars
        
        # Test with spaces
        variations_with_space = self.generator._create_variations("Dairy Milk")
        self.assertIn("dairy milk", variations_with_space)
        self.assertIn("dairy_milk", variations_with_space)
        self.assertIn("dairy-milk", variations_with_space)
        
        # Test with company terms
        variations_company = self.generator._create_variations("Cadbury Manufacturing")
        self.assertIn("cadbury mfg", variations_company)
    
    def test_generate_aliases(self):
        """Test alias generation from entities."""
        aliases = self.generator.generate_aliases(self.sample_entities)
        
        # Should generate multiple aliases per entity
        self.assertGreater(len(aliases), len(self.sample_entities["manufacturers"]))
        
        # Check alias structure
        alias = aliases[0]
        self.assertIn("type", alias)
        self.assertIn("name", alias)
        self.assertIn("alias", alias)
        self.assertIn("id", alias)
        self.assertIn("confidence", alias)
        
        # Check confidence scores
        self.assertGreaterEqual(alias["confidence"], 0.0)
        self.assertLessEqual(alias["confidence"], 1.0)
        
        # Check that original names have confidence 1.0
        original_aliases = [a for a in aliases if a["confidence"] == 1.0]
        self.assertGreater(len(original_aliases), 0)
    
    def test_build_gazetteer(self):
        """Test gazetteer structure building."""
        gazetteer = self.generator.build_gazetteer(self.sample_entities)
        
        # Check main structure
        self.assertIn("entities", gazetteer)
        self.assertIn("metrics", gazetteer)
        self.assertIn("timewords", gazetteer)
        self.assertIn("special_tokens", gazetteer)
        
        # Check entities structure
        entities = gazetteer["entities"]
        self.assertIn("manufacturers", entities)
        self.assertIn("brands", entities)
        self.assertIn("categories", entities)
        self.assertIn("products", entities)
        
        # Check that entity names are extracted correctly
        self.assertEqual(entities["manufacturers"], ["Cadbury", "Mars"])
        self.assertEqual(entities["brands"], ["Dairy Milk", "Galaxy"])
        
        # Check that metrics are included
        self.assertIn("revenue", gazetteer["metrics"])
        self.assertIn("market share", gazetteer["metrics"])
        
        # Check that timewords are included
        self.assertIn("Q1", gazetteer["timewords"])
        self.assertIn("January", gazetteer["timewords"])
    
    def test_dry_run_mode(self):
        """Test that dry run mode doesn't write files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output directory for test
            self.generator.output_dir = Path(temp_dir)
            self.generator.gazetteer_path = Path(temp_dir) / "gazetteer.json"
            self.generator.aliases_path = Path(temp_dir) / "aliases.jsonl"
            
            gazetteer = self.generator.build_gazetteer(self.sample_entities)
            aliases = self.generator.generate_aliases(self.sample_entities)
            
            # Should not create files in dry run mode
            self.generator.save_artifacts(gazetteer, aliases)
            
            self.assertFalse(self.generator.gazetteer_path.exists())
            self.assertFalse(self.generator.aliases_path.exists())
    
    def test_save_artifacts_real_mode(self):
        """Test artifact saving in real mode."""
        generator = EntityArtifactGenerator(dry_run=False, verbose=False)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output directory for test
            generator.output_dir = Path(temp_dir)
            generator.gazetteer_path = Path(temp_dir) / "gazetteer.json"
            generator.aliases_path = Path(temp_dir) / "aliases.jsonl"
            
            gazetteer = generator.build_gazetteer(self.sample_entities)
            aliases = generator.generate_aliases(self.sample_entities)
            
            generator.save_artifacts(gazetteer, aliases)
            
            # Files should be created
            self.assertTrue(generator.gazetteer_path.exists())
            self.assertTrue(generator.aliases_path.exists())
            
            # Validate JSON format
            with open(generator.gazetteer_path) as f:
                loaded_gazetteer = json.load(f)
                self.assertEqual(loaded_gazetteer, gazetteer)
            
            # Validate JSONL format
            with open(generator.aliases_path) as f:
                lines = f.readlines()
                self.assertEqual(len(lines), len(aliases))
                
                # Check first line is valid JSON
                first_alias = json.loads(lines[0])
                self.assertIn("type", first_alias)
                self.assertIn("alias", first_alias)
    
    @patch('generate_entity_artifacts.redis')
    def test_redis_push_dry_run(self, mock_redis):
        """Test Redis push in dry run mode."""
        gazetteer = self.generator.build_gazetteer(self.sample_entities)
        aliases = self.generator.generate_aliases(self.sample_entities)
        
        result = self.generator.push_to_redis(gazetteer, aliases)
        
        # Should return True but not actually push
        self.assertTrue(result)
        mock_redis.Redis.assert_not_called()
    
    @patch('generate_entity_artifacts.redis')
    def test_redis_push_no_redis(self, mock_redis):
        """Test Redis push when Redis is not available."""
        # Simulate Redis not being available
        mock_redis = None
        generator = EntityArtifactGenerator(dry_run=False, verbose=False)
        
        with patch('generate_entity_artifacts.redis', None):
            gazetteer = generator.build_gazetteer(self.sample_entities)
            aliases = generator.generate_aliases(self.sample_entities)
            
            result = generator.push_to_redis(gazetteer, aliases)
            self.assertFalse(result)
    
    @patch('generate_entity_artifacts.redis')
    def test_redis_push_success(self, mock_redis):
        """Test successful Redis push."""
        generator = EntityArtifactGenerator(dry_run=False, verbose=False)
        
        # Mock Redis connection
        mock_redis_instance = MagicMock()
        mock_redis.Redis.return_value = mock_redis_instance
        
        gazetteer = generator.build_gazetteer(self.sample_entities)
        aliases = generator.generate_aliases(self.sample_entities)
        
        result = generator.push_to_redis(gazetteer, aliases)
        
        self.assertTrue(result)
        mock_redis_instance.ping.assert_called_once()
        self.assertEqual(mock_redis_instance.setex.call_count, 2)  # gazetteer + aliases
    
    def test_extract_entities_dry_run(self):
        """Test entity extraction in dry run mode."""
        entities = self.generator.extract_entities()
        
        # Should return sample data
        self.assertIn("manufacturers", entities)
        self.assertIn("brands", entities)
        self.assertIn("categories", entities)
        self.assertIn("products", entities)
        
        # Should have sample data structure
        self.assertGreater(len(entities["manufacturers"]), 0)
        self.assertEqual(entities["manufacturers"][0]["name"], "Cadbury")
    
    def test_run_pipeline_dry_run(self):
        """Test complete pipeline execution in dry run mode."""
        # Should complete without errors
        try:
            self.generator.run(push_redis=False)
        except Exception as e:
            self.fail(f"Pipeline run failed: {e}")
    
    def test_json_output_format(self):
        """Test that output artifacts are valid JSON/JSONL."""
        gazetteer = self.generator.build_gazetteer(self.sample_entities)
        aliases = self.generator.generate_aliases(self.sample_entities)
        
        # Test gazetteer JSON serialization
        try:
            json_str = json.dumps(gazetteer)
            reloaded = json.loads(json_str)
            self.assertEqual(gazetteer, reloaded)
        except (TypeError, ValueError) as e:
            self.fail(f"Gazetteer JSON serialization failed: {e}")
        
        # Test aliases JSONL serialization
        try:
            for alias in aliases:
                json_str = json.dumps(alias)
                reloaded = json.loads(json_str)
                self.assertEqual(alias, reloaded)
        except (TypeError, ValueError) as e:
            self.fail(f"Aliases JSONL serialization failed: {e}")
    
    def test_entity_metadata_completeness(self):
        """Test that entities have all required metadata."""
        entities = self.generator._get_sample_entities()
        
        required_fields = ["id", "name", "type", "display_name"]
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                for field in required_fields:
                    self.assertIn(field, entity, 
                                f"Entity {entity} missing required field: {field}")
    
    def test_alias_confidence_scores(self):
        """Test that alias confidence scores are reasonable."""
        aliases = self.generator.generate_aliases(self.sample_entities)
        
        for alias in aliases:
            confidence = alias["confidence"]
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
            # Original names should have confidence 1.0
            if alias["alias"] == alias["name"].lower():
                self.assertEqual(confidence, 1.0)


class TestEntityArtifactGeneratorIntegration(unittest.TestCase):
    """Integration tests for the complete artifact generation process."""
    
    def test_end_to_end_dry_run(self):
        """Test complete end-to-end process in dry run mode."""
        generator = EntityArtifactGenerator(dry_run=True, verbose=True)
        
        # Should complete without errors
        try:
            generator.run(push_redis=True)
        except Exception as e:
            self.fail(f"End-to-end dry run failed: {e}")
    
    def test_artifact_size_limits(self):
        """Test that generated artifacts stay within size limits."""
        generator = EntityArtifactGenerator(dry_run=True, verbose=False)
        
        entities = generator._get_sample_entities()
        gazetteer = generator.build_gazetteer(entities)
        aliases = generator.generate_aliases(entities)
        
        # Estimate sizes
        gazetteer_size = len(json.dumps(gazetteer).encode('utf-8'))
        aliases_size = sum(len(json.dumps(alias).encode('utf-8')) + 1 for alias in aliases)  # +1 for newline
        
        total_size_mb = (gazetteer_size + aliases_size) / (1024 * 1024)
        
        # Should be well under 10MB limit for sample data
        self.assertLess(total_size_mb, 10.0, 
                       f"Artifact size ({total_size_mb:.2f} MB) exceeds 10MB limit")


if __name__ == "__main__":
    unittest.main()