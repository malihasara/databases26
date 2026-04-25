from flask import Blueprint, render_template, request

from db import query


bp = Blueprint("public", __name__, url_prefix="/public")


@bp.route("/clubs")
def clubs():
    q = request.args.get("q", "").strip()
    sql = [
        "SELECT c.ClubID, c.ClubName, c.ClubDescription, cat.CategoryName",
        "FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID",
    ]
    params = []
    if q:
        sql.append("WHERE c.ClubName LIKE %s")
        params.append(f"%{q}%")
    sql.append("ORDER BY c.ClubName")
    rows = query(" ".join(sql), tuple(params))
    return render_template("public/clubs.html", clubs=rows, q=q)


@bp.route("/events")
def events():
    q = request.args.get("q", "").strip()
    sql = [
        "SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,",
        "       c.ClubName, l.BuildingName, l.RoomNumber",
        "FROM Event e",
        "JOIN Club c     ON c.ClubID     = e.ClubID",
        "JOIN Location l ON l.LocationID = e.LocationID",
        "WHERE e.EventVisibility = 'Public' AND e.EventStatus = 'Scheduled'",
    ]
    params = []
    if q:
        sql.append("AND e.EventTitle LIKE %s")
        params.append(f"%{q}%")
    sql.append("ORDER BY e.EventStartTime")
    rows = query(" ".join(sql), tuple(params))
    return render_template("public/events.html", events=rows, q=q)
