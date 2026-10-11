from datetime import datetime
import unittest
from unittest.mock import patch

import app
from algorithms.expression_handler import evaluate_simple_expression
from algorithms.problem_solver import schedule_maximum_matches
from algorithms.search_sort import binary_search, linear_search, merge_sort, selection_sort
from data_structures.graph import Graph
from data_structures.linked_list import LinkedList
from data_structures.queue import Queue
from data_structures.stack import Stack
from data_structures.tree import BinarySearchTree


class PhaseOneTests(unittest.TestCase):
    def test_linked_list_insert_traverse_delete_and_tail_recovery(self):
        items = LinkedList()
        self.assertEqual(items.traverse(), [])
        self.assertIsNone(items.delete_by_student_id("missing"))
        first, second, third = ({"student_id": key} for key in ("A", "B", "C"))
        items.insert_at_end(first)
        items.insert_at_start(second)
        items.insert_at_end(third)
        self.assertEqual(items.traverse(), [second, first, third])
        self.assertEqual(items.delete_by_student_id("B"), second)
        self.assertEqual(items.delete_by_student_id("C"), third)
        items.insert_at_end({"student_id": "D"})
        self.assertEqual([row["student_id"] for row in items.traverse()], ["A", "D"])
        self.assertEqual(len(items), 2)

    def test_linked_stack_is_lifo(self):
        stack = Stack()
        self.assertTrue(stack.is_empty())
        self.assertIsNone(stack.peek())
        self.assertIsNone(stack.pop())
        stack.push("register")
        stack.push("score")
        self.assertEqual(stack.to_list(), ["score", "register"])
        self.assertEqual(stack.pop(), "score")
        self.assertEqual(stack.peek(), "register")
        self.assertEqual(len(stack), 1)

    def test_linked_queue_is_fifo_and_recovers_after_empty(self):
        queue = Queue()
        self.assertIsNone(queue.peek())
        self.assertIsNone(queue.dequeue())
        queue.enqueue("first")
        queue.enqueue("second")
        self.assertEqual(queue.to_list(), ["first", "second"])
        self.assertEqual(queue.dequeue(), "first")
        self.assertEqual(queue.dequeue(), "second")
        self.assertIsNone(queue.rear)
        queue.enqueue("after empty")
        self.assertEqual(queue.peek(), "after empty")
        self.assertEqual(len(queue), 1)

    def test_stack_based_expression_evaluation(self):
        self.assertEqual(evaluate_simple_expression("1200 + 40 * 2"), 1280)
        self.assertEqual(evaluate_simple_expression("(12 + 8) * 3"), 60)
        self.assertEqual(evaluate_simple_expression("-(4 + 2) * -3"), 18)
        self.assertAlmostEqual(evaluate_simple_expression("7 / 2"), 3.5)

    def test_expression_errors_are_rejected(self):
        for expression in ("", "2 +", "(2 * 3", "2(3)", "2 ** 3", "2 / 0"):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                evaluate_simple_expression(expression)


class PhaseTwoTests(unittest.TestCase):
    def test_bst_storage_traversals_and_search(self):
        tree = BinarySearchTree()
        self.assertEqual(tree.inorder(), [])
        self.assertFalse(tree.contains(10))
        for score in (8, 3, 10, 1, 6, 14, 6):
            tree.insert(score)
        self.assertEqual(tree.inorder(), [1, 3, 6, 6, 8, 10, 14])
        self.assertEqual(tree.preorder(), [8, 3, 1, 6, 6, 10, 14])
        self.assertEqual(tree.postorder(), [1, 6, 6, 3, 14, 10, 8])
        self.assertTrue(tree.contains(14))
        self.assertFalse(tree.contains(12))
        self.assertEqual(len(tree), 7)

    def test_graph_adjacency_list_bfs_dfs_and_directed_edges(self):
        graph = Graph(("Arena",))
        graph.add_edge("Arena", "Hall")
        graph.add_edge("Arena", "Court")
        graph.add_edge("Hall", "Court")
        self.assertEqual(graph.bfs("Arena"), ["Arena", "Hall", "Court"])
        self.assertEqual(graph.dfs("Arena"), ["Arena", "Hall", "Court"])
        self.assertEqual(graph.bfs("missing"), [])
        directed = Graph(directed=True)
        directed.add_edge("A", "B")
        self.assertEqual(directed.bfs("B"), ["B"])
        self.assertEqual(directed.adjacency["B"], [])


