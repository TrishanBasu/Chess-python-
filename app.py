import streamlit as st
import chess
import random
import time
import math

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Chess AI",
    page_icon="♟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
    .stApp {
        background: #161512;
        color: #ffffff;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }

    .title {
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        color: #aaa;
        margin-bottom: 20px;
    }

    .player-box {
        background: #262522;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border: 1px solid #3b3935;
    }

    .player-name {
        font-size: 16px;
        font-weight: 700;
    }

    .clock {
        font-family: monospace;
        font-size: 25px;
        font-weight: 800;
        background: #111;
        padding: 5px 12px;
        border-radius: 6px;
        display: inline-block;
        float: right;
    }

    .clock-active {
        color: #ffffff;
    }

    .clock-danger {
        color: #ff5555;
    }

    .move-panel {
        background: #262522;
        border-radius: 10px;
        padding: 15px;
        min-height: 250px;
        border: 1px solid #3b3935;
    }

    .status {
        text-align: center;
        font-size: 17px;
        font-weight: 700;
        margin: 8px 0 12px 0;
    }

    .captured {
        color: #aaa;
        font-size: 20px;
        letter-spacing: 2px;
        min-height: 28px;
    }

    div[data-testid="stButton"] button {
        border-radius: 5px;
        font-weight: 600;
    }

    .board-label {
        color: #aaa;
        font-size: 11px;
    }

    .setup-card {
        background: #262522;
        border: 1px solid #3b3935;
        border-radius: 12px;
        padding: 25px;
        margin: 20px auto;
        max-width: 600px;
    }

    .footer {
        text-align: center;
        color: #777;
        font-size: 12px;
        margin-top: 20px;
    }

    /* Remove Streamlit default top gap */
    header[data-testid="stHeader"] {
        background: transparent;
    }

    @media (max-width: 700px) {
        .title {
            font-size: 25px;
        }

        .clock {
            font-size: 20px;
        }
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# PIECES
# ============================================================

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
    "k": "♚",
}

# Material values
VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "game_started": False,
        "board": None,
        "player_color": chess.WHITE,
        "ai_level": 3,
        "time_control": "No Time",
        "white_time": 0.0,
        "black_time": 0.0,
        "last_tick": time.time(),
        "selected_square": None,
        "last_move": None,
        "game_over": False,
        "result_text": "",
        "move_history": [],
        "thinking": False,
        "pending_promotion": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ============================================================
# AI SETTINGS
# ============================================================

LEVELS = {
    1: {
        "name": "Level 1",
        "elo": "~250 Elo",
        "depth": 1,
        "randomness": 0.80,
    },
    2: {
        "name": "Level 2",
        "elo": "~500–600 Elo",
        "depth": 1,
        "randomness": 0.30,
    },
    3: {
        "name": "Level 3",
        "elo": "~1000–1100 Elo",
        "depth": 2,
        "randomness": 0.08,
    },
    4: {
        "name": "Level 4",
        "elo": "~1500–1600 Elo",
        "depth": 3,
        "randomness": 0.025,
    },
    5: {
        "name": "Level 5",
        "elo": "~2200–2500 Elo",
        "depth": 4,
        "randomness": 0.0,
    },
}


# ============================================================
# EVALUATION
# ============================================================

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
     0,  0,  5, 10, 10,  5,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]


def positional_value(piece_type, square, color):
    tables = {
        chess.PAWN: PAWN_TABLE,
        chess.KNIGHT: KNIGHT_TABLE,
        chess.BISHOP: BISHOP_TABLE,
        chess.ROOK: ROOK_TABLE,
        chess.QUEEN: QUEEN_TABLE,
        chess.KING: KING_TABLE,
    }

    table = tables.get(piece_type)

    if table is None:
        return 0

    # Tables are written from White's perspective.
    if color == chess.WHITE:
        index = square
    else:
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        index = chess.square((7 - rank), file)

    return table[index]


def evaluate_board(board):
    """
    Positive = good for White
    Negative = good for Black
    """

    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return -100000
        return 100000

    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0

    for square, piece in board.piece_map().items():
        value = VALUES[piece.piece_type]
        position = positional_value(
            piece.piece_type,
            square,
            piece.color
        )

        if piece.color == chess.WHITE:
            score += value + position
        else:
            score -= value + position

    # Small bonus for mobility
    current_turn = board.turn
    try:
        mobility = board.legal_moves.count()
        board.turn = not current_turn
        enemy_mobility = board.legal_moves.count()
        board.turn = current_turn

        score += (mobility - enemy_mobility) * 2

    except Exception:
        board.turn = current_turn

    # Center control
    center_squares = [
        chess.D4,
        chess.E4,
        chess.D5,
        chess.E5
    ]

    for square in center_squares:
        piece = board.piece_at(square)

        if piece:
            if piece.color == chess.WHITE:
                score += 8
            else:
                score -= 8

    return score


