from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as pe
import numpy as np
import io
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Shared palette ─────────────────────────────────────────────────────────────
BG          = "#0f1117"
PANEL       = "#161b26"
GRID_COLOR  = "#1e2535"
C1          = "#4f9cf9"   # team 1 – electric blue
C2          = "#f97316"   # team 2 – vivid orange
C1_GLOW     = "#4f9cf944"
C2_GLOW     = "#f9731644"
TEXT_MAIN   = "#e8eaf0"
TEXT_DIM    = "#5a6278"
FONT_TITLE  = "monospace"   # clean mono for a scoreboard feel

def _base_fig(w=9, h=5):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    ax  = fig.add_subplot(111, facecolor=PANEL)
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
        spine.set_linewidth(1.2)
    ax.tick_params(colors=TEXT_DIM, labelsize=8)
    ax.xaxis.label.set_color(TEXT_DIM)
    ax.yaxis.label.set_color(TEXT_DIM)
    ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.7, alpha=0.6)
    return fig, ax

def _glow_line(ax, x, y, color, glow_color, **kwargs):
    """Draw a line with a soft glow halo beneath it."""
    # shadow / glow layers
    for lw, alpha in [(12, 0.07), (6, 0.12), (3, 0.20)]:
        ax.plot(x, y, color=color, linewidth=lw, alpha=alpha, zorder=2)
    ax.plot(x, y, color=color, linewidth=1.8, zorder=3, **kwargs)

def _dot(ax, xi, yi, color, size=70):
    ax.scatter(xi, yi, s=size, color=color, zorder=5, edgecolors=BG, linewidths=1.5)

def _label(ax, xi, yi, val, color, offset_y):
    ax.text(
        xi, yi + offset_y, str(val),
        ha="center", va="center", fontsize=7.5,
        color=color, fontweight="bold", fontfamily=FONT_TITLE,
        path_effects=[pe.withStroke(linewidth=2, foreground=BG)]
    )

def _title_bar(fig, ax, title_text):
    ax.set_title(
        title_text,
        color=TEXT_MAIN, fontsize=13, fontweight="bold",
        fontfamily=FONT_TITLE, pad=14,
        loc="left"
    )
    # decorative accent line under title area
    fig.text(0.13, 0.93, "─" * 60, color=GRID_COLOR, fontsize=7, alpha=0.6)

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

    # ── GRAPH 1 : Analiz ────────────────────────────────────────────────────────
    fig1, ax1 = _base_fig(9, 5.2)
    _title_bar(fig1, ax1, "ANALİZ")

    # shaded area between the two curves
    y1_arr = np.array(cum1)
    y2_arr = np.array(cum2)
    ax1.fill_between(x, y1_arr, y2_arr,
                     where=y1_arr >= y2_arr,
                     interpolate=True, alpha=0.08, color=C1, zorder=1)
    ax1.fill_between(x, y1_arr, y2_arr,
                     where=y1_arr < y2_arr,
                     interpolate=True, alpha=0.08, color=C2, zorder=1)

    _glow_line(ax1, x, cum1, C1, C1_GLOW)
    _glow_line(ax1, x, cum2, C2, C2_GLOW)

    for i, v in enumerate(cum1):
        _dot(ax1, i, v, C1)
        _label(ax1, i, v, v, C1, (max(cum1) - min(cum1 + cum2)) * 0.06 + 15)
    for i, v in enumerate(cum2):
        _dot(ax1, i, v, C2)
        _label(ax1, i, v, v, C2, -((max(cum1) - min(cum1 + cum2)) * 0.06 + 28))

    ax1.set_xticks(x)
    ax1.set_xticklabels(rounds, color=TEXT_DIM, fontfamily=FONT_TITLE)
    ax1.yaxis.set_visible(False)

    # custom legend chips
    patch1 = mpatches.Patch(color=C1, label=team1)
    patch2 = mpatches.Patch(color=C2, label=team2)
    legend = ax1.legend(
        handles=[patch1, patch2],
        loc="lower center", ncol=2,
        facecolor=PANEL, edgecolor=GRID_COLOR,
        labelcolor=TEXT_MAIN, fontsize=9,
        framealpha=0.9, borderpad=0.8
    )

    # final score badge top-right
    score_text = f"{cum1[-1]}  —  {cum2[-1]}"
    fig1.text(0.88, 0.91, score_text,
              ha="right", va="top",
              color=TEXT_MAIN, fontsize=11, fontweight="bold",
              fontfamily=FONT_TITLE)

    plt.tight_layout(pad=1.6)
    img1 = _to_b64(fig1)

    # ── GRAPH 2 : Fark ───────────────────────────────────────────────────────────
    fig2, ax2 = _base_fig(9, 5.2)
    _title_bar(fig2, ax2, "FARK")

    x2 = list(range(1, round_count + 1))
    diff_arr = np.array(diff)

    # colour-fill positive / negative regions
    ax2.fill_between(x2, diff_arr, 0,
                     where=diff_arr >= 0, interpolate=True,
                     alpha=0.12, color=C1)
    ax2.fill_between(x2, diff_arr, 0,
                     where=diff_arr < 0, interpolate=True,
                     alpha=0.12, color=C2)

    _glow_line(ax2, x2, diff_arr, C1, C1_GLOW)

    # colour dots per sign
    for i, v in enumerate(diff):
        dot_col = C1 if v >= 0 else C2
        _dot(ax2, x2[i], v, dot_col, size=60)
        offset = (max(abs(d) for d in diff) * 0.09 + 20) * (1 if v >= 0 else -1)
        _label(ax2, x2[i], v, v, dot_col, offset)

    # zero axis
    if min(diff) < 0 < max(diff):
        ax2.axhline(0, color=TEXT_DIM, linestyle="--", linewidth=0.9, alpha=0.5)

    ax2.set_xticks(x2)
    ax2.set_xticklabels([f"R{i}" for i in x2], color=TEXT_DIM, fontfamily=FONT_TITLE)
    ax2.yaxis.set_visible(False)

    plt.tight_layout(pad=1.6)
    img2 = _to_b64(fig2)

    return jsonify({"analizGraph": img1, "farkGraph": img2})


if __name__ == "__main__":
    app.run(debug=True)
