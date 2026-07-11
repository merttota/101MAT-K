from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
import io
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Poker table palette ─────────────────────────────────────────────────────
BG          = "#0b3d2e"   # casino felt green
PANEL       = "#0e4735"   # slightly lighter felt for the panel
GRID_COLOR  = "#1f6b4f"   # felt seam lines
GOLD        = "#d4af37"   # trim / accents
GOLD_DIM    = "#8a7328"
TEXT_MAIN   = "#f4ead1"   # cream card-stock white
TEXT_DIM    = "#9fcdb6"

C1          = "#e0483e"   # poker chip red  (♥ / ♦)
C1_GLOW     = "#e0483e33"
C2          = "#f4ead1"   # poker chip cream/white (♠ / ♣ printed in black on white chip)
C2_GLOW     = "#f4ead133"

SUIT_1      = "♥"   # team 1 marker
SUIT_2      = "♠"   # team 2 marker

FONT_TITLE  = "monospace"

def _base_fig(w=9, h=5.2):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    ax  = fig.add_subplot(111, facecolor=PANEL)
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(GOLD_DIM)
        spine.set_linewidth(1.3)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    ax.xaxis.label.set_color(TEXT_DIM)
    ax.yaxis.label.set_color(TEXT_DIM)
    ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.7, alpha=0.55)
    return fig, ax

def _felt_border(fig):
    """Thin gold card-table rail around the whole figure."""
    rect = plt.Rectangle(
        (0.012, 0.012), 0.976, 0.976,
        transform=fig.transFigure, fill=False,
        edgecolor=GOLD_DIM, linewidth=1.4, zorder=10
    )
    fig.patches.append(rect)

def _glow_line(ax, x, y, color, **kwargs):
    for lw, alpha in [(12, 0.06), (6, 0.10), (3, 0.16)]:
        ax.plot(x, y, color=color, linewidth=lw, alpha=alpha, zorder=2)
    ax.plot(x, y, color=color, linewidth=1.6, zorder=3, alpha=0.85, **kwargs)

def _suit_marker(ax, xi, yi, suit, color, size=17, outline="#000000"):
    """Draw a suit glyph as the data point marker instead of a plain dot."""
    stroke_color = BG if color != C2 else "#00000055"
    ax.text(
        xi, yi, suit, ha="center", va="center",
        fontsize=size, color=color, zorder=5,
        path_effects=[pe.withStroke(linewidth=2.2, foreground=stroke_color)]
    )

def _label(ax, xi, yi, val, color, offset_y):
    ax.text(
        xi, yi + offset_y, str(val),
        ha="center", va="center", fontsize=7.5,
        color=color, fontweight="bold", fontfamily=FONT_TITLE,
        path_effects=[pe.withStroke(linewidth=2.4, foreground=BG)]
    )

def _title_bar(fig, ax, title_text):
    ax.set_title(
        f"♣  {title_text}  ♦",
        color=GOLD, fontsize=13, fontweight="bold",
        fontfamily=FONT_TITLE, pad=14, loc="left"
    )
    fig.text(0.13, 0.93, "─" * 60, color=GOLD_DIM, fontsize=7, alpha=0.6)

def _to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/")
def index():
    return "Backend is running."


