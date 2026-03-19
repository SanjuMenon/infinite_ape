"""
Unit tests for FSM engine.

Tests the FSMEngine class to ensure it correctly executes FSMs,
manages context, handles state transitions, and produces correct reports.
"""

import pytest
import json
import copy
from pathlib import Path
from declarative_fsm import FSMEngine, load_config


class TestFSMEngineInit:
    """Tests for FSMEngine initialization."""
    
    def test_init_with_config(self):
        """Test that engine initializes with config."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        assert engine.config == config
        assert len(engine.fields) == 1
        assert "test_field" in engine.fields
    
    def test_init_with_canonical_config(self, tmp_path):
        """Test that engine loads canonical config if provided."""
        config = {"fields": {}}
        canonical_config_path = tmp_path / "canonical.yaml"
        canonical_config_path.write_text("test_field:\n  old_key: new_key\n")
        
        engine = FSMEngine(config, canonical_config_path=str(canonical_config_path))
        
        assert "test_field" in engine.canonical_mappings
        assert engine.canonical_mappings["test_field"]["old_key"] == "new_key"
    
    def test_init_without_canonical_config(self):
        """Test that engine works without canonical config."""
        config = {"fields": {}}
        
        engine = FSMEngine(config)
        
        assert engine.canonical_mappings == {}
    
    def test_init_nonexistent_canonical_config(self):
        """Test that engine handles nonexistent canonical config gracefully."""
        config = {"fields": {}}
        
        engine = FSMEngine(config, canonical_config_path="nonexistent.yaml")
        
        assert engine.canonical_mappings == {}


class TestFSMEngineExecute:
    """Tests for FSMEngine.execute method."""
    
    def test_execute_with_dict_data(self):
        """Test that execute works with dict data."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}
        
        report = engine.execute(data)
        
        assert "execution_summary" in report
        assert "fields" in report
        assert "list_of_bundles" in report
        assert report["execution_summary"]["total_fields"] == 1
    
    def test_execute_with_json_string(self):
        """Test that execute parses JSON string data."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data_str = json.dumps({"test_field": {"field1": "value1"}})
        
        report = engine.execute(data_str)
        
        assert report["execution_summary"]["total_fields"] == 1
    
    def test_execute_multiple_fields(self):
        """Test that execute processes multiple fields."""
        config = {
            "fields": {
                "field1": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["key1"]}
                    }
                },
                "field2": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["key2"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {
            "field1": {"key1": "value1"},
            "field2": {"key2": "value2"}
        }
        
        report = engine.execute(data)
        
        assert report["execution_summary"]["total_fields"] == 2
        assert len(report["fields"]) == 2
        assert len(report["list_of_bundles"]) == 2
    
    def test_execute_field_passes(self):
        """Test that execute correctly reports passed fields."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}
        
        report = engine.execute(data)
        
        assert report["execution_summary"]["fields_passed"] == 1
        assert report["execution_summary"]["fields_failed"] == 0
        assert report["fields"]["test_field"]["status"] == "passed"
    
    def test_execute_field_fails(self):
        """Test that execute correctly reports failed fields."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1", "field2"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}  # Missing field2
        
        report = engine.execute(data)
        
        assert report["execution_summary"]["fields_passed"] == 0
        assert report["execution_summary"]["fields_failed"] == 1
        assert report["fields"]["test_field"]["status"] == "not_passed"
    
    def test_execute_initializes_most_current_data(self):
        """Test that execute initializes most_current_data correctly."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1", "field2": "value2"}}
        
        report = engine.execute(data)
        
        bundle = report["fields"]["test_field"]["bundle"]
        assert "most_current_data" in bundle
        assert bundle["most_current_data"] == {"field1": "value1", "field2": "value2"}
    
    def test_execute_most_current_data_list(self):
        """Test that execute collects most_current_data_list correctly."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    },
                    "generation_strategy": {
                        "format": {"description": "table"}
                    },
                    "validation_strategy": {
                        "llm_eval": {"description": ["metric1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}
        
        report = engine.execute(data)
        
        assert "most_current_data_list" in report
        assert len(report["most_current_data_list"]) == 1
        item = report["most_current_data_list"][0]
        assert item["field_name"] == "test_field"
        assert "most_current_data" in item
        assert item["format"] == "table"
        assert item["eval_type"] == "llm"
        assert item["metrics"] == ["metric1"]


class TestFSMEngineExecuteField:
    """Tests for FSMEngine._execute_field method."""
    
    def test_execute_field_single_strategy(self):
        """Test that _execute_field executes single strategy."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_field("test_field", config["fields"]["test_field"], data, context)
        
        assert result["status"] == "passed"
        assert "field_selection_strategy" in result["strategies"]
    
    def test_execute_field_multiple_strategies(self):
        """Test that _execute_field executes multiple strategies."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1"]}
                    },
                    "extraction_strategy": {
                        "validate_type": {"description": "str"}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_field("test_field", config["fields"]["test_field"], data, context)
        
        assert len(result["strategies"]) == 2
        assert "field_selection_strategy" in result["strategies"]
        assert "extraction_strategy" in result["strategies"]
    
    def test_execute_field_fails_on_first_strategy(self):
        """Test that _execute_field stops when strategy fails."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["field1", "field2"]}
                    },
                    "extraction_strategy": {
                        "validate_type": {"description": "str"}
                    }
                }
            }
        }
        engine = FSMEngine(config)
        data = {"test_field": {"field1": "value1"}}  # Missing field2
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_field("test_field", config["fields"]["test_field"], data, context)
        
        assert result["status"] == "not_passed"
        # Both strategies should still be executed
        assert len(result["strategies"]) == 2


