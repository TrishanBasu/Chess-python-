import streamlit as st
import chess
import random
import math

st.set_page_config(
    page_title="Chess vs AI",
    page_icon="♟",
    layout="centered"
)

PIECES = {
    "P": "♙", "N": "♘", "B": "♗",
    "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝",
    "r": "♜", "q": "♛", "k": "♚"
}

LEVELS = {
    1: ("250 Elo", 1, 0.50),
    2: ("500-600 Elo", 1, 0.20),
    3: ("1000-1100 Elo", 2, 0.06),
    4: ("1500-1600 Elo", 3, 0.01),
    5: ("2200-2500 Elo*", 4, 0.00)
}

TIMES = {
    "10 Minutes": 600,
    "5 Minutes": 300,
    "1 Minute": 60,
    "No Time": None
}

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


def reset_game():
    st.session_state.board = chess.Board()
    st.session_state.selected = None
    st.session_state.game_over = False
    st.session_state.message = ""


if "board" not in st.session_state:
    reset_game()

if "level" not in st.session_state:
    st.session_state.level = 3

if "color" not in st.session_state:
    st.session_state.color = "White"

if "time_control" not in st.session_state:
    st.session_state.time_control = "10 Minutes"


def evaluate(board):
    score = 0

    for piece_type, value in VALUES.items():
        white = len(board.pieces(piece_type, chess.WHITE))
        black = len(board.pieces(piece_type, chess.BLACK))
        score += value * (white - black)

    return score


def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate(board)

    moves = list(board.legal_moves)
    random.shuffle(moves)

    if maximizing:
        best = -math.inf

        for move in moves:
            board.push(move)

            score = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                False
            )

            board.pop()

            best = max(best, score)
            alpha = max(alpha, best)

            if beta <= alpha:
                break

        return best

    best = math.inf

    for move in moves:
        board.push(move)

        score = minimax(
            board,
            depth - 1,
            alpha,
            beta,
            True
        )

        board.pop()

        best = min(best, score)
        beta = min(beta, best)

        if beta <= alpha:
            break

    return best


def make_ai_move():
    board = st.session_state.board

    if board.is_game_over():
        return

    moves = list(board.legal_moves)

    if not moves:
        return

    name, depth, randomness = LEVELS[
        st.session_state.level
    ]

    ai_is_white = board.turn == chess.WHITE

    best_score = (
        -math.inf
        if ai_is_white
        else math.inf
    )

    best_moves = []

    for move in moves:
        board.push(move)

        score = minimax(
            board,
            depth - 1,
            -math.inf,
            math.inf,
            not ai_is_white
        )

        board.pop()

        score += random.uniform(
            -100,
            100
        ) * randomness

        if ai_is_white:
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        else:
            if score < best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

    board.push(random.choice(best_moves))


def finish