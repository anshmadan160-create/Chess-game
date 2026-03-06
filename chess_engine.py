import math
import hashlib
from enum import Enum

class PieceType(Enum):
    PAWN = 'P'
    KNIGHT = 'N'
    BISHOP = 'B'
    ROOK = 'R'
    QUEEN = 'Q'
    KING = 'K'

class Move:
    def __init__(self, from_pos, to_pos, piece, captured='.', promotion=None, is_castling=False, is_en_passant=False):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece = piece
        self.captured = captured
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
    
    def __str__(self):
        return f"{self.piece}{self.from_pos}->{self.to_pos}"

class ChessBoard:
    def __init__(self):
        self.board = self.create_starting_board()
        self.white_to_move = True
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.move_history = []
        self.halfmove_clock = 0
        self.fullmove_number = 1
    
    def create_starting_board(self):
        return [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
    
    def in_bounds(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_piece(self, row, col):
        if self.in_bounds(row, col):
            return self.board[row][col]
        return None
    
    def set_piece(self, row, col, piece):
        if self.in_bounds(row, col):
            self.board[row][col] = piece
    
    def is_empty(self, row, col):
        return self.get_piece(row, col) == '.'
    
    def is_opponent(self, row, col, color):
        piece = self.get_piece(row, col)
        if piece == '.':
            return False
        return (color == 'w' and piece.islower()) or (color == 'b' and piece.isupper())
    
    def is_ally(self, row, col, color):
        piece = self.get_piece(row, col)
        if piece == '.':
            return False
        return (color == 'w' and piece.isupper()) or (color == 'b' and piece.islower())
    
    def get_legal_moves(self, color=None):
        if color is None:
            color = 'w' if self.white_to_move else 'b'
        
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece != '.' and ((color == 'w' and piece.isupper()) or (color == 'b' and piece.islower())):
                    moves.extend(self.get_piece_moves(r, c, piece))
        
        # Remove moves that would leave king in check
        legal_moves = []
        for move in moves:
            self.push_move(move)
            if not self.is_in_check(color):
                legal_moves.append(move)
            self.undo_move()
        
        return legal_moves
    
    def get_piece_moves(self, row, col, piece):
        piece_type = piece.upper()
        if piece_type == 'P':
            return self.get_pawn_moves(row, col, piece)
        elif piece_type == 'N':
            return self.get_knight_moves(row, col, piece)
        elif piece_type == 'B':
            return self.get_bishop_moves(row, col, piece)
        elif piece_type == 'R':
            return self.get_rook_moves(row, col, piece)
        elif piece_type == 'Q':
            return self.get_queen_moves(row, col, piece)
        elif piece_type == 'K':
            return self.get_king_moves(row, col, piece)
        return []
    
    def get_pawn_moves(self, row, col, piece):
        moves = []
        color = 'w' if piece.isupper() else 'b'
        direction = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        
        # Forward move
        if self.in_bounds(row + direction, col) and self.is_empty(row + direction, col):
            moves.append(self.create_move(row, col, row + direction, col, piece))
            
            # Double move from starting position
            if row == start_row and self.is_empty(row + 2*direction, col) and self.is_empty(row + direction, col):
                moves.append(self.create_move(row, col, row + 2*direction, col, piece))
        
        # Captures
        for dcol in [-1, 1]:
            if self.in_bounds(row + direction, col + dcol):
                target = self.get_piece(row + direction, col + dcol)
                if target != '.' and self.is_opponent(row + direction, col + dcol, color):
                    moves.append(self.create_move(row, col, row + direction, col + dcol, piece, target))
                
                # En passant
                if self.en_passant == (row + direction, col + dcol):
                    moves.append(Move((row, col), (row + direction, col + dcol), piece, 
                                    captured='p' if color == 'w' else 'P', is_en_passant=True))
        
        # Promotions
        promotion_row = 0 if color == 'b' else 7
        promotion_moves = []
        for move in moves:
            if move.to_pos[0] == promotion_row:
                for promo_piece in ['Q', 'R', 'B', 'N']:
                    promo_move = Move(move.from_pos, move.to_pos, move.piece, 
                                    move.captured, promotion=promo_piece, 
                                    is_castling=move.is_castling, is_en_passant=move.is_en_passant)
                    promotion_moves.append(promo_move)
        if promotion_moves:
            return promotion_moves
        
        return moves
    
    def get_knight_moves(self, row, col, piece):
        moves = []
        color = 'w' if piece.isupper() else 'b'
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self.in_bounds(new_row, new_col):
                if self.is_empty(new_row, new_col) or self.is_opponent(new_row, new_col, color):
                    captured = self.get_piece(new_row, new_col) if not self.is_empty(new_row, new_col) else '.'
                    moves.append(self.create_move(row, col, new_row, new_col, piece, captured))
        
        return moves
    
    def get_bishop_moves(self, row, col, piece):
        return self.get_sliding_moves(row, col, piece, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    
    def get_rook_moves(self, row, col, piece):
        return self.get_sliding_moves(row, col, piece, [(-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def get_queen_moves(self, row, col, piece):
        return self.get_sliding_moves(row, col, piece, 
                                    [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)])
    
    def get_sliding_moves(self, row, col, piece, directions):
        moves = []
        color = 'w' if piece.isupper() else 'b'
        
        for dr, dc in directions:
            for distance in range(1, 8):
                new_row, new_col = row + dr * distance, col + dc * distance
                if not self.in_bounds(new_row, new_col):
                    break
                
                if self.is_empty(new_row, new_col):
                    moves.append(self.create_move(row, col, new_row, new_col, piece))
                elif self.is_opponent(new_row, new_col, color):
                    captured = self.get_piece(new_row, new_col)
                    moves.append(self.create_move(row, col, new_row, new_col, piece, captured))
                    break
                else:
                    break
        
        return moves
    
    def get_king_moves(self, row, col, piece):
        moves = []
        color = 'w' if piece.isupper() else 'b'
        
        # Regular king moves
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                
                new_row, new_col = row + dr, col + dc
                if self.in_bounds(new_row, new_col):
                    if self.is_empty(new_row, new_col) or self.is_opponent(new_row, new_col, color):
                        captured = self.get_piece(new_row, new_col) if not self.is_empty(new_row, new_col) else '.'
                        moves.append(self.create_move(row, col, new_row, new_col, piece, captured))
        
        # Castling
        if not self.is_in_check(color):
            moves.extend(self.get_castling_moves(row, col, piece))
        
        return moves
    
    def get_castling_moves(self, row, col, piece):
        moves = []
        color = 'w' if piece.isupper() else 'b'
        king_side = 'K' if color == 'w' else 'k'
        queen_side = 'Q' if color == 'w' else 'q'
        
        # Kingside castling
        if self.castling_rights.get(king_side, False):
            if (self.is_empty(row, col+1) and self.is_empty(row, col+2) and
                not self.is_square_attacked((row, col+1), color) and
                not self.is_square_attacked((row, col+2), color)):
                moves.append(Move((row, col), (row, col+2), piece, is_castling=True))
        
        # Queenside castling
        if self.castling_rights.get(queen_side, False):
            if (self.is_empty(row, col-1) and self.is_empty(row, col-2) and self.is_empty(row, col-3) and
                not self.is_square_attacked((row, col-1), color) and
                not self.is_square_attacked((row, col-2), color)):
                moves.append(Move((row, col), (row, col-2), piece, is_castling=True))
        
        return moves
    
    def create_move(self, from_row, from_col, to_row, to_col, piece, captured='.'):
        return Move((from_row, from_col), (to_row, to_col), piece, captured)
    
    def push_move(self, move):
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        
        # Save current state for undo
        old_state = {
            'board': [row[:] for row in self.board],
            'castling': self.castling_rights.copy(),
            'en_passant': self.en_passant,
            'captured': move.captured
        }
        self.move_history.append(old_state)
        
        # Handle castling
        if move.is_castling:
            self.handle_castling(move)
        # Handle en passant
        elif move.is_en_passant:
            self.handle_en_passant(move)
        else:
            # Regular move
            self.board[to_row][to_col] = move.piece if not move.promotion else move.promotion
            self.board[from_row][from_col] = '.'
        
        # Update castling rights
        self.update_castling_rights(move)
        
        # Set en passant target
        self.en_passant = self.get_en_passant_target(move)
        
        # Switch turns
        self.white_to_move = not self.white_to_move
        if not self.white_to_move:
            self.fullmove_number += 1
    
    def handle_castling(self, move):
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        color = 'w' if move.piece.isupper() else 'b'
        
        # Move king
        self.board[to_row][to_col] = move.piece
        self.board[from_row][from_col] = '.'
        
        # Move rook
        if to_col > from_col:  # Kingside
            rook_from_col = 7
            rook_to_col = to_col - 1
            rook = 'R' if color == 'w' else 'r'
        else:  # Queenside
            rook_from_col = 0
            rook_to_col = to_col + 1
            rook = 'R' if color == 'w' else 'r'
        
        self.board[to_row][rook_to_col] = rook
        self.board[to_row][rook_from_col] = '.'
    
    def handle_en_passant(self, move):
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        
        # Move pawn
        self.board[to_row][to_col] = move.piece
        self.board[from_row][from_col] = '.'
        
        # Remove captured pawn
        capture_row = from_row
        self.board[capture_row][to_col] = '.'
    
    def update_castling_rights(self, move):
        piece = move.piece.upper()
        from_row, from_col = move.from_pos
        
        # King moved
        if piece == 'K':
            if move.piece.isupper():
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False
        
        # Rook moved
        elif piece == 'R':
            if from_row == 7:
                if from_col == 0:
                    self.castling_rights['Q'] = False
                elif from_col == 7:
                    self.castling_rights['K'] = False
            elif from_row == 0:
                if from_col == 0:
                    self.castling_rights['q'] = False
                elif from_col == 7:
                    self.castling_rights['k'] = False
        
        # Rook captured
        if move.captured.upper() == 'R':
            to_row, to_col = move.to_pos
            if to_row == 7:
                if to_col == 0:
                    self.castling_rights['Q'] = False
                elif to_col == 7:
                    self.castling_rights['K'] = False
            elif to_row == 0:
                if to_col == 0:
                    self.castling_rights['q'] = False
                elif to_col == 7:
                    self.castling_rights['k'] = False
    
    def get_en_passant_target(self, move):
        piece = move.piece.upper()
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        
        if piece == 'P' and abs(from_row - to_row) == 2:
            return ((from_row + to_row) // 2, from_col)
        return None
    
    def undo_move(self):
        if not self.move_history:
            return
        
        old_state = self.move_history.pop()
        self.board = old_state['board']
        self.castling_rights = old_state['castling']
        self.en_passant = old_state['en_passant']
        self.white_to_move = not self.white_to_move
        if self.white_to_move:
            self.fullmove_number -= 1
    
    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        return self.is_square_attacked(king_pos, color)
    
    def find_king(self, color):
        king = 'K' if color == 'w' else 'k'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return (r, c)
        return None
    
    def is_square_attacked(self, square, color):
        attacked_by = 'b' if color == 'w' else 'w'
        
        # Check pawn attacks
        pawn_dir = 1 if color == 'w' else -1
        for dcol in [-1, 1]:
            attack_square = (square[0] + pawn_dir, square[1] + dcol)
            if self.in_bounds(*attack_square):
                piece = self.get_piece(*attack_square)
                if piece.upper() == 'P' and ((color == 'w' and piece.islower()) or (color == 'b' and piece.isupper())):
                    return True
        
        # Check knight attacks
        knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
        for dr, dc in knight_moves:
            attack_square = (square[0] + dr, square[1] + dc)
            if self.in_bounds(*attack_square):
                piece = self.get_piece(*attack_square)
                if piece.upper() == 'N' and ((color == 'w' and piece.islower()) or (color == 'b' and piece.isupper())):
                    return True
        
        # Check sliding pieces (bishop, rook, queen)
        directions = [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]
        for dr, dc in directions:
            for distance in range(1, 8):
                attack_square = (square[0] + dr * distance, square[1] + dc * distance)
                if not self.in_bounds(*attack_square):
                    break
                
                piece = self.get_piece(*attack_square)
                if piece == '.':
                    continue
                
                if (color == 'w' and piece.islower()) or (color == 'b' and piece.isupper()):
                    piece_type = piece.upper()
                    if (dr != 0 and dc != 0 and piece_type in ['B', 'Q']) or \
                       ((dr == 0 or dc == 0) and piece_type in ['R', 'Q']) or \
                       (distance == 1 and piece_type == 'K'):
                        return True
                    break
                else:
                    break
        
        return False
    
    def is_checkmate(self, color):
        return self.is_in_check(color) and len(self.get_legal_moves(color)) == 0
    
    def is_stalemate(self, color):
        return not self.is_in_check(color) and len(self.get_legal_moves(color)) == 0
    
    def is_game_draw(self):
        # 50-move rule
        if self.halfmove_clock >= 100:
            return True
        
        # Insufficient material
        pieces = []
        for row in self.board:
            for piece in row:
                if piece != '.':
                    pieces.append(piece.upper())
        
        pieces_count = len(pieces)
        if pieces_count == 2:  # Only kings
            return True
        if pieces_count == 3 and ('B' in pieces or 'N' in pieces):
            return True
        
        # TODO: Add threefold repetition
        
        return False

class ChessEngine:
    def __init__(self, depth=3):
        self.depth = depth
        self.transposition_table = {}
        self.nodes_evaluated = 0
        
    def evaluate(self, board):
        """Enhanced evaluation function with positional scoring."""
        piece_values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1000}
        
        # Piece-square tables for positional evaluation
        pawn_table = [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10, -5, -5, 10, 10,  5,
            5, -5, -5,  5,  5, -5, -5,  5,
            0,  0,  0, 10, 10,  0,  0,  0,
            5,  5, 10, 15, 15, 10,  5,  5,
            10, 10, 20, 20, 20, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
            0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        knight_table = [
            -5, -4, -3, -3, -3, -3, -4, -5,
            -4, -2,  0,  0,  0,  0, -2, -4,
            -3,  0,  1,  1,  1,  1,  0, -3,
            -3,  0,  1,  2,  2,  1,  0, -3,
            -3,  0,  1,  2,  2,  1,  0, -3,
            -3,  0,  1,  1,  1,  1,  0, -3,
            -4, -2,  0,  0,  0,  0, -2, -4,
            -5, -4, -3, -3, -3, -3, -4, -5
        ]
        
        bishop_table = [
            -2, -1, -1, -1, -1, -1, -1, -2,
            -1,  0,  0,  0,  0,  0,  0, -1,
            -1,  0,  1,  1, 1,  1,  0, -1,
            -1,  0,  1,  2,  2,  1,  0, -1,
            -1,  0,  1,  2,  2,  1,  0, -1,
            -1,  0,  1,  1,  1,  1,  0, -1,
            -1,  0,  0,  0,  0,  0,  0, -1,
            -2, -1, -1, -1, -1, -1, -1, -2
        ]
        
        rook_table = [
            0,  0,  0,  5,  5,  0,  0,  0,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            5, 10, 10, 10, 10, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ]
        
        queen_table = [
            -2, -1, -1, -1, -1, -1, -1, -2,
            -1,  0,  0,  0,  0,  0,  0, -1,
            -1,  0,  1,  1,  1,  1,  0, -1,
            -1,  0,  1,  1,  1,  1,  0, -1,
            -1,  0,  1,  1,  1,  1,  0, -1,
            -1,  0,  1,  1,  1,  1,  0, -1,
            -1,  0,  0,  0,  0,  0,  0, -1,
            -2, -1, -1, -1, -1, -1, -1, -2
        ]
        
        king_table = [
            2,  3,  1,  0,  0,  1,  3,  2,
            2,  2,  0,  0,  0,  0,  2,  2,
            -1, -2, -2, -2, -2, -2, -2, -1,
            -2, -3, -3, -4, -4, -3, -3, -2,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3,
            -3, -4, -4, -5, -5, -4, -4, -3
        ]
        
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece != ".":
                    val = piece_values.get(piece.upper(), 0)
                    
                    # Add positional value
                    idx = r * 8 + c
                    if piece.upper() == 'P':
                        pos_val = pawn_table[idx] if piece.isupper() else pawn_table[63-idx]
                        val += pos_val * 0.1
                    elif piece.upper() == 'N':
                        pos_val = knight_table[idx] if piece.isupper() else knight_table[63-idx]
                        val += pos_val * 0.1
                    elif piece.upper() == 'B':
                        pos_val = bishop_table[idx] if piece.isupper() else bishop_table[63-idx]
                        val += pos_val * 0.1
                    elif piece.upper() == 'R':
                        pos_val = rook_table[idx] if piece.isupper() else rook_table[63-idx]
                        val += pos_val * 0.1
                    elif piece.upper() == 'Q':
                        pos_val = queen_table[idx] if piece.isupper() else queen_table[63-idx]
                        val += pos_val * 0.1
                    elif piece.upper() == 'K':
                        pos_val = king_table[idx] if piece.isupper() else king_table[63-idx]
                        val += pos_val * 0.1
                    
                    if piece.isupper():  # White
                        score += val
                    else:  # Black
                        score -= val
                        
        # Add mobility score (number of legal moves)
        mobility = len(board.get_legal_moves('w')) - len(board.get_legal_moves('b'))
        score += mobility * 0.1
        
        # Add king safety evaluation
        white_king_pos = board.find_king('w')
        black_king_pos = board.find_king('b')
        
        if white_king_pos:
            score -= 0.5 * len([sq for sq in [(white_king_pos[0]+dr, white_king_pos[1]+dc) 
                                            for dr in [-1,0,1] for dc in [-1,0,1] 
                                            if (dr != 0 or dc != 0)] 
                              if board.in_bounds(sq[0], sq[1]) and board.is_square_attacked(sq, 'b')])
        
        if black_king_pos:
            score += 0.5 * len([sq for sq in [(black_king_pos[0]+dr, black_king_pos[1]+dc) 
                                            for dr in [-1,0,1] for dc in [-1,0,1] 
                                            if (dr != 0 or dc != 0)] 
                              if board.in_bounds(sq[0], sq[1]) and board.is_square_attacked(sq, 'w')])
        
        return score

    def order_moves(self, board, moves, maximizing_player):
        """Order moves to improve alpha-beta pruning efficiency."""
        scored_moves = []
        for move in moves:
            score = 0
            
            # Prioritize captures by the value of the captured piece
            if move.captured != '.':
                piece_values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1000}
                score = 10 * piece_values.get(move.captured.upper(), 0)
                
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
                attacker_value = piece_values.get(move.piece.upper(), 0)
                victim_value = piece_values.get(move.captured.upper(), 0)
                score += victim_value - attacker_value
            
            # Prioritize checks
            board.push_move(move)
            if board.is_in_check('b' if maximizing_player else 'w'):
                score += 5
            board.undo_move()
            
            # Prioritize promotions
            if move.promotion:
                score += 9  # Queen promotion value
            
            scored_moves.append((score, move))
        
        # Sort moves by score (highest first for maximizing, lowest for minimizing)
        scored_moves.sort(key=lambda x: x[0], reverse=maximizing_player)
        return [move for _, move in scored_moves]

    def is_game_over(self, board):
        """Check if the game is over (checkmate, stalemate, or draw)."""
        color = 'w' if board.white_to_move else 'b'
        return (board.is_checkmate(color) or 
                board.is_stalemate(color) or 
                board.is_game_draw())

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        self.nodes_evaluated += 1
        
        # Store original alpha and beta values for transposition table
        alpha_original = alpha
        beta_original = beta
        
        # Check for terminal conditions
        if depth == 0:
            return self.quiescence_search(board, alpha, beta, maximizing_player), None
            
        if self.is_game_over(board):
            return self.evaluate(board), None

        # Create a hash of the board state for transposition table
        board_hash = hashlib.md5((str(board.board) + str(board.white_to_move) + 
                                 str(board.castling_rights) + str(board.en_passant)).encode()).hexdigest()
        
        # Check if we've seen this position before
        if board_hash in self.transposition_table:
            stored_depth, stored_eval, stored_flag = self.transposition_table[board_hash]
            if stored_depth >= depth:
                if stored_flag == "exact":
                    return stored_eval, None
                elif stored_flag == "lowerbound":
                    alpha = max(alpha, stored_eval)
                elif stored_flag == "upperbound":
                    beta = min(beta, stored_eval)
                
                if alpha >= beta:
                    return stored_eval, None

        # Get and order moves (good moves first for better pruning)
        moves = board.get_legal_moves()
        if not moves:
            eval_score = self.evaluate(board)
            # Store in transposition table
            self.transposition_table[board_hash] = (depth, eval_score, "exact")
            return eval_score, None
            
        ordered_moves = self.order_moves(board, moves, maximizing_player)

        best_move = None
        best_score = -math.inf if maximizing_player else math.inf
        
        if maximizing_player:
            max_eval = -math.inf
            for move in ordered_moves:
                board.push_move(move)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, False)
                board.undo_move()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
                    
            # Store the result in the transposition table
            if max_eval <= alpha_original:
                flag = "upperbound"
            elif max_eval >= beta_original:
                flag = "lowerbound"
            else:
                flag = "exact"
                
            self.transposition_table[board_hash] = (depth, max_eval, flag)
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in ordered_moves:
                board.push_move(move)
                eval_score, _ = self.minimax(board, depth - 1, alpha, beta, True)
                board.undo_move()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
                    
            # Store the result in the transposition table
            if min_eval <= alpha_original:
                flag = "upperbound"
            elif min_eval >= beta_original:
                flag = "lowerbound"
            else:
                flag = "exact"
                
            self.transposition_table[board_hash] = (depth, min_eval, flag)
            return min_eval, best_move

    def quiescence_search(self, board, alpha, beta, maximizing_player):
        """Quiescence search to avoid horizon effect."""
        stand_pat = self.evaluate(board)
        
        if maximizing_player:
            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
        else:
            if stand_pat <= alpha:
                return alpha
            if beta > stand_pat:
                beta = stand_pat
        
        # Only consider capture moves
        moves = board.get_legal_moves()
        capture_moves = [move for move in moves if move.captured != '.']
        ordered_captures = self.order_moves(board, capture_moves, maximizing_player)
        
        for move in ordered_captures:
            board.push_move(move)
            score = self.quiescence_search(board, alpha, beta, not maximizing_player)
            board.undo_move()
            
            if maximizing_player:
                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            else:
                if score <= alpha:
                    return alpha
                if score < beta:
                    beta = score
        
        return alpha if maximizing_player else beta

    def get_best_move(self, board):
        """Public method to get the best move for the current position."""
        self.nodes_evaluated = 0
        score, best_move = self.minimax(board, self.depth, -math.inf, math.inf, board.white_to_move)
        print(f"Nodes evaluated: {self.nodes_evaluated}, Score: {score}")
        return best_move

# Example usage
if __name__ == "__main__":
    board = ChessBoard()
    engine = ChessEngine(depth=3)
    
    # Test the engine
    best_move = engine.get_best_move(board)
    print(f"Best move: {best_move}")