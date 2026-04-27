"""
clubs.py

Club directory + detail endpoints, multi-category aware. Also handles
join/leave actions and student-initiated club-creation requests that admins
review through the admin portal.
"""

from flask import Blueprint, g, jsonify, request

from auth import login_required
from db import execute, query, next_id


bp = Blueprint("clubs", __name__)


def fetch_club_categories(club_ids):
    if not club_ids:
        return {}
    placeholders = ",".join(["%s"] * len(club_ids))
    rows = query(
        f"SELECT cc.ClubID, cat.CategoryID, cat.CategoryName "
        f"FROM ClubCategory cc JOIN Category cat ON cat.CategoryID = cc.CategoryID "
        f"WHERE cc.ClubID IN ({placeholders}) "
        f"ORDER BY cat.CategoryName",
        tuple(club_ids),
    )
    out = {}
    for r in rows:
        out.setdefault(r["ClubID"], []).append({"CategoryID": r["CategoryID"], "CategoryName": r["CategoryName"]})
    return out


@bp.get("/")
@login_required
def directory():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()
    sort = request.args.get("sort", "name")

    sql = [
        "SELECT DISTINCT c.ClubID, c.ClubName, c.ClubDescription, c.ClubCreationDate",
        "FROM Club c",
        "LEFT JOIN ClubCategory cc ON cc.ClubID = c.ClubID",
        "WHERE 1=1",
    ]
    params = []
    if q:
        sql.append("AND c.ClubName LIKE %s")
        params.append(f"%{q}%")
    if category_id:
        sql.append("AND cc.CategoryID = %s")
        params.append(category_id)
    order_by = {"name": "c.ClubName", "newest": "c.ClubCreationDate DESC"}.get(sort, "c.ClubName")
    sql.append(f"ORDER BY {order_by}")

    clubs_rows = query(" ".join(sql), tuple(params))
    cat_map = fetch_club_categories([c["ClubID"] for c in clubs_rows])
    for c in clubs_rows:
        c["Categories"] = cat_map.get(c["ClubID"], [])
    categories = query("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName")
    return jsonify(clubs=clubs_rows, categories=categories)


@bp.get("/<club_id>")
@login_required
def detail(club_id):
    club = query("SELECT * FROM Club WHERE ClubID = %s", (club_id,), one=True)
    if not club:
        return jsonify(error="club not found"), 404
    club["Categories"] = fetch_club_categories([club_id]).get(club_id, [])

    membership = query(
        "SELECT MembershipRole, MembershipStatus FROM ClubMembership "
        "WHERE ClubID = %s AND UserID = %s",
        (club_id, g.user["UserID"]), one=True,
    )
    has_pending = bool(query(
        "SELECT 1 FROM JoinRequest WHERE ClubID = %s AND UserID = %s AND RequestStatus = 'Pending'",
        (club_id, g.user["UserID"]), one=True,
    ))
    is_admin = g.user.get("AccountType") == "Admin"
    is_member = bool(membership and membership["MembershipStatus"] == "Active")
    can_see_private = is_member or is_admin

    if can_see_private:
        announcements = query(
            "SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody, "
            "AnnouncementDate, AnnouncementVisibility "
            "FROM Announcement WHERE ClubID = %s "
            "ORDER BY AnnouncementDate DESC LIMIT 10",
            (club_id,),
        )
        upcoming = query(
            "SELECT EventID, EventTitle, EventStartTime, EventVisibility "
            "FROM Event WHERE ClubID = %s AND EventStatus = 'Scheduled' AND EventStartTime >= NOW() "
            "ORDER BY EventStartTime",
            (club_id,),
        )
    else:
        announcements = query(
            "SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody, "
            "AnnouncementDate, AnnouncementVisibility "
            "FROM Announcement WHERE ClubID = %s AND AnnouncementVisibility = 'Public' "
            "ORDER BY AnnouncementDate DESC LIMIT 10",
            (club_id,),
        )
        upcoming = query(
            "SELECT EventID, EventTitle, EventStartTime, EventVisibility "
            "FROM Event WHERE ClubID = %s AND EventStatus = 'Scheduled' "
            "AND EventVisibility = 'Public' AND EventStartTime >= NOW() "
            "ORDER BY EventStartTime",
            (club_id,),
        )

    return jsonify(
        club=club,
        membership=membership,
        has_pending=has_pending,
        announcements=announcements,
        upcoming=upcoming,
    )


@bp.post("/<club_id>/join")
@login_required
def join(club_id):
    if query(
        "SELECT 1 FROM ClubMembership WHERE ClubID = %s AND UserID = %s AND MembershipStatus='Active'",
        (club_id, g.user["UserID"]), one=True,
    ):
        return jsonify(error="already a member"), 409
    if query(
        "SELECT 1 FROM JoinRequest WHERE ClubID = %s AND UserID = %s AND RequestStatus='Pending'",
        (club_id, g.user["UserID"]), one=True,
    ):
        return jsonify(error="request already pending"), 409
    new_id = next_id("JR", "JoinRequest", "RequestID")
    execute(
        "INSERT INTO JoinRequest (RequestID, RequestStatus, ClubID, UserID) "
        "VALUES (%s, 'Pending', %s, %s)",
        (new_id, club_id, g.user["UserID"]),
    )
    return jsonify(ok=True, request_id=new_id)


@bp.post("/<club_id>/leave")
@login_required
def leave(club_id):
    try:
        execute(
            "DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s",
            (club_id, g.user["UserID"]),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.get("/categories")
@login_required
def categories_list():
    return jsonify(categories=query(
        "SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName"
    ))


@bp.post("/request")
@login_required
def request_new_club():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    desc = (body.get("description") or "").strip()
    category_ids = body.get("category_ids") or []
    proposed_officer = body.get("officer_user_id") or g.user["UserID"]
    if not (name and desc and category_ids):
        return jsonify(error="name, description, and at least one category required"), 400
    if query("SELECT 1 FROM Club WHERE ClubName = %s", (name,), one=True):
        return jsonify(error="a club with that name already exists"), 409
    if query(
        "SELECT 1 FROM ClubCreationRequest WHERE ProposedName = %s AND RequestStatus = 'Pending'",
        (name,), one=True,
    ):
        return jsonify(error="a request with that name is already pending"), 409

    new_id = next_id("CR", "ClubCreationRequest", "RequestID")
    execute(
        "INSERT INTO ClubCreationRequest "
        "(RequestID, ProposedName, ProposedDescription, ProposedOfficerUserID, RequestedByUserID) "
        "VALUES (%s,%s,%s,%s,%s)",
        (new_id, name, desc, proposed_officer, g.user["UserID"]),
    )
    for cid in category_ids:
        execute(
            "INSERT INTO ClubCreationRequestCategory (RequestID, CategoryID) VALUES (%s,%s)",
            (new_id, cid),
        )
    return jsonify(ok=True, request_id=new_id)
