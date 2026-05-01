from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import sqlite3, requests, datetime
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "eco_secret"

DB = "database.db"

def db():
    return sqlite3.connect(DB)

# INIT DATABASE
def init():
    con = db()
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY,
        url TEXT,
        product_name TEXT,
        score INTEGER,
        date TEXT)""")

    try:
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)",("admin","admin123"))
    except:
        pass

    con.commit()
    con.close()

init()

# ECO SCORE
def eco_score(text):
    eco = ["eco","green","organic","natural"]
    bad = ["plastic","chemical","synthetic"]

    score = 5
    text = text.lower()

    for i in eco:
        if i in text: score += 1
    for i in bad:
        if i in text: score -= 1

    return max(1,min(10,score))

# PRODUCT SCRAPER
def get_product(url):
    try:
        headers={"User-Agent":"Mozilla/5.0"}
        res = requests.get(url,headers=headers,timeout=5)
        soup = BeautifulSoup(res.text,"html.parser")

        title = soup.title.string if soup.title else "Unknown"
        meta = soup.find("meta",{"name":"description"})
        desc = meta["content"] if meta else title

        price = "Not found"
        price_tag = soup.find(string=lambda x:x and "₹" in x)
        if price_tag:
            price = price_tag.strip()

        score = eco_score(desc)

        return {"name":title,"price":price,"score":score}
    except:
        return None

# HOME
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("login"))

# LOGIN
@app.route("/login",methods=["GET","POST"])
def login():
    error=None

    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        con=db()
        cur=con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user=cur.fetchone()
        con.close()

        if user:
            session["user"]=u
            return redirect(url_for("dashboard"))
        else:
            error="Invalid credentials"

    return render_template("login.html",error=error)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# ANALYZE
@app.route("/analyze",methods=["GET","POST"])
def analyze():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method=="POST":
        url=request.form["url"]
        p=get_product(url)

        if not p:
            return render_template("result.html",error="Invalid URL")

        con=db()
        cur=con.cursor()
        cur.execute("INSERT INTO history(url,product_name,score,date) VALUES(?,?,?,?)",
                    (url,p["name"],p["score"],datetime.datetime.now()))
        con.commit()
        con.close()

        return render_template("result.html",p=p)

    return redirect(url_for("dashboard"))

# COMPARE
@app.route("/compare",methods=["GET","POST"])
def compare():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method=="POST":
        p1=get_product(request.form["url1"])
        p2=get_product(request.form["url2"])

        if not p1 or not p2:
            return render_template("compare.html",error="Invalid URL")

        return render_template("compare.html",p1=p1,p2=p2)

    return redirect(url_for("dashboard"))

# HISTORY
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))

    con=db()
    cur=con.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    data=cur.fetchall()
    con.close()

    return render_template("history.html",data=data)

# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    con=db()
    cur=con.cursor()
    cur.execute("DELETE FROM history WHERE id=?",(id,))
    con.commit()
    con.close()
    return redirect(url_for("history"))

# EXPORT CSV
@app.route("/export")
def export():
    con=db()
    cur=con.cursor()
    cur.execute("SELECT * FROM history")
    data=cur.fetchall()
    con.close()

    def generate():
        yield "ID,URL,Product,Score,Date\n"
        for r in data:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}\n"

    return Response(generate(),mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=data.csv"})

# GRAPH
@app.route("/graph")
def graph():
    con=db()
    cur=con.cursor()
    cur.execute("SELECT product_name,score FROM history")
    data=cur.fetchall()
    con.close()

    labels=[i[0] for i in data]
    values=[i[1] for i in data]

    return render_template("graph.html",labels=labels,values=values)

# CHATBOT
@app.route("/chatbot",methods=["POST"])
def chatbot():
    msg=request.json["message"].lower()

    if "eco" in msg:
        reply="Use eco products 🌱"
    elif "plastic" in msg:
        reply="Avoid plastic"
    else:
        reply="Choose sustainable"

    return jsonify({"reply":reply})

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)