@app.route("/analyze", methods=["POST"])
def analyze():
    data         = request.get_json()
    team1        = data["team1"]
    team2        = data["team2"]
    scores1      = data["scoresTeam1"]
    scores2      = data["scoresTeam2"]
    round_count  = len(scores1)
    rounds       = [f"R{i+1}" for i in range(round_count)]
    x            = list(range(round_count))

    cum1 = [sum(scores1[:i+1]) for i in range(round_count)]
    cum2 = [sum(scores2[:i+1]) for i in range(round_count)]
    diff = [cum1[i] - cum2[i] for i in range(round_count)]

    # ── GRAPH 1 : Analiz ─────────────────────────────────────────────────────
    fig1, ax1 = _base_fig(9, 5.2)
    _title_bar(fig1, ax1, "ANALİZ")
    _felt_border(fig1)

    y1_arr = np.array(cum1)
    y2_arr = np.array(cum2)
    ax1.fill_between(x, y1_arr, y2_arr, where=y1_arr >= y2_arr,
                      interpolate=True, alpha=0.10, color=C1, zorder=1)
    ax1.fill_between(x, y1_arr, y2_arr, where=y1_arr < y2_arr,
                      interpolate=True, alpha=0.10, color=C2, zorder=1)

    _glow_line(ax1, x, cum1, C1)
    _glow_line(ax1, x, cum2, C2)

    label_gap = (max(cum1 + cum2) - min(cum1 + cum2) or 1) * 0.07 + 16
    for i, v in enumerate(cum1):
        _suit_marker(ax1, i, v, SUIT_1, C1)
        _label(ax1, i, v, v, C1, label_gap)
    for i, v in enumerate(cum2):
        _suit_marker(ax1, i, v, SUIT_2, C2)
        _label(ax1, i, v, v, C2, -label_gap)

    ax1.set_xticks(x)
    ax1.set_xticklabels(rounds, color=TEXT_DIM, fontfamily=FONT_TITLE)
    ax1.yaxis.set_visible(False)

    patch1 = mpatches.Patch(color=C1, label=f"{SUIT_1} {team1}")
    patch2 = mpatches.Patch(color=C2, label=f"{SUIT_2} {team2}")
    ax1.legend(
        handles=[patch1, patch2], loc="lower center", ncol=2,
        facecolor=PANEL, edgecolor=GOLD_DIM, labelcolor=TEXT_MAIN,
        fontsize=9, framealpha=0.92, borderpad=0.8
    )

    score_text = f"{cum1[-1]}  —  {cum2[-1]}"
    fig1.text(0.88, 0.91, score_text, ha="right", va="top",
              color=GOLD, fontsize=12, fontweight="bold", fontfamily=FONT_TITLE)

    fig1.subplots_adjust(top=0.86, bottom=0.13, left=0.04, right=0.97)
    img1 = _to_b64(fig1)

    # ── GRAPH 2 : Fark ───────────────────────────────────────────────────────
    fig2, ax2 = _base_fig(9, 5.2)
    _title_bar(fig2, ax2, "FARK")
    _felt_border(fig2)

    x2 = list(range(1, round_count + 1))
    diff_arr = np.array(diff)

    ax2.fill_between(x2, diff_arr, 0, where=diff_arr >= 0,
                      interpolate=True, alpha=0.14, color=C1)
    ax2.fill_between(x2, diff_arr, 0, where=diff_arr < 0,
                      interpolate=True, alpha=0.14, color=C2)

    pos_mask = diff_arr >= 0
    _glow_line(ax2, x2, diff_arr, GOLD)

    max_abs = max(abs(d) for d in diff) or 1
    for i, v in enumerate(diff):
        suit  = SUIT_1 if v >= 0 else SUIT_2
        color = C1 if v >= 0 else C2
        _suit_marker(ax2, x2[i], v, suit, color, size=15)
        offset = (max_abs * 0.09 + 18) * (1 if v >= 0 else -1)
        _label(ax2, x2[i], v, v, color, offset)

    if min(diff) < 0 < max(diff):
        ax2.axhline(0, color=GOLD_DIM, linestyle="--", linewidth=0.9, alpha=0.6)

    ax2.set_xticks(x2)
    ax2.set_xticklabels([f"R{i}" for i in x2], color=TEXT_DIM, fontfamily=FONT_TITLE)
    ax2.yaxis.set_visible(False)

    fig2.subplots_adjust(top=0.86, bottom=0.13, left=0.04, right=0.97)
    img2 = _to_b64(fig2)

    return jsonify({"analizGraph": img1, "farkGraph": img2})


if __name__ == "__main__":
    app.run(debug=True)
