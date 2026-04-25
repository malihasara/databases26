from datetime import date
import bcrypt
from flask import Blueprint, jsonify, request

from auth import faculty_required
from db import execute, query, next_id


bp = Blueprint("admin_portal", __name__)


@bp.get("/overview")
@faculty_required
def overview():
    counts = query(
        """
        SELECT
          (SELECT COUNT(*) FROM User WHERE AccountStatus='Active')                AS users,
          (SELECT COUNT(*) FROM User WHERE AccountType='Faculty')                  AS faculty,
          (SELECT COUNT(*) FROM Club)                                              AS clubs,
          (SELECT COUNT(*) FROM Event WHERE EventStatus='Scheduled')               AS scheduled_events,
          (SELECT COUNT(*) FROM RSVP  WHERE RSVPStatus='Going')                    AS going_rsvps,
          (SELECT COUNT(*) FROM Attendance)                                        AS check_ins
        """,
        one=True,
    )
    clubs = query(
        """
        SELECT c.ClubID, c.ClubName, cat.CategoryName,
               (SELECT COUNT(*) FROM ClubMembership cm WHERE cm.ClubID=c.ClubID AND cm.MembershipStatus='Active') AS members,
               (SELECT COUNT(*) FROM Event e          WHERE e.ClubID=c.ClubID AND e.EventStatus='Scheduled')      AS events,
               (SELECT COUNT(*) FROM Attendance a JOIN Event e ON e.EventID=a.EventID WHERE e.ClubID=c.ClubID)    AS check_ins
        FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID
        ORDER BY c.ClubName
        """
    )
    return jsonify(counts=counts, clubs=clubs)


@bp.get("/users")
@faculty_required
def list_users():
    q = request.args.get("q", "").strip()
    sql = [
        "SELECT UserID, FirstName, LastName, Email, AccountType, AccountStatus, AccountCreationDate",
        "FROM User",
    ]
    params = []
    if q:
        sql.append("WHERE FirstName LIKE %s OR LastName LIKE %s OR Email LIKE %s")
        like = f"%{q}%"
        params.extend([like, like, like])
    sql.append("ORDER BY AccountType DESC, LastName")
    return jsonify(users=query(" ".join(sql), tuple(params)))


@bp.post("/users")
@faculty_required
def create_user():
    body = request.get_json(silent=True) or {}
    first = (body.get("first_name") or "").strip()
    last = (body.get("last_name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    account_type = body.get("account_type") or "Student"

    if not (first and last and email and len(password) >= 8):
        return jsonify(error="all fields required; password >= 8 chars"), 400
    if account_type not in ("Student", "Faculty"):
        return jsonify(error="invalid account_type"), 400
    if query("SELECT 1 FROM User WHERE Email = %s", (email,), one=True):
        return jsonify(error="email already registered"), 409

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_id = next_id("US", "User", "UserID")
    execute(
        "INSERT INTO User (UserID, FirstName, LastName, Email, PasswordHash, "
        "AccountCreationDate, AccountStatus, AccountType) VALUES (%s,%s,%s,%s,%s,%s,'Active',%s)",
        (new_id, first, last, email, pw_hash, date.today(), account_type),
    )
    return jsonify(ok=True, user_id=new_id)


@bp.get("/faculty-requests")
@faculty_required
def faculty_requests():
    rows = query(
        "SELECT UserID, FirstName, LastName, Email, FacultyRequestStatus, FacultyRequestTime "
        "FROM User WHERE FacultyRequestStatus = 'Pending' "
        "ORDER BY FacultyRequestTime"
    )
    return jsonify(requests=rows)


@bp.post("/faculty-requests/<user_id>/approve")
@faculty_required
def approve_faculty_request(user_id):
    row = query(
        "SELECT FacultyRequestStatus FROM User WHERE UserID = %s",
        (user_id,), one=True,
    )
    if not row or row["FacultyRequestStatus"] != "Pending":
        return jsonify(error="no pending request for this user"), 400
    execute(
        "UPDATE User SET AccountType = 'Faculty', FacultyRequestStatus = 'Approved' "
        "WHERE UserID = %s",
        (user_id,),
    )
    return jsonify(ok=True)


@bp.post("/faculty-requests/<user_id>/reject")
@faculty_required
def reject_faculty_request(user_id):
    execute(
        "UPDATE User SET FacultyRequestStatus = 'Rejected' "
        "WHERE UserID = %s AND FacultyRequestStatus = 'Pending'",
        (user_id,),
    )
    return jsonify(ok=True)


@bp.post("/users/<user_id>/account-type")
@faculty_required
def set_account_type(user_id):
    body = request.get_json(silent=True) or {}
    account_type = body.get("account_type")
    if account_type not in ("Student", "Faculty"):
        return jsonify(error="invalid account_type"), 400
    execute("UPDATE User SET AccountType = %s WHERE UserID = %s", (account_type, user_id))
    return jsonify(ok=True)


@bp.post("/users/<user_id>/status")
@faculty_required
def set_account_status(user_id):
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in ("Active", "Inactive"):
        return jsonify(error="invalid status"), 400
    execute("UPDATE User SET AccountStatus = %s WHERE UserID = %s", (status, user_id))
    return jsonify(ok=True)


@bp.get("/club-options")
@faculty_required
def club_options():
    categories = query("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName")
    owners = query(
        "SELECT UserID, FirstName, LastName, Email FROM User "
        "WHERE AccountStatus = 'Active' ORDER BY LastName, FirstName"
    )
    return jsonify(categories=categories, owners=owners)


@bp.post("/clubs")
@faculty_required
def create_club():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    desc = (body.get("description") or "").strip()
    category_id = body.get("category_id")
    owner_user_id = body.get("owner_user_id")
    if not (name and desc and category_id and owner_user_id):
        return jsonify(error="all fields required"), 400
    new_id = next_id("CL", "Club", "ClubID")
    try:
        from db import call_proc
        call_proc("sp_create_club_with_owner", (new_id, name, desc, category_id, owner_user_id))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True, club_id=new_id)


@bp.post("/clubs/<club_id>/delete")
@faculty_required
def delete_club(club_id):
    try:
        execute("DELETE a FROM Attendance a JOIN Event e ON e.EventID = a.EventID WHERE e.ClubID = %s", (club_id,))
        execute("DELETE r FROM RSVP r JOIN Event e ON e.EventID = r.EventID WHERE e.ClubID = %s", (club_id,))
        execute("DELETE FROM Event          WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM Announcement   WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM JoinRequest    WHERE ClubID = %s", (club_id,))
        execute("UPDATE ClubMembership SET MembershipRole = 'Member' WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM ClubMembership WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM Club           WHERE ClubID = %s", (club_id,))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.get("/attendance")
@faculty_required
def cross_club_attendance():
    rows = query(
        """
        SELECT e.EventID, e.EventTitle, e.EventStartTime, c.ClubName,
               (SELECT COUNT(*) FROM RSVP r WHERE r.EventID=e.EventID AND r.RSVPStatus='Going') AS going,
               (SELECT COUNT(*) FROM Attendance a WHERE a.EventID=e.EventID)                   AS attended,
               e.EventCapacity
        FROM Event e JOIN Club c ON c.ClubID = e.ClubID
        ORDER BY e.EventStartTime DESC
        LIMIT 100
        """
    )
    return jsonify(events=rows)
