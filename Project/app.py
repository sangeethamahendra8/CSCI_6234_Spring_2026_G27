"""
Student library demo — 7 use cases, SQLite, basic member login.
"""
from datetime import date, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import (
    Book,
    BookCopy,
    Fine,
    Librarian,
    Loan,
    Member,
    Payment,
    Reservation,
    available_copies_for_book,
    db,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "student-demo-secret-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library_demo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

LOAN_DAYS = 14
EXTEND_DAYS = 7
MAX_RENEWALS = 1
OVERDUE_FINE_PER_DAY = 0.5
DEMO_PASSWORD = "demo123"

# Flask endpoint names = exact use case titles (for url_for).
UC_BROWSE_BOOKS = "Browse Books"
UC_REQUEST_BORROW = "Request Borrow"
UC_RETURN_ITEM = "Return Item"
UC_EXTEND_LOAN = "Extend Loan"
UC_PLACE_HOLD = "Place Hold"
UC_PAY_FINE = "Pay Fine"
UC_VIEW_ACCOUNT = "View Account"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "member_id" not in session:
            flash("Please log in.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_member():
    return Member.query.get(session["member_id"])


def seed_sample_data():
    if Member.query.first():
        return

    lib = Librarian(name="Pat Johnson", username="pjohnson")
    db.session.add(lib)

    m1 = Member(name="Sangeetha", email="sangeetha.mahendra@gwu.edu", password=DEMO_PASSWORD)
    m2 = Member(name="Bob Student", email="bob@campus.edu", password=DEMO_PASSWORD)
    db.session.add_all([m1, m2])
    db.session.flush()

    books_data = [
        ("Python Basics", "S. Lee", "978-111"),
        ("Data Structures 101", "M. Chen", "978-222"),
        ("Web Apps with Flask", "J. Rivera", "978-333"),
    ]
    books = []
    for title, author, isbn in books_data:
        b = Book(title=title, author=author, isbn=isbn)
        db.session.add(b)
        books.append(b)
    db.session.flush()

    copy_id = 0
    for b in books:
        for i in range(2):
            copy_id += 1
            code = f"{b.id}-{chr(65 + i)}"
            db.session.add(BookCopy(book_id=b.id, copy_code=code))

    db.session.flush()

    copies = BookCopy.query.all()
    c_m1 = copies[0]
    c_bob = copies[2]

    today = date.today()
    loan_m1 = Loan(
        member_id=m1.id,
        book_copy_id=c_m1.id,
        checkout_date=today - timedelta(days=10),
        due_date=today + timedelta(days=4),
        returned_at=None,
        renewal_count=0,
    )
    loan_bob = Loan(
        member_id=m2.id,
        book_copy_id=c_bob.id,
        checkout_date=today - timedelta(days=20),
        due_date=today - timedelta(days=5),
        returned_at=None,
        renewal_count=1,
    )
    db.session.add_all([loan_m1, loan_bob])
    db.session.flush()

    fine = Fine(
        member_id=m2.id,
        loan_id=loan_bob.id,
        amount=3.50,
        reason="Small processing fee (sample)",
        is_paid=False,
    )
    db.session.add(fine)

    db.session.add(
        Reservation(member_id=m1.id, book_id=books[2].id, placed_at=today - timedelta(days=1), status="active")
    )

    db.session.commit()


def sync_demo_accounts():
    """Fix older databases that still use the previous primary demo email."""
    legacy = Member.query.filter(
        func.lower(Member.email) == "alice@campus.edu"
    ).first()
    if legacy:
        legacy.email = "sangeetha.mahendra@gwu.edu"
        legacy.name = "Sangeetha"
        legacy.password = DEMO_PASSWORD
        db.session.commit()


@app.route("/")
def home():
    if "member_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        key = login_id.lower()
        member = Member.query.filter(func.lower(Member.email) == key).first()
        if not member and "@" not in key:
            member = Member.query.filter(func.lower(Member.name) == key).first()
        if member and member.password == password:
            session["member_id"] = member.id
            flash(f"Welcome, {member.name}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("member_id", None)
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    member = current_member()
    today = date.today()
    loan_list = Loan.query.filter_by(member_id=member.id, returned_at=None).all()
    active_loans = len(loan_list)
    overdue_loans = sum(1 for ln in loan_list if ln.due_date < today)
    extendable_loans = sum(
        1
        for ln in loan_list
        if ln.due_date >= today and ln.renewal_count < MAX_RENEWALS
    )
    holds = Reservation.query.filter_by(member_id=member.id, status="active").count()
    owed = (
        db.session.query(func.sum(Fine.amount))
        .filter(Fine.member_id == member.id, Fine.is_paid.is_(False))
        .scalar()
    )
    unpaid_total = float(owed or 0)
    unpaid_fine_count = Fine.query.filter_by(member_id=member.id, is_paid=False).count()
    all_books = Book.query.all()
    titles_with_available_copy = sum(1 for b in all_books if available_copies_for_book(b.id))
    total_titles = len(all_books)
    can_borrow_now = any(available_copies_for_book(b.id) for b in all_books)

    return render_template(
        "dashboard.html",
        member=member,
        today=today,
        active_loans=active_loans,
        overdue_loans=overdue_loans,
        extendable_loans=extendable_loans,
        holds=holds,
        unpaid_total=unpaid_total,
        unpaid_fine_count=unpaid_fine_count,
        titles_with_available_copy=titles_with_available_copy,
        total_titles=total_titles,
        can_borrow_now=can_borrow_now,
    )


@app.route("/browse-books", methods=["GET", "POST"], endpoint=UC_BROWSE_BOOKS)
@login_required
def Browse_Books():
    q_title = (request.form.get("title") or request.args.get("title") or "").strip()
    q_author = (request.form.get("author") or request.args.get("author") or "").strip()

    query = Book.query
    if q_title:
        query = query.filter(Book.title.ilike(f"%{q_title}%"))
    if q_author:
        query = query.filter(Book.author.ilike(f"%{q_author}%"))

    books = query.order_by(Book.title).all()
    rows = []
    for b in books:
        avail = len(available_copies_for_book(b.id))
        rows.append({"book": b, "available": avail, "total": len(b.copies)})

    return render_template("browse_books.html", rows=rows, q_title=q_title, q_author=q_author)


@app.route("/request-borrow", methods=["GET", "POST"], endpoint=UC_REQUEST_BORROW)
@login_required
def Request_Borrow():
    member = current_member()
    if request.method == "POST":
        book_id = request.form.get("book_id", type=int)
        book = Book.query.get(book_id)
        if not book:
            flash("Book not found.", "error")
            return redirect(url_for(UC_REQUEST_BORROW))

        candidates = available_copies_for_book(book.id)
        if not candidates:
            flash("No copy is available right now. Try placing a hold.", "error")
            return redirect(url_for(UC_REQUEST_BORROW))

        copy = candidates[0]
        today = date.today()
        loan = Loan(
            member_id=member.id,
            book_copy_id=copy.id,
            checkout_date=today,
            due_date=today + timedelta(days=LOAN_DAYS),
            returned_at=None,
            renewal_count=0,
        )
        db.session.add(loan)
        db.session.commit()
        flash(f"Borrowed “{book.title}” (copy {copy.copy_code}). Due {loan.due_date}.", "success")
        return redirect(url_for("dashboard"))

    preselect_book_id = request.args.get("book_id", type=int)
    books = Book.query.order_by(Book.title).all()
    options = []
    for b in books:
        n = len(available_copies_for_book(b.id))
        options.append({"book": b, "available": n})
    can_borrow = any(o["available"] > 0 for o in options)
    return render_template(
        "request_borrow.html",
        options=options,
        can_borrow=can_borrow,
        preselect_book_id=preselect_book_id,
    )


@app.route("/return-item", methods=["GET", "POST"], endpoint=UC_RETURN_ITEM)
@login_required
def Return_Item():
    member = current_member()
    loans = (
        Loan.query.filter_by(member_id=member.id, returned_at=None)
        .join(BookCopy)
        .join(Book)
        .order_by(Loan.due_date)
        .all()
    )

    if request.method == "POST":
        loan_id = request.form.get("loan_id", type=int)
        loan = Loan.query.filter_by(id=loan_id, member_id=member.id, returned_at=None).first()
        if not loan:
            flash("That loan was not found or already returned.", "error")
            return redirect(url_for(UC_RETURN_ITEM))

        today = date.today()
        loan.returned_at = today
        if loan.due_date < today:
            days_late = (today - loan.due_date).days
            amt = round(days_late * OVERDUE_FINE_PER_DAY, 2)
            if amt > 0:
                db.session.add(
                    Fine(
                        member_id=member.id,
                        loan_id=loan.id,
                        amount=amt,
                        reason=f"Overdue return ({days_late} day(s))",
                        is_paid=False,
                    )
                )
                flash(f"Returned. Overdue fine: ${amt:.2f}", "success")
            else:
                flash("Returned successfully.", "success")
        else:
            flash("Returned on time. Thank you!", "success")

        db.session.commit()
        return redirect(url_for("dashboard"))

    enriched = []
    for ln in loans:
        enriched.append({"loan": ln, "book": ln.book_copy.book})

    return render_template("return_item.html", items=enriched)


@app.route("/extend-loan", methods=["GET", "POST"], endpoint=UC_EXTEND_LOAN)
@login_required
def Extend_Loan():
    member = current_member()
    loans = Loan.query.filter_by(member_id=member.id, returned_at=None).order_by(Loan.due_date).all()

    if request.method == "POST":
        loan_id = request.form.get("loan_id", type=int)
        loan = Loan.query.filter_by(id=loan_id, member_id=member.id, returned_at=None).first()
        if not loan:
            flash("Loan not found.", "error")
            return redirect(url_for(UC_EXTEND_LOAN))

        if loan.renewal_count >= MAX_RENEWALS:
            flash("Maximum renewals already used for this loan.", "error")
            return redirect(url_for(UC_EXTEND_LOAN))

        if loan.due_date < date.today():
            flash("Cannot renew an overdue loan. Please return the item.", "error")
            return redirect(url_for(UC_EXTEND_LOAN))

        loan.due_date = loan.due_date + timedelta(days=EXTEND_DAYS)
        loan.renewal_count = loan.renewal_count + 1
        db.session.commit()
        flash(f"Loan extended. New due date: {loan.due_date}.", "success")
        return redirect(url_for("dashboard"))

    items = [{"loan": ln, "book": ln.book_copy.book} for ln in loans]
    return render_template("extend_loan.html", items=items, max_renewals=MAX_RENEWALS, extend_days=EXTEND_DAYS)


@app.route("/place-hold", methods=["GET", "POST"], endpoint=UC_PLACE_HOLD)
@login_required
def Place_Hold():
    member = current_member()
    books = Book.query.order_by(Book.title).all()

    if request.method == "POST":
        book_id = request.form.get("book_id", type=int)
        book = Book.query.get(book_id)
        if not book:
            flash("Book not found.", "error")
            return redirect(url_for(UC_PLACE_HOLD))

        existing = Reservation.query.filter_by(
            member_id=member.id, book_id=book.id, status="active"
        ).first()
        if existing:
            flash("You already have an active hold on that title.", "error")
            return redirect(url_for(UC_PLACE_HOLD))

        db.session.add(
            Reservation(member_id=member.id, book_id=book.id, placed_at=date.today(), status="active")
        )
        db.session.commit()
        flash(f"Hold placed on “{book.title}”.", "success")
        return redirect(url_for("dashboard"))

    preselect_book_id = request.args.get("book_id", type=int)
    return render_template("place_hold.html", books=books, preselect_book_id=preselect_book_id)


@app.route("/pay-fine", methods=["GET", "POST"], endpoint=UC_PAY_FINE)
@login_required
def Pay_Fine():
    member = current_member()
    unpaid = Fine.query.filter_by(member_id=member.id, is_paid=False).order_by(Fine.id).all()

    if request.method == "POST":
        fine_id = request.form.get("fine_id", type=int)
        fine = Fine.query.filter_by(id=fine_id, member_id=member.id, is_paid=False).first()
        if not fine:
            flash("Fine not found or already paid.", "error")
            return redirect(url_for(UC_PAY_FINE))

        fine.is_paid = True
        db.session.add(
            Payment(
                member_id=member.id,
                fine_id=fine.id,
                amount=fine.amount,
                paid_at=date.today(),
            )
        )
        db.session.commit()
        flash(f"Paid ${fine.amount:.2f}. Thank you!", "success")
        return redirect(url_for("dashboard"))

    return render_template("pay_fine.html", fines=unpaid)


@app.route("/view-account", endpoint=UC_VIEW_ACCOUNT)
@login_required
def View_Account():
    member = current_member()

    active_loans = (
        Loan.query.filter_by(member_id=member.id, returned_at=None)
        .join(BookCopy)
        .join(Book)
        .order_by(Loan.due_date)
        .all()
    )
    loan_rows = [{"loan": ln, "book": ln.book_copy.book, "copy": ln.book_copy} for ln in active_loans]

    holds = (
        Reservation.query.filter_by(member_id=member.id, status="active")
        .join(Book)
        .order_by(Reservation.placed_at.desc())
        .all()
    )
    hold_rows = [{"res": r, "book": r.book} for r in holds]

    open_fines = Fine.query.filter_by(member_id=member.id, is_paid=False).all()

    return render_template(
        "view_account.html",
        member=member,
        loan_rows=loan_rows,
        hold_rows=hold_rows,
        open_fines=open_fines,
    )


with app.app_context():
    db.create_all()
    seed_sample_data()
    sync_demo_accounts()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
