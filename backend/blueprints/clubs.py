from flask import Blueprint, g, jsonify, request

from auth import login_required
from db import execute, query, next_id


bp = Blueprint("clubs", __name__)


@bp.get("/")
@login_required
def directory():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()
    sort = request.args.get("sort", "name")

    sql = [
        "SELECT c.ClubID, c.ClubName, c.ClubDescription, c.ClubCreationDate,",
        "       cat.CategoryID, cat.CategoryName",
        "FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID",
        "WHERE 1=1",
    ]
    params = []
    if q:
        sql.append("AND c.ClubName LIKE %s")
        params.append(f"%{q}%")
    if category_id:
        sql.append("AND c.CategoryID = %s")
        params.append(category_id)
    order_by = {"name": "c.ClubName", "newest": "c.ClubCreationDate DESC"}.get(sort, "c.ClubName")
    sql.append(f"ORDER BY {order_by}")

    clubs_rows = query(" ".join(sql), tuple(params))
    categories = query("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName")
    return jsonify(clubs=clubs_rows, categories=categories)


@bp.get("/<club_id>")
@login_required
def detail(club_id):
    club = query(
        "SELECT c.*, cat.CategoryName "
        "FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID "
        "WHERE c.ClubID = %s",
        (club_id,),
        one=True,
    )
    if not club:
        return jsonify(error="club not found"), 404

    membership = query(
        "SELECT MembershipRole, MembershipStatus FROM ClubMembership "
        "WHERE ClubID = %s AND UserID = %s",
        (club_id, g.user["UserID"]),
        one=True,
    )
    has_pending = bool(query(
        "SELECT 1 FROM JoinRequest WHERE ClubID = %s AND UserID = %s AND RequestStatus = 'Pending'",
        (club_id, g.user["UserID"]),
        one=True,
    ))
    can_see_private = bool(membership and membership["MembershipStatus"] == "Active") \
        or g.user.get("AccountType") == "Faculty"
    if can_see_private:
        announcements = query(
            "SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody, "
            "AnnouncementDate, AnnouncementVisibility "
            "FROM Announcement WHERE ClubID = %s "
            "ORDER BY AnnouncementDate DESC LIMIT 10",
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
    if can_see_private:
        upcoming = query(
            "SELECT EventID, EventTitle, EventStartTime, EventVisibility "
            "FROM Event WHERE ClubID = %s AND EventStatus = 'Scheduled' AND EventStartTime >= NOW() "
            "ORDER BY EventStartTime",
            (club_id,),
        )
    else:
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
