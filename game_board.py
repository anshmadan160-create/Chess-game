import copy
from dataclasses import dataclass

@dataclass
class Move:
    fr: tuple          # (row, col)
    to: tuple
    piece: str
    captured: str = '.'
    promotion: str = None
    is_en_passant: bool = False
    is_castling: bool = False

class Board:
    def __init__(self):
        self.board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        self.white_to_move = True
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.history = []
        self._stack = []

    # --- Helpers ---
    def in_bounds(self, r, c): return 0 <= r < 8 and 0 <= c < 8
    def piece_color(self, piece):
        if piece == '.': return None
        return 'w' if piece.isupper() else 'b'

    def print_board(self):
        print("  a b c d e f g h")
        for r in range(8):
            print(8-r, end=' ')
            for c in range(8):
                print(self.board[r][c], end=' ')
            print()
        print()
    
    def get_legal_moves_for_square(self, r, c):
        """Return all legal moves for the piece at (r, c)."""
        return [m for m in self.get_legal_moves() if m.fr == (r, c)]

    # --- King / Check ---
    def find_king(self, color):
        target = 'K' if color == 'w' else 'k'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def is_square_attacked(self, sq, by_color):
        r, c = sq
        # pawns
        step = 1 if by_color == 'w' else -1
        pawn = 'P' if by_color == 'w' else 'p'
        for dc in (-1, 1):
            rr, cc = r + step, c + dc
            if self.in_bounds(rr, cc) and self.board[rr][cc] == pawn:
                return True
        # knights
        for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            rr, cc = r + dr, c + dc
            if self.in_bounds(rr, cc):
                p = self.board[rr][cc]
                if p != '.' and self.piece_color(p) == by_color and p.lower() == 'n':
                    return True
        # sliding rook/queen
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            rr, cc = r + dr, c + dc
            while self.in_bounds(rr, cc):
                p = self.board[rr][cc]
                if p != '.':
                    if self.piece_color(p) == by_color and p.lower() in ('r', 'q'): return True
                    break
                rr += dr; cc += dc
        # sliding bishop/queen
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            rr, cc = r + dr, c + dc
            while self.in_bounds(rr, cc):
                p = self.board[rr][cc]
                if p != '.':
                    if self.piece_color(p) == by_color and p.lower() in ('b', 'q'): return True
                    break
                rr += dr; cc += dc
        # king
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr == 0 and dc == 0: continue
                rr, cc = r + dr, c + dc
                if self.in_bounds(rr, cc):
                    p = self.board[rr][cc]
                    if p != '.' and self.piece_color(p) == by_color and p.lower() == 'k': return True
        return False

    def is_in_check(self, color):
        king_sq = self.find_king(color)
        if not king_sq: return True
        return self.is_square_attacked(king_sq, 'w' if color == 'b' else 'b')

    # --- Move generation ---
    def get_legal_moves(self, color=None):
        color = 'w' if self.white_to_move else 'b' if color is None else color
        moves = self.generate_all_pseudo_legal_moves(color)
        moves += self.generate_castling_moves(color)
        legal = []
        for m in moves:
            self.push_move(m)
            if not self.is_in_check(color):
                legal.append(m)
            self.undo_move()
        return legal

    def generate_pawn_moves(self, r, c, color):
        """Generate all pseudo-legal moves for a pawn at position (r, c)."""
        moves = []
        step = -1 if color == 'w' else 1
        start_row = 6 if color == 'w' else 1
        
        # Single move forward
        if self.in_bounds(r+step, c) and self.board[r+step][c] == '.':
            # Check for promotion
            if (r+step == 0 and color == 'b') or (r+step == 7 and color == 'w'):
                for promo in 'qrbn': 
                    moves.append(Move((r,c),(r+step,c),self.board[r][c],promotion=promo))
            else:
                moves.append(Move((r,c),(r+step,c),self.board[r][c]))
            
            # Double move from starting position
            if r == start_row and self.in_bounds(r+2*step, c) and self.board[r+2*step][c] == '.':
                moves.append(Move((r,c),(r+2*step,c),self.board[r][c]))
        
        # Captures (including en passant)
        for dc in (-1, 1):
            if self.in_bounds(r+step, c+dc):
                target = self.board[r+step][c+dc]
                
                # Regular capture
                if target != '.' and self.piece_color(target) != color:
                    # Check for promotion
                    if (r+step == 0 and color == 'b') or (r+step == 7 and color == 'w'):
                        for promo in 'qrbn': 
                            moves.append(Move((r,c),(r+step,c+dc),self.board[r][c],captured=target,promotion=promo))
                    else:
                        moves.append(Move((r,c),(r+step,c+dc),self.board[r][c],captured=target))
                
                # En passant capture
                if self.en_passant == (r+step, c+dc):
                    moves.append(Move((r,c),(r+step,c+dc),self.board[r][c],is_en_passant=True))
        
        return moves

    def generate_all_pseudo_legal_moves(self, color):
        moves = []
        # Directions for each piece type
        directions = {
            'N': [(-2,1),(-2,-1),(-1,2),(-1,-2),(1,2),(1,-2),(2,1),(2,-1)],
            'B': [(-1,-1),(-1,1),(1,-1),(1,1)],
            'R': [(-1,0),(1,0),(0,-1),(0,1)],
            'Q': [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)],
            'K': [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]
        }
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == '.' or self.piece_color(piece) != color:
                    continue
                    
                piece_type = piece.upper()
                
                # Handle pawns separately
                if piece_type == 'P':
                    moves.extend(self.generate_pawn_moves(r, c, color))
                    continue
                
                # Handle other pieces
                if piece_type in directions:
                    for dr, dc in directions[piece_type]:
                        rr, cc = r + dr, c + dc
                        
                        # For sliding pieces (B, R, Q), continue in the same direction
                        if piece_type in 'BRQ':
                            while self.in_bounds(rr, cc):
                                target = self.board[rr][cc]
                                if target == '.':
                                    moves.append(Move((r,c),(rr,cc),piece))
                                elif self.piece_color(target) != color:
                                    moves.append(Move((r,c),(rr,cc),piece,captured=target))
                                    break
                                else:
                                    break
                                rr += dr
                                cc += dc
                        # For non-sliding pieces (N, K), just check the target square
                        else:
                            if self.in_bounds(rr, cc):
                                target = self.board[rr][cc]
                                if target == '.':
                                    moves.append(Move((r,c),(rr,cc),piece))
                                elif self.piece_color(target) != color:
                                    moves.append(Move((r,c),(rr,cc),piece,captured=target))
        
        return moves

    # --- Castling ---
    def generate_castling_moves(self, color):
        moves=[]
        b=self.board
        if color=='w':
            if self.castling_rights.get('K',False) and b[7][5]=='.' and b[7][6]=='.':
                if not self.is_square_attacked((7,4),'b') and not self.is_square_attacked((7,5),'b') and not self.is_square_attacked((7,6),'b'):
                    moves.append(Move((7,4),(7,6),'K',is_castling=True))
            if self.castling_rights.get('Q',False) and b[7][3]=='.' and b[7][2]=='.' and b[7][1]=='.':
                if not self.is_square_attacked((7,4),'b') and not self.is_square_attacked((7,3),'b') and not self.is_square_attacked((7,2),'b'):
                    moves.append(Move((7,4),(7,2),'K',is_castling=True))
        else:
            if self.castling_rights.get('k',False) and b[0][5]=='.' and b[0][6]=='.':
                if not self.is_square_attacked((0,4),'w') and not self.is_square_attacked((0,5),'w') and not self.is_square_attacked((0,6),'w'):
                    moves.append(Move((0,4),(0,6),'k',is_castling=True))
            if self.castling_rights.get('q',False) and b[0][3]=='.' and b[0][2]=='.' and b[0][1]=='.':
                if not self.is_square_attacked((0,4),'w') and not self.is_square_attacked((0,3),'w') and not self.is_square_attacked((0,2),'w'):
                    moves.append(Move((0,4),(0,2),'k',is_castling=True))
        return moves

    # --- Move push/pop ---
    def push_move(self, move):
        snapshot = {
            'board': copy.deepcopy(self.board),
            'white_to_move': self.white_to_move,
            'castling_rights': self.castling_rights.copy(),
            'en_passant': self.en_passant,
            'halfmove_clock': self.halfmove_clock,
            'fullmove_number': self.fullmove_number
        }
        self._stack.append(snapshot)

        r0,c0=move.fr; r1,c1=move.to
        piece=self.board[r0][c0]
        
        # Set default captured piece if not specified
        if not hasattr(move, 'captured') or move.captured is None:
            move.captured = self.board[r1][c1]

        # en passant
        if move.is_en_passant and self.en_passant:
            # In en passant, the captured pawn is on the same row, different column
            cap_r, cap_c = r0, c1
            move.captured = self.board[cap_r][cap_c]
            self.board[cap_r][cap_c]='.'

        # castling rook
        if move.is_castling:
            if piece in ('K','k'):
                if c1==6: 
                    self.board[r1][5]=self.board[r1][7] 
                    self.board[r1][7]='.'
                else: 
                    self.board[r1][3]=self.board[r1][0] 
                    self.board[r1][0]='.'

        # normal / promotion
        self.board[r0][c0]='.'
        if move.promotion:
            self.board[r1][c1] = move.promotion.upper() if piece.isupper() else move.promotion.lower()
        else:
            self.board[r1][c1] = piece

        # update castling rights
        if piece.lower()=='k':
            if piece.isupper(): 
                self.castling_rights['K']=False 
                self.castling_rights['Q']=False
            else: 
                self.castling_rights['k']=False 
                self.castling_rights['q']=False
        if piece.lower()=='r':
            if (r0,c0)==(7,0): self.castling_rights['Q']=False
            if (r0,c0)==(7,7): self.castling_rights['K']=False
            if (r0,c0)==(0,0): self.castling_rights['q']=False
            if (r0,c0)==(0,7): self.castling_rights['k']=False
        
        # Remove castling rights if a rook is captured
        if move.captured and move.captured.lower()=='r':
            if (r1,c1)==(7,0): self.castling_rights['Q']=False
            if (r1,c1)==(7,7): self.castling_rights['K']=False
            if (r1,c1)==(0,0): self.castling_rights['q']=False
            if (r1,c1)==(0,7): self.castling_rights['k']=False

        # en passant target
        self.en_passant=None
        if piece.lower()=='p' and abs(r1-r0)==2:
            self.en_passant=((r0+r1)//2,c0)

        # halfmove clock
        if piece.lower()=='p' or (move.captured and move.captured!='.'): 
            self.halfmove_clock=0
        else: 
            self.halfmove_clock+=1

        # fullmove number
        if not self.white_to_move: 
            self.fullmove_number+=1

        self.white_to_move = not self.white_to_move
        self.history.append(str(self.board))

    def undo_move(self):
        if not self._stack:
            return
            
        snapshot = self._stack.pop()
        self.board = snapshot['board']
        self.white_to_move = snapshot['white_to_move']
        self.castling_rights = snapshot['castling_rights']
        self.en_passant = snapshot['en_passant']
        self.halfmove_clock = snapshot['halfmove_clock']
        self.fullmove_number = snapshot['fullmove_number']
        if self.history: 
            self.history.pop()

    # Alias methods for chess engine compatibility
    def make_move(self, move):
        """Alias for push_move to match chess engine expectations."""
        self.push_move(move)

    def pop_move(self):
        """Alias for undo_move to match chess engine expectations."""
        self.undo_move()

    # --- Game end detection ---
    def is_fifty_move_rule(self): 
        return self.halfmove_clock>=100
        
    def is_threefold_repetition(self): 
        return self.history.count(str(self.board))>=3
        
    def is_insufficient_material(self):
        pieces=[]
        for r in range(8):
            for c in range(8):
                p=self.board[r][c]
                if p!='.' and p.lower()!='k': 
                    pieces.append((p,(r,c)))
        if not pieces: 
            return True
        if len(pieces)==1 and pieces[0][0].lower() in ('n','b'): 
            return True
        if len(pieces)==2:
            p1,pos1=pieces[0]; p2,pos2=pieces[1]
            if p1.lower()=='b' and p2.lower()=='b':
                if (pos1[0]+pos1[1])%2==(pos2[0]+pos2[1])%2: 
                    return True
        return False

    def is_game_draw(self):
        return self.is_fifty_move_rule() or self.is_threefold_repetition() or self.is_insufficient_material()

    def is_checkmate(self,color):
        moves = self.get_legal_moves(color)
        return len(moves)==0 and self.is_in_check(color)

    def is_stalemate(self,color):
        moves = self.get_legal_moves(color)
        return len(moves)==0 and not self.is_in_check(color)