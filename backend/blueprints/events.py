from datetime import datetime
from flask import Blueprint, g, jsonify, request

from auth import login_required
from db import call_proc, execute, query, next_id


bp = Blueprint("events", __name__)


@bp.get("/")
@login_required
def list_events():
    club_id = request.args.get("club", "").strip()
    type_id = request.args.get("type", "").strip()
    visibility = request.args.get("visibility", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "soonest")

    is_faculty = g.user.get("AccountType") == "Faculty"
    sql = [
        "SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,",
        "       e.EventEndTime, e.EventCapacity, e.EventStatus, e.EventVisibility,",
        "       c.ClubID, c.ClubName, t.EventTypeName, l.BuildingName, l.RoomNumber",
        "FROM Event e",
        "JOIN Club c      ON c.ClubID      = e.ClubID",
        "JOIN EventType t ON t.EventTypeID = e.EventTypeID",
        "JOIN Location l  ON l.LocationID  = e.LocationID",
    ]
    params = []
    if is_faculty:
        sql.append("WHERE e.EventStatus = 'Scheduled'")
    else:
        sql.append("LEFT JOIN ClubMembership cm ON cm.ClubID = e.ClubID AND cm.UserID = %s AND cm.MembershipStatus='Active'")
        sql.append("WHERE e.EventStatus = 'Scheduled'")
        sql.append("AND (e.EventVisibility = 'Public' OR cm.UserID IS NOT NULL)")
        params.append(g.user["UserID"])
    if club_id:
        sql.append("AND e.ClubID = %s"); params.append(club_id)
    if type_id:
        sql.append("AND e.EventTypeID = %s"); params.append(type_id)
    if visibility:
        sql.append("AND e.EventVisibility = %s"); params.append(visibility)
    if q:
        sql.append("AND e.EventTitle LIKE %s"); params.append(f"%{q}%")
    order = {"soonest": "e.EventStartTime", "latest": "e.EventStartTime DESC"}.get(sort, "e.EventStartTime")
    sql.append(f"ORDER BY {order}")

    events_rows = query(" ".join(sql), tuple(params))
    clubs_rows = query("SELECT ClubID, ClubName FROM Club ORDER BY ClubName")
    types_rows = query("SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName")
    return jsonify(events=events_rows, clubs=clubs_rows, types=types_rows)


@bp.get("/<event_id>")
@login_required
def detail(event_id):
    event = query(
        """
        SELECT e.*, c.ClubName, t.EventTypeName, l.BuildingName, l.RoomNumber, l.HomeAddress,
               fn_event_seats_remaining(e.EventID) AS SeatsLeft
        FROM Event e
        JOIN Club c      ON c.ClubID      = e.ClubID
        JOIN EventType t ON t.EventTypeID = e.EventTypeID
        JOIN Location l  ON l.LocationID  = e.LocationID
        WHERE e.EventID = %s
        """,
        (event_id,), one=True,
    )
    if not event:
        return jsonify(error="event not found"), 404

    is_faculty = g.user.get("AccountType") == "Faculty"
    if event["EventVisibility"] == "MembersOnly" and not is_faculty:
        member = query(
            "SELECT 1 FROM ClubMembership "
            "WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active'",
            (event["ClubID"], g.user["UserID"]), one=True,
        )
        if not member:
            return jsonify(error="this event is members-only"), 403

    rsvp = query(
        "SELECT RSVPID, RSVPStatus FROM RSVP WHERE EventID = %s AND UserID = %s",
        (event_id, g.user["UserID"]), one=True,
    )
    checked_in = False
    if rsvp:
        checked_in = bool(query(
            "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
            (event_id, rsvp["RSVPID"]), one=True,
        ))
    going_count = query(
        "SELECT COUNT(*) AS c FROM RSVP WHERE EventID = %s AND RSVPStatus = 'Going'",
        (event_id,), one=True,
    )["c"]
    return jsonify(event=event, rsvp=rsvp, checked_in=checked_in, going_count=going_count)


@bp.post("/<event_id>/rsvp")
@login_required
def rsvp(event_id):
    body = request.get_json(silent=True) or {}
    status = body.get("status", "Going")
    if status not in ("Going", "NotGoing", "Tentative"):
        return jsonify(error="invalid status"), 400

    ev = query(
        "SELECT EventEndTime, EventStatus FROM Event WHERE EventID = %s",
        (event_id,), one=True,
    )
    if not ev:
        return jsonify(error="event not found"), 404
    if ev["EventStatus"] != "Scheduled" or ev["EventEndTime"] <= datetime.now():
        return jsonify(error="RSVP closed: event has ended or is not scheduled"), 400

    existing = query(
        "SELECT RSVPID FROM RSVP WHERE EventID = %s AND UserID = %s",
        (event_id, g.user["UserID"]), one=True,
    )
    try:
        if existing:
            execute(
                "UPDATE RSVP SET RSVPStatus = %s WHERE RSVPID = %s",
                (status, existing["RSVPID"]),
            )
        else:
            new_id = next_id("RS", "RSVP", "RSVPID")
            call_proc("sp_create_rsvp", (new_id, g.user["UserID"], event_id, status))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip() or "could not RSVP"), 400
    return jsonify(ok=True)


@bp.post("/<event_id>/check-in")
@login_required
def check_in(event_id):
    ev = query(
        "SELECT EventStartTime, EventEndTime, EventStatus FROM Event WHERE EventID = %s",
        (event_id,), one=True,
    )
    if not ev:
        return jsonify(error="event not found"), 404
    if ev["EventStatus"] == "Cancelled":
        return jsonify(error="event was cancelled"), 400

    rsvp_row = query(
        "SELECT RSVPID FROM RSVP WHERE EventID = %s AND UserID = %s AND RSVPStatus = 'Going'",
        (event_id, g.user["UserID"]), one=True,
    )
    if not rsvp_row:
        return jsonify(error="must RSVP 'Going' before check-in"), 400
    if query(
        "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
        (event_id, rsvp_row["RSVPID"]), one=True,
    ):
        return jsonify(ok=True, already=True)
    execute(
        "INSERT INTO Attendance (EventID, RSVPID, CheckInMethod) VALUES (%s, %s, 'SelfCheckIn')",
        (event_id, rsvp_row["RSVPID"]),
    )
    return jsonify(ok=True)
