import pygame
import sys
from collections import deque

CELL_SIZE = 60
MARGIN = 2
BOARD_SIZE = 4
SCREEN_SIZE = (CELL_SIZE * BOARD_SIZE, CELL_SIZE * BOARD_SIZE)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY_COLOR = (128, 128, 128)
PURPLE_COLOR = (128, 0, 128)
RED_COLOR = (255, 0, 0)

DIRECTIONS = {
    'UP': (0, -1),
    'DOWN': (0, 1),
    'LEFT': (-1, 0),
    'RIGHT': (1, 0)
}

GRAY = 'gray'
PURPLE = 'purple'
RED = 'red'


class Piece:
    def __init__(self, piece_type, position, fixed=False):
        self.piece_type = piece_type
        self.position = position
        self.fixed = fixed
        self.color = self.get_color()

    def get_color(self):
        if self.piece_type == GRAY:
            return GRAY_COLOR
        elif self.piece_type == PURPLE:
            return PURPLE_COLOR
        elif self.piece_type == RED:
            return RED_COLOR
        return WHITE

    def is_movable(self):
        return not self.fixed and self.piece_type in [PURPLE, RED]


class Board:
    def __init__(self, size):
        self.size = size
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        self.voids = []

    def add_piece(self, piece):
        x, y = piece.position
        self.grid[y][x] = piece

    def move_piece(self, piece, direction):
        if not piece.is_movable() or direction not in DIRECTIONS:
            return False

        dx, dy = DIRECTIONS[direction]
        new_x = piece.position[0] + dx
        new_y = piece.position[1] + dy

        if 0 <= new_x < self.size and 0 <= new_y < self.size and self.grid[new_y][new_x] is None:
            self.grid[piece.position[1]][piece.position[0]] = None
            piece.position = (new_x, new_y)
            self.grid[new_y][new_x] = piece

            if piece.piece_type == PURPLE:
                self.handle_repulsion(new_x, new_y)
            elif piece.piece_type == RED:
                self.handle_attraction(new_x, new_y)

            return True
        return False

    def handle_repulsion(self, x, y):

        for col in range(self.size):
            target_piece = self.grid[y][col]
            if target_piece and target_piece.piece_type == GRAY:
                if col < x:
                    target_col = 0
                    while target_col <x and self.grid[y][target_col] is not None:
                        target_col += 1
                else:
                    target_col = self.size - 1
                    while target_col >= x and self.grid[y][target_col - 1] is not None:
                        target_col -= 1

                if (target_col != col) and (self.grid[y][target_col] is None):
                    self.grid[y][col] = None
                    target_piece.position = (target_col, y)
                    self.grid[y][target_col] = target_piece

        for row in range(self.size):
            target_piece = self.grid[row][x]
            if target_piece and target_piece.piece_type == GRAY:
                if row < y:  # Gray piece is above the purple piece
                    # Move it to the farthest up position
                    target_row = 0
                    while target_row < y and self.grid[target_row][x] is not None:
                        target_row += 1
                else:
                    target_row = self.size - 1
                    while target_row > y and self.grid[target_row - 1][x] is not None:
                        target_row -= 1

                if (target_row != row) and (self.grid[target_row][x] is None):
                    self.grid[row][x] = None  # Clear original position
                    target_piece.position = (x, target_row)
                    self.grid[target_row][x] = target_piece

        self.grid[y][x] = Piece(PURPLE, (x, y))

    def handle_attraction(self, x, y):

        for col in range(self.size):
            target_piece = self.grid[y][col]
            if target_piece and target_piece.piece_type == GRAY:
                if col < x:  # On the left side of the red piece
                    target_col = x - 1
                    while target_col > col and self.grid[y][target_col] is None:
                        target_col -= 1
                    target_col += 1
                else:
                    target_col = x + 1
                    while target_col < col and self.grid[y][target_col] is None:
                        target_col += 1
                    target_col -= 1

                if target_col != col and self.grid[y][target_col] is None:
                    self.grid[y][col] = None
                    target_piece.position = (target_col, y)
                    self.grid[y][target_col] = target_piece

        for row in range(self.size):
            target_piece = self.grid[row][x]
            if target_piece and target_piece.piece_type == GRAY:
                if row < y:
                    target_row = y - 1
                    while target_row > row and self.grid[target_row][x] is None:
                        target_row -= 1
                    target_row += 1
                else:
                    target_row = y + 1
                    while target_row < row and self.grid[target_row][x] is None:
                        target_row += 1
                    target_row -= 1

                if target_row != row and self.grid[target_row][x] is None:
                    self.grid[row][x] = None
                    target_piece.position = (x, target_row)
                    self.grid[target_row][x] = target_piece

    def is_solved(self):
        # Count how many voids are filled with any of the target pieces (GRAY, RED, or PURPLE)
        filled_voids = sum(
            1 for x, y in self.voids if self.grid[y][x] and self.grid[y][x].piece_type in [GRAY, RED, PURPLE]
        )
        # The game is solved when exactly two voids are filled
        return filled_voids == 3

    def get_piece_positions(self):
        """Return positions of movable pieces."""
        positions = {}
        for y in range(self.size):
            for x in range(self.size):
                piece = self.grid[y][x]
                if piece and piece.piece_type in [PURPLE, RED]:
                    positions[piece.piece_type] = (x, y)
        return positions

    def clone(self):
        """Create a deep copy of the board."""
        new_board = Board(self.size)
        new_board.voids = self.voids
        for y in range(self.size):
            for x in range(self.size):
                piece = self.grid[y][x]
                if piece:
                    new_piece = Piece(piece.piece_type, piece.position, piece.fixed)
                    new_board.add_piece(new_piece)
        return new_board

