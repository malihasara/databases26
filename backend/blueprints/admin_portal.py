"""
admin_portal.py

Platform-wide admin endpoints: overview counts, user/admin management,
admin-access requests, club CRUD with multi-category support, and
student-initiated club creation request approvals.
"""

from datetime import date
import bcrypt
from flask import Blueprint, jsonify, request

from auth import admin_required
from db import call_proc, execute, query, next_id


bp = Blueprint("admin_portal", __name__)


@bp.get("/overview")
@admin_required
def overview():
    counts = query(
        """
        SELECT
          (SELECT COUNT(*) FROM User WHERE AccountStatus='Active')                AS users,
          (SELECT COUNT(*) FROM User WHERE AccountType='Admin')                    AS admins,
          (SELECT COUNT(*) FROM Club)                                              AS clubs,
          (SELECT COUNT(*) FROM Event WHERE EventStatus='Scheduled')               AS scheduled_events,
          (SELECT COUNT(*) FROM RSVP  WHERE RSVPStatus='Going')                    AS going_rsvps,
          (SELECT COUNT(*) FROM Attendance)                                        AS check_ins
        """,
        one=True,
    )
    clubs = query(
        """
        SELECT c.ClubID, c.ClubName,
               GROUP_CONCAT(DISTINCT cat.CategoryName ORDER BY cat.CategoryName SEPARATOR ', ') AS Categories,
               (SELECT COUNT(*) FROM ClubMembership cm WHERE cm.ClubID=c.ClubID AND cm.MembershipStatus='Active') AS members,
               (SELECT COUNT(*) FROM Event e          WHERE e.ClubID=c.ClubID AND e.EventStatus='Scheduled')      AS events,
               (SELECT COUNT(*) FROM Attendance a JOIN Event e ON e.EventID=a.EventID WHERE e.ClubID=c.ClubID)    AS check_ins
        FROM Club c
        LEFT JOIN ClubCategory cc ON cc.ClubID = c.ClubID
        LEFT JOIN Category cat   ON cat.CategoryID = cc.CategoryID
        GROUP BY c.ClubID, c.ClubName
        ORDER BY c.ClubName
        """
    )
    return jsonify(counts=counts, clubs=clubs)


@bp.get("/users")
@admin_required
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


@bp.get("/admin-requests")
@admin_required
def admin_requests():
    rows = query(
        "SELECT UserID, FirstName, LastName, Email, AdminRequestStatus, AdminRequestTime "
        "FROM User WHERE AdminRequestStatus = 'Pending' ORDER BY AdminRequestTime"
    )
    return jsonify(requests=rows)


@bp.post("/admin-requests/<user_id>/approve")
@admin_required
def approve_admin_request(user_id):
    row = query("SELECT AdminRequestStatus FROM User WHERE UserID = %s", (user_id,), one=True)
    if not row or row["AdminRequestStatus"] != "Pending":
        return jsonify(error="no pending request for this user"), 400
    execute(
        "UPDATE User SET AccountType = 'Admin', AdminRequestStatus = 'Approved' WHERE UserID = %s",
        (user_id,),
    )
    return jsonify(ok=True)


@bp.post("/admin-requests/<user_id>/reject")
@admin_required
def reject_admin_request(user_id):
    execute(
        "UPDATE User SET AdminRequestStatus = 'Rejected' "
        "WHERE UserID = %s AND AdminRequestStatus = 'Pending'",
        (user_id,),
    )
    return jsonify(ok=True)


@bp.post("/users/<user_id>/account-type")
@admin_required
def set_account_type(user_id):
    body = request.get_json(silent=True) or {}
    account_type = body.get("account_type")
    if account_type not in ("Student", "Admin"):
        return jsonify(error="invalid account_type"), 400
    execute("UPDATE User SET AccountType = %s WHERE UserID = %s", (account_type, user_id))
    return jsonify(ok=True)


@bp.post("/users/<user_id>/status")
@admin_required
def set_account_status(user_id):
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    if status not in ("Active", "Inactive"):
        return jsonify(error="invalid status"), 400
    execute("UPDATE User SET AccountStatus = %s WHERE UserID = %s", (status, user_id))
    return jsonify(ok=True)


@bp.get("/club-options")
@admin_required
def club_options():
    categories = query("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName")
    owners = query(
        "SELECT UserID, FirstName, LastName, Email FROM User "
        "WHERE AccountStatus = 'Active' AND AccountType = 'Student' "
        "ORDER BY LastName, FirstName"
    )
    return jsonify(categories=categories, owners=owners)


@bp.post("/clubs")
@admin_required
def create_club():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    desc = (body.get("description") or "").strip()
    category_ids = body.get("category_ids") or ([body["category_id"]] if body.get("category_id") else [])
    officer_user_id = body.get("officer_user_id") or body.get("owner_user_id")
    if not (name and desc and category_ids and officer_user_id):
        return jsonify(error="all fields required (including >=1 category)"), 400
    new_id = next_id("CL", "Club", "ClubID")
    try:
        call_proc("sp_create_club_with_officer", (new_id, name, desc, officer_user_id))
        for cid in category_ids:
            execute("INSERT INTO ClubCategory (ClubID, CategoryID) VALUES (%s, %s)", (new_id, cid))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True, club_id=new_id)


