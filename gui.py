import pygame
import os
from game_board import Board
from ai_player import AIPlayer
from game_board import Move

# Constants
WIDTH, HEIGHT = 480, 520  # Increased height for status area
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
FPS = 60

# Colors
WHITE = (245, 245, 220)
BLACK = (100, 100, 100)
HIGHLIGHT = (186, 202, 68)
STATUS_BG = (240, 240, 240)

# Load piece images
IMAGES = {}
pieces = ['p','r','n','b','q','k']
colors = ['w','b']

def create_missing_image(color, piece):
    """Create a simple colored rectangle with text as fallback for missing images."""
    img = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    bg_color = (200, 200, 200) if color == 'w' else (50, 50, 50)
    text_color = (0, 0, 0) if color == 'w' else (255, 255, 255)
    img.fill(bg_color)
    font = pygame.font.SysFont('Arial', 30)
    text = font.render(piece.upper(), True, text_color)
    img.blit(text, (SQUARE_SIZE//2 - text.get_width()//2, 
                   SQUARE_SIZE//2 - text.get_height()//2))
    # Save the image for future use
    if not os.path.exists("images"):
        os.makedirs("images")
    pygame.image.save(img, f"images/{color}{piece}.png")
    return img

# Load or create images
for color in colors:
    for piece in pieces:
        name = f"{color}{piece}"
        path = f"images/{name}.png"
        try:
            IMAGES[name] = pygame.transform.scale(
                pygame.image.load(path), (SQUARE_SIZE, SQUARE_SIZE)
            )
        except FileNotFoundError:
            print(f"Missing image file: {path}, creating a fallback")
            IMAGES[name] = create_missing_image(color, piece)

class Game:
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Engine")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.ai = AIPlayer(depth=3)
        self.selected = None
        self.valid_moves = []
    
    def draw_board(self):
        # Draw chess board
        for r in range(ROWS):
            for c in range(COLS):
                color = WHITE if (r+c)%2==0 else BLACK
                pygame.draw.rect(self.win, color, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        
        # Highlight selected square
        if self.selected:
            r, c = self.selected
            pygame.draw.rect(self.win, HIGHLIGHT, (c*SQUARE_SIZE, r*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)
        
        # Highlight valid moves
        for m in self.valid_moves:
            pygame.draw.rect(self.win, HIGHLIGHT, (m.to[1]*SQUARE_SIZE, m.to[0]*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)

    def draw_pieces(self):
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board.board[r][c]
                if piece != '.':
                    key = ''
                    if piece.isupper():  # white
                        key = 'w' + piece.lower()  # e.g., 'wq' for white queen
                    else:  # black
                        key = 'b' + piece  # e.g., 'bn' for black knight
                    self.win.blit(IMAGES[key], (c*SQUARE_SIZE, r*SQUARE_SIZE))

    def draw_status(self):
        # Draw status area background
        pygame.draw.rect(self.win, STATUS_BG, (0, HEIGHT - 40, WIDTH, 40))
        
        font = pygame.font.SysFont('Arial', 16)
        
        # Show whose turn it is
        turn_text = "White's Turn" if self.board.white_to_move else "Black's Turn"
        text = font.render(turn_text, True, (0, 0, 0))
        self.win.blit(text, (10, HEIGHT - 30))
        
        # Show game status
        status = ""
        if self.board.is_checkmate('w' if self.board.white_to_move else 'b'):
            status = "Checkmate! " + ("Black wins" if self.board.white_to_move else "White wins")
        elif self.board.is_stalemate('w' if self.board.white_to_move else 'b'):
            status = "Stalemate! Draw!"
        elif self.board.is_game_draw():
            status = "Draw!"
        elif self.board.is_in_check('w' if self.board.white_to_move else 'b'):
            status = "Check!"
        
        if status:
            text = font.render(status, True, (255, 0, 0))
            self.win.blit(text, (WIDTH - text.get_width() - 10, HEIGHT - 30))

    def main_loop(self):
        run = True
        while run:
            self.clock.tick(FPS)
            self.win.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_status()
            pygame.display.flip()

            if not self.board.white_to_move:
                # AI move
                move = self.ai.get_best_move(self.board)
                if move:
                    self.board.push_move(move)
                    # Reset selection after AI move
                    self.selected = None
                    self.valid_moves = []

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.board.white_to_move:
                    x, y = pygame.mouse.get_pos()
                    # Only process clicks on the board, not the status area
                    if y < HEIGHT - 40:
                        r, c = y//SQUARE_SIZE, x//SQUARE_SIZE
                        if self.selected:
                            # Try to move
                            move_obj = None
                            for m in self.valid_moves:
                                if m.to == (r,c):
                                    move_obj = m
                                    break
                            if move_obj:
                                self.board.push_move(move_obj)
                                self.selected = None
                                self.valid_moves = []
                            else:
                                # Select a different piece
                                piece = self.board.board[r][c]
                                if piece != '.' and piece.isupper():  # Only select white pieces
                                    self.selected = (r,c)
                                    self.valid_moves = self.board.get_legal_moves_for_square(r,c)
                                else:
                                    self.selected = None
                                    self.valid_moves = []
                        else:
                            # Select a piece
                            piece = self.board.board[r][c]
                            if piece != '.' and piece.isupper():  # Only select white pieces
                                self.selected = (r,c)
                                self.valid_moves = self.board.get_legal_moves_for_square(r,c)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.main_loop()