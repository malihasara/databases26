"""
auth.py

Login/register/logout endpoints, session loading, role decorators
(login_required, admin_required, officer_required), and the 5-year inactive
account sweep.
"""

from functools import wraps
from datetime import date
import bcrypt
from flask import Blueprint, g, jsonify, request, session

from db import query, execute, next_id


bp = Blueprint("auth", __name__)

ACCOUNT_MAX_AGE_DAYS = 365 * 5


def deactivate_if_expired(user_id: str) -> None:
    execute(
        "UPDATE User SET AccountStatus = 'Inactive' "
        "WHERE UserID = %s AND AccountStatus = 'Active' "
        "AND DATEDIFF(CURDATE(), AccountCreationDate) > %s",
        (user_id, ACCOUNT_MAX_AGE_DAYS),
    )


@bp.before_app_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if not user_id:
        return
    deactivate_if_expired(user_id)
    g.user = query(
        "SELECT UserID, FirstName, LastName, Email, AccountType "
        "FROM User WHERE UserID = %s AND AccountStatus = 'Active'",
        (user_id,), one=True,
    )
    if not g.user:
        session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return jsonify(error="auth required"), 401
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return jsonify(error="auth required"), 401
        if g.user.get("AccountType") != "Admin":
            return jsonify(error="admin access required"), 403
        return view(*args, **kwargs)
    return wrapped


def officer_required(club_id_param="club_id"):
    """Allow President / VicePresident / Officer of the club, or any Admin."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user.get("AccountType") == "Admin":
                return view(*args, **kwargs)
            club_id = kwargs.get(club_id_param)
            row = query(
                "SELECT MembershipRole FROM ClubMembership "
                "WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active'",
                (club_id, g.user["UserID"]), one=True,
            )
            if not row or row["MembershipRole"] not in ("President", "VicePresident", "Officer"):
                return jsonify(error="officer access required"), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def role_in_club(user_id, club_id):
    row = query(
        "SELECT MembershipRole FROM ClubMembership "
        "WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active'",
        (club_id, user_id), one=True,
    )
    return row["MembershipRole"] if row else None


@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    role = body.get("role") or ""
    row = query(
        "SELECT UserID, FirstName, LastName, Email, AccountType, PasswordHash, AccountCreationDate "
        "FROM User WHERE Email = %s AND AccountStatus = 'Active'",
        (email,), one=True,
    )
    if not row or not bcrypt.checkpw(password.encode(), row["PasswordHash"].encode()):
        return jsonify(error="invalid email or password"), 401

    deactivate_if_expired(row["UserID"])
    fresh = query("SELECT AccountStatus FROM User WHERE UserID = %s", (row["UserID"],), one=True)
    if not fresh or fresh["AccountStatus"] != "Active":
        return jsonify(error="account is inactive (over 5 years old). Contact an admin."), 403

    if role and role != row["AccountType"]:
        return jsonify(error=f"this account is not a {role} account"), 403
    session.clear()
    session["user_id"] = row["UserID"]
    return jsonify(user={k: row[k] for k in ("UserID", "FirstName", "LastName", "Email", "AccountType")})


@bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    first = (body.get("first_name") or "").strip()
    last = (body.get("last_name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    requested = body.get("requested_account_type") or "Student"
    if requested not in ("Student", "Admin"):
        return jsonify(error="invalid requested_account_type"), 400
    if not (first and last and email and len(password) >= 8):
        return jsonify(error="all fields required; password >= 8 chars"), 400
    if query("SELECT 1 FROM User WHERE Email = %s", (email,), one=True):
        return jsonify(error="email already registered"), 409
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_id = next_id("US", "User", "UserID")
    if requested == "Admin":
        execute(
            "INSERT INTO User (UserID, FirstName, LastName, Email, PasswordHash, "
            "AccountCreationDate, AccountStatus, AccountType, AdminRequestStatus, AdminRequestTime) "
            "VALUES (%s,%s,%s,%s,%s,%s,'Active','Student','Pending', NOW())",
            (new_id, first, last, email, pw_hash, date.today()),
        )
    else:
        execute(
            "INSERT INTO User (UserID, FirstName, LastName, Email, PasswordHash, "
            "AccountCreationDate, AccountStatus, AccountType) "
            "VALUES (%s,%s,%s,%s,%s,%s,'Active','Student')",
            (new_id, first, last, email, pw_hash, date.today()),
        )
    session.clear()
    session["user_id"] = new_id
    return jsonify(
        user=dict(UserID=new_id, FirstName=first, LastName=last, Email=email, AccountType="Student"),
        admin_request_pending=(requested == "Admin"),
    )


@bp.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@bp.get("/me")
def me():
    return jsonify(user=g.user)
