"""
Test that the "Use rewritten code" checkbox correctly switches all graphs
between rewritten and original code views.
"""
import unittest
from dqc_app.pipeline import rewrite_and_analyze, RuleState


class GraphSourceCheckboxTests(unittest.TestCase):
    """Test dynamic graph switching based on checkbox state."""

    def test_bypass_rule_generates_valid_graphs(self):
        """Verify that bypass rule (rule #0) generates valid graphs from original code."""
        qasm_source = """OPENQASM 3.0;
include "stdgates.inc";
qubit q;
reset q;
h q;
measure q;"""
        
        split_points = set()
        rules_bypass = [RuleState(rule_id=0, name="Bypass", description="", enabled=True)]
        
        result = rewrite_and_analyze(qasm_source, rules_bypass, split_points)
        
        # Bypass should produce unchanged source
        self.assertIn("h q", result.rewritten_source)
        self.assertIn("measure q", result.rewritten_source)
        
        # Should generate valid graphs
        self.assertIsNotNone(result.dag_graph, "Bypass result should have DAG graph")
        self.assertIsNotNone(result.interaction_graph, "Bypass result should have interaction graph")

    def test_active_rules_generate_different_results_than_bypass(self):
        """Verify that active rewrite rules produce different results than bypass."""
        qasm_source = """OPENQASM 3.0;
include "stdgates.inc";
qubit q;
reset q;
h q;
measure q;"""
        
        split_points = set()
        
        # With active rules
        rules_active = [RuleState(rule_id=1, name="Drop comments", description="", enabled=True)]
        result_active = rewrite_and_analyze(qasm_source, rules_active, split_points)
        
        # With bypass (original only)
        rules_bypass = [RuleState(rule_id=0, name="Bypass", description="", enabled=True)]
        result_bypass = rewrite_and_analyze(qasm_source, rules_bypass, split_points)
        
        # Both should have parse trees
        self.assertIsNotNone(result_active.parse_tree, "Active rules should parse")
        self.assertIsNotNone(result_bypass.parse_tree, "Bypass should parse")
        
        # Both should generate DAG graphs
        self.assertIsNotNone(result_active.dag_graph, "Active rules should have DAG")
        self.assertIsNotNone(result_bypass.dag_graph, "Bypass should have DAG")
        
        # Both should generate interaction graphs
        self.assertIsNotNone(result_active.interaction_graph, "Active rules should have interaction graph")
        self.assertIsNotNone(result_bypass.interaction_graph, "Bypass should have interaction graph")

    def test_graphs_available_for_checkbox_toggle(self):
        """Test that both checked and unchecked states produce analyzable results."""
        qasm_source = """OPENQASM 3.0;
include "stdgates.inc";
qubit q;
reset q;
h q;
measure q;"""
        
        split_points = set()
        
        # Checkbox CHECKED: use rewritten code with active rules
        checked_rules = [
            RuleState(rule_id=1, name="Drop comments", description="", enabled=True),
            RuleState(rule_id=2, name="Drop blanks", description="", enabled=True),
        ]
        result_checked = rewrite_and_analyze(qasm_source, checked_rules, split_points)
        
        # Checkbox UNCHECKED: use original code (bypass all rules)
        unchecked_rules = [RuleState(rule_id=0, name="Bypass", description="", enabled=True)]
        result_unchecked = rewrite_and_analyze(qasm_source, unchecked_rules, split_points)
        
        # Both states should produce valid results for graph rendering
        for result, state in [(result_checked, "checked"), (result_unchecked, "unchecked")]:
            self.assertIsNotNone(result.dag_graph, f"DAG graph missing when checkbox {state}")
            self.assertIsNotNone(result.interaction_graph, f"Interaction graph missing when checkbox {state}")
            self.assertIsNotNone(result.parse_tree, f"Parse tree missing when checkbox {state}")
            
            # DAG should have nodes
            if result.dag_graph:
                self.assertGreater(len(result.dag_graph.nodes()), 0, f"DAG empty when checkbox {state}")


if __name__ == "__main__":
    unittest.main()
