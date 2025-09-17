import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

# إنشاء التطبيق
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DB_NAME = "study.db"

# === إنشاء قاعدة البيانات والجداول ===
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # جدول الحصص
    c.execute("""CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY,
                day TEXT,
                time TEXT,
                subject TEXT)""")

    # جدول الدروس
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY,
                day TEXT,
                subject TEXT)""")

    # جدول المهام
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                subject TEXT,
                description TEXT,
                date TEXT,
                time TEXT)""")

    # جدول الواجب
    c.execute("""CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY,
                subject TEXT,
                details TEXT,
                image TEXT,
                date TEXT,
                time TEXT)""")

    # جدول الامتحانات
    c.execute("""CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY,
                subject TEXT,
                date TEXT,
                details TEXT)""")

    conn.commit()
    conn.close()

init_db()

# === استخراج التنبيهات (مهام + واجب + امتحانات قريبة) ===
def get_notifications():
    today = str(date.today())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    notifications = []

    # المهام
    c.execute("SELECT subject, description, date, time FROM tasks WHERE date >= ?", (today,))
    for row in c.fetchall():
        notifications.append({
            "subject": row[0],
            "details": row[1],
            "date": row[2],
            "time": row[3]
        })

    # الواجب
    c.execute("SELECT subject, details, date, time FROM homework WHERE date >= ?", (today,))
    for row in c.fetchall():
        notifications.append({
            "subject": row[0],
            "details": row[1],
            "date": row[2],
            "time": row[3]
        })

    # الامتحانات
    c.execute("SELECT subject, date, details FROM exams WHERE date >= ?", (today,))
    for row in c.fetchall():
        notifications.append({
            "subject": row[0],
            "details": row[2],
            "date": row[1],
            "time": "08:00"
        })

    conn.close()
    return notifications

# === الرئيسية ===
@app.route("/")
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # جدول الحصص
    c.execute("SELECT day, time, subject FROM schedule ORDER BY id")
    data = c.fetchall()
    table = {}
    for day, time, subject in data:
        table.setdefault(day, []).append(subject)

    # باقي الجداول
    c.execute("SELECT * FROM lessons ORDER BY day")
    lessons = c.fetchall()

    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()

    c.execute("SELECT * FROM homework")
    homework = c.fetchall()

    c.execute("SELECT * FROM exams")
    exams = c.fetchall()

    conn.close()

    return render_template("index.html",
                           table=table,
                           lessons=lessons,
                           tasks=tasks,
                           homework=homework,
                           exams=exams,
                           notifications=get_notifications())

# === جدول الحصص ===
@app.route("/schedule", methods=["POST"])
def schedule():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    day = request.form["day"]
    subjects = [request.form.get(f"p{i}") for i in range(1, 9)]

    # امسح القديم
    c.execute("DELETE FROM schedule WHERE day=?", (day,))

    # أضف الجديد
    for i, subject in enumerate(subjects, start=1):
        if subject:
            c.execute("INSERT INTO schedule (day,time,subject) VALUES (?,?,?)",
                      (day, f"الحصة {i}", subject))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# === الدروس ===
@app.route("/lessons", methods=["POST"])
def lessons():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    day = request.form["day"]
    subject = request.form["subject"]
    c.execute("INSERT INTO lessons (day,subject) VALUES (?,?)", (day, subject))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# === المهام ===
@app.route("/tasks", methods=["POST"])
def tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    subject = request.form["subject"]
    desc = request.form["description"]
    date_val = request.form.get("date", str(date.today()))
    time_val = request.form.get("time", "08:00")
    c.execute("INSERT INTO tasks (subject,description,date,time) VALUES (?,?,?,?)",
              (subject, desc, date_val, time_val))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# === الواجب ===
@app.route("/homework", methods=["POST"])
def homework():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    subject = request.form["subject"]
    details = request.form["details"]
    date_val = str(date.today())
    time_val = datetime.now().strftime("%H:%M")

    file = request.files["image"]
    filename = None
    if file and file.filename:
        filename = file.filename
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    c.execute("INSERT INTO homework (subject,details,image,date,time) VALUES (?,?,?,?,?)",
              (subject, details, filename, date_val, time_val))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# === الامتحانات ===
@app.route("/exams", methods=["POST"])
def exams():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    subject = request.form["subject"]
    date_val = request.form["date"]
    details = request.form["details"]
    c.execute("INSERT INTO exams (subject,date,details) VALUES (?,?,?)",
              (subject, date_val, details))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# === تشغيل التطبيق ===
if __name__ == "__main__":
    app.run(debug=True)
