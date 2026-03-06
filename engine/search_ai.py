import chess
from engine.evaluator import MaterialEvaluator

MATE_SCORE = 100000

# Piece values for MVV-LVA / ordering
ORDER_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

PROMOTION_BONUS = {
    chess.QUEEN: 900,
    chess.ROOK: 500,
    chess.BISHOP: 330,
    chess.KNIGHT: 320,
}

class SearchAI:
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.evaluator = MaterialEvaluator()

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if board.is_game_over():
            return None

        color = 1 if board.turn == chess.WHITE else -1

        best_move = None
        best_score = -10**9

        # Principal Variation move from previous iteration
        pv_move = None

        # Iterative deepening: 1..self.depth
        for current_depth in range(1, self.depth + 1):
            alpha = -10**9
            beta = 10**9

            iter_best_move = None
            iter_best_score = -10**9

            moves = list(board.legal_moves)
            moves = self._order_moves(board, moves, pv_move=pv_move)

            for move in moves:
                board.push(move)
                score = -self._negamax(board, current_depth - 1, -beta, -alpha, -color)
                board.pop()

                if score > iter_best_score:
                    iter_best_score = score
                    iter_best_move = move

                if score > alpha:
                    alpha = score

            # Update PV for next iteration
            pv_move = iter_best_move

            # Update global best
            if iter_best_move is not None:
                best_move = iter_best_move
                best_score = iter_best_score

        return best_move

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, color: int) -> int:
        # Terminal conditions
        if board.is_checkmate():
            # side to move is checkmated
            return -color * MATE_SCORE

        # treat common draws as 0
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        if depth == 0:
            return color * self.evaluator.evaluate(board)

        best = -10**9

        moves = list(board.legal_moves)
        moves = self._order_moves(board, moves, pv_move=None)

        for move in moves:
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, -color)
            board.pop()

            if score > best:
                best = score

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break  # alpha-beta cutoff

        return best

    def _order_moves(self, board: chess.Board, moves: list[chess.Move], pv_move: chess.Move | None):
        def move_score(m: chess.Move) -> int:
            score = 0

            # PV move always first (very large bonus)
            if pv_move is not None and m == pv_move:
                return 10**9

            # Promotions: prefer queen > rook > bishop > knight
            if m.promotion is not None:
                score += 200000 + PROMOTION_BONUS.get(m.promotion, 0)

            # Captures: MVV-LVA (victim value - attacker value)
            if board.is_capture(m):
                victim_value = 0
                attacker = board.piece_at(m.from_square)
                attacker_value = ORDER_VALUES.get(attacker.piece_type, 0) if attacker else 0

                captured = board.piece_at(m.to_square)
                if captured is None:
                    # en passant capture: victim is pawn
                    victim_value = ORDER_VALUES[chess.PAWN]
                else:
                    victim_value = ORDER_VALUES.get(captured.piece_type, 0)

                score += 100000 + (victim_value - attacker_value)

            # Checks: good to try early (but after captures/promotions typically)
            if board.gives_check(m):
                score += 50000

            return score

        return sorted(moves, key=move_score, reverse=True)
