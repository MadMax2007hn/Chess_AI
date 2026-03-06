import tkinter as tk
import chess
from engine.board import ChessGame
from engine.search_ai import SearchAI

SQUARE_SIZE = 80

PIECE_UNICODE = {
    "P": "♙", "R": "♖", "N": "♘", "B": "♗", "Q": "♕", "K": "♔",
    "p": "♟", "r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚",
}

class ChessGUI:
    def __init__(self):
        self.game = ChessGame()

        # Etappe 1 Engine: feste Tiefe
        self.ai = SearchAI(depth=4)  # -> wenn es zu langsam ist: 2; wenn schnell: 4

        self.root = tk.Tk()
        self.root.title("Chess AI")

        self.player_color = self.ask_player_color()
        self.ai_color = not self.player_color

        self.canvas = tk.Canvas(
            self.root,
            width=8 * SQUARE_SIZE,
            height=8 * SQUARE_SIZE
        )
        self.canvas.pack()

        self.selected_square = None
        self.legal_target_squares = []

        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_board()

        # KI beginnt, falls Spieler Schwarz ist
        if self.game.board.turn == self.ai_color:
            self.root.after(300, self.make_ai_move)

        self.root.mainloop()

    # ---------- PLAYER COLOR ----------

    def ask_player_color(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Farbe wählen")
        dialog.grab_set()

        choice = tk.BooleanVar()

        tk.Label(dialog, text="Welche Farbe willst du spielen?").pack(pady=10)

        tk.Button(
            dialog, text="Weiß",
            command=lambda: (choice.set(chess.WHITE), dialog.destroy())
        ).pack(fill="x", padx=20)

        tk.Button(
            dialog, text="Schwarz",
            command=lambda: (choice.set(chess.BLACK), dialog.destroy())
        ).pack(fill="x", padx=20, pady=10)

        self.root.wait_window(dialog)
        return choice.get()

    def ask_promotion_piece(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Umwandlung")
        dialog.grab_set()

        choice = tk.IntVar(value=chess.QUEEN)  # Default Dame

        tk.Label(dialog, text="Wähle eine Figur für die Umwandlung:").pack(pady=10)

        def select(piece):
            choice.set(piece)
            dialog.destroy()

        tk.Button(dialog, text="Dame", command=lambda: select(chess.QUEEN)).pack(fill="x", padx=20)
        tk.Button(dialog, text="Turm", command=lambda: select(chess.ROOK)).pack(fill="x", padx=20)
        tk.Button(dialog, text="Läufer", command=lambda: select(chess.BISHOP)).pack(fill="x", padx=20)
        tk.Button(dialog, text="Springer", command=lambda: select(chess.KNIGHT)).pack(fill="x", padx=20)

        self.root.wait_window(dialog)
        return choice.get()

    # ---------- DRAWING ----------

    def draw_board(self):
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                color = "#EEEED2" if (row + col) % 2 == 0 else "#769656"
                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        self.draw_pieces()
        self.draw_legal_moves()

    def draw_pieces(self):
        board_str = self.game.board.board_fen().split("/")
        for row in range(8):
            col = 0
            for char in board_str[row]:
                if char.isdigit():
                    col += int(char)
                else:
                    piece = PIECE_UNICODE[char]
                    x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                    self.canvas.create_text(x, y, text=piece, font=("Arial", 44))
                    col += 1

    def draw_legal_moves(self):
        for square in self.legal_target_squares:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            self.canvas.create_oval(x-10, y-10, x+10, y+10, fill="black", outline="")

    # ---------- INPUT ----------

    def on_click(self, event):
        if self.game.board.turn != self.player_color:
            return  # Spieler ist nicht dran
        if self.game.board.is_game_over():
            return

        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        square = chess.square(col, 7 - row)

        # Erste Auswahl: Figur anklicken
        if self.selected_square is None:
            piece = self.game.board.piece_at(square)
            if piece is None or piece.color != self.player_color:
                return

            self.selected_square = square
            self.legal_target_squares = [
                move.to_square
                for move in self.game.board.legal_moves
                if move.from_square == square
            ]

        # Zweite Auswahl: Zug ausführen
        else:
            piece = self.game.board.piece_at(self.selected_square)
            promotion = None

            # Prüfen, ob Promotion nötig ist
            if piece and piece.piece_type == chess.PAWN:
                target_rank = chess.square_rank(square)
                if (piece.color == chess.WHITE and target_rank == 7) or \
                        (piece.color == chess.BLACK and target_rank == 0):
                    promotion = self.ask_promotion_piece()

            move = chess.Move(self.selected_square, square, promotion=promotion)

            if move in self.game.board.legal_moves:
                self.game.board.push(move)

                self.selected_square = None
                self.legal_target_squares = []
                self.draw_board()

                self.check_game_over()
                if not self.game.board.is_game_over():
                    self.root.after(200, self.make_ai_move)
                return

            # falls illegal (z. B. Klick daneben)
            self.selected_square = None
            self.legal_target_squares = []

        self.draw_board()

    # ---------- AI MOVE ----------

    def make_ai_move(self):
        if self.game.board.is_game_over():
            return
        if self.game.board.turn != self.ai_color:
            return

        move = self.ai.choose_move(self.game.board)
        if move:
            self.game.board.push(move)

        self.draw_board()
        self.check_game_over()

    # ---------- GAME OVER + REMATCH ----------

    def check_game_over(self):
        if not self.game.board.is_game_over():
            return

        result = self.game.board.result()
        outcome = self.game.board.outcome()

        reason = outcome.termination if outcome else None
        reason_text = {
            chess.Termination.CHECKMATE: "Schachmatt",
            chess.Termination.STALEMATE: "Patt",
            chess.Termination.INSUFFICIENT_MATERIAL: "Unzureichendes Material",
            chess.Termination.THREEFOLD_REPETITION: "Dreifache Stellungswiederholung",
            chess.Termination.FIVEFOLD_REPETITION: "Fünffache Stellungswiederholung",
            chess.Termination.SEVENTYFIVE_MOVES: "75-Züge-Regel",
        }.get(reason, "Spiel beendet")

        if result == "1-0":
            winner = "Weiß gewinnt"
        elif result == "0-1":
            winner = "Schwarz gewinnt"
        else:
            winner = "Unentschieden"

        self.show_game_over_dialog(f"{reason_text}\n\n{winner}")

    def show_game_over_dialog(self, message):
        dialog = tk.Toplevel(self.root)
        dialog.title("Spiel beendet")
        dialog.grab_set()

        tk.Label(dialog, text=message, font=("Arial", 12)).pack(padx=20, pady=15)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Revanche",
            width=12,
            command=lambda: (dialog.destroy(), self.restart_game())
        ).pack(side="left", padx=10)

        tk.Button(
            button_frame,
            text="Beenden",
            width=12,
            command=self.root.destroy
        ).pack(side="right", padx=10)

    def restart_game(self):
        self.game.board.reset()
        self.selected_square = None
        self.legal_target_squares = []
        self.draw_board()

        # KI beginnt, falls Spieler Schwarz ist
        if self.game.board.turn == self.ai_color:
            self.root.after(300, self.make_ai_move)
