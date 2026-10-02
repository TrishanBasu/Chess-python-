import streamlit as st
import chess
import chess.svg
import time
import random

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Streamlit Chess vs AI",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Theme & Touch Board Centering
st.markdown("""
<style>
    .stApp {
        background-color: #262421;
        color: #BABABA;
    }
    section[data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }
    .board-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        max-width: 500px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

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

# Clocks State
if "white_time" not in st.session_state:
    st.session_state.white_time = 600.0
if "black_time" not in st.session_state:
    st.session_state.black_time = 600.0
if "last_clock_update" not in st.session_state:
    st.session_state.last_clock_update = None
if "active_time_control" not in st.session_state:
    st.session_state.active_time_control = "10 Min"

# Handle query param clicks from HTML image map
query_params = st.query_params
if "tap" in query_params:
    tapped_sq = int(query_params["tap"])
    st.query_params.clear()
    
    board = st.session_state.board
    selected = st.session_state.selected_square

    if selected is None:
        piece = board.piece_at(tapped_sq)
        if piece and piece.color == board.turn:
            st.session_state.selected_square = tapped_sq
            st.session_state.legal_destinations = [
                m.to_square for m in board.legal_moves if m.from_square == tapped_sq
            ]
    else:
        if selected == tapped_sq:
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
        elif board.piece_at(tapped_sq) and board.piece_at(tapped_sq).color == board.turn:
            st.session_state.selected_square = tapped_sq
            st.session_state.legal_destinations = [
                m.to_square for m in board.legal_moves if m.from_square == tapped_sq
            ]
        elif tapped_sq in st.session_state.legal_destinations:
            piece = board.piece_at(selected)
            if piece and piece.piece_type == chess.PAWN:
                if (piece.color == chess.WHITE and chess.square_rank(tapped_sq) == 7) or \
                   (piece.color == chess.BLACK and chess.square_rank(tapped_sq) == 0):
                    st.session_state.pending_promotion_move = (selected, tapped_sq)
                    st.rerun()

            move = chess.Move(selected, tapped_sq)
            san_str = board.san(move)
            board.push(move)
            st.session_state.move_history.append(san_str)
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.session_state.last_clock_update = time.time()
        else:
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []

# ==========================================
# CLOCK CONTROL
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

# ==========================================
# AI EVALUATION & ENGINE (LEVELS 1-5)
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

# Check Game State after player move
check_game_status()

# ==========================================
# SIDEBAR CONTROLS & SETTINGS
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

# Automatic AI Move Trigger
if st.session_state.board.turn == ai_color and not st.session_state.game_over:
    with st.spinner("AI thinking..."):
        make_ai_move(difficulty)
        st.rerun()

# ==========================================
# MAIN GAME UI LAYOUT
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

    # Highlight dictionary
    fill_squares = {}
    if st.session_state.selected_square is not None:
        fill_squares[st.session_state.selected_square] = "#baca44"
        for dest in st.session_state.legal_destinations:
            fill_squares[dest] = "#f6f669"

    if len(b.move_stack) > 0:
        last_move = b.peek()
        if last_move.from_square not in fill_squares:
            fill_squares[last_move.from_square] = "#aaa23a"
        if last_move.to_square not in fill_squares:
            fill_squares[last_move.to_square] = "#aaa23a"

    if b.is_check():
        fill_squares[b.king(b.turn)] = "#e63946"

    # SVG Board generation
    board_svg = chess.svg.board(
        board=b,
        orientation=chess.WHITE if player_color == "White" else chess.BLACK,
        fill=fill_squares,
        size=400
    )

    # HTML Image Map for direct phone taps
    map_areas = ""
    for r in range(8):
        for f in range(8):
            sq = chess.square(f, r)
            
            if player_color == "White":
                x1 = int(f * 50)
                y1 = int((7 - r) * 50)
            else:
                x1 = int((7 - f) * 50)
                y1 = int(r * 50)
                
            x2 = x1 + 50
            y2 = y1 + 50
            map_areas += f'<area shape="rect" coords="{x1},{y1},{x2},{y2}" href="?tap={sq}" target="_self">\n'

    import base64
    encoded_svg = base64.b64encode(board_svg.encode('utf-8')).decode('utf-8')
    
    html_code = f"""
    <div style="display: flex; justify-content: center; width: 100%;">
        <img src="data:image/svg+xml;base64,{encoded_svg}" usemap="#chessmap" style="width: 100%; max-width: 400px; height: auto;" />
        <map name="chessmap">
            {map_areas}
        </map>
    </div>
    """
    st.components.v1.html(html_code, height=420)
