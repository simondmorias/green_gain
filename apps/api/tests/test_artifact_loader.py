"""
Unit tests for artifact loader service.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from app.services.artifact_loader import ArtifactLoader, get_artifact_loader


class TestArtifactLoader:
    """Test the artifact loader service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache_manager.enabled = True

        # Create test data
        self.test_gazetteer = {
            "entities": {
                "manufacturers": ["Cadbury", "Mars"],
                "brands": ["Dairy Milk", "Galaxy"],
            },
            "metrics": ["revenue", "sales"],
            "timewords": ["Q1", "Q2"],
        }

        self.test_aliases = [
            {
                "type": "manufacturer",
                "name": "Cadbury",
                "alias": "cadburys",
                "confidence": 0.9,
            },
            {
                "type": "brand",
                "name": "Dairy Milk",
                "alias": "dairy milk chocolate",
                "confidence": 0.9,
            },
        ]

    def test_initialization(self):
        """Test artifact loader initialization."""
        loader = ArtifactLoader(self.mock_cache_manager)

        assert loader.cache_manager == self.mock_cache_manager
        assert loader.loaded is False
        assert loader.load_time == 0.0
        assert isinstance(loader.artifacts_dir, Path)

    def test_load_from_cache_success(self):
        """Test successful loading from cache."""
        self.mock_cache_manager.get.side_effect = [
            self.test_gazetteer,  # entity:gazetteer
            self.test_aliases,  # entity:aliases
        ]

        loader = ArtifactLoader(self.mock_cache_manager)
        result = loader.load_artifacts()

        assert result is True
        assert loader.loaded is True
        assert loader.gazetteer == self.test_gazetteer
        assert loader.aliases == self.test_aliases
        assert self.mock_cache_manager.get.call_count == 2

    def test_load_from_cache_miss(self):
        """Test cache miss scenario."""
        self.mock_cache_manager.get.return_value = None

        # Mock file loading
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "exists", return_value=True):
                # Mock JSON loading
                mock_file.return_value.read.side_effect = [
                    json.dumps(self.test_gazetteer),
                    "\n".join([json.dumps(alias) for alias in self.test_aliases]),
                ]

                loader = ArtifactLoader(self.mock_cache_manager)
                result = loader.load_artifacts()

        assert result is True
        assert loader.loaded is True
        # Should have tried cache first, then loaded from files
        assert self.mock_cache_manager.get.call_count == 2

    def test_load_from_cache_disabled(self):
        """Test loading when cache is disabled."""
        self.mock_cache_manager.enabled = False

        # Mock file loading
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "exists", return_value=True):
                mock_file.return_value.read.side_effect = [
                    json.dumps(self.test_gazetteer),
                    "\n".join([json.dumps(alias) for alias in self.test_aliases]),
                ]

                loader = ArtifactLoader(self.mock_cache_manager)
                result = loader.load_artifacts()

        assert result is True
        assert loader.loaded is True
        # Should not have tried cache
        assert self.mock_cache_manager.get.call_count == 0

    def test_load_from_files_success(self):
        """Test successful loading from files."""
        self.mock_cache_manager.get.return_value = None  # Cache miss

        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            gazetteer_path = Path(temp_dir) / "gazetteer.json"
            aliases_path = Path(temp_dir) / "aliases.jsonl"

            # Write test data
            with open(gazetteer_path, "w") as f:
                json.dump(self.test_gazetteer, f)

            with open(aliases_path, "w") as f:
                for alias in self.test_aliases:
                    f.write(json.dumps(alias) + "\n")

            loader = ArtifactLoader(self.mock_cache_manager)
            loader.gazetteer_path = gazetteer_path
            loader.aliases_path = aliases_path

            result = loader.load_artifacts()

        assert result is True
        assert loader.loaded is True
        assert loader.gazetteer == self.test_gazetteer
        assert loader.aliases == self.test_aliases

    def test_load_from_files_not_found(self):
        """Test loading when files don't exist."""
        self.mock_cache_manager.get.return_value = None  # Cache miss

        loader = ArtifactLoader(self.mock_cache_manager)
        # Set paths to non-existent files
        loader.gazetteer_path = Path("/nonexistent/gazetteer.json")
        loader.aliases_path = Path("/nonexistent/aliases.jsonl")

        result = loader.load_artifacts()

        # Should fall back to defaults
        assert result is True  # Successfully loaded defaults
        assert loader.loaded is True
        assert "manufacturers" in loader.gazetteer["entities"]
        assert len(loader.aliases) > 0

    def test_load_defaults(self):
        """Test loading default artifacts."""
        loader = ArtifactLoader(self.mock_cache_manager)
        loader._load_defaults()

        assert loader.loaded is True
        assert "entities" in loader.gazetteer
        assert "manufacturers" in loader.gazetteer["entities"]
        assert "metrics" in loader.gazetteer
        assert len(loader.aliases) > 0
        assert all("type" in alias for alias in loader.aliases)

    def test_warm_cache_success(self):
        """Test successful cache warming."""
        self.mock_cache_manager.warm_cache.return_value = True

        loader = ArtifactLoader(self.mock_cache_manager)
        loader.gazetteer = self.test_gazetteer
        loader.aliases = self.test_aliases

        loader._warm_cache()

        self.mock_cache_manager.warm_cache.assert_called_once()
        call_args = self.mock_cache_manager.warm_cache.call_args[0][0]
        assert call_args["gazetteer"] == self.test_gazetteer
        assert call_args["aliases"] == self.test_aliases

    def test_warm_cache_failure(self):
        """Test cache warming failure."""
        self.mock_cache_manager.warm_cache.return_value = False

        loader = ArtifactLoader(self.mock_cache_manager)
        loader.gazetteer = self.test_gazetteer
        loader.aliases = self.test_aliases

        with patch("app.services.artifact_loader.logger") as mock_logger:
            loader._warm_cache()
            mock_logger.warning.assert_called_once()

    def test_get_gazetteer_lazy_load(self):
        """Test gazetteer getter with lazy loading."""
        loader = ArtifactLoader(self.mock_cache_manager)
        loader.loaded = False

        with patch.object(loader, "load_artifacts") as mock_load:
            mock_load.return_value = True
            loader.gazetteer = self.test_gazetteer

            result = loader.get_gazetteer()

            mock_load.assert_called_once()
            assert result == self.test_gazetteer

    def test_get_aliases_lazy_load(self):
        """Test aliases getter with lazy loading."""
        loader = ArtifactLoader(self.mock_cache_manager)
        loader.loaded = False

        with patch.object(loader, "load_artifacts") as mock_load:
            mock_load.return_value = True
            loader.aliases = self.test_aliases

            result = loader.get_aliases()

            mock_load.assert_called_once()
            assert result == self.test_aliases

    def test_invalidate_cache_success(self):
        """Test successful cache invalidation."""
        self.mock_cache_manager.delete_pattern.side_effect = [5, 3]  # Return counts

        loader = ArtifactLoader(self.mock_cache_manager)
        result = loader.invalidate_cache()

        assert result is True
        assert self.mock_cache_manager.delete_pattern.call_count == 2
        self.mock_cache_manager.delete_pattern.assert_any_call("entity:*")
        self.mock_cache_manager.delete_pattern.assert_any_call("result:*")

    def test_invalidate_cache_disabled(self):
        """Test cache invalidation when cache is disabled."""
        self.mock_cache_manager.enabled = False

        loader = ArtifactLoader(self.mock_cache_manager)
        result = loader.invalidate_cache()

        assert result is False

    def test_reload_artifacts(self):
        """Test artifact reloading."""
        loader = ArtifactLoader(self.mock_cache_manager)
        loader.loaded = True

        with patch.object(loader, "load_artifacts") as mock_load:
            mock_load.return_value = True

            result = loader.reload()

            assert result is True
            assert loader.loaded is False  # Should be reset before reload
            mock_load.assert_called_once_with(force_reload=True)

    def test_get_stats(self):
        """Test statistics retrieval."""
        self.mock_cache_manager.get_stats.return_value = {"hits": 10, "misses": 2}

        loader = ArtifactLoader(self.mock_cache_manager)
        loader.loaded = True
        loader.load_time = 1.5
        loader.gazetteer = {"entities": {"manufacturers": ["A", "B"]}}
        loader.aliases = [{"name": "test"}]

        stats = loader.get_stats()

        assert stats["loaded"] is True
        assert stats["load_time_seconds"] == 1.5
        assert stats["gazetteer_entities"] == 1
        assert stats["aliases_count"] == 1
        assert stats["cache_stats"]["hits"] == 10

    def test_force_reload(self):
        """Test force reload bypasses cache."""
        self.mock_cache_manager.get.return_value = self.test_gazetteer  # Cache hit

        # Mock file loading
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "exists", return_value=True):
                mock_file.return_value.read.side_effect = [
                    json.dumps(self.test_gazetteer),
                    "\n".join([json.dumps(alias) for alias in self.test_aliases]),
                ]

                loader = ArtifactLoader(self.mock_cache_manager)
                result = loader.load_artifacts(force_reload=True)

        assert result is True
        # Should not have tried cache due to force_reload
        assert self.mock_cache_manager.get.call_count == 0

    def test_load_time_warning(self):
        """Test warning when loading takes too long."""
        self.mock_cache_manager.get.return_value = None  # Cache miss

        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "exists", return_value=True):
                with patch("app.services.artifact_loader.time.time") as mock_time:
                    mock_time.side_effect = [0, 6]  # 6 second elapsed time

                    mock_file.return_value.read.side_effect = [
                        json.dumps(self.test_gazetteer),
                        "\n".join([json.dumps(alias) for alias in self.test_aliases]),
                    ]

                    with patch("app.services.artifact_loader.logger") as mock_logger:
                        loader = ArtifactLoader(self.mock_cache_manager)
                        result = loader.load_artifacts()

                        assert result is True
                        mock_logger.warning.assert_called()
                        assert (
                            "exceeded 5-second target"
                            in mock_logger.warning.call_args[0][0]
                        )