@bp.post("/clubs/<club_id>/delete")
@admin_required
def delete_club(club_id):
    try:
        execute("DELETE a FROM Attendance a JOIN Event e ON e.EventID = a.EventID WHERE e.ClubID = %s", (club_id,))
        execute("DELETE r FROM RSVP r JOIN Event e ON e.EventID = r.EventID WHERE e.ClubID = %s", (club_id,))
        execute("DELETE FROM Event              WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM Announcement       WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM JoinRequest        WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM MemberActionRequest WHERE ClubID = %s", (club_id,))
        execute("UPDATE ClubMembership SET MembershipRole = 'Member' WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM ClubMembership    WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM ClubCategory      WHERE ClubID = %s", (club_id,))
        execute("DELETE FROM Club              WHERE ClubID = %s", (club_id,))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.get("/club-requests")
@admin_required
def list_club_requests():
    rows = query(
        """
        SELECT ccr.RequestID, ccr.ProposedName, ccr.ProposedDescription, ccr.RequestStatus,
               ccr.RequestTime, ccr.ResolvedTime,
               r.UserID  AS RequesterUserID, r.FirstName  AS RequesterFirstName, r.LastName  AS RequesterLastName, r.Email AS RequesterEmail,
               o.UserID  AS OfficerUserID,   o.FirstName  AS OfficerFirstName,   o.LastName  AS OfficerLastName,   o.Email AS OfficerEmail,
               GROUP_CONCAT(DISTINCT cat.CategoryName ORDER BY cat.CategoryName SEPARATOR ', ') AS Categories
        FROM ClubCreationRequest ccr
        JOIN User r ON r.UserID = ccr.RequestedByUserID
        JOIN User o ON o.UserID = ccr.ProposedOfficerUserID
        LEFT JOIN ClubCreationRequestCategory ccrc ON ccrc.RequestID = ccr.RequestID
        LEFT JOIN Category cat                    ON cat.CategoryID = ccrc.CategoryID
        WHERE ccr.RequestStatus = 'Pending'
        GROUP BY ccr.RequestID, ccr.ProposedName, ccr.ProposedDescription, ccr.RequestStatus,
                 ccr.RequestTime, ccr.ResolvedTime,
                 r.UserID, r.FirstName, r.LastName, r.Email,
                 o.UserID, o.FirstName, o.LastName, o.Email
        ORDER BY ccr.RequestTime
        """
    )
    return jsonify(requests=rows)


@bp.post("/club-requests/<request_id>/approve")
@admin_required
def approve_club_request(request_id):
    req = query(
        "SELECT ProposedName, ProposedDescription, ProposedOfficerUserID, RequestStatus "
        "FROM ClubCreationRequest WHERE RequestID = %s",
        (request_id,), one=True,
    )
    if not req or req["RequestStatus"] != "Pending":
        return jsonify(error="request not pending"), 400
    cats = query(
        "SELECT CategoryID FROM ClubCreationRequestCategory WHERE RequestID = %s",
        (request_id,),
    )
    if not cats:
        return jsonify(error="request has no categories"), 400
    if query("SELECT 1 FROM Club WHERE ClubName = %s", (req["ProposedName"],), one=True):
        return jsonify(error="a club with that name already exists"), 409

    new_id = next_id("CL", "Club", "ClubID")
    try:
        call_proc("sp_create_club_with_officer",
                  (new_id, req["ProposedName"], req["ProposedDescription"], req["ProposedOfficerUserID"]))
        for c in cats:
            execute("INSERT INTO ClubCategory (ClubID, CategoryID) VALUES (%s, %s)",
                    (new_id, c["CategoryID"]))
        execute(
            "UPDATE ClubCreationRequest SET RequestStatus = 'Approved', ResolvedTime = NOW() "
            "WHERE RequestID = %s",
            (request_id,),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True, club_id=new_id)


@bp.post("/club-requests/<request_id>/reject")
@admin_required
def reject_club_request(request_id):
    execute(
        "UPDATE ClubCreationRequest SET RequestStatus = 'Rejected', ResolvedTime = NOW() "
        "WHERE RequestID = %s AND RequestStatus = 'Pending'",
        (request_id,),
    )
    return jsonify(ok=True)


@bp.get("/attendance")
@admin_required
def cross_club_attendance():
    rows = query(
        """
        SELECT e.EventID, e.EventTitle, e.EventStartTime, c.ClubName,
               (SELECT COUNT(*) FROM RSVP r WHERE r.EventID=e.EventID AND r.RSVPStatus='Going') AS going,
               (SELECT COUNT(*) FROM Attendance a WHERE a.EventID=e.EventID)                   AS attended,
               e.EventCapacity
        FROM Event e JOIN Club c ON c.ClubID = e.ClubID
        ORDER BY e.EventStartTime DESC LIMIT 100
        """
    )
    return jsonify(events=rows)
