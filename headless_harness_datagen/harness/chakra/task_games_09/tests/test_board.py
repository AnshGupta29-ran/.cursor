import unittest
from board import Board

class TestBoard(unittest.TestCase):
    def test_initial_no_matches(self):
        board = Board(rows=8, cols=8, seed=1)
        self.assertFalse(board.find_matches())
        self.assertTrue(board.has_legal_move())

    def test_legal_swap_and_score(self):
        board = Board(rows=5, cols=5, seed=2)
        # Find a legal swap
        move = None
        for r in range(board.rows):
            for c in range(board.cols):
                if c + 1 < board.cols and board.is_legal_swap((r, c), (r, c+1)):
                    move = ((r, c), (r, c+1))
                    break
                if r + 1 < board.rows and board.is_legal_swap((r, c), (r+1, c)):
                    move = ((r, c), (r+1, c))
                    break
            if move:
                break
        self.assertIsNotNone(move, "No legal move found");
        board.swap(*move)
        score, cascades = board.resolve_cascades()
        self.assertGreater(score, 0)
        self.assertGreaterEqual(cascades, 1)

if __name__ == '__main__':
    unittest.main()
