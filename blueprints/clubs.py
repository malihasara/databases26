from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from auth import login_required
from db import execute, query, next_id


bp = Blueprint("clubs", __name__, url_prefix="/clubs")


@bp.route("/")
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
    return render_template(
        "clubs/directory.html",
        clubs=clubs_rows,
        categories=categories,
        q=q,
        category_id=category_id,
        sort=sort,
    )


@bp.route("/<club_id>")
@login_required
def detail(club_id):
    club = query(
        """
        SELECT c.*, cat.CategoryName
        FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID
        WHERE c.ClubID = %s
        """,
        (club_id,),
        one=True,
    )
    if not club:
        flash("Club not found.", "error")
        return redirect(url_for("clubs.directory"))

    membership = query(
        "SELECT MembershipRole, MembershipStatus FROM ClubMembership "
        "WHERE ClubID = %s AND UserID = %s",
        (club_id, g.user["UserID"]),
        one=True,
    )
    pending = query(
        "SELECT 1 FROM JoinRequest WHERE ClubID = %s AND UserID = %s AND RequestStatus = 'Pending'",
        (club_id, g.user["UserID"]),
        one=True,
    )
    announcements = query(
        """
        SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody, AnnouncementDate
        FROM Announcement WHERE ClubID = %s
        ORDER BY AnnouncementDate DESC LIMIT 10
        """,
        (club_id,),
    )
    upcoming = query(
        """
        SELECT EventID, EventTitle, EventStartTime, EventVisibility
        FROM Event
        WHERE ClubID = %s AND EventStatus = 'Scheduled' AND EventStartTime >= NOW()
        ORDER BY EventStartTime
        """,
        (club_id,),
    )
    return render_template(
        "clubs/detail.html",
        club=club,
        membership=membership,
        has_pending=bool(pending),
        announcements=announcements,
        upcoming=upcoming,
    )


@bp.route("/<club_id>/join", methods=("POST",))
@login_required
def join(club_id):
    existing = query(
        "SELECT 1 FROM ClubMembership WHERE ClubID = %s AND UserID = %s AND MembershipStatus='Active'",
        (club_id, g.user["UserID"]),
        one=True,
    )
    if existing:
        flash("You are already a member.", "message")
        return redirect(url_for("clubs.detail", club_id=club_id))

    pending = query(
        "SELECT 1 FROM JoinRequest WHERE ClubID = %s AND UserID = %s AND RequestStatus='Pending'",
        (club_id, g.user["UserID"]),
        one=True,
    )
    if pending:
        flash("Request already pending.", "message")
        return redirect(url_for("clubs.detail", club_id=club_id))

    new_id = next_id("JR", "JoinRequest", "RequestID")
    execute(
        "INSERT INTO JoinRequest (RequestID, RequestStatus, ClubID, UserID) "
        "VALUES (%s, 'Pending', %s, %s)",
        (new_id, club_id, g.user["UserID"]),
    )
    flash("Join request sent.", "success")
    return redirect(url_for("clubs.detail", club_id=club_id))


@bp.route("/<club_id>/leave", methods=("POST",))
@login_required
def leave(club_id):
    try:
        execute(
            "DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s",
            (club_id, g.user["UserID"]),
        )
        flash("You have left the club.", "success")
    except Exception as exc:
        flash(f"Could not leave: {exc}", "error")
    return redirect(url_for("clubs.detail", club_id=club_id))
