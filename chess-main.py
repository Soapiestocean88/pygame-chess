import pygame
import pygame.gfxdraw
import os
import sys
import datetime
import copy

pygame.init()


class ResourceManager:
    @staticmethod
    def resource_path(relative_path):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)


class Game:
    def __init__(self):
        self.TILESIZE = 64
        self.can_black_castle = True
        self.can_white_castle = True
        self.game_running = True
        self.turn = "w"
        self.board = Board(self.TILESIZE)
        self.selected = None
        self.move_history = []
        self.previous_boards = []
        self.screen = pygame.display.set_mode((8 * self.TILESIZE, 8 * self.TILESIZE))
        pygame.display.set_caption("Google Chrome")
        self.load_icon()

    def load_icon(self):
        icon_path = ResourceManager.resource_path("images/icon.png")
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)
            icon = pygame.transform.scale(icon, (32, 32))
            pygame.display.set_icon(icon)

    def click(self, mouse_x, mouse_y):
        selected_tile_x = mouse_x // self.TILESIZE
        selected_tile_y = mouse_y // self.TILESIZE
        selected_piece = self.board.get_piece_at((selected_tile_x, selected_tile_y))

        if selected_piece and selected_piece.colour == self.turn:
            self.selected = (selected_tile_x, selected_tile_y)

    def make_move(self, start_pos, end_pos):
        piece = self.board.get_piece_at(start_pos)
        if (
            piece
            and piece.colour == self.turn
            and end_pos in piece.get_moves(self.board)
        ):
            self.previous_boards.append(copy.deepcopy(self.board.board))
            san_move = self.convert_to_san(start_pos, end_pos, piece)
            self.move_history.append(san_move)
            self.board.move_piece(start_pos, end_pos)
            self.switch_turn()
            self.selected = None

    def undo_move(self):
        if self.previous_boards:
            self.board.board = self.previous_boards.pop()
            self.move_history.pop()
            self.switch_turn()

    def convert_to_san(self, start_pos, end_pos, piece):
        col_names = "abcdefgh"
        start_file, start_rank = start_pos
        end_file, end_rank = end_pos
        start_square = f"{col_names[start_file]}{8 - start_rank}"
        end_square = f"{col_names[end_file]}{8 - end_rank}"
        return f"{piece.symbol}{end_square}"

    def switch_turn(self):
        self.turn = "b" if self.turn == "w" else "w"

    def save_pgn(self, filename="game.pgn"):
        pgn_data = self.format_pgn()
        with open(filename, "w") as file:
            file.write(pgn_data)

    def format_pgn(self):
        event = "Casual Game"
        date = datetime.datetime.now().strftime("%Y.%m.%d")
        header = f"""[Event "{event}"]
                     [Date "{date}"]
                     [White "White Player"]
                     [Black "Black Player"]
                     [Result "*"]
                     """
        moves_str = " ".join(self.move_history)
        return header + moves_str + " *\n"

    def run(self):
        self.board.render(self.screen, self.selected, self.turn)
        pygame.display.update()
        while self.game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    self.click(mouse_x, mouse_y)
                    self.board.render(self.screen, self.selected, self.turn)
                    pygame.display.update()
        pygame.quit()


class Board:
    def __init__(self, tile_size):
        self.tile_size = tile_size
        self.board = [
            [
                Rook("b", (0, 0)),
                Knight("b", (1, 0)),
                Bishop("b", (2, 0)),
                Queen("b", (3, 0)),
                King("b", (4, 0)),
                Bishop("b", (5, 0)),
                Knight("b", (6, 0)),
                Rook("b", (7, 0)),
            ],
            [Pawn("b", (i, 1)) for i in range(8)],
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [Pawn("w", (i, 6)) for i in range(8)],
            [
                Rook("w", (0, 7)),
                Knight("w", (1, 7)),
                Bishop("w", (2, 7)),
                Queen("w", (3, 7)),
                King("w", (4, 7)),
                Bishop("w", (5, 7)),
                Knight("w", (6, 7)),
                Rook("w", (7, 7)),
            ],
        ]
        self.piece_images = self.load_piece_images()
        self.capture_image = pygame.transform.smoothscale(
            pygame.image.load(ResourceManager.resource_path("images/captures.png")),
            (self.tile_size, self.tile_size),
        )
        self.move_image = pygame.transform.smoothscale(
            pygame.image.load(ResourceManager.resource_path("images/moves.png")),
            (self.tile_size, self.tile_size),
        )

    def load_piece_images(self):
        images = {}
        for row in self.board:
            for piece in row:
                if piece and piece.symbol not in images:
                    image_path = ResourceManager.resource_path(
                        f"images/{piece.symbol}.png"
                    )
                    images[piece.symbol] = pygame.image.load(image_path)
                    images[piece.symbol] = pygame.transform.smoothscale(
                        images[piece.symbol], (self.tile_size, self.tile_size)
                    )
        return images

    def get_piece_at(self, position):
        x, y = position
        return self.board[y][x]

    def move_piece(self, start_pos, end_pos):
        x1, y1 = start_pos
        x2, y2 = end_pos
        self.board[y2][x2] = self.board[y1][x1]
        self.board[y1][x1] = None

    def render(self, screen, selected, turn):
        for row_idx, row in enumerate(self.board):
            for col_idx, piece in enumerate(row):
                tile_colour = "#F5DDB7" if (row_idx + col_idx) % 2 == 0 else "#B88763"
                pygame.draw.rect(
                    screen,
                    tile_colour,
                    (
                        col_idx * self.tile_size,
                        row_idx * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    ),
                )

        if selected:
            x, y = selected
            piece = self.board[y][x]
            if piece and piece.colour == turn:
                highlight = pygame.Surface(
                    (self.tile_size, self.tile_size), pygame.SRCALPHA
                )
                highlight.fill((255, 255, 0, 128))
                screen.blit(highlight, (x * self.tile_size, y * self.tile_size))
                moves = piece.get_moves()
                for move in moves:
                    mx, my = move
                    if self.get_piece_at(move):
                        screen.blit(
                            self.capture_image,
                            (mx * self.tile_size, my * self.tile_size),
                        )
                    else:
                        screen.blit(
                            self.move_image, (mx * self.tile_size, my * self.tile_size)
                        )
        for row_idx, row in enumerate(self.board):
            for col_idx, piece in enumerate(row):
                if piece:
                    screen.blit(
                        self.piece_images[piece.symbol],
                        (col_idx * self.tile_size, row_idx * self.tile_size),
                    )


