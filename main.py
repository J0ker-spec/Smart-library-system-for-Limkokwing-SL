import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox,
    QStackedWidget, QFormLayout, QSpinBox
)
import db  # your simplified db.py

# ---------------- Login Page ----------------
class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        layout = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.Password)
        layout.addRow("Username", self.username)
        layout.addRow("Password", self.password)
        btn = QPushButton("Login"); btn.clicked.connect(self.login)
        layout.addRow(btn)
        self.setLayout(layout)

    def login(self):
        username, password = self.username.text(), self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Enter both username and password")
            return
        try:
            user = db.verify_user(username, password)  # plain text check
            if user:
                self.on_login_success(user)
            else:
                QMessageBox.critical(self, "Error", "Invalid credentials")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# ---------------- Pages ----------------
class AddBookPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.isbn = QLineEdit()
        self.title = QLineEdit()
        self.author = QLineEdit()
        self.copies = QSpinBox(); self.copies.setMinimum(1); self.copies.setMaximum(999)
        layout.addRow("ISBN", self.isbn)
        layout.addRow("Title", self.title)
        layout.addRow("Author", self.author)
        layout.addRow("Copies", self.copies)
        btn = QPushButton("Add Book"); btn.clicked.connect(self.add_book)
        layout.addRow(btn)
        self.setLayout(layout)

    def add_book(self):
        isbn, title, author, copies = self.isbn.text(), self.title.text(), self.author.text(), self.copies.value()
        if not isbn or not title or not author:
            QMessageBox.warning(self, "Error", "Fill all fields"); return
        try:
            msg = db.add_book(isbn, title, author, "Unknown", copies)
            QMessageBox.information(self, "Success", str(msg))
            self.isbn.clear(); self.title.clear(); self.author.clear(); self.copies.setValue(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class ShowBooksPage(QWidget):
    def __init__(self, table):
        super().__init__()
        self.table = table
        layout = QVBoxLayout()
        btn = QPushButton("Refresh"); btn.clicked.connect(self.refresh)
        layout.addWidget(btn)
        self.setLayout(layout)

    def refresh(self):
        try:
            rows = db.get_all_books()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e)); return
        if not rows:
            self.table.setRowCount(0); return
        cols = ["isbn","title","author","total_copies","available_copies"]
        self.table.setColumnCount(len(cols)); self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(0)
        for r in rows:
            idx = self.table.rowCount(); self.table.insertRow(idx)
            for c, col in enumerate(cols):
                self.table.setItem(idx, c, QTableWidgetItem(str(r.get(col, ""))))

class AddMemberPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.member_id = QLineEdit(); self.name = QLineEdit(); self.email = QLineEdit()
        layout.addRow("ID", self.member_id); layout.addRow("Name", self.name); layout.addRow("Email", self.email)
        btn = QPushButton("Add Member"); btn.clicked.connect(self.add_member)
        layout.addRow(btn); self.setLayout(layout)

    def add_member(self):
        mid, name, email = self.member_id.text(), self.name.text(), self.email.text()
        if not mid or not name:
            QMessageBox.warning(self, "Error", "ID and Name required"); return
        try:
            msg = db.add_member(mid, name, email or None)
            QMessageBox.information(self, "Success", str(msg))
            self.member_id.clear(); self.name.clear(); self.email.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class ShowMembersPage(QWidget):
    def __init__(self, table):
        super().__init__()
        self.table = table
        layout = QVBoxLayout()
        btn = QPushButton("Refresh"); btn.clicked.connect(self.refresh)
        layout.addWidget(btn)
        self.setLayout(layout)

    def refresh(self):
        try:
            rows = db.fetch_all_members()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e)); return
        if not rows:
            self.table.setRowCount(0); return
        cols = ["member_id","name","email","role"]
        self.table.setColumnCount(len(cols)); self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(0)
        for r in rows:
            idx = self.table.rowCount(); self.table.insertRow(idx)
            for c, col in enumerate(cols):
                self.table.setItem(idx, c, QTableWidgetItem(str(r.get(col, ""))))

# ---------------- Main Window ----------------
class MainWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"SmartLibrary - Logged in as {user['username']}")
        self.resize(900, 500)
        root = QHBoxLayout(); self.setLayout(root)

        # Sidebar
        sidebar = QVBoxLayout()
        for text, page in [("Add Book","add_book"),("Show Books","show_books"),
                           ("Add Member","add_member"),("Show Members","show_members")]:
            btn = QPushButton(text); btn.clicked.connect(lambda _, p=page: self.switch_to(p))
            sidebar.addWidget(btn)
        sidebar.addStretch(1)
        root.addLayout(sidebar, 1)

        # Main area
        self.table = QTableWidget(); self.table.setEditTriggers(self.table.NoEditTriggers)
        self.stack = QStackedWidget()
        self.pages = {
            "add_book": AddBookPage(),
            "show_books": ShowBooksPage(self.table),
            "add_member": AddMemberPage(),
            "show_members": ShowMembersPage(self.table)
        }
        for p in self.pages.values(): self.stack.addWidget(p)
        main_layout = QVBoxLayout(); main_layout.addWidget(self.stack); main_layout.addWidget(self.table, 2)
        root.addLayout(main_layout, 3)

        self.switch_to("show_books")

    def switch_to(self, page_key):
        page = self.pages.get(page_key)
        if page:
            self.stack.setCurrentWidget(page)
            if hasattr(page, "refresh"):
                try: page.refresh()
                except: pass

# ---------------- App ----------------
def main():
    app = QApplication(sys.argv)

    def start_main(user):
        main_win = MainWindow(user)
        main_win.show()
        login_win.close()

    login_win = LoginPage(on_login_success=start_main)
    login_win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
