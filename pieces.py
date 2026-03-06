from game_board import Move

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def get_piece_moves(r, c, piece, board):
    moves = []
    is_white = piece.isupper()
    directions = []

    # Pawn
    if piece.upper() == "P":
        step = -1 if is_white else 1
        start_row = 6 if is_white else 1

        # single move
        nr, nc = r + step, c
        if in_bounds(nr, nc) and board[nr][nc] == ".":
            if (nr == 0 and is_white) or (nr == 7 and not is_white):
                for promo in 'qrbn':
                    moves.append(Move((r,c),(nr,nc),piece,promotion=promo))
            else:
                moves.append(Move((r,c),(nr,nc),piece))
            # double move
            nr2 = r + 2*step
            if r == start_row and board[nr2][nc] == '.':
                moves.append(Move((r,c),(nr2,nc),piece))

        # captures
        for dc in (-1,1):
            rr, cc = r+step, c+dc
            if in_bounds(rr, cc):
                target = board[rr][cc]
                if target != "." and target.isupper() != is_white:
                    if (rr == 0 and is_white) or (rr == 7 and not is_white):
                        for promo in 'qrbn':
                            moves.append(Move((r,c),(rr,cc),piece,captured=target,promotion=promo))
                    else:
                        moves.append(Move((r,c),(rr,cc),piece,captured=target))
                # en passant
                if getattr(board, 'en_passant', None) == (rr, cc):
                    moves.append(Move((r,c),(rr,cc),piece,captured='p' if is_white else 'P',is_en_passant=True))
        return moves

    # Knight
    elif piece.upper() == "N":
        jumps = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        for dr, dc in jumps:
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target == '.' or target.isupper() != is_white:
                    moves.append(Move((r,c),(nr,nc),piece,captured=target if target != '.' else '.'))
        return moves

    # King
    elif piece.upper() == "K":
        jumps = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in jumps:
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                target = board[nr][nc]
                if target == '.' or target.isupper() != is_white:
                    moves.append(Move((r,c),(nr,nc),piece,captured=target if target != '.' else '.'))
        return moves

    # Sliding pieces
    if piece.upper() == "R":
        directions = [(1,0),(-1,0),(0,1),(0,-1)]
    elif piece.upper() == "B":
        directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
    elif piece.upper() == "Q":
        directions = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            target = board[nr][nc]
            if target == '.':
                moves.append(Move((r,c),(nr,nc),piece))
            elif target.isupper() != is_white:
                moves.append(Move((r,c),(nr,nc),piece,captured=target))
                break
            else:
                break
            if piece.upper() in "NKB": break
            nr += dr
            nc += dc

    return moves