class Piece:
    def __init__(self, colour, piece_type, position):
        self.colour = colour
        self.symbol = f"{colour}{piece_type}"
        self.position = position

    def get_moves(self):
        pass


class Pawn(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "p", position)
        self.direction = -1 if colour == "w" else 1

    def get_moves(self):
        x, y = self.position
        moves = []
        forward_one = (x, y + self.direction)
        forward_two = (x, y + 2 * self.direction)
        capture_left = (x - 1, y + self.direction)
        capture_right = (x + 1, y + self.direction)

        if 0 <= forward_one[1] < 8 and not game.board.get_piece_at(forward_one):
            moves.append(forward_one)
            if (self.colour == "w" and y == 6) or (self.colour == "b" and y == 1):
                if not game.board.get_piece_at(forward_two):
                    moves.append(forward_two)

        for capture in [capture_left, capture_right]:
            if 0 <= capture[0] < 8 and 0 <= capture[1] < 8:
                piece = game.board.get_piece_at(capture)
                if piece and piece.colour != self.colour:
                    moves.append(capture)

        if self.can_en_passant():
            moves.append(self.en_passant_target())

        return moves

    def can_en_passant(self):
        if not game.move_history:
            return False
        last_move = game.move_history[-1]
        if self.colour == "w" and self.position[1] == 3:
            return last_move == f"p{self.position[0]}5" and game.board.get_piece_at((self.position[0], 4))
        if self.colour == "b" and self.position[1] == 4:
            return last_move == f"p{self.position[0]}4" and game.board.get_piece_at((self.position[0], 3))
        return False

    def en_passant_target(self):
        return (self.position[0], self.position[1] + self.direction)

    def promote(self):
        while True:
            choice = input("Promote to (q, r, b, n): ").lower()
            if choice in ["q", "r", "b", "n"]:
                return choice


class Rook(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "r", position)

    def get_moves(self):
        x, y = self.position
        moves = []
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                piece = game.board.get_piece_at((nx, ny))
                if piece:
                    if piece.colour != self.colour:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx
                ny += dy
        return moves


class Knight(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "n", position)

    def get_moves(self):
        moves = []
        directions = [
            (2, 1),
            (-2, -1),
            (1, 2),
            (-1, -2),
            (2, -1),
            (-2, 1),
            (1, -2),
            (-1, 2)
        ]
        x, y = self.position
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                piece = game.board.get_piece_at((nx, ny))
                if not piece or piece.colour != self.colour:
                    moves.append((nx, ny))
        return moves


class Bishop(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "b", position)

    def get_moves(self):
        x, y = self.position
        moves = []
        directions = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                piece = game.board.get_piece_at((nx, ny))
                if piece:
                    if piece.colour != self.colour:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx
                ny += dy
        return moves


class Queen(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "q", position)

    def get_moves(self):
        x, y = self.position
        moves = []
        directions = [
            (1, 1),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                piece = game.board.get_piece_at((nx, ny))
                if piece:
                    if piece.colour != self.colour:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx
                ny += dy
        return moves


class King(Piece):
    def __init__(self, colour, position):
        super().__init__(colour, "k", position)

    def get_moves(self):
        moves = []
        directions = [
            (1, 1),
            (-1, -1),
            (1, -1),
            (-1, 1),
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]
        x, y = self.position
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                piece = game.board.get_piece_at((nx, ny))
                if not piece or piece.colour != self.colour:
                    moves.append((nx, ny))
        return moves


if __name__ == "__main__":
    game = Game()
    game.run()
