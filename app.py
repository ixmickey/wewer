from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
import bcrypt
import os
from config import MASTER_KEY, TELEGRAM_TOKEN, ADMIN_CHAT_ID

app = Flask(__name__)
app.secret_key = "secret123"

KEY_HASH = bcrypt.hashpw(MASTER_KEY.encode(), bcrypt.gensalt())

def verify_key(user_key):
    return bcrypt.checkpw(user_key.encode(), KEY_HASH)


def send_telegram(msg, request_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Approve", "callback_data": f"approve_{request_id}"},
                {"text": "Reject", "callback_data": f"reject_{request_id}"}
            ]
        ]
    }

    requests.post(url, json={
        "chat_id": ADMIN_CHAT_ID,
        "text": msg,
        "reply_markup": keyboard
    })


def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact TEXT,
        orderid TEXT,
        paymentref TEXT,
        product TEXT,
        count INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/", methods=["GET", "POST"])
def key():

    if request.method == "POST":
        key = request.form["key"]

        if verify_key(key):
            session["verified"] = True
            return redirect("/steps")

        return "Invalid key"

    return render_template("key.html")


@app.route("/steps")
def steps():

    if not session.get("verified"):
        return redirect("/")

    return render_template("steps.html")


@app.route("/form", methods=["GET", "POST"])
def form():

    if not session.get("verified"):
        return redirect("/")

    if request.method == "POST":

        contact = request.form["contact"]
        order = request.form["order"]
        payment = request.form["payment"]
        product = request.form["product"]
        count = request.form["count"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO requests(contact,orderid,paymentref,product,count,status) VALUES(?,?,?,?,?,?)",
            (contact, order, payment, product, count, "Pending")
        )

        request_id = c.lastrowid

        conn.commit()
        conn.close()

        msg = f"""
New Demo Request

Contact: {contact}
Order: {order}
Payment Ref: {payment}
Product: {product}
Count: {count}
"""

        send_telegram(msg, request_id)

        return redirect(f"/processing/{request_id}")

    return render_template("form.html")


@app.route("/processing/<int:request_id>")
def processing(request_id):
    return render_template("processing.html", request_id=request_id)


@app.route("/status/<int:request_id>")
def status(request_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT status FROM requests WHERE id=?", (request_id,))
    result = c.fetchone()

    conn.close()

    return {"status": result[0]}


# 🔥 IMPORTANT ROUTE FOR TELEGRAM BOT
@app.route("/update_status", methods=["POST"])
def update_status():

    data = request.json
    request_id = data.get("id")
    status = data.get("status")

    if not request_id:
        return {"error": "invalid request"}, 400

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "UPDATE requests SET status=? WHERE id=?",
        (status, request_id)
    )

    conn.commit()
    conn.close()

    return {"success": True}


# Render PORT FIX
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
```
