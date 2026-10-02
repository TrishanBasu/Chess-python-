import streamlit as st
import chess
import math
import random
import time

st.set_page_config(
    page_title="Chess vs AI",
    page_icon="♟️",
    layout="centered"
)

# =========================
# PIECES
# =========================

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

# =========================
# AI LEVELS
# =========================

AI_LEVELS = {
    1: {"name": "250 Elo", "depth": 1, "randomness": 0.50},
    2: {"name": "500–600 Elo", "depth": 1, "randomness": 0.20},
    3: {"name": "1000–1100 Elo", "depth": 2, "randomness": 0.06},
    4: {"name": "1500–1600 Elo", "depth": 3, "randomness": 0.015},
    5: {"name": "2200–2500 Elo*", "depth": 4, "randomness": 0.0}
}

TIME_CONTROLS = {
    "10 Minutes": 600,
    "5 Minutes": 300,
    "1 Minute": 60,
    "No Time": None
}

# =========================
# INITIALIZE
# =========================

if "board" not in st.session_state:
    st.session_state.board = chess.Board()

if "level" not in st.session_state:
    st.session_state.level = 3

if "player_color" not