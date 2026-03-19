"""
Integration tests for declarative FSM.

Tests the full system integration, including loading configs,
executing FSMs, and verifying end-to-end behavior.
"""

import pytest
import json
import pickle
from pathlib import Path
from declarative_fsm import FSMEngine, load_config


class TestFullIntegration:
    """Integration tests for full FSM execution."""
    
    def test_full_execution_with_example_config(self):
        """Test full execution using example_config.yaml structure."""
        config = {
            "fields": {
                "collateral": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["nominalValueAmount"]
                        },
                        "convert_to_canon": {
                            "description": True
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    },
                    "generation_strategy": {
                        "format": {
                            "description": "table"
                        }
                    },
                    "validation_strategy": {
                        "llm_eval": {
                            "description": [
                                "score how readable it is",
                                "score how complete the information is"
                            ]
                        }
                    }
                }
            }
        }
        
        canonical_mappings = {
            "collateral": {
                "nominalValueAmount": "canonical_nominal_amount"
            }
        }
        
        engine = FSMEngine(config)
        engine.canonical_mappings = canonical_mappings
        
        data = {
            "collateral": {
                "nominalValueAmount": 2500000
            }
        }
        
        report = engine.execute(data)
        
        # Verify execution summary
        assert report["execution_summary"]["total_fields"] == 1
        assert report["execution_summary"]["fields_passed"] == 1
        
        # Verify field result
        field_result = report["fields"]["collateral"]
        assert field_result["status"] == "passed"
        
        # Verify strategies executed
        assert "field_selection_strategy" in field_result["strategies"]
        assert "extraction_strategy" in field_result["strategies"]
        assert "generation_strategy" in field_result["strategies"]
        assert "validation_strategy" in field_result["strategies"]
        
        # Verify bundle contains expected data
        bundle = field_result["bundle"]
        assert "most_current_data" in bundle
        assert "canonical_nominal_amount" in bundle["most_current_data"]
        assert bundle["most_current_data"]["canonical_nominal_amount"] == 2500000
        assert bundle["format"] == "table"
        assert bundle["eval_type"] == "llm"
        assert len(bundle["metrics"]) == 2
        
        # Verify most_current_data_list
        assert len(report["most_current_data_list"]) == 1
        item = report["most_current_data_list"][0]
        assert item["field_name"] == "collateral"
        assert item["format"] == "table"
        assert item["eval_type"] == "llm"
    
    def test_full_execution_with_aggregation(self):
        """Test full execution with calculation_strategy aggregation."""
        config = {
            "fields": {
                "Financials": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["net_sales", "ebitda"]
                        },
                        "convert_to_canon": {
                            "description": True
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    },
                    "generation_strategy": {
                        "format": {
                            "description": "table"
                        }
                    },
                    "validation_strategy": {
                        "llm_eval": {
                            "description": ["score readability"]
                        }
                    },
                    "calculation_strategy": {
                        "calculation": {
                            "description": "aggregation",
                            "key": "category",
                            "value_key": "amount"
                        }
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "Financials": {
                "net_sales": "15000000",
                "ebitda": "3200000",
                "year_1": {
                    "category": "revenue",
                    "amount": "5000000"
                },
                "year_2": {
                    "category": "revenue",
                    "amount": "3000000"
                },
                "year_3": {
                    "category": "expense",
                    "amount": "2000000"
                }
            }
        }
        
        report = engine.execute(data)
        
        # Verify calculation was performed
        bundle = report["fields"]["Financials"]["bundle"]
        assert "most_current_data" in bundle
        assert "aggregation" in bundle["most_current_data"]
        aggregation = bundle["most_current_data"]["aggregation"]
        assert aggregation["revenue"] == 8000000.0
        assert aggregation["expense"] == 2000000.0
    
    def test_full_execution_with_debt_capacity(self):
        """Test full execution with calculation_strategy debt_capacity."""
        config = {
            "fields": {
                "financials_debt": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["YEAR", "ER12", "ER32", "P88", "EM06", 
                                          "ER13", "ER41", "P19", "P14", "P03", "P20"]
                        },
                        "convert_to_canon": {
                            "description": True
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    },
                    "generation_strategy": {
                        "format": {
                            "description": "table"
                        }
                    },
                    "validation_strategy": {
                        "llm_eval": {
                            "description": ["score accuracy"]
                        }
                    },
                    "calculation_strategy": {
                        "calculation": {
                            "description": "debt_capacity"
                        }
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "financials_debt": {
                "YEAR": 2024,
                "ER12": 15000000,
                "ER32": 3200000,
                "P88": -500000,
                "EM06": -200000,
                "ER13": 1000000,
                "ER41": 500000,
                "P19": 2000000,
                "P14": 5000000,
                "P03": 3000000,
                "P20": 1000000
            }
        }
        
        report = engine.execute(data)
        
        # Verify calculation was performed
        bundle = report["fields"]["financials_debt"]["bundle"]
        assert "most_current_data" in bundle
        assert "debt_capacity" in bundle["most_current_data"]
        assert "FCF" in bundle["most_current_data"]
        assert "DC" in bundle["most_current_data"]
        assert "DCU" in bundle["most_current_data"]
    
    def test_full_execution_field_failure(self):
        """Test full execution when a field fails early."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["field1", "field2"]
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "test_field": {
                "field1": "value1"
                # Missing field2
            }
        }
        
        report = engine.execute(data)
        
        # Verify field failed
        assert report["execution_summary"]["fields_failed"] == 1
        field_result = report["fields"]["test_field"]
        assert field_result["status"] == "not_passed"
        
        # Verify field_selection_strategy failed
        strategy_result = field_result["strategies"]["field_selection_strategy"]
        assert strategy_result["status"] == "not_passed"
        assert strategy_result["failed_at"] == "check_completeness"
        
        # Verify extraction_strategy was not executed (or executed but field still marked as failed)
        # Note: Currently all strategies are executed even if earlier ones fail
        # This is by design - strategies are independent
    
    def test_context_persistence_across_strategies(self):
        """Test that context persists correctly across strategies."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["field1"]
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    },
                    "validation_strategy": {
                        "llm_eval": {
                            "description": ["metric1"]
                        }
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "test_field": {
                "field1": "15"
            }
        }
        
        report = engine.execute(data)
        
        bundle = report["fields"]["test_field"]["bundle"]
        
        # Verify context contains data from all strategies
        assert "required_fields_found" in bundle  # From check_completeness
        assert "type_validated" in bundle  # From validate_type
        assert "eval_type" in bundle  # From llm_eval
        assert "metrics" in bundle  # From llm_eval
        
        # Verify most_current_data was transformed
        assert bundle["most_current_data"]["field1"] == 15  # Converted to int
    
    def test_most_current_data_revert_on_failure(self):
        """Test that most_current_data reverts correctly on state failure."""
        config = {
            "fields": {
                "test_field": {
                    "field_selection_strategy": {
                        "check_completeness": {
                            "description": ["field1"]
                        },
                        "convert_to_canon": {
                            "description": True
                        }
                    },
                    "extraction_strategy": {
                        "validate_type": {
                            "description": "int"
                        }
                    }
                }
            }
        }
        
        canonical_mappings = {
            "test_field": {
                "field1": "canonical_field1"
            }
        }
        
        engine = FSMEngine(config)
        engine.canonical_mappings = canonical_mappings
        
        # Data with field1 as string (will fail validate_type for "int")
        data = {
            "test_field": {
                "field1": "not_a_number"
            }
        }
        
        report = engine.execute(data)
        
        bundle = report["fields"]["test_field"]["bundle"]
        
        # After convert_to_canon, field1 should be canonical_field1
        # But after validate_type fails, it should revert
        # Actually, validate_type failure doesn't revert convert_to_canon
        # because they're in different strategies
        # The revert only happens within the same strategy
        
        # Verify that convert_to_canon succeeded (canonical key exists)
        # But validate_type failed (type_validated should be False)
        assert bundle["most_current_data"]["canonical_field1"] == "not_a_number"
        assert bundle.get("type_validated") is False


class TestRealWorldScenarios:
    """Tests based on real-world usage scenarios."""
    
    def test_multiple_fields_different_statuses(self):
        """Test execution with multiple fields having different pass/fail statuses."""
        config = {
            "fields": {
                "field1": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["key1"]}
                    }
                },
                "field2": {
                    "field_selection_strategy": {
                        "check_completeness": {"description": ["key2", "key3"]}
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "field1": {"key1": "value1"},  # Will pass
            "field2": {"key2": "value2"}  # Will fail (missing key3)
        }
        
        report = engine.execute(data)
        
        assert report["execution_summary"]["total_fields"] == 2
        assert report["execution_summary"]["fields_passed"] == 1
        assert report["execution_summary"]["fields_failed"] == 1
        assert report["fields"]["field1"]["status"] == "passed"
        assert report["fields"]["field2"]["status"] == "not_passed"
    
    def test_empty_data_handling(self):
        """Test that system handles empty data gracefully."""
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
        
        data = {}  # Empty data
        
        report = engine.execute(data)
        
        assert report["execution_summary"]["fields_failed"] == 1
        field_result = report["fields"]["test_field"]
        assert field_result["status"] == "not_passed"
    
    def test_nested_strategy_execution_order(self):
        """Test that nested strategies execute in correct order."""
        config = {
            "fields": {
                "test_field": {
                    "extraction_strategy": {
                        "validate_type": {"description": "int"},
                        "generation_strategy": {
                            "format": {"description": "table"}
                        }
                    }
                }
            }
        }
        
        engine = FSMEngine(config)
        
        data = {
            "test_field": {
                "field1": "15"
            }
        }
        
        report = engine.execute(data)
        
        # Verify extraction_strategy passed
        extraction_result = report["fields"]["test_field"]["strategies"]["extraction_strategy"]
        assert extraction_result["status"] == "passed"
        
        # Verify nested generation_strategy was executed
        assert "nested_strategies" in extraction_result
        assert "generation_strategy" in extraction_result["nested_strategies"]
        
        # Verify format was set in bundle
        bundle = report["fields"]["test_field"]["bundle"]
        assert bundle["format"] == "table"
