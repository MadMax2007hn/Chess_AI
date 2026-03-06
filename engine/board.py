import chess

class ChessGame:
    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        self.board.reset()

    def make_move(self, move_uci: str) -> bool:
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except:
            return False

    def undo(self):
        if self.board.move_stack:
            self.board.pop()

    def is_game_over(self):
        return self.board.is_game_over()

    def get_legal_moves(self):
        return [move.uci() for move in self.board.legal_moves]

    def get_fen(self):
        return self.board.fen()