class PhaseThreeTests(unittest.TestCase):
    def setUp(self):
        self.players = [
            {"name": "Mira", "points": 8},
            {"name": "Aarav", "points": 12},
            {"name": "Zoya", "points": 4},
        ]

    def test_linear_and_binary_search(self):
        self.assertEqual(linear_search(self.players, "mIRA"), 0)
        ordered = sorted(self.players, key=lambda row: row["name"].casefold())
        self.assertEqual(ordered[binary_search(ordered, "ZOYA")]["name"], "Zoya")
        self.assertEqual(binary_search(ordered, "Missing"), -1)
        self.assertEqual(linear_search(self.players, "Missing"), -1)

    def test_selection_and_merge_sorts_are_correct_and_non_mutating(self):
        for sorter in (selection_sort, merge_sort):
            self.assertEqual([p["points"] for p in sorter(self.players)], [12, 8, 4])
            self.assertEqual([p["points"] for p in sorter(self.players, descending=False)], [4, 8, 12])
        tied = [{"name": "first", "points": 5}, {"name": "second", "points": 5}]
        self.assertEqual([p["name"] for p in merge_sort(tied)], ["first", "second"])
        self.assertEqual([p["name"] for p in tied], ["first", "second"])


class PhaseFourTests(unittest.TestCase):
    def test_greedy_scheduler_selects_maximum_compatible_intervals(self):
        matches = [
            {"name": "long", "start": 1, "end": 5},
            {"name": "early", "start": 0, "end": 2},
            {"name": "middle", "start": 2, "end": 4},
            {"name": "late", "start": 4, "end": 6},
        ]
        self.assertEqual(
            [m["name"] for m in schedule_maximum_matches(matches)],
            ["early", "middle", "late"],
        )

    def test_greedy_scheduler_rejects_invalid_intervals(self):
        with self.assertRaises(ValueError):
            schedule_maximum_matches([{"start": 4, "end": 2}])
        with self.assertRaises(ValueError):
            schedule_maximum_matches([{"start": "soon", "end": "later"}])

    def test_application_demo_integrates_structures_without_mysql(self):
        choices = [
            {"user_id": 7, "display_name": "Aarav", "game": "Chess"},
            {"user_id": 9, "display_name": "Mira", "game": "Badminton"},
        ]
        games = [
            {"name": "Morning", "starts_at": datetime(2026, 1, 1, 9), "rounds": 1},
            {"name": "Overlap", "starts_at": datetime(2026, 1, 1, 9, 30), "rounds": 1},
            {"name": "Afternoon", "starts_at": datetime(2026, 1, 1, 11), "rounds": 1},
        ]
        with (
            patch("app.database.choices", return_value=choices),
            patch("app.database.games", return_value=games),
            patch("app.player_rows", return_value=[{"points": 20}, {"points": 40}, {"points": 60}]),
        ):
            demo = app.phase_demo()
        self.assertEqual([row["name"] for row in demo["linkedList"]], ["Aarav", "Mira"])
        self.assertEqual(demo["stackTop"], "Score recorded")
        self.assertEqual(demo["stackActions"][0], "Score recorded")
        self.assertEqual(demo["queueFront"], "Next match check-in")
        self.assertEqual(demo["tree"]["inorder"], [20, 40, 60])
        self.assertTrue(demo["tree"]["searchFound"])
        self.assertEqual(demo["graph"]["bfs"][0], "Arena")
        self.assertEqual([row["name"] for row in demo["greedySchedule"]], ["Morning", "Afternoon"])


if __name__ == "__main__":
    unittest.main()