class TestArtifactLoaderSingleton:
    """Test the artifact loader singleton functionality."""

    def test_get_artifact_loader_singleton(self):
        """Test that get_artifact_loader returns the same instance."""
        # Clear any existing singleton
        import app.services.artifact_loader

        app.services.artifact_loader._artifact_loader = None

        loader1 = get_artifact_loader()
        loader2 = get_artifact_loader()

        assert loader1 is loader2


class TestArtifactLoaderIntegration:
    """Integration tests for artifact loader with real file operations."""

    def test_real_file_loading(self):
        """Test loading with real temporary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            gazetteer_path = Path(temp_dir) / "gazetteer.json"
            aliases_path = Path(temp_dir) / "aliases.jsonl"

            test_gazetteer = {
                "entities": {"manufacturers": ["TestCorp"]},
                "metrics": ["revenue"],
            }

            test_aliases = [
                {"type": "manufacturer", "name": "TestCorp", "alias": "test corp"}
            ]

            with open(gazetteer_path, "w") as f:
                json.dump(test_gazetteer, f)

            with open(aliases_path, "w") as f:
                for alias in test_aliases:
                    f.write(json.dumps(alias) + "\n")

            # Test loading
            mock_cache_manager = Mock()
            mock_cache_manager.enabled = False  # Disable cache for this test

            loader = ArtifactLoader(mock_cache_manager)
            loader.gazetteer_path = gazetteer_path
            loader.aliases_path = aliases_path

            result = loader.load_artifacts()

            assert result is True
            assert loader.gazetteer == test_gazetteer
            assert loader.aliases == test_aliases

    def test_malformed_json_handling(self):
        """Test handling of malformed JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create malformed files
            gazetteer_path = Path(temp_dir) / "gazetteer.json"
            aliases_path = Path(temp_dir) / "aliases.jsonl"

            with open(gazetteer_path, "w") as f:
                f.write("invalid json {")

            with open(aliases_path, "w") as f:
                f.write("invalid json line\n")

            mock_cache_manager = Mock()
            mock_cache_manager.enabled = False

            loader = ArtifactLoader(mock_cache_manager)
            loader.gazetteer_path = gazetteer_path
            loader.aliases_path = aliases_path

            result = loader.load_artifacts()

            # Should fall back to defaults
            assert result is True  # Successfully loaded defaults
            assert loader.loaded is True  # But defaults were loaded
            assert "manufacturers" in loader.gazetteer["entities"]
