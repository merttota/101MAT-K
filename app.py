from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "Backend is running."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    team1 = data["team1"]
    team2 = data["team2"]
    scoresTeam1 = data["scoresTeam1"]
    scoresTeam2 = data["scoresTeam2"]

    round_count = len(scoresTeam1)
    rounds = [f"R{i+1}" for i in range(round_count)]

    # Calculate cumulative totals
    cumulative_team1 = [sum(scoresTeam1[:i+1]) for i in range(round_count)]
    cumulative_team2 = [sum(scoresTeam2[:i+1]) for i in range(round_count)]
    difference = [cumulative_team1[i] - cumulative_team2[i] for i in range(round_count)]

    # ---------- GRAPH 1: Analiz (Cumulative scores) ----------
    plt.figure(figsize=(8, 5))
    plt.plot(rounds, cumulative_team1, marker='o', color='royalblue', label=team1)
    plt.plot(rounds, cumulative_team2, marker='o', color='darkorange', label=team2)
    plt.title("Analiz", fontsize=14, fontweight='bold')
    plt.xlabel("")
    plt.ylabel("")
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.legend(loc='lower center', ncol=2)

    # Display numeric values on points
    for i, val in enumerate(cumulative_team1):
        plt.text(i, val + 20, str(val), ha='center', fontsize=8, color='royalblue')
    for i, val in enumerate(cumulative_team2):
        plt.text(i, val + 20, str(val), ha='center', fontsize=8, color='darkorange')

    buf1 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf1, format='png', dpi=200)
    plt.close()
    buf1.seek(0)
    img1 = base64.b64encode(buf1.getvalue()).decode()
    
    # ---------- GRAPH 2: Fark (Difference) ----------
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, round_count + 1), difference, marker='o', color='royalblue')
    plt.title("Fark", fontsize=14, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.xticks(range(1, round_count + 1))
    
    # ✅ Draw horizontal zero-line only if 0 is between min & max
    if min(difference) < 0 < max(difference):
        plt.axhline(0, linestyle='--', linewidth=1)
    
    # Display numeric values on points
    for i, val in enumerate(difference):
        plt.text(i + 1, val + (50 if val >= 0 else -50), str(val), ha='center', fontsize=8)


    buf2 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf2, format='png', dpi=200)
    plt.close()
    buf2.seek(0)
    img2 = base64.b64encode(buf2.getvalue()).decode()

    return jsonify({
        "analizGraph": img1,
        "farkGraph": img2
    })


if __name__ == "__main__":
    app.run(debug=True)
