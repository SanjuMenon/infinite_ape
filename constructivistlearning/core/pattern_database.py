"""
Pattern and Force database for the constructivist learning system.
Contains example patterns and forces across multiple domains.
"""

from typing import Dict, List
from .schemas import (
    Pattern, Force, CoreConcept, LearningIndicators, ForceEvolutionMap,
    ForceDefinition, ApplicationConditions, EvolutionOutcomes, ForceCategory
)


class PatternDatabase:
    """Database of learning patterns across different domains."""
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {}
        self.forces: Dict[str, Force] = {}
        self._initialize_patterns()
        self._initialize_forces()
    
    def _initialize_patterns(self):
        """Initialize the pattern database with example patterns."""
        
        # Programming Domain Patterns
        self.patterns["var_basic"] = Pattern(
            pattern_id="var_basic",
            name="Variable Storage",
            description="Storing a single piece of data with a name",
            complexity_level=2,
            domain_tags=["programming", "computer_science"],
            core_concept=CoreConcept(
                simple_definition="A named container that holds one value",
                key_components=["name", "value", "assignment"],
                examples=["age = 25", "name = 'Alice'", "is_active = True"]
            ),
            prerequisites=[],
            evolution_paths=["var_typed", "var_scope"],
            forces=ForceEvolutionMap(
                applicable_forces=["type_safety", "scope_context", "reliability"],
                force_evolution_map={
                    "type_safety": "var_typed",
                    "scope_context": "var_scope",
                    "reliability": "var_immutable"
                }
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=["can_create_variables", "understands_assignment", "uses_meaningful_names"],
                struggle_signals=["confuses_variables_with_values", "forgets_assignment_syntax"],
                readiness_criteria=["creates_variables_independently", "explains_variable_purpose"]
            )
        )
        
        self.patterns["var_typed"] = Pattern(
            pattern_id="var_typed",
            name="Typed Variables",
            description="Variables with specific data types and constraints",
            complexity_level=3,
            domain_tags=["programming", "computer_science"],
            core_concept=CoreConcept(
                simple_definition="A variable that can only hold values of a specific type",
                key_components=["type_declaration", "type_constraint", "type_safety"],
                examples=["int age = 25", "string name = 'Alice'", "bool isActive = true"]
            ),
            prerequisites=["var_basic"],
            evolution_paths=["var_scope", "var_complex"],
            forces=ForceEvolutionMap(
                applicable_forces=["scope_context", "complexity_requirement", "performance_pressure"],
                force_evolution_map={
                    "scope_context": "var_scope",
                    "complexity_requirement": "var_complex",
                    "performance_pressure": "var_optimized"
                }
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=["chooses_appropriate_types", "handles_type_errors", "explains_type_benefits"],
                struggle_signals=["confuses_types", "ignores_type_errors"],
                readiness_criteria=["consistently_uses_types", "explains_type_safety"]
            )
        )
        
        # Math Domain Patterns
        self.patterns["number_basic"] = Pattern(
            pattern_id="number_basic",
            name="Number Representation",
            description="Using symbols to represent quantities",
            complexity_level=1,
            domain_tags=["mathematics", "arithmetic"],
            core_concept=CoreConcept(
                simple_definition="A symbol that represents a specific quantity",
                key_components=["digit", "place_value", "magnitude"],
                examples=["5", "42", "1000"]
            ),
            prerequisites=[],
            evolution_paths=["number_signed", "number_decimal"],
            forces=ForceEvolutionMap(
                applicable_forces=["negative_context", "precision_requirement", "scale_context"],
                force_evolution_map={
                    "negative_context": "number_signed",
                    "precision_requirement": "number_decimal",
                    "scale_context": "number_scientific"
                }
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=["recognizes_numbers", "understands_quantity", "can_count"],
                struggle_signals=["confuses_digits", "doesn't_understand_quantity"],
                readiness_criteria=["consistently_recognizes_numbers", "explains_quantity"]
            )
        )
        
        self.patterns["number_signed"] = Pattern(
            pattern_id="number_signed",
            name="Signed Numbers",
            description="Numbers that can be positive or negative",
            complexity_level=2,
            domain_tags=["mathematics", "arithmetic"],
            core_concept=CoreConcept(
                simple_definition="A number that can represent values above or below zero",
                key_components=["sign", "magnitude", "direction"],
                examples=["+5", "-3", "0"]
            ),
            prerequisites=["number_basic"],
            evolution_paths=["number_decimal", "number_rational"],
            forces=ForceEvolutionMap(
                applicable_forces=["precision_requirement", "fraction_context", "real_world_application"],
                force_evolution_map={
                    "precision_requirement": "number_decimal",
                    "fraction_context": "number_rational",
                    "real_world_application": "number_measurement"
                }
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=["understands_negative_values", "can_compare_signed_numbers", "explains_direction"],
                struggle_signals=["confuses_signs", "doesn't_understand_zero"],
                readiness_criteria=["consistently_uses_signed_numbers", "explains_negative_concept"]
            )
        )
        
        # Language Domain Patterns
        self.patterns["word_basic"] = Pattern(
            pattern_id="word_basic",
            name="Word Meaning",
            description="A word represents a concept or object",
            complexity_level=1,
            domain_tags=["language", "vocabulary"],
            core_concept=CoreConcept(
                simple_definition="A sound or symbol that represents something",
                key_components=["sound", "meaning", "context"],
                examples=["cat", "run", "happy"]
            ),
            prerequisites=[],
            evolution_paths=["word_context", "word_relationship"],
            forces=ForceEvolutionMap(
                applicable_forces=["context_requirement", "relationship_context", "ambiguity_pressure"],
                force_evolution_map={
                    "context_requirement": "word_context",
                    "relationship_context": "word_relationship",
                    "ambiguity_pressure": "word_precise"
                }
            ),
            learning_indicators=LearningIndicators(
                mastery_signals=["understands_word_meanings", "uses_words_correctly", "recognizes_new_words"],
                struggle_signals=["confuses_similar_words", "doesn't_understand_context"],
                readiness_criteria=["consistently_uses_words", "explains_word_meanings"]
            )
        )
    
    def _initialize_forces(self):
        """Initialize the force database with example forces."""
        
        # Type Safety Force
        self.forces["type_safety"] = Force(
            force_id="type_safety",
            name="Type Safety Requirement",
            description="System must ensure data types are consistent and valid",
            category=ForceCategory.REQUIREMENT,
            intensity=4,
            domain_agnostic=True,
            force_definition=ForceDefinition(
                core_pressure="Data must be validated and consistent to prevent errors",
                evolution_direction="Pushes patterns toward type-aware, validated solutions",
                universal_examples=["type checking", "validation", "error prevention"]
            ),
            application_conditions=ApplicationConditions(
                pattern_compatibility=["var_basic", "data_input", "user_interaction"],
                prerequisite_forces=[],
                timing_considerations="Introduce when errors become frequent or reliability is needed"
            ),
            evolution_outcomes=EvolutionOutcomes(
                pattern_transformations={
                    "var_basic": "var_typed",
                    "data_input": "data_validated",
                    "user_interaction": "interaction_safe"
                },
                complexity_increase=2,
                new_capabilities=["error_prevention", "data_validation", "type_checking"]
            )
        )
        
        # Scope Context Force
        self.forces["scope_context"] = Force(
            force_id="scope_context",
            name="Scope Context",
            description="System must handle multiple contexts and access levels",
            category=ForceCategory.CONTEXT,
            intensity=3,
            domain_agnostic=True,
            force_definition=ForceDefinition(
                core_pressure="Different parts of the system need different access to resources",
                evolution_direction="Pushes patterns toward scoped, organized solutions",
                universal_examples=["local vs global", "public vs private", "context boundaries"]
            ),
            application_conditions=ApplicationConditions(
                pattern_compatibility=["var_typed", "function_basic", "data_structure"],
                prerequisite_forces=["type_safety"],
                timing_considerations="Introduce when multiple components need to interact"
            ),
            evolution_outcomes=EvolutionOutcomes(
                pattern_transformations={
                    "var_typed": "var_scope",
                    "function_basic": "function_scoped",
                    "data_structure": "structure_encapsulated"
                },
                complexity_increase=2,
                new_capabilities=["access_control", "organization", "modularity"]
            )
        )
        
        # Reliability Requirement Force
        self.forces["reliability"] = Force(
            force_id="reliability",
            name="Reliability Requirement",
            description="System must work consistently and predictably",
            category=ForceCategory.REQUIREMENT,
            intensity=4,
            domain_agnostic=True,
            force_definition=ForceDefinition(
                core_pressure="System must handle errors gracefully and maintain consistency",
                evolution_direction="Pushes patterns toward robust, error-handling solutions",
                universal_examples=["error checking", "validation", "backup systems"]
            ),
            application_conditions=ApplicationConditions(
                pattern_compatibility=["var_scope", "function_scoped", "data_operation"],
                prerequisite_forces=["type_safety", "scope_context"],
                timing_considerations="Introduce when system failures become problematic"
            ),
            evolution_outcomes=EvolutionOutcomes(
                pattern_transformations={
                    "var_scope": "var_immutable",
                    "function_scoped": "function_robust",
                    "data_operation": "operation_safe"
                },
                complexity_increase=2,
                new_capabilities=["error_handling", "consistency", "predictability"]
            )
        )
        
        # Negative Context Force (Math)
        self.forces["negative_context"] = Force(
            force_id="negative_context",
            name="Negative Context",
            description="System must handle values below zero or opposite directions",
            category=ForceCategory.CONTEXT,
            intensity=2,
            domain_agnostic=True,
            force_definition=ForceDefinition(
                core_pressure="Real-world situations require representing values below zero",
                evolution_direction="Pushes patterns toward bidirectional, directional solutions",
                universal_examples=["temperatures below zero", "debt", "opposite directions"]
            ),
            application_conditions=ApplicationConditions(
                pattern_compatibility=["number_basic", "measurement", "direction"],
                prerequisite_forces=[],
                timing_considerations="Introduce when real-world context requires negative values"
            ),
            evolution_outcomes=EvolutionOutcomes(
                pattern_transformations={
                    "number_basic": "number_signed",
                    "measurement": "measurement_signed",
                    "direction": "direction_bidirectional"
                },
                complexity_increase=1,
                new_capabilities=["negative_values", "direction", "opposition"]
            )
        )
        
        # Precision Requirement Force
        self.forces["precision_requirement"] = Force(
            force_id="precision_requirement",
            name="Precision Requirement",
            description="System must handle fractional or decimal values",
            category=ForceCategory.REQUIREMENT,
            intensity=3,
            domain_agnostic=True,
            force_definition=ForceDefinition(
                core_pressure="Real-world measurements and calculations require fractional precision",
                evolution_direction="Pushes patterns toward precise, fractional solutions",
                universal_examples=["money calculations", "scientific measurements", "time precision"]
            ),
            application_conditions=ApplicationConditions(
                pattern_compatibility=["number_signed", "calculation", "measurement"],
                prerequisite_forces=["negative_context"],
                timing_considerations="Introduce when whole numbers are insufficient for accuracy"
            ),
            evolution_outcomes=EvolutionOutcomes(
                pattern_transformations={
                    "number_signed": "number_decimal",
                    "calculation": "calculation_precise",
                    "measurement": "measurement_precise"
                },
                complexity_increase=2,
                new_capabilities=["fractional_values", "precision", "accuracy"]
            )
        )
    
    def get_pattern(self, pattern_id: str) -> Pattern:
        """Get a pattern by ID."""
        return self.patterns.get(pattern_id)
    
    def get_force(self, force_id: str) -> Force:
        """Get a force by ID."""
        return self.forces.get(force_id)
    
    def get_compatible_forces(self, pattern_id: str) -> List[Force]:
        """Get all forces compatible with a given pattern."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return []
        
        compatible_forces = []
        for force_id in pattern.forces.applicable_forces:
            force = self.get_force(force_id)
            if force:
                compatible_forces.append(force)
        
        return compatible_forces
    
    def get_evolution_paths(self, pattern_id: str, force_id: str) -> List[str]:
        """Get possible evolution paths for a pattern under a specific force."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return []
        
        return [pattern.forces.force_evolution_map.get(force_id, pattern_id)]
    
    def get_prerequisites(self, pattern_id: str) -> List[Pattern]:
        """Get all prerequisite patterns for a given pattern."""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return []
        
        prerequisites = []
        for prereq_id in pattern.prerequisites:
            prereq = self.get_pattern(prereq_id)
            if prereq:
                prerequisites.append(prereq)
        
        return prerequisites 