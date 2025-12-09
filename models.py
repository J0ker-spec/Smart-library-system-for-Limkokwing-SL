# models.py
from datetime import date, timedelta

class Book:
    def __init__(self, isbn, title, author, genre, total_copies, available_copies=None):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.genre = genre
        self.total_copies = int(total_copies)
        self.available_copies = int(available_copies) if available_copies is not None else int(total_copies)

    def is_available(self):
        return self.available_copies > 0


class Member:
    def __init__(self, member_id, name, email=None, role='member'):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.role = role
        self.borrowed_books = []  # can hold Book objects

    def can_borrow(self):
        return len(self.borrowed_books) < 3


class Loan:
    def __init__(self, loan_id, member_id, isbn, date_borrowed, due_date, date_returned=None):
        self.loan_id = loan_id
        self.member_id = member_id
        self.isbn = isbn
        self.date_borrowed = date_borrowed
        self.due_date = due_date
        self.date_returned = date_returned

    def is_overdue(self):
        return self.date_returned is None and self.due_date < date.today()


class BookClub:
    def __init__(self, club_id, club_name, description=None):
        self.club_id = club_id
        self.club_name = club_name
        self.description = description
        self.members = []  #  list of Member objects


class User:
    def __init__(self, user_id, username, password, member_ref=None, role='member'):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.member_ref = member_ref  # links to Member if exists
        self.role = role
