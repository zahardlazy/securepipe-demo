"""
SecurePipe Demo App - minimal Flask app with INTENTIONAL security issues.
All secrets here are AWS PUBLIC example keys (safe, non-functional).
"""
from flask import Flask, request

app = Flask(__name__)

# [SEEDED #1] Hardcoded fake secret (CICD-SEC-6) - target for Gitleaks/TruffleHog
AWS_ACCESS_KEY_ID = "AKIAABCDEFGHIJKLMNOP"
AWS_SECRET_ACCESS_KEY = "Yx9wKq2LmT5vBnZ8Rc4sE7uF1hJ3pGdA6oVbN0Ce"


@app.route("/")
def index():
    return {"app": "securepipe-demo", "version": "1.0"}


@app.route("/health")
def health():
    return {"status": "ok"}


# [SEEDED #3 - bonus for SAST] Intentional SQL injection - target for Semgrep
@app.route("/user")
def get_user():
    import sqlite3
    conn = sqlite3.connect("users.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users (name) VALUES ('alice')")
        conn.execute("INSERT INTO users (name) VALUES ('bob')")
        conn.commit()
    uid = request.args.get("id", "1")
    row = conn.execute(f"SELECT * FROM users WHERE id = {uid}").fetchone()
    conn.close()
    if row:
        return {"user": row}
    return ("not found", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
