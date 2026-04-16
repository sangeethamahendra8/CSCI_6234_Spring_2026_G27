"""Domain models for the library student demo (7 use cases)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Member(db.Model):
    __tablename__ = "member"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    loans = db.relationship("Loan", backref="member", lazy=True)
    reservations = db.relationship("Reservation", backref="member", lazy=True)
    fines = db.relationship("Fine", backref="member", lazy=True)
    payments = db.relationship("Payment", backref="member", lazy=True)


class Librarian(db.Model):
    __tablename__ = "librarian"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)


class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20))

    copies = db.relationship("BookCopy", backref="book", lazy=True, cascade="all, delete-orphan")
    reservations = db.relationship("Reservation", backref="book", lazy=True)


class BookCopy(db.Model):
    __tablename__ = "book_copy"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    copy_code = db.Column(db.String(50), unique=True, nullable=False)


class Loan(db.Model):
    __tablename__ = "loan"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    book_copy_id = db.Column(db.Integer, db.ForeignKey("book_copy.id"), nullable=False)
    checkout_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    returned_at = db.Column(db.Date)
    renewal_count = db.Column(db.Integer, default=0)

    book_copy = db.relationship("BookCopy", backref="loans", lazy=True)
    fines = db.relationship("Fine", backref="loan", lazy=True)


class Reservation(db.Model):
    __tablename__ = "reservation"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    placed_at = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")


class Fine(db.Model):
    __tablename__ = "fine"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"))
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(200))
    is_paid = db.Column(db.Boolean, default=False)

    payments = db.relationship("Payment", backref="fine", lazy=True)


class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    fine_id = db.Column(db.Integer, db.ForeignKey("fine.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.Date, nullable=False)


def loan_is_active(loan):
    return loan.returned_at is None


def copy_is_available(copy_id):
    active = Loan.query.filter_by(book_copy_id=copy_id, returned_at=None).first()
    return active is None


def available_copies_for_book(book_id):
    copies = BookCopy.query.filter_by(book_id=book_id).all()
    return [c for c in copies if copy_is_available(c.id)]
