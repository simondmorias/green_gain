#!/usr/bin/env python3
"""
Simple test runner for the entity artifact generation script.
This validates the implementation without requiring external dependencies.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from generate_entity_artifacts import EntityArtifactGenerator
    print("✅ Successfully imported EntityArtifactGenerator")
except ImportError as e:
    print(f"❌ Failed to import EntityArtifactGenerator: {e}")
    sys.exit(1)


def test_dry_run():
    """Test the generator in dry run mode."""
    print("\n🧪 Testing dry run mode...")

    try:
        generator = EntityArtifactGenerator(dry_run=True, verbose=False)
        print("✅ Generator initialized successfully")

        # Test sample entity generation
        entities = generator._get_sample_entities()
        print(f"✅ Generated {sum(len(e) for e in entities.values())} sample entities")

        # Test alias generation
        aliases = generator.generate_aliases(entities)
        print(f"✅ Generated {len(aliases)} aliases")

        # Test gazetteer building
        gazetteer = generator.build_gazetteer(entities)
        print("✅ Built gazetteer structure")

        # Test JSON serialization
        json.dumps(gazetteer)
        for alias in aliases[:5]:  # Test first 5 aliases
            json.dumps(alias)
        print("✅ JSON serialization works")

        # Test complete pipeline
        generator.run(push_redis=False)
        print("✅ Complete pipeline executed successfully")

        return True

    except Exception as e:
        print(f"❌ Dry run test failed: {e}")
        return False


def test_artifact_structure():
    """Test the structure of generated artifacts."""
    print("\n🧪 Testing artifact structure...")

    try:
        generator = EntityArtifactGenerator(dry_run=True, verbose=False)
        entities = generator._get_sample_entities()

        # Test gazetteer structure
        gazetteer = generator.build_gazetteer(entities)
        required_keys = ["entities", "metrics", "timewords", "special_tokens"]
        for key in required_keys:
            if key not in gazetteer:
                raise ValueError(f"Missing key in gazetteer: {key}")

        entity_types = ["manufacturers", "brands", "categories", "products"]
        for entity_type in entity_types:
            if entity_type not in gazetteer["entities"]:
                raise ValueError(f"Missing entity type: {entity_type}")

        print("✅ Gazetteer structure is correct")

        # Test aliases structure
        aliases = generator.generate_aliases(entities)
        if not aliases:
            raise ValueError("No aliases generated")

        required_alias_keys = ["type", "name", "alias", "id", "confidence"]
        for key in required_alias_keys:
            if key not in aliases[0]:
                raise ValueError(f"Missing key in alias: {key}")

        print("✅ Aliases structure is correct")

        return True

    except Exception as e:
        print(f"❌ Artifact structure test failed: {e}")
        return False


def test_variation_generation():
    """Test alias variation generation."""
    print("\n🧪 Testing variation generation...")

    try:
        generator = EntityArtifactGenerator(dry_run=True, verbose=False)

        # Test basic variations
        variations = generator._create_variations("Cadbury")
        expected = {"cadbury", "cadburys", "cadbury's", "cad"}
        if not expected.issubset(variations):
            missing = expected - variations
            raise ValueError(f"Missing expected variations: {missing}")

        print("✅ Basic variations generated correctly")

        # Test variations with spaces
        variations_space = generator._create_variations("Dairy Milk")
        expected_space = {"dairy milk", "dairy_milk", "dairy-milk"}
        if not expected_space.issubset(variations_space):
            missing = expected_space - variations_space
            raise ValueError(f"Missing expected space variations: {missing}")

        print("✅ Space variations generated correctly")

        return True

    except Exception as e:
        print(f"❌ Variation generation test failed: {e}")
        return False


def test_file_operations():
    """Test file operations in non-dry-run mode."""
    print("\n🧪 Testing file operations...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = EntityArtifactGenerator(dry_run=False, verbose=False)

            # Override output paths to temp directory
            generator.output_dir = Path(temp_dir)
            generator.gazetteer_path = Path(temp_dir) / "gazetteer.json"
            generator.aliases_path = Path(temp_dir) / "aliases.jsonl"

            entities = generator._get_sample_entities()
            gazetteer = generator.build_gazetteer(entities)
            aliases = generator.generate_aliases(entities)

            # Save artifacts
            generator.save_artifacts(gazetteer, aliases)

            # Verify files were created
            if not generator.gazetteer_path.exists():
                raise ValueError("Gazetteer file was not created")

            if not generator.aliases_path.exists():
                raise ValueError("Aliases file was not created")

            # Verify file contents
            with open(generator.gazetteer_path) as f:
                loaded_gazetteer = json.load(f)
                if loaded_gazetteer != gazetteer:
                    raise ValueError("Gazetteer file content mismatch")

            with open(generator.aliases_path) as f:
                lines = f.readlines()
                if len(lines) != len(aliases):
                    raise ValueError("Aliases file line count mismatch")

                # Verify first line is valid JSON
                json.loads(lines[0])

            print("✅ File operations work correctly")
            return True

    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Running Entity Artifact Generator Tests")
    print("=" * 50)

    tests = [
        test_dry_run,
        test_artifact_structure,
        test_variation_generation,
        test_file_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())