# ============================================================
# MOVE ORDERING
# ============================================================

def move_order_score(board, move):
    score = 0

    # Captures first
    if board.is_capture(move):
        if board.is_en_passant(move):
            score += 100
        else:
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)

            if victim and attacker:
                score += 10 * VALUES[victim.piece_type] - VALUES[attacker.piece_type]

    # Promotions
    if move.promotion:
        score += VALUES.get(move.promotion, 0)

    # Checks
    try:
        board.push(move)
        if board.is_check():
            score += 500
        board.pop()
    except Exception:
        pass

    # Castling
    if board.is_castling(move):
        score += 100

    return score


def ordered_moves(board):
    moves = list(board.legal_moves)

    scored = []

    for move in moves:
        try:
            s = move_order_score(board, move)
        except Exception:
            s = 0
        scored.append((s, move))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [m for _, m in scored]


# ============================================================
# MINIMAX
# ============================================================

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    moves = ordered_moves(board)

    if not moves:
        return evaluate_board(board), None

    best_move = moves[0]

    if maximizing:
        best_value = -math.inf

        for move in moves:
            board.push(move)

            value, _ = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                False
            )

            board.pop()

            if value > best_value:
                best_value = value
                best_move = move

            alpha = max(alpha, best_value)

            if beta <= alpha:
                break

        return best_value, best_move

    else:
        best_value = math.inf

        for move in moves:
            board.push(move)

            value, _ = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                True
            )

            board.pop()

            if value < best_value:
                best_value = value
                best_move = move

            beta = min(beta, best_value)

            if beta <= alpha:
                break

        return best_value, best_move


# ============================================================
# AI MOVE
# ============================================================

def choose_ai_move(board, level):
    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return None

    settings = LEVELS[level]

    depth = settings["depth"]
    randomness = settings["randomness"]

    # Level 1 intentionally plays weakly.
    if level == 1:
        # Frequently choose random moves.
        if random.random() < 0.80:
            return random.choice(legal_moves)

    # Level 2 occasionally chooses a random move.
    if level == 2 and random.random() < randomness:
        return random.choice(legal_moves)

    # Search from AI's perspective.
    maximizing = board.turn == chess.WHITE

    _, best_move = minimax(
        board,
        depth,
        -math.inf,
        math.inf,
        maximizing
    )

    if best_move is None:
        return random.choice(legal_moves)

    # Levels 2-3 can occasionally make a weaker choice.
    if level in (2, 3) and random.random() < randomness:
        candidates = ordered_moves(board)

        if len(candidates) > 1:
            return random.choice(
                candidates[:min(4, len(candidates))]
            )

    return best_move


# ============================================================
# TIME
# ============================================================

TIME_VALUES = {
    "10 Minutes": 600,
    "5 Minutes": 300,
    "1 Minute": 60,
    "No Time": 0,
}


def format_clock(seconds):
    if seconds < 0:
        seconds = 0

    total = int(seconds)

    minutes = total // 60
    secs = total % 60

    return f"{minutes:02d}:{secs:02d}"


def update_clock():
    if not st.session_state.game_started:
        return

    if st.session_state.game_over:
        return

    if st.session_state.time_control == "No Time":
        st.session_state.last_tick = time.time()
        return

    now = time.time()
    elapsed = now - st.session_state.last_tick

    st.session_state.last_tick = now

    board = st.session_state.board

    if board is None:
        return

    if board.turn == chess.WHITE:
        st.session_state.white_time -= elapsed

        if st.session_state.white_time <= 0:
            st.session_state.white_time = 0
            st.session_state.game_over = True

            if st.session_state.player_color == chess.WHITE:
                st.session_state.result_text = "Time out — AI wins"
            else:
                st.session_state.result_text = "Time out — You win"

    else:
        st.session_state.black_time -= elapsed

        if st.session_state.black_time <= 0:
            st.session_state.black_time = 0
            st.session_state.game_over = True

            if st.session_state.player_color == chess.BLACK:
                st.session_state.result_text = "Time out — AI wins"
            else:
                st.session_state.result_text = "Time out — You win"


