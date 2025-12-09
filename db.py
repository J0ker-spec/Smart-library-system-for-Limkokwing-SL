import psycopg2
from psycopg2.extras import RealDictCursor

DB = {
    "dbname": "smartlibrary",
    "user": "postgres",
    "password": "@Francess123",
    "host": "localhost",
    "port": 5432
}

def _get_conn():
    return psycopg2.connect(**DB)

# ----------------- AUTHORS -----------------
def add_author(name):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT author_id FROM authors WHERE name=%s", (name,))
        result = cur.fetchone()
        if result:
            return result[0]
        cur.execute("INSERT INTO authors(name) VALUES(%s) RETURNING author_id", (name,))
        return cur.fetchone()[0]

# ----------------- BOOKS -----------------
def add_book(isbn, title, author_name, genre, copies):
    author_id = add_author(author_name)
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM books WHERE isbn=%s", (isbn,))
        if cur.fetchone():
            return "Book already exists!"
        cur.execute(
            "INSERT INTO books(isbn, title, author_id, genre, total_copies, available_copies) "
            "VALUES(%s,%s,%s,%s,%s,%s)",
            (isbn, title, author_id, genre, copies, copies)
        )
    return "Book added successfully!"

def update_book(isbn, title=None, author_name=None, genre=None, copies=None):
    parts, params = [], []
    if title:
        parts.append("title=%s")
        params.append(title)
    if author_name:
        parts.append("author_id=%s")
        params.append(add_author(author_name))
    if genre:
        parts.append("genre=%s")
        params.append(genre)
    if copies is not None:
        parts.append("total_copies=%s")
        params.append(int(copies))
    if not parts:
        return "Nothing to update!"
    sql = "UPDATE books SET " + ", ".join(parts) + " WHERE isbn=%s"
    params.append(isbn)
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM books WHERE isbn=%s", (isbn,))
        if not cur.fetchone():
            return "Book not found!"
        cur.execute(sql, tuple(params))
    return "Book updated!"

def delete_book(isbn):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM loans WHERE isbn=%s AND date_returned IS NULL", (isbn,))
        if cur.fetchone()[0] > 0:
            return "Cannot delete: book has active loans"
        cur.execute("DELETE FROM books WHERE isbn=%s", (isbn,))
        return "Book deleted!" if cur.rowcount else "Book not found!"

def get_all_books():
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT b.isbn, b.title, b.genre, b.total_copies, b.available_copies, a.name AS author
            FROM books b JOIN authors a ON b.author_id = a.author_id
            ORDER BY b.title
        """)
        return cur.fetchall()

def search_books(keyword):
    kw = f"%{keyword}%"
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT b.isbn, b.title, b.genre, b.available_copies, a.name AS author
            FROM books b JOIN authors a ON b.author_id = a.author_id
            WHERE LOWER(b.title) LIKE LOWER(%s) OR LOWER(a.name) LIKE LOWER(%s)
            ORDER BY b.title
        """, (kw, kw))
        return cur.fetchall()

# ----------------- MEMBERS -----------------
def add_member(member_id, name, email=None):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM members WHERE member_id=%s", (member_id,))
        if cur.fetchone():
            return "Member already exists!"
        cur.execute("INSERT INTO members(member_id,name,email) VALUES(%s,%s,%s)", (member_id, name, email))
    return "Member added successfully!"

def fetch_all_members():
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT member_id, name, email, role FROM members ORDER BY name")
        return cur.fetchall()

def get_member(member_id):
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM members WHERE member_id=%s", (member_id,))
        return cur.fetchone()

# ----------------- LOANS -----------------
def borrow_book(member_id, isbn):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM members WHERE member_id=%s", (member_id,))
        if not cur.fetchone():
            return "Member not found!"
        cur.execute("SELECT COUNT(*) FROM loans WHERE member_id=%s AND date_returned IS NULL", (member_id,))
        if cur.fetchone()[0] >= 3:
            return "Borrow limit reached!"
        cur.execute("SELECT available_copies FROM books WHERE isbn=%s", (isbn,))
        r = cur.fetchone()
        if not r:
            return "Book not found!"
        if r[0] <= 0:
            return "No copies left!"
        cur.execute(
            "INSERT INTO loans(member_id,isbn,date_borrowed,due_date) VALUES(%s,%s,CURRENT_DATE,CURRENT_DATE+INTERVAL '7 day')",
            (member_id, isbn)
        )
    return "Book borrowed!"

def return_book(member_id, isbn):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT loan_id FROM loans WHERE member_id=%s AND isbn=%s AND date_returned IS NULL", (member_id, isbn))
        r = cur.fetchone()
        if not r:
            return "This book was not borrowed!"
        cur.execute("UPDATE loans SET date_returned=CURRENT_DATE WHERE loan_id=%s", (r[0],))
    return "Book returned!"

def borrowed_view():
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM borrowed_books ORDER BY due_date")
        return cur.fetchall()

def check_overdue():
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM check_overdue()")
        return cur.fetchall()

# ----------------- BOOK CLUBS -----------------
def get_club_members(club_id):
    with _get_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT m.member_id, m.name
            FROM members m JOIN member_clubs mc ON mc.member_id=m.member_id
            WHERE mc.club_id=%s
        """, (club_id,))
        return cur.fetchall()

def add_book_to_club(member_id, club_id):
    with _get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM members WHERE member_id=%s", (member_id,))
        if not cur.fetchone():
            return "Member not found!"
        cur.execute("SELECT 1 FROM book_clubs WHERE club_id=%s", (club_id,))
        if not cur.fetchone():
            return "Club not found!"
        cur.execute("SELECT 1 FROM member_clubs WHERE member_id=%s AND club_id=%s", (member_id, club_id))
        if cur.fetchone():
            return "Member already in club!"
        cur.execute("INSERT INTO member_clubs(member_id, club_id) VALUES(%s,%s)", (member_id, club_id))
    return "Member added to club!"

# ----------------- USER LOGIN -----------------
def verify_user(username, password):
    """Check username/password and return user info if valid (plain text)"""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, role FROM users WHERE username=%s AND password=%s",
                (username, password)  # plain text check
            )
            return cur.fetchone()  # None if invalid
