from game_board import Board, Move
from ai_player import AIPlayer

def print_board(board):
    print("  a b c d e f g h")
    for r in range(8):
        print(8-r, end=' ')
        for c in range(8):
            print(board.board[r][c], end=' ')
        print()
    print()

def parse_move(user_input, board):
    # Convert "e2e4" -> Move object
    if len(user_input) < 4: return None
    col_map = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}
    try:
        fr = (8-int(user_input[1]), col_map[user_input[0].lower()])
        to = (8-int(user_input[3]), col_map[user_input[2].lower()])
    except:
        return None
    for m in board.get_legal_moves():
        if m.fr==fr and m.to==to:
            return m
    return None

def main():
    board = Board()
    ai = AIPlayer(depth=3)

    print("Welcome to Chess Engine (Minimax + Alpha-Beta)")
    print("You are White, AI is Black.")

    while True:
        print_board(board)

        if board.white_to_move:
            move_str = input("Enter your move (e.g., e2e4) or 'quit': ").strip()
            if move_str.lower() == "quit":
                print("Exiting game...")
                break

            move = parse_move(move_str, board)
            if move:
                board.push_move(move)
            else:
                print("Invalid move. Try again.")
                continue
        else:
            print("AI is thinking...")
            _, ai_move = ai.minimax(board, ai.depth, -float('inf'), float('inf'), False)
            if ai_move is None:
                print("Game over!")
                break
            board.push_move(ai_move)
            print(f"AI plays: {chr(ai_move.fr[1]+97)}{8-ai_move.fr[0]}{chr(ai_move.to[1]+97)}{8-ai_move.to[0]}")

        # Check for game end
        if board.is_checkmate('w' if board.white_to_move else 'b'):
            print_board(board)
            print("Checkmate! " + ("Black wins" if board.white_to_move else "White wins"))
            break
        elif board.is_stalemate('w' if board.white_to_move else 'b'):
            print_board(board)
            print("Stalemate! Draw!")
            break
        elif board.is_game_draw():
            print_board(board)
            print("Draw!")
            break
        elif board.is_in_check('w' if board.white_to_move else 'b'):
            print("Check!")

if __name__ == "__main__":
    main()