class TestFSMEngineExecuteStrategy:
    """Tests for FSMEngine._execute_strategy method."""
    
    def test_execute_strategy_linear_fsm(self):
        """Test that _execute_strategy executes linear FSM."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        strategy_config = {
            "check_completeness": {"description": ["field1"]},
            "convert_to_canon": {"description": True}
        }
        data = {"test_field": {"field1": "value1"}}
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_strategy(
            "field_selection_strategy",
            strategy_config,
            data,
            "test_field",
            context
        )
        
        assert result["status"] == "passed"
        assert len(result["states_executed"]) == 2
        assert "check_completeness" in result["states_executed"]
        assert "convert_to_canon" in result["states_executed"]
    
    def test_execute_strategy_fails_at_state(self):
        """Test that _execute_strategy stops at failing state."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        strategy_config = {
            "check_completeness": {"description": ["field1", "field2"]},
            "convert_to_canon": {"description": True}
        }
        data = {"test_field": {"field1": "value1"}}  # Missing field2
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_strategy(
            "field_selection_strategy",
            strategy_config,
            data,
            "test_field",
            context
        )
        
        assert result["status"] == "not_passed"
        assert result["failed_at"] == "check_completeness"
        assert len(result["states_executed"]) == 1
    
    def test_execute_strategy_nested_strategies(self):
        """Test that _execute_strategy executes nested strategies."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        strategy_config = {
            "validate_type": {"description": "str"},
            "generation_strategy": {
                "format": {"description": "table"}
            }
        }
        data = {"test_field": {"field1": "value1"}}
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_strategy(
            "extraction_strategy",
            strategy_config,
            data,
            "test_field",
            context
        )
        
        assert result["status"] == "passed"
        assert "nested_strategies" in result
        assert "generation_strategy" in result["nested_strategies"]
    
    def test_execute_strategy_skips_nested_on_failure(self):
        """Test that nested strategies are skipped when parent fails."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        strategy_config = {
            "validate_type": {"description": "int"},  # Will fail for string
            "generation_strategy": {
                "format": {"description": "table"}
            }
        }
        data = {"test_field": {"field1": "value1"}}  # String, not int
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_strategy(
            "extraction_strategy",
            strategy_config,
            data,
            "test_field",
            context
        )
        
        assert result["status"] == "not_passed"
        # Nested strategy should not be executed
        assert "nested_strategies" not in result or len(result["nested_strategies"]) == 0


class TestFSMEngineExecuteLinearFSM:
    """Tests for FSMEngine._execute_linear_fsm method."""
    
    def test_execute_linear_fsm_all_pass(self):
        """Test that _execute_linear_fsm executes all states when they pass."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        states = {
            "check_completeness": {"description": ["field1"]},
            "convert_to_canon": {"description": True}
        }
        data = {"test_field": {"field1": "value1"}}
        context = {"most_current_data": copy.deepcopy(data["test_field"])}
        
        result = engine._execute_linear_fsm(
            states,
            data,
            "test_field",
            "field_selection_strategy",
            context
        )
        
        assert result["status"] == "passed"
        assert len(result["states_executed"]) == 2
        assert result["failed_at"] is None
    
    def test_execute_linear_fsm_reverts_on_failure(self):
        """Test that _execute_linear_fsm reverts most_current_data on failure."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        states = {
            "check_completeness": {"description": ["field1"]},
            "convert_to_canon": {"description": True}
        }
        data = {"test_field": {"field1": "value1"}}
        original_data = copy.deepcopy(data["test_field"])
        context = {"most_current_data": copy.deepcopy(original_data)}
        
        # Modify most_current_data in first state
        # Then second state will fail
        states_with_modification = {
            "check_completeness": {"description": ["field1"]},
            "convert_to_canon": {"description": False}  # This will fail
        }
        
        result = engine._execute_linear_fsm(
            states_with_modification,
            data,
            "test_field",
            "field_selection_strategy",
            context
        )
        
        assert result["status"] == "not_passed"
        # most_current_data should be reverted to original
        assert context["most_current_data"] == original_data
    
    def test_execute_linear_fsm_empty_states(self):
        """Test that _execute_linear_fsm handles empty states."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        states = {}
        data = {}
        context = {}
        
        result = engine._execute_linear_fsm(
            states,
            data,
            "test_field",
            "test_strategy",
            context
        )
        
        assert result["status"] == "passed"
        assert len(result["states_executed"]) == 0


class TestFSMEngineLoadCanonicalConfig:
    """Tests for FSMEngine._load_canonical_config method."""
    
    def test_load_canonical_config_valid(self, tmp_path):
        """Test that _load_canonical_config loads valid YAML."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        canonical_path = tmp_path / "canonical.yaml"
        canonical_path.write_text("field1:\n  old_key: new_key\n")
        
        result = engine._load_canonical_config(str(canonical_path))
        
        assert "field1" in result
        assert result["field1"]["old_key"] == "new_key"
    
    def test_load_canonical_config_nonexistent(self):
        """Test that _load_canonical_config handles nonexistent file."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        
        result = engine._load_canonical_config("nonexistent.yaml")
        
        assert result == {}
    
    def test_load_canonical_config_empty(self, tmp_path):
        """Test that _load_canonical_config handles empty file."""
        config = {"fields": {}}
        engine = FSMEngine(config)
        canonical_path = tmp_path / "canonical.yaml"
        canonical_path.write_text("")
        
        result = engine._load_canonical_config(str(canonical_path))
        
        assert result == {}
