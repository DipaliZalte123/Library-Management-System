from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "library_secret_key"


# ---------------- DATABASE CONNECTION ----------------

def get_db_connection():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE TABLES ----------------

def create_tables():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            author TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid username or password"

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- VIEW BOOKS ----------------

@app.route("/books")
def books():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    return render_template("books.html", books=books)


# ---------------- ADD BOOK ----------------

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book_id = request.form["book_id"]
        book_name = request.form["book_name"]
        author_name = request.form["author_name"]

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO books (id, name, author) VALUES (?, ?, ?)",
                (book_id, book_name, author_name)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Book ID already exists."

        conn.close()

        return redirect("/books")

    return render_template("add_book.html")


# ---------------- DELETE BOOK ----------------

@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    conn = get_db_connection()

    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()

    conn.close()

    return redirect("/books")


# ---------------- UPDATE BOOK ----------------

@app.route("/update_book/<int:book_id>", methods=["GET", "POST"])
def update_book(book_id):
    conn = get_db_connection()

    book = conn.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()

    if request.method == "POST":
        book_name = request.form["book_name"]
        author_name = request.form["author_name"]

        conn.execute(
            "UPDATE books SET name = ?, author = ? WHERE id = ?",
            (book_name, author_name, book_id)
        )

        conn.commit()
        conn.close()

        return redirect("/books")

    conn.close()

    return render_template("update_book.html", book=book)


# ---------------- VIEW STUDENTS ----------------

@app.route("/students")
def students():
    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template("students.html", students=students)


# ---------------- ADD STUDENT ----------------

@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        student_id = request.form["student_id"]
        student_name = request.form["student_name"]
        email = request.form["email"]

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO students (id, name, email) VALUES (?, ?, ?)",
                (student_id, student_name, email)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Student ID already exists."

        conn.close()

        return redirect("/students")

    return render_template("add_student.html")


# ---------------- DELETE STUDENT ----------------

@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/students")


# ---------------- ISSUE BOOK ----------------

@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        student_id = request.form["student_id"]
        book_id = request.form["book_id"]
        issue_date = request.form["issue_date"]

        conn = get_db_connection()

        # Check student
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        # Check book
        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if student is None:
            conn.close()
            return "Student ID not found."

        if book is None:
            conn.close()
            return "Book ID not found."

        conn.execute(
            """
            INSERT INTO issues (student_id, book_id, issue_date)
            VALUES (?, ?, ?)
            """,
            (student_id, book_id, issue_date)
        )

        conn.commit()
        conn.close()

        return redirect("/issued_books")

    return render_template("issue_book.html")


# ---------------- VIEW ISSUED BOOKS ----------------

@app.route("/issued_books")
def issued_books():
    conn = get_db_connection()

    issues = conn.execute("""
        SELECT
            issues.id,
            issues.student_id,
            students.name AS student_name,
            issues.book_id,
            books.name AS book_name,
            issues.issue_date
        FROM issues
        LEFT JOIN students
            ON issues.student_id = students.id
        LEFT JOIN books
            ON issues.book_id = books.id
        ORDER BY issues.id DESC
    """).fetchall()

    conn.close()

    return render_template("issued_book.html", issues=issues)


# ---------------- DELETE ISSUED BOOK ----------------

@app.route("/delete_issue/<int:issue_id>")
def delete_issue(issue_id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM issues WHERE id = ?",
        (issue_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/issued_books")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()

    total_books = conn.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_issued = conn.execute(
        "SELECT COUNT(*) FROM issues"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        total_students=total_students,
        total_issued=total_issued
    )


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)