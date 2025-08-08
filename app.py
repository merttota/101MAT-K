from flask import Flask, request, jsonify
import matplotlib.pyplot as plt
import io
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin for development

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

    # 1. Create total score per round
    total_per_round = [scoresTeam1[i] + scoresTeam2[i] for i in range(round_count)]

    # 2. Create team total scores
    team1_total = sum(scoresTeam1)
    team2_total = sum(scoresTeam2)

    # ---------- GRAPH 1: Total per round ----------
    plt.figure()
    plt.plot(range(1, round_count + 1), total_per_round, marker='o')
    plt.title("Total Scores Per Round")
    plt.xlabel("Round")
    plt.ylabel("Total Score")
    plt.grid(True)
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    img1 = base64.b64encode(buf1.getvalue()).decode()

    # ---------- GRAPH 2: Team point difference ----------
    plt.figure()
    plt.bar([team1, team2], [team1_total, team2_total])
    plt.title("Team Point Totals")
    plt.ylabel("Total Points")
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    img2 = base64.b64encode(buf2.getvalue()).decode()

    return jsonify({
        "roundGraph": img1,
        "diffGraph": img2
    })

if __name__ == "__main__":
    app.run(debug=True)
