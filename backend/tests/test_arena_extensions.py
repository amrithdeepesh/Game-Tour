import unittest
from algorithms.expression_handler import (
    evaluate_simple_expression,
    evaluate_expression_detailed,
)
from algorithms.problem_solver import schedule_tournament_events
from algorithms.search_sort import (
    linear_search_detailed,
    binary_search_detailed,
    merge_sort_detailed,
    benchmark_search_sort,
)
from data_structures.graph import Graph
from data_structures.linked_list import LinkedList
from data_structures.queue import Queue
from data_structures.stack import Stack
from data_structures.tree import BinarySearchTree, TournamentBinaryTree


class ArenaExtensionTests(unittest.TestCase):
    def test_linked_list_positional_insert_and_delete(self):
        ll = LinkedList()
        ll.insert_at_end({"id": 1, "name": "Sprint"})
        ll.insert_at_start({"id": 0, "name": "Warmup"})
        ll.insert_at_position(1, {"id": 0.5, "name": "Stretching"})

        items = [x["name"] for x in ll.traverse()]
        self.assertEqual(items, ["Warmup", "Stretching", "Sprint"])
        self.assertEqual(len(ll), 3)

        # Bounds check
        with self.assertRaises(IndexError):
            ll.insert_at_position(10, {"id": 99})

        # Search
        idx, data = ll.search("Stretching", "name")
        self.assertEqual(idx, 1)
        self.assertEqual(data["name"], "Stretching")

        # Delete by position
        del_item = ll.delete_at_position(1)
        self.assertEqual(del_item["name"], "Stretching")
        self.assertEqual([x["name"] for x in ll.traverse()], ["Warmup", "Sprint"])

        # Delete by value
        ll.delete_by_value("Warmup", "name")
        self.assertEqual([x["name"] for x in ll.traverse()], ["Sprint"])
        self.assertEqual(len(ll), 1)

    def test_bst_deletion_and_extrema(self):
        bst = BinarySearchTree()
        self.assertIsNone(bst.find_min())
        self.assertIsNone(bst.find_max())
        self.assertFalse(bst.delete(99))

        values = [50, 30, 70, 20, 40, 60, 80]
        for v in values:
            bst.insert(v)

        self.assertEqual(bst.find_min(), 20)
        self.assertEqual(bst.find_max(), 80)
        self.assertEqual(bst.inorder(), [20, 30, 40, 50, 60, 70, 80])

        # Delete leaf node (20)
        self.assertTrue(bst.delete(20))
        self.assertEqual(bst.inorder(), [30, 40, 50, 60, 70, 80])

        # Delete node with 2 children (50 root)
        self.assertTrue(bst.delete(50))
        self.assertEqual(bst.inorder(), [30, 40, 60, 70, 80])
        self.assertEqual(bst.find_min(), 30)

    def test_tournament_bracket_tree(self):
        tree = TournamentBinaryTree.build_sample_bracket()
        bracket_dict = tree.to_dict()
        self.assertEqual(bracket_dict["match"], "Championship Final")
        self.assertEqual(bracket_dict["winner"], "Falcons A")
        self.assertIn("Championship Final", tree.preorder())
        self.assertEqual(len(tree.preorder()), 7)

    def test_graph_bfs_detailed_queue_states(self):
        g = Graph(("Court 1", "Court 2", "Court 3"))
        g.add_edge("Court 1", "Court 2")
        g.add_edge("Court 2", "Court 3")

        trace = g.bfs_detailed("Court 1")
        self.assertEqual(trace["order"], ["Court 1", "Court 2", "Court 3"])
        self.assertTrue(len(trace["steps"]) >= 3)
        # Check first step has queue with start venue
        self.assertIn("Court 1", trace["steps"][0]["queue"])

    def test_expression_detailed_conversion_and_evaluation(self):
        expr = "(10 + 5) * 2"
        res = evaluate_expression_detailed(expr)
        self.assertEqual(res["result"], 30)
        self.assertIn("10", res["postfix"])
        self.assertTrue(len(res["conversion_steps"]) > 0)
        self.assertTrue(len(res["evaluation_steps"]) > 0)

    def test_search_and_sort_detailed(self):
        data = [
            {"name": "Zoya", "points": 10},
            {"name": "Aarav", "points": 50},
            {"name": "Meera", "points": 30},
        ]
        # Linear search detailed
        lin_res = linear_search_detailed(data, "Aarav", "name")
        self.assertTrue(lin_res["found"])
        self.assertEqual(lin_res["index"], 1)

        # Binary search detailed
        bin_res = binary_search_detailed(data, "Aarav", "name")
        self.assertTrue(bin_res["found"])
        self.assertEqual(bin_res["item"]["name"], "Aarav")

        # Merge sort detailed
        merge_res = merge_sort_detailed(data, "points", descending=True)
        self.assertEqual([x["points"] for x in merge_res["sorted"]], [50, 30, 10])
        self.assertTrue(len(merge_res["splits"]) > 0)
        self.assertTrue(len(merge_res["merges"]) > 0)

    def test_benchmark_runner(self):
        bench = benchmark_search_sort()
        self.assertIn("benchmarks", bench)
        self.assertTrue(len(bench["benchmarks"]) > 0)
        self.assertIn("linear_search", bench["complexities"])

    def test_greedy_tournament_scheduler_conflict_resolution(self):
        candidates = [
            {"id": 1, "name": "Sprint 100m", "venue": "Track", "start": 9.0, "end": 10.0, "participants": ["Aarav"]},
            {"id": 2, "name": "Relay 4x100m", "venue": "Track", "start": 9.5, "end": 10.5, "participants": ["Ishan"]},  # Venue overlap
            {"id": 3, "name": "Badminton R1", "venue": "Court 1", "start": 9.5, "end": 10.5, "participants": ["Aarav"]}, # Participant overlap with Sprint
            {"id": 4, "name": "Chess Blitz", "venue": "Hall A", "start": 10.0, "end": 11.0, "participants": ["Zoya"]},    # Feasible
        ]
        result = schedule_tournament_events(candidates)
        scheduled_names = [x["name"] for x in result["scheduled"]]
        rejected_names = [x["name"] for x in result["rejected"]]

        self.assertIn("Sprint 100m", scheduled_names)
        self.assertIn("Chess Blitz", scheduled_names)
        self.assertIn("Relay 4x100m", rejected_names)
        self.assertIn("Badminton R1", rejected_names)
        self.assertEqual(result["total_requested"], 4)
        self.assertEqual(len(result["decision_trace"]), 4)


if __name__ == "__main__":
    unittest.main()