# ============================================================
# GAME MANAGEMENT
# ============================================================

def start_game():
    st.session_state.board = chess.Board()

    st.session_state.game_started = True
    st.session_state.game_over = False
    st.session_state.result_text = ""

    st.session_state.selected_square = None
    st.session_state.last_move = None
    st.session_state.move_history = []
    st.session_state.pending_promotion = None

    seconds = TIME_VALUES[st.session_state.time_control]

    st.session_state.white_time = float(seconds)
    st.session_state.black_time = float(seconds)

    st.session_state.last_tick = time.time()

    st.rerun()


def new_game():
    st.session_state.game_started = False
    st.session_state.board = None
    st.session_state.game_over = False
    st.session_state.result_text = ""
    st.session_state.selected_square = None
    st.session_state.last_move = None
    st.session_state.move_history = []
    st.session_state.pending_promotion = None
    st.session_state.thinking = False


def finish_game():
    board = st.session_state.board

    if board.is_checkmate():
        winner = not board.turn

        if winner == st.session_state.player_color:
            st.session_state.result_text = "Checkmate — You win!"
        else:
            st.session_state.result_text = "Checkmate — AI wins!"

        st.session_state.game_over = True

    elif board.is_stalemate():
        st.session_state.result_text = "Draw — Stalemate"
        st.session_state.game_over = True

    elif board.is_insufficient_material():
        st.session_state.result_text = "Draw — Insufficient material"
        st.session_state.game_over = True

    elif board.is_fifty_moves():
        st.session_state.result_text = "Draw — 50-move rule"
        st.session_state.game_over = True

    elif board.is_repetition():
        st.session_state.result_text = "Draw — Threefold repetition"
        st.session_state.game_over = True


def make_move(move):
    board = st.session_state.board

    if move not in board.legal_moves:
        return False

    san = board.san(move)

    board.push(move)

    st.session_state.last_move = move

    st.session_state.move_history.append(san)

    st.session_state.selected_square = None

    st.session_state.pending_promotion = None

    finish_game()

    st.session_state.last_tick = time.time()

    return True


# ============================================================
# BOARD UI
# ============================================================

def board_square_style(square, board):
    rank = chess.square_rank(square)
    file = chess.square_file(square)

    # Standard board colors
    if (rank + file) % 2 == 0:
        base = "#f0d9b5"
    else:
        base = "#b58863"

    # Selected square
    if st.session_state.selected_square == square:
        base = "#f6f669"

    # Last move
    last_move = st.session_state.last_move

    if last_move and (
        square == last_move.from_square
        or square == last_move.to_square
    ):
        base = "#cdd26a"

    # Check king
    piece = board.piece_at(square)

    if (
        piece
        and piece.piece_type == chess.KING
        and piece.color == board.turn
        and board.is_check()
    ):
        base = "#e05252"

    return base


def render_board():
    board = st.session_state.board

    if board is None:
        return

    player_color = st.session_state.player_color

    if player_color == chess.WHITE:
        ranks = range(7, -1, -1)
        files = range(0, 8)
    else:
        ranks = range(0, 8)
        files = range(7, -1, -1)

    # Board dimensions
    board_width = 640

    st.markdown(
        f"""
        <div style="
            width:100%;
            max-width:{board_width}px;
            margin:auto;
        ">
        """,
        unsafe_allow_html=True
    )

    for rank in ranks:

        cols = st.columns(8, gap="0px")

        for display_file, file in enumerate(files):

            square = chess.square(file, rank)

            piece = board.piece_at(square)

            symbol = PIECES.get(
                piece.symbol(),
                ""
            ) if piece else ""

            background = board_square_style(
                square,
                board
            )

            # Determine piece color
            piece_color = "#ffffff"

            if piece and piece.color == chess.BLACK:
                piece_color = "#111111"

            # Legal move indicator
            legal_indicator = False

            selected = st.session_state.selected_square

            if selected is not None:
                try:
                    for move in board.legal_moves:
                        if (
                            move.from_square == selected
                            and move.to_square == square
                        ):
                            legal_indicator = True
                            break
                except Exception:
                    pass

            if legal_indicator and not piece:
                symbol = "•"
                piece_color = "#555555"

            elif legal_indicator and piece:
                # Ring-like effect using text
                pass

            button_label = symbol if symbol else " "

            with cols[display_file]:

                st.markdown(
                    f"""
                    <style>
                    div[data-testid="stButton"] button {{
                        min-height: {board_width // 8}px;
                        height: {board_width // 8}px;