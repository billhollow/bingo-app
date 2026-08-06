from django.test import SimpleTestCase

from rooms.board_generator import InvalidBoardError, generate_board
from rooms.choices import BoardType


def make_goals(n):
    return [f"goal {i}" for i in range(n)]


class GenerateBoardFixedTests(SimpleTestCase):
    def test_exact_length_is_used_as_is(self):
        goals = make_goals(25)
        board = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.FIXED, seed="")
        self.assertEqual(board, goals)

    def test_wrong_length_raises(self):
        with self.assertRaises(InvalidBoardError):
            generate_board(goals=make_goals(24), rows=5, cols=5, board_type=BoardType.FIXED, seed="")

    def test_blank_goal_raises(self):
        goals = make_goals(24) + [""]
        with self.assertRaises(InvalidBoardError):
            generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.FIXED, seed="")


class GenerateBoardRandomizedTests(SimpleTestCase):
    def test_picks_requested_size_with_no_duplicates(self):
        goals = make_goals(40)
        board = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="123")
        self.assertEqual(len(board), 25)
        self.assertEqual(len(set(board)), 25)
        self.assertTrue(set(board) <= set(goals))

    def test_same_seed_is_deterministic(self):
        goals = make_goals(40)
        board_a = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="123")
        board_b = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="123")
        self.assertEqual(board_a, board_b)

    def test_different_seed_gives_a_different_board(self):
        goals = make_goals(40)
        board_a = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="123")
        board_b = generate_board(goals=goals, rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="456")
        self.assertNotEqual(board_a, board_b)

    def test_too_few_goals_raises(self):
        with self.assertRaises(InvalidBoardError):
            generate_board(
                goals=make_goals(10), rows=5, cols=5, board_type=BoardType.RANDOMIZED, seed="1"
            )


class GenerateBoardConfigurableSizeTests(SimpleTestCase):
    def test_non_square_board(self):
        board = generate_board(goals=make_goals(12), rows=3, cols=4, board_type=BoardType.FIXED, seed="")
        self.assertEqual(len(board), 12)

    def test_smaller_than_five_by_five(self):
        board = generate_board(goals=make_goals(9), rows=3, cols=3, board_type=BoardType.FIXED, seed="")
        self.assertEqual(len(board), 9)
