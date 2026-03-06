from chess_engine import ChessEngine

class AIPlayer:
    def __init__(self, depth=3):
        self.engine = ChessEngine(depth)
        self.depth = depth

    def get_best_move(self, board):
        """Return the best Move object for the current board."""
        # Reset node counter
        self.engine.nodes_evaluated = 0
        
        # Get the best move
        score, best_move = self.engine.minimax(board, self.engine.depth, float('-inf'), float('inf'), not board.white_to_move)
        
        # Print search statistics
        print(f"AI evaluated {self.engine.nodes_evaluated} nodes, best score: {score}")
        
        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """Wrapper for the engine's minimax function."""
        return self.engine.minimax(board, depth, alpha, beta, maximizing_player)

def get_ai_move(board, depth=3):
    ai = AIPlayer(depth)
    return ai.get_best_move(board)