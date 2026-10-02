import streamlit as st
import chess
import chess.svg
import random

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Streamlit Chess vs AI",
    page_icon="♟️",
    layout="wide"
)

# Initialize Session State Variables
if "board" not in st.session_state:
    st.session_state.board = chess.Board()
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "selected_square" not in st.session_state:
    st.session_state.selected_square = None
if "legal_destinations" not in st.session_state:
    st.session_state.legal_destinations = []
if "ai_thinking" not in st.session_state:
    st.session_state.ai_thinking = False

# ==========================================
# AI EVALUATION & MINIMAX ENGINE
# ==========================================
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
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

BISHOPS_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOKS_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEENS_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
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
            
            p_type = piece.piece_type
            if p_type == chess.PAWN:
                value += PAWN_TABLE[sq_idx]
            elif p_type == chess.KNIGHT:
                value += KNIGHTS_TABLE[sq_idx]
            elif p_type == chess.BISHOP:
                value += BISHOPS_TABLE[sq_idx]
            elif p_type == chess.ROOK:
                value += ROOKS_TABLE[sq_idx]
            elif p_type == chess.QUEEN:
                value += QUEENS_TABLE[sq_idx]

            if piece.color == chess.WHITE:
                score += value
            else:
                score -= value

    return score


def minimax(board: chess.Board, depth: int, alpha: float, beta: float, is_maximizing: bool) -> tuple[float, chess.Move | None]:
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    legal_moves = list(board.legal_moves)
    random.shuffle(legal_moves)  # Adds variability to equal-score choices
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


def make_ai_move(difficulty: str):
    board = st.session_state.board
    if board.is_game_over():
        return

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return

    if difficulty == "Easy":
        chosen_move = random.choice(legal_moves)
    elif difficulty == "Medium":
        _, chosen_move = minimax(board, depth=2, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))
    else:  # Hard
        _, chosen_move = minimax(board, depth=3, alpha=float('-inf'), beta=float('inf'), is_maximizing=(board.turn == chess.WHITE))

    if chosen_move is None:
        chosen_move = random.choice(legal_moves)

    san_move = board.san(chosen_move)
    board.push(chosen_move)
    st.session_state.move_history.append(san_move)
    st.session_state.selected_square = None
    st.session_state.legal_destinations = []


# ==========================================
# INTERFACE & LAYOUT
# ==========================================
st.title("♟️ Streamlit Chess vs AI")

# Sidebar - Game Settings & Controls
with st.sidebar:
    st.header("⚙️ Game Controls")
    
    player_color = st.selectbox("Play As", ["White", "Black"], index=0)
    ai_color = chess.BLACK if player_color == "White" else chess.WHITE
    
    difficulty = st.selectbox("AI Difficulty", ["Easy", "Medium", "Hard"], index=1)
    
    col_reset, col_undo = st.columns(2)
    with col_reset:
        if st.button("New Game", use_container_width=True):
            st.session_state.board = chess.Board()
            st.session_state.move_history = []
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.rerun()

    with col_undo:
        if st.button("Undo Move", use_container_width=True):
            b = st.session_state.board
            # Pop AI move and Player move if possible
            if len(b.move_stack) >= 2:
                b.pop()
                b.pop()
                if len(st.session_state.move_history) >= 2:
                    st.session_state.move_history.pop()
                    st.session_state.move_history.pop()
            elif len(b.move_stack) == 1:
                b.pop()
                if st.session_state.move_history:
                    st.session_state.move_history.pop()
            st.session_state.selected_square = None
            st.session_state.legal_destinations = []
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Move History")
    if st.session_state.move_history:
        history_str = ""
        for i in range(0, len(st.session_state.move_history), 2):
            move_num = (i // 2) + 1
            w_move = st.session_state.move_history[i]
            b_move = st.session_state.move_history[i+1] if i+1 < len(st.session_state.move_history) else ""
            history_str += f"**{move_num}.** {w_move} {b_move}  \n"
        st.write(history_str)
    else:
        st.write("No moves played yet.")

# Main Layout
board = st.session_state.board
col_board, col_controls = st.columns([2, 1])

# Handle Automatic AI First Move if Player selects Black
if board.turn == ai_color and not board.is_game_over():
    with st.spinner("AI is thinking..."):
        make_ai_move(difficulty)
        st.rerun()

# Display Game Status Banner
with col_controls:
    st.subheader("📊 Game Status")
    if board.is_checkmate():
        st.error(f"Checkmate! {'Black' if board.turn == chess.WHITE else 'White'} wins!")
    elif board.is_stalemate():
        st.warning("Draw by Stalemate!")
    elif board.is_insufficient_material():
        st.warning("Draw by Insufficient Material!")
    elif board.is_check():
        st.warning("⚠️ Check!")
    else:
        current_turn = "White (You)" if board.turn == chess.WHITE and player_color == "White" else \
                       "Black (You)" if board.turn == chess.BLACK and player_color == "Black" else "AI"
        st.info(f"Turn: **{current_turn}**")

    # Pawn Promotion Choice
    promotion_piece = st.radio(
        "Pawn Promotion Choice:",
        ["Queen", "Rook", "Bishop", "Knight"],
        index=0,
        horizontal=True
    )
    promo_map = {
        "Queen": chess.QUEEN,
        "Rook": chess.ROOK,
        "Bishop": chess.BISHOP,
        "Knight": chess.KNIGHT
    }

# Render Board Display & Click Selectors
with col_board:
    # Build highlight list
    fill_squares = {}
    if st.session_state.selected_square is not None:
        fill_squares[st.session_state.selected_square] = "#769656"
        for dest in st.session_state.legal_destinations:
            fill_squares[dest] = "#baca44"

    board_svg = chess.svg.board(
        board=board,
        orientation=chess.WHITE if player_color == "White" else chess.BLACK,
        fill=fill_squares,
        size=450
    )
    st.image(board_svg, use_container_width=False)

    # Interactive Move Selection
    if board.turn != ai_color and not board.is_game_over():
        st.markdown("### Make Your Move")
        
        # Square dropdown mapping
        square_names = [chess.square_name(sq) for sq in chess.SQUARES]
        if player_color == "Black":
            square_names.reverse()

        c1, c2, c3 = st.columns([2, 2, 1])
        
        with c1:
            # Piece selection source square
            pieces_squares = [
                chess.square_name(sq) for sq in chess.SQUARES 
                if board.piece_at(sq) and board.piece_at(sq).color == board.turn
            ]
            selected_from = st.selectbox(
                "Select Piece From:",
                ["-- Select --"] + sorted(pieces_squares),
                key="from_sq"
            )

        with c2:
            if selected_from != "-- Select --":
                from_square_idx = chess.parse_square(selected_from)
                st.session_state.selected_square = from_square_idx
                
                # Filter legal moves for selected piece
                legal_dests = [
                    chess.square_name(m.to_square) for m in board.legal_moves 
                    if m.from_square == from_square_idx
                ]
                st.session_state.legal_destinations = [chess.parse_square(d) for d in legal_dests]
                
                selected_to = st.selectbox(
                    "Move To:",
                    ["-- Select --"] + sorted(legal_dests),
                    key="to_sq"
                )
            else:
                selected_to = "-- Select --"
                st.session_state.selected_square = None
                st.session_state.legal_destinations = []

        with c3:
            st.write(" ")
            st.write(" ")
            if st.button("Execute Move", type="primary", use_container_width=True):
                if selected_from != "-- Select --" and selected_to != "-- Select --":
                    from_idx = chess.parse_square(selected_from)
                    to_idx = chess.parse_square(selected_to)
                    
                    # Create move object
                    move = chess.Move(from_idx, to_idx)
                    
                    # Check for promotion condition
                    piece = board.piece_at(from_idx)
                    if piece and piece.piece_type == chess.PAWN:
                        if (piece.color == chess.WHITE and chess.square_rank(to_idx) == 7) or \
                           (piece.color == chess.BLACK and chess.square_rank(to_idx) == 0):
                            move.promotion = promo_map[promotion_piece]

                    if move in board.legal_moves:
                        san_str = board.san(move)
                        board.push(move)
                        st.session_state.move_history.append(san_str)
                        st.session_state.selected_square = None
                        st.session_state.legal_destinations = []
                        st.rerun()
                    else:
                        st.error("Illegal move chosen.")
