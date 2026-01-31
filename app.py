from flask import Flask, render_template, request
import requests
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT)')

def search_platforms(username):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    targets = {"GitHub": f"https://github.com/{username}", "Reddit": f"https://www.reddit.com/user/{username}/"}
    exact, similar = [], []
    for platform, url in targets.items():
        try:
            r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                html = r.text.lower()
                is_real = True
                if platform == "Reddit" and ("nobody on reddit" in html or "unclaimed" in html):
                    is_real = False
                if is_real: exact.append({"platform": platform, "url": url, "user": username})
            
            for v in [f"{username}_", f"{username}123"]:
                v_url = url.replace(username, v)
                vr = requests.get(v_url, headers=headers, timeout=2)
                if vr.status_code == 200:
                    v_html = vr.text.lower()
                    if not (platform == "Reddit" and ("nobody on reddit" in v_html or "unclaimed" in v_html)):
                        similar.append({"platform": platform, "url": v_url, "user": v})
        except: pass
    return exact, similar

@app.route("/", methods=["GET", "POST"])
def index():
    res, ex, sim, score = "", [], [], 100
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        if user:
            ex, sim = search_platforms(user)
            score = max(5, 100 - (len(ex) * 30) - min(len(sim) * 10, 40))
            res = "✅ Highly Unique" if score >= 80 else "⚠️ Moderate Risk" if score >= 50 else "🚨 High Risk"
            with sqlite3.connect('database.db') as conn:
                conn.execute("INSERT INTO history (username) VALUES (?)", (user,))
    with sqlite3.connect('database.db') as conn:
        hist = conn.execute("SELECT DISTINCT username FROM history ORDER BY id DESC LIMIT 6").fetchall()
    return render_template("index.html", result=res, exact=ex, similar=sim, history=hist, score=score)

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
