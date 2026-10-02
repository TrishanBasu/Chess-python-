import streamlit as st
import chess
import math
import random
import time
from streamlit_autorefresh import st_autorefresh

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Chess vs AI",
    page_icon="♟️",
    layout="centered"
)

# Refresh every second for the chess clocks
st_autorefresh(interval=1000, key="chess_clock")


# =========================================================
# PIECES
# =========================================================

PIECES = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",

    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚"
}


# =========================================================
# AI SETTINGS
# =========================================================

AI_LEVELS = {
    1: {
        "name": "250 Elo",
        "depth": 1,
        "randomness": 0.45
    },
    2: {
        "name": "500–600 Elo",
        "depth": 1,
        "randomness": 0.20
    },
    3: {
        "name": "1000–1100 Elo",
        "depth": 2,
        "randomness": 0.07
    },
    4: {
        "name": "1500–1600 Elo",
        "depth": 3,
        "randomness": 0.02
    },
    5: {
        "name": "2200–2500 Elo*",
        "depth": 4,
        "randomness": 0.00
    }
}


# =========================================================
# TIME CONTROLS
# =========================================================

TIME_CONTROLS = {
    "10 Minutes": 600,
    "5 Minutes": 300,
    "1 Minute": 60,
    "No Time": None
}


# =========================================================
# SESSION STATE
# =========================================================

def initialize_game():

    if "board" not in st.session_state:
        st.session_state.board = chess.Board()

    if "level" not in st.session_state:
        st.session_state.level = 3

    if "player_color" not in st.session_state:
        st.session_state.player_color = chess.WHITE

    if "time_control" not in st.session_state:
        st.session_state.time_control = "10 Minutes"

    if "white_time" not in st.session_state:
        st.session_state.white_time = 600

    if "black_time" not in st.session_state:
        st.session_state.black_time = 600

    if "last_time" not in st.session_state:
        st.session_state.last_time = time.time()

    if "selected_square" not in st.session_state:
        st.session_state.selected_square = None

    if "promotion" not in st.session_state:
        st.session_state.promotion = None

    if "game_over" not in st.session_state:
        st.session_state.game_over = False

    if "result_message" not in st.session_state:
        st.session_state.result_message = ""

    if "game_started" not in st.session_state:
        st.session_state.game_started = False


initialize_game()


# =========================================================
# NEW GAME
# =========================================================

def start_new_game():

    st.session_state.board = chess.Board()

    seconds = TIME_CONTROLS[st.session_state.time_control]

    st.session_state.white_time = seconds
    st.session_state.black_time = seconds

    st.session_state.last_time = time.time()

    st.session_state.selected_square = None
    st.session_state.promotion = None

    st.session_state.game_over = False
    st.session_state.result_message = ""

    st.session_state.game_started = False


# =========================================================
# CLOCK
# =========================================================

def update_clock():

    if st.session_state.game_over:
        return

    if not st.session_state.game_started:
        st.session_state.last_time = time.time()
        return

    limit = TIME_CONTROLS[st.session_state.time_control]

    if limit is None:
        return

    current = time.time()

    elapsed = current - st.session_state.last_time

    st.session_state.last_time = current

    board = st.session_state.board

    if board.turn == chess.WHITE:

        st.session_state.white_time -= elapsed

        if st.session_state.white_time <= 0:

            st.session_state.white_time = 0

            st.session_state.game_over = True

            st.session_state.result_message = (
                "Black wins on time!"
            )

    else:

        st.session_state.black_time -= elapsed

        if st.session_state.black_time <= 0:

            st.session_state.black_time = 0

            st.session_state.game_over = True

            st.session_state.result_message = (
                "White wins on time!"
            )


def format_time(seconds):

    if seconds is None:
        return "∞"

    seconds = max(0, int(seconds))

    minutes = seconds // 60
    secs = seconds % 60

    return f"{minutes}:{secs:02d}"


update_clock()


# =========================================================
# EVALUATION
# =========================================================

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


def evaluate(board):

    score = 0

    for piece_type, value in PIECE_VALUES.items():

        white_count = len(
            board.pieces(piece_type, chess.WHITE)
        )

        black_count = len(
            board.pieces(piece_type, chess.BLACK)
        )

        score += value * (white_count - black_count)

    # Center control bonus
    for square, piece in board.piece_map().items():

        file = chess.square_file(square)
        rank = chess.square_rank(square)

        center_distance = (
            abs(file - 3.5) +
            abs(rank - 3.5)
        )

        bonus = max(0, 8 - center_distance * 2)

        if piece.color == chess.WHITE:
            score += bonus
        else:
            score -= bonus

    # Check bonus
    if board.is_check():

        if board.turn == chess.WHITE:
            score -= 40
        else:
            score += 40

    return score


# =========================================================
# MINIMAX
# =========================================================

def minimax(board, depth, alpha, beta, maximizing):

    if depth <= 0 or board.is_game_over():
        return evaluate(board)

    moves = list(board.legal_moves)

    random.shuffle(moves)

    if maximizing:

        best_score = -math.inf

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

            best_score = max(best_score, score)

            alpha = max(alpha, best_score)

            if beta <= alpha:
                break

        return best_score

    else:

        best_score = math.inf

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

            best_score = min(best_score, score)

            beta = min(beta, best_score)

            if beta <= alpha:
                break

        return best_score


# =========================================================
# AI MOVE
# =========================================================

def make_ai_move():

    board = st.session_state.board