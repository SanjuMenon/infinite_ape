"""
Unit tests for loader and config validation.

Tests the load_config and validate_config functions to ensure they
correctly load and validate YAML configurations.
"""

import pytest
import yaml
from pathlib import Path
from declarative_fsm import load_config, validate_config


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_valid_config(self, tmp_path):
        """Test that load_config loads valid YAML config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
fields:
  test_field:
    field_selection_strategy:
      check_completeness:
        description: ["field1"]
""")
        
        config = load_config(str(config_file))
        
        assert "fields" in config
        assert "test_field" in config["fields"]
    
    def test_load_config_with_validation(self, tmp_path):
        """Test that load_config validates config when validate=True."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
fields:
  test_field:
    field_selection_strategy:
      check_completeness:
        description: ["field1"]
""")
        
        config = load_config(str(config_file), validate=True)
        
        assert "fields" in config
    
    def test_load_config_without_validation(self, tmp_path):
        """Test that load_config skips validation when validate=False."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
fields:
  test_field:
    field_selection_strategy:
      invalid_state:
        description: "test"
""")
        
        # Should not raise even though config is invalid
        config = load_config(str(config_file), validate=False)
        
        assert "fields" in config
    
    def test_load_config_nonexistent_file(self):
        """Test that load_config raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
    
    def test_load_config_empty_file(self, tmp_path):
        """Test that load_config raises ValueError for empty file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        
        with pytest.raises(ValueError, match="empty"):
            load_config(str(config_file))
    
    def test_load_config_missing_fields_key(self, tmp_path):
        """Test that load_config raises ValueError when 'fields' key is missing."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("other_key: value")
        
        with pytest.raises(ValueError, match="fields"):
            load_config(str(config_file))
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """Test that load_config raises YAMLError for invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            load_config(str(config_file))


class TestValidateConfig:
    """Tests for validate_config function."""
    
    def test_validate_valid_config(self):
        """Test that validate_config passes for valid config."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]},
                        "convert_to_canon": {"description": True}
                    },
                    "extraction_strategy": {
                        "validate_type": {"description": "int"},
                        "check_format": {}
                    }
                }
            }
        }
        
        # Should not raise
        validate_config(config)
    
    def test_validate_invalid_state_in_strategy(self):
        """Test that validate_config catches invalid states."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]},
                        "invalid_state": {"description": "test"}
                    }
                }
            }
        }
        
        with pytest.raises(ValueError, match="Invalid states"):
            validate_config(config)
    
    def test_validate_invalid_state_in_nested_strategy(self):
        """Test that validate_config catches invalid states in nested strategies."""
        config = {
            "fields": {
                "test_field": {
                    "extraction_strategy": {
                        "validate_type": {"description": "int"},
                        "generation_strategy": {
                            "format": {"description": "table"},
                            "invalid_nested_state": {"description": "test"}
                        }
                    }
                }
            }
        }
        
        with pytest.raises(ValueError, match="Invalid states"):
            validate_config(config)
    
    def test_validate_config_missing_fields(self):
        """Test that validate_config handles missing 'fields' key."""
        config = {}
        
        # Should not raise (will be caught by load_config)
        validate_config(config)
    
    def test_validate_config_field_not_dict(self):
        """Test that validate_config catches non-dict fields."""
        config = {
            "fields": {
                "test_field": "not a dict"
            }
        }
        
        with pytest.raises(ValueError, match="must be a dictionary"):
            validate_config(config)
    
    def test_validate_config_strategy_not_dict(self):
        """Test that validate_config catches non-dict strategies."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": "not a dict"
                }
            }
        }
        
        with pytest.raises(ValueError, match="must be a dictionary"):
            validate_config(config)
    
    def test_validate_config_unknown_strategy(self):
        """Test that validate_config allows unknown strategies."""
        config = {
            "fields": {
                "test_field": {
                    "unknown_strategy": {
                        "some_state": {"description": "test"}
                    }
                }
            }
        }
        
        # Should not raise (unknown strategies are allowed for extensibility)
        validate_config(config)
    
    def test_validate_config_multiple_fields(self):
        """Test that validate_config validates all fields."""
        config = {
            "fields": {
                "field1": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["key1"]}
                    }
                },
                "field2": {
                    "field_selection_strategy": {
                        "invalid_state": {"description": "test"}
                    }
                }
            }
        }
        
        with pytest.raises(ValueError, match="field2"):
            validate_config(config)
    
    def test_validate_config_all_allowed_states(self):
        """Test that validate_config accepts all allowed states."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]},
                        "convert_to_canon": {"description": True}
                    },
                    "extraction_strategy": {
                        "validate_type": {"description": "int"},
                        "check_format": {},
                        "validate_length": {}
                    },
                    "generation_strategy": {
                        "format": {"description": "table"}
                    },
                    "validation_strategy": {
                        "llm_eval": {"description": ["metric1"]}
                    },
                    "calculation_strategy": {
                        "calculation": {"description": "aggregation", "key": "category"}
                    }
                }
            }
        }
        
        # Should not raise
        validate_config(config)
