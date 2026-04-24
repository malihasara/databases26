from functools import wraps
from datetime import date
import bcrypt
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from db import query, execute, next_id


bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        g.user = query(
            "SELECT UserID, FirstName, LastName, Email FROM User WHERE UserID = %s",
            (user_id,),
            one=True,
        )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def officer_required(club_id_param="club_id"):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            club_id = kwargs.get(club_id_param)
            row = query(
                "SELECT MembershipRole FROM ClubMembership "
                "WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active'",
                (club_id, g.user["UserID"]),
                one=True,
            )
            if not row or row["MembershipRole"] not in ("Owner", "Officer"):
                flash("Officer access required.", "error")
                return redirect(url_for("clubs.detail", club_id=club_id))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        row = query(
            "SELECT UserID, PasswordHash FROM User WHERE Email = %s AND AccountStatus = 'Active'",
            (email,),
            one=True,
        )
        if row and bcrypt.checkpw(password.encode(), row["PasswordHash"].encode()):
            session.clear()
            session["user_id"] = row["UserID"]
            return redirect(request.args.get("next") or url_for("my_clubs.index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not (first and last and email and password):
            flash("All fields are required.", "error")
        elif query("SELECT 1 FROM User WHERE Email = %s", (email,), one=True):
            flash("Email is already registered.", "error")
        else:
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            new_id = next_id("US", "User", "UserID")
            execute(
                "INSERT INTO User (UserID, FirstName, LastName, Email, PasswordHash, "
                "AccountCreationDate, AccountStatus) VALUES (%s,%s,%s,%s,%s,%s,'Active')",
                (new_id, first, last, email, pw_hash, date.today()),
            )
            session.clear()
            session["user_id"] = new_id
            return redirect(url_for("my_clubs.index"))
    return render_template("register.html")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
