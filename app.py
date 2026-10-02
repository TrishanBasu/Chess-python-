import streamlit as st
import chess
import time
import random

# ==========================================
# PAGE CONFIGURATION & MOBILE CSS
# ==========================================
st.set_page_config(
    page_title="Streamlit Chess vs AI",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Theme */
    .stApp {
        background-color: #262421;
        color: #BABABA;
    }
    section[data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }

    /* Board Grid Mobile Fixes */
    div[data-testid="column"] {
        padding: 1px !important;
        min-width: 0px !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        flex-wrap: nowrap !important;
    }

    /* Square Button Styling */
    div.stButton > button {
        width: 100% !important;
        height: 48px !important;
        min-height: 48px !important;
        max-height: 48px !important;
        padding: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        font-size: 26px !important;
        line-height: 48px !important;
        margin: 0px !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Colors for Squares */
    .sq-light button { background-color: #EBECD0 !important; color: #000000 !important; }
    .sq-dark button { background-color: #739552 !important; color: #000000 !important; }
    .sq-selected button { background-color: #BACA44 !important; color: #000000 !important; }
    .sq-highlight button { background-color: #F6F669 !important; color: #000000 !important; }
    .sq-lastmove button { background-color: #AAA23A !important; color: #000000 !important; }
    .sq-check button { background-color: #E63946 !important; color: #FFFFFF !important; }

    div.stButton > button:hover {
        opacity: 0.9 !important;
    }
</style>
""", unsafe_allow_html=True)

# Unicode Chess Piece Symbols
PIECE_UNICODE = {
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    '': ' '
}

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "legal_destinations" not in st.session_state:
    st.session_state.legal_destinations = []
if "pending_promotion_move" not in st.session_state:
    st.session_state.pending_promotion_move = None
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "game_result" not in st.session_state:
    st.session_state.game_result = ""

# Clocks
if "white_time" not in st.session_state:
    st.session_state.white_time = 600.0
if "black_time" not in st.session_state:
    st.session_state.black_time = 600.0
if "last_clock_update" not in st.session_state:
    st.session_state.last_clock_update = None
if "active_time_control" not in st.session_state:
    st.session_state.active_time_control = "10 Min"

# ==========================================
# CLOCK & GAME MANAGEMENT
# ==========================================
def update_clocks():
    if st.session_state.game_over or st.session_state.active_time_control == "No Time":
        return
    now = time.time()
    if st.session_state.last_clock_update is not None:
        elapsed = now - st.session_state.last_clock_update
        if st.session_state.board.turn == chess.WHITE:
            st.session_state.white_time = max(0.0, st.session_state.white_time - elapsed)
            if st.session_state.white_time <= 0:
                st.session_state.game_over = True
                st.session_state.game_result = "Black wins on time!"
        else:
            st.session_state.black_time = max(0.0, st.session_state.black_time - elapsed)
            if st.session_state.black_time <= 0:
                st.session_state.game_over = True
                st.session_state.game_result = "White wins on time!"
    st.session_state.last_clock_update = now

def reset_clocks(time_control_str):
    st.session_state.active_time_control = time_control_str
    st.session_state.last_clock_update = None
    if time_control_str == "10 Min":
        st.session_state.white_time = 600.0
        st.session_state.black_time = 600.0
    elif time_control_str == "5 Min":
        st.session_state.white_time = 300.0
        st.session_state.black_time = 300.0
    elif time_control_str == "1 Min":
        st.session_state.white_time = 60.0
        st.session_state.black_time = 60.0
    else:
        st.session_state.white_time = 0.0
        st.session_state.black_time = 0.0

def format_time(seconds):
    if st.session_state.active_time_control == "No Time":
        return "∞"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def check_game_status():
    b = st.session_state.board
    if b.is_checkmate():
        st.session_state.game_over = True
        winner = "Black" if b.turn == chess.WHITE else "White"
        st.session_state.game_result = f"Checkmate! {winner} wins!"
    elif b.is_stalemate():
        st.session_state.game_over = True
        st.session_state.game_result = "Draw by Stalemate!"
    elif b.is_insufficient_material():
        st.session_state.game_over = True
        st.session_state.game_result = "Draw by Insufficient Material!"

# ==========================================
# AI ENGINE (LEVELS 1-5)
# ==========================================
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHTS_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

def evaluate_board(board: chess.Board) -> int:
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = PIECE_VALUES[piece.piece_type]
            sq_idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
            if piece.piece_type == chess.PAWN:
                value += PAWN_TABLE[sq_idx]
            elif piece.piece_type == chess.KNIGHT:
                value += KNIGHTS_TABLE[sq_idx]

            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value
    return score

def minimax(board: chess.Board, depth: int, alpha: float, beta: float, is_maximizing: bool) -> tuple[float, chess.Move | None]:
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    legal_moves = list(board.legal_moves)
    random.shuffle(legal_moves)
    best_move = None

    if is_maximizing:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def make_ai_move(difficulty_level: str):
    board = st.session_state.board
    if board.is_game_over() or st.session_state.game_over:
        return

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return

    chosen_move = None
    if "Level 1" in difficulty_level:
        chosen_move = random.choice(legal_moves)
    elif "Level 2" in difficulty_level:
        if random.random() < 0.4:
            chosen_move = random.choice(legal_moves)
        else:
            _, chosen_move = minimax(board, depth=1, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))
    elif "Level 3" in difficulty_level:
        _, chosen_move = minimax(board, depth=2, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))
    elif "Level 4" in difficulty_level:
        _, chosen_move = minimax(board, depth=3, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))
    else:
        _, chosen_move = minimax(board, depth=4, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))

    if chosen_move is None:
        chosen_move = random.choice(legal_moves)

    san_move = board.san(chosen_move)
    board.push(chosen_move)
    st.session_state.move_history.append(san_move)
    st.session_state.selected_square = None
    st.session_state.legal_destinations = []
    st.session_state.last_clock_update = time.time()
    check_game_status()

# ==========================================
# TOUCH BOARD CALLBACK
# ==========================================
def handle_square_click(sq_index):
    if st.session_state.game_over:
        return

    board = st.session_state.board
    selected = st.session_state.selected_square

    if selected is None:
        piece = board.piece_at(sq_index)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = sq_index
            st.session_state.legal_destinations = [
                m.to_square for m in board.legal_moves if m.from_square == sq_index
            ]
    else:
        if selected == sq_index:
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
        elif board.piece_at(sq_index) and board.piece_at(sq_index).color == board.turn:
            st.session_state.selected_square = sq_index
            st.session_state.legal_destinations = [
                m.to_square for m in board.legal_moves if m.from_square == sq_index
            ]
        elif sq_index in st.session_state.legal_destinations:
            piece = board.piece_at(selected)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(sq_index) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(sq_index) == 0):
                    st.session_state.pending_promotion_move = (selected, sq_index)
                    return

            move = chess.Move(selected, sq_index)
            san_str = board.san(move)
            board.push(move)
            st.session_state.move_history.append(san_str)
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.session_state.last_clock_update = time.time()
            check_game_status()
        else:
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.title("⚙️ Options")
    
    player_color = st.radio("Play As:", ["White", "Black"], index=0, horizontal=True)
    ai_color = chess.BLACK if player_color == "White" else chess.WHITE

    difficulty = st.selectbox(
        "AI Difficulty:",
        [
            "Level 1 — ~250 Elo",
            "Level 2 — ~500–600 Elo",
            "Level 3 — ~1000–1100 Elo",
            "Level 4 — ~1500–1600 Elo",
            "Level 5 — ~2200–2500 Elo"
        ],
        index=2
    )

    time_control = st.selectbox(
        "Time Control:",
        ["10 Min", "5 Min", "1 Min", "No Time"],
        index=0
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("New Game", use_container_width=True, type="primary"):
            st.session_state.board = chess.Board()
            st.session_state.move_history = []
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.session_state.pending_promotion_move = None
            st.session_state.game_over = False
            st.session_state.game_result = ""
            reset_clocks(time_control)
            st.rerun()

    with col_btn2:
        if st.button("Resign", use_container_width=True):
            if not st.session_state.game_over:
                st.session_state.game_over = True
                st.session_state.game_result = "You Resigned. AI wins!"
                st.rerun()

    st.markdown("---")
    st.subheader("📜 Move History")
    if st.session_state.move_history:
        history_text = ""
        for i in range(0, len(st.session_state.move_history), 2):
            move_num = (i // 2) + 1
            w_move = st.session_state.move_history[i]
            b_move = st.session_state.move_history[i+1] if i+1 < len(st.session_state.move_history) else ""
            history_text += f"**{move_num}.** {w_move} {b_move}  \n"
        st.markdown(history_text)
    else:
        st.caption("No moves played yet.")

# Update Clocks
update_clocks()

# Trigger AI turn if applicable
if st.session_state.board.turn == ai_color and not st.session_state.game_over:
    with st.spinner("AI thinking..."):
        make_ai_move(difficulty)
        st.rerun()

# ==========================================
# MAIN GAME BOARD & UI
# ==========================================
st.title("♟️ Streamlit Chess")

col_board, col_info = st.columns([2, 1])

with col_info:
    st.subheader("Game Information")
    
    if st.session_state.game_over:
        st.error(f"**Game Over:** {st.session_state.game_result}")
    elif st.session_state.board.is_check():
        st.warning("⚠️ **CHECK!**")
    else:
        current_turn = "Your Turn" if st.session_state.board.turn != ai_color else "AI Thinking..."
        st.info(f"Status: **{current_turn}**")

    st.markdown("### ⏱️ Clocks")
    c_w, c_b = st.columns(2)
    with c_w:
        st.metric("White", format_time(st.session_state.white_time))
    with c_b:
        st.metric("Black", format_time(st.session_state.black_time))

    if st.session_state.pending_promotion_move is not None:
        st.markdown("---")
        st.warning("♟️ **Choose Promotion Piece:**")
        promo_col1, promo_col2 = st.columns(2)
        from_sq, to_sq = st.session_state.pending_promotion_move
        
        def complete_promotion(piece_type):
            move = chess.Move(from_sq, to_sq, promotion=piece_type)
            san_str = st.session_state.board.san(move)
            st.session_state.board.push(move)
            st.session_state.move_history.append(san_str)
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.session_state.pending_promotion_move = None
            st.session_state.last_clock_update = time.time()
            check_game_status()
            if not st.session_state.game_over:
                make_ai_move(difficulty)
            st.rerun()

        with promo_col1:
            if st.button("♛ Queen", use_container_width=True):
                complete_promotion(chess.QUEEN)
            if st.button("♜ Rook", use_container_width=True):
                complete_promotion(chess.ROOK)
        with promo_col2:
            if st.button("♝ Bishop", use_container_width=True):
                complete_promotion(chess.BISHOP)
            if st.button("♞ Knight", use_container_width=True):
                complete_promotion(chess.KNIGHT)

with col_board:
    b = st.session_state.board
    
    ranks = range(7, -1, -1) if player_color == "White" else range(0, 8)
    files = range(0, 8) if player_color == "White" else range(7, -1, -1)

    last_from = st.session_state.board.peek().from_square if len(st.session_state.board.move_stack) > 0 else None
    last_to = st.session_state.board.peek().to_square if len(st.session_state.board.move_stack) > 0 else None
    check_sq = b.king(b.turn) if b.is_check() else None

    # 8x8 Interactive Touch Board
    for r in ranks:
        cols = st.columns(8)
        for f_idx, f in enumerate(files):
            sq = chess.square(f, r)
            piece = b.piece_at(sq)
            piece_str = PIECE_UNICODE[piece.symbol()] if piece else " "

            is_dark = (r + f) % 2 == 0
            sq_class = "sq-dark" if is_dark else "sq-light"

            if sq == st.session_state.selected_square:
                sq_class = "sq-selected"
            elif sq in st.session_state.legal_destinations:
                sq_class = "sq-highlight"
            elif sq in [last_from, last_to]:
                sq_class = "sq-lastmove"
            elif sq == check_sq:
                sq_class = "sq-check"

            with cols[f_idx]:
                st.markdown(f'<div class="{sq_class}">', unsafe_allow_html=True)
                st.button(
                    piece_str,
                    key=f"btn_{sq}",
                    on_click=handle_square_click,
                    args=(sq,)
                )
                st.markdown('</div>', unsafe_allow_html=True)