def get_cell(pos):
    x, y = pos
    return x // CELL_SIZE, y // CELL_SIZE


def determine_direction(old_pos, new_pos):
    ox, oy = old_pos
    nx, ny = new_pos
    if nx > ox:
        return 'RIGHT'
    elif nx < ox:
        return 'LEFT'
    elif ny > oy:
        return 'DOWN'
    elif ny < oy:
        return 'UP'
    return None


def draw_board(screen, board):
    for y in range(board.size):
        for x in range(board.size):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, WHITE, rect)
            pygame.draw.rect(screen, BLACK, rect, MARGIN)

            piece = board.grid[y][x]
            if piece:
                pygame.draw.circle(screen, piece.color, rect.center, CELL_SIZE // 2 - MARGIN * 2)

            if (x, y) in board.voids:
                pygame.draw.circle(screen, (200, 200, 200), rect.center, CELL_SIZE // 4)

def bfs_solve(board):
    queue = deque([(board, [])])
    visited = set()

    initial_positions = tuple(board.get_piece_positions().items())
    visited.add(initial_positions)

    while queue:
        current_board, path = queue.popleft()

        if current_board.is_solved():
            return path

        for piece_type, pos in current_board.get_piece_positions().items():
            for direction in DIRECTIONS:
                new_board = current_board.clone()
                piece = new_board.grid[pos[1]][pos[0]]

                if new_board.move_piece(piece, direction):
                    new_positions = tuple(new_board.get_piece_positions().items())

                    if new_positions not in visited:
                        visited.add(new_positions)
                        queue.append((new_board, path + [(piece_type, direction)]))

    return None
def dfs_solve(board):
    stack = [(board, [])]
    visited = set()

    initial_positions = tuple(board.get_piece_positions().items())
    visited.add(initial_positions)

    while stack:
        current_board, path = stack.pop()

        if current_board.is_solved():
            return path

        for piece_type, pos in current_board.get_piece_positions().items():
            for direction in DIRECTIONS:
                new_board = current_board.clone()
                piece = new_board.grid[pos[1]][pos[0]]

                if new_board.move_piece(piece, direction):
                    new_positions = tuple(new_board.get_piece_positions().items())

                    if new_positions not in visited:
                        visited.add(new_positions)
                        stack.append((new_board, path + [(piece_type, direction)]))

    return None

def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Logic Magnets")

    board = Board(BOARD_SIZE)
    board.add_piece(Piece(GRAY, (0, 0), fixed=True))
    board.add_piece(Piece(PURPLE, (0, 1)))  # Place near void
    board.add_piece(Piece(RED, (1, 2)))  # Place near void
    board.voids = [(1, 0), (2, 2), (3, 3)]  # Ensure voids are accessible

    bfs_solution = bfs_solve(board)
    if bfs_solution:
        print("BFS Solution found:")
        for move in bfs_solution:
            print(f"Move {move[0]} piece {move[1]}")
    else:
        print("No solution found with BFS.")

    dfs_solution = dfs_solve(board)
    if dfs_solution:
        print("\nDFS Solution found:")
        for move in dfs_solution:
            print(f"Move {move[0]} piece {move[1]}")
    else:
        print("No solution found with DFS.")

    running = True
    selected_piece = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                cell_x, cell_y = get_cell(pygame.mouse.get_pos())
                if 0 <= cell_x < BOARD_SIZE and 0 <= cell_y < BOARD_SIZE:
                    selected_piece = board.grid[cell_y][cell_x]

            elif event.type == pygame.MOUSEBUTTONUP:
                if selected_piece:
                    new_cell_x, new_cell_y = get_cell(pygame.mouse.get_pos())
                    direction = determine_direction(selected_piece.position, (new_cell_x, new_cell_y))
                    if direction:
                        moved = board.move_piece(selected_piece, direction)
                        if moved and board.is_solved():
                            print("Puzzle Solved!")
                            running = False
                    selected_piece = None

        screen.fill(BLACK)
        draw_board(screen, board)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
