from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from auth import login_required
from db import call_proc, execute, query, next_id


bp = Blueprint("events", __name__, url_prefix="/events")


@bp.route("/")
@login_required
def list_events():
    club_id = request.args.get("club", "").strip()
    type_id = request.args.get("type", "").strip()
    visibility = request.args.get("visibility", "").strip()
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "soonest")

    sql = [
        "SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,",
        "       e.EventEndTime, e.EventCapacity, e.EventStatus, e.EventVisibility,",
        "       c.ClubID, c.ClubName, t.EventTypeName, l.BuildingName, l.RoomNumber",
        "FROM Event e",
        "JOIN Club c      ON c.ClubID      = e.ClubID",
        "JOIN EventType t ON t.EventTypeID = e.EventTypeID",
        "JOIN Location l  ON l.LocationID  = e.LocationID",
        "LEFT JOIN ClubMembership cm ON cm.ClubID = e.ClubID AND cm.UserID = %s AND cm.MembershipStatus='Active'",
        "WHERE e.EventStatus = 'Scheduled'",
        "AND (e.EventVisibility = 'Public' OR cm.UserID IS NOT NULL)",
    ]
    params = [g.user["UserID"]]
    if club_id:
        sql.append("AND e.ClubID = %s")
        params.append(club_id)
    if type_id:
        sql.append("AND e.EventTypeID = %s")
        params.append(type_id)
    if visibility:
        sql.append("AND e.EventVisibility = %s")
        params.append(visibility)
    if q:
        sql.append("AND e.EventTitle LIKE %s")
        params.append(f"%{q}%")
    order = {"soonest": "e.EventStartTime", "latest": "e.EventStartTime DESC"}.get(sort, "e.EventStartTime")
    sql.append(f"ORDER BY {order}")

    events_rows = query(" ".join(sql), tuple(params))
    clubs_rows = query("SELECT ClubID, ClubName FROM Club ORDER BY ClubName")
    types_rows = query("SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName")
    return render_template(
        "events/list.html",
        events=events_rows,
        clubs=clubs_rows,
        types=types_rows,
        filters={"club": club_id, "type": type_id, "visibility": visibility, "q": q, "sort": sort},
    )


@bp.route("/<event_id>")
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
        (event_id,),
        one=True,
    )
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("events.list_events"))

    rsvp = query(
        "SELECT RSVPID, RSVPStatus FROM RSVP WHERE EventID = %s AND UserID = %s",
        (event_id, g.user["UserID"]),
        one=True,
    )
    checked_in = False
    if rsvp:
        checked_in = bool(query(
            "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
            (event_id, rsvp["RSVPID"]),
            one=True,
        ))
    going_count = query(
        "SELECT COUNT(*) AS c FROM RSVP WHERE EventID = %s AND RSVPStatus = 'Going'",
        (event_id,),
        one=True,
    )["c"]
    return render_template(
        "events/detail.html",
        event=event,
        rsvp=rsvp,
        checked_in=checked_in,
        going_count=going_count,
    )


@bp.route("/<event_id>/rsvp", methods=("POST",))
@login_required
def rsvp(event_id):
    status = request.form.get("status", "Going")
    if status not in ("Going", "NotGoing", "Tentative"):
        flash("Invalid RSVP status.", "error")
        return redirect(url_for("events.detail", event_id=event_id))

    existing = query(
        "SELECT RSVPID FROM RSVP WHERE EventID = %s AND UserID = %s",
        (event_id, g.user["UserID"]),
        one=True,
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
        flash("RSVP saved.", "success")
    except Exception as exc:
        flash(str(exc).split(":")[-1].strip() or "Could not RSVP.", "error")
    return redirect(url_for("events.detail", event_id=event_id))


@bp.route("/<event_id>/check-in", methods=("POST",))
@login_required
def check_in(event_id):
    rsvp_row = query(
        "SELECT RSVPID FROM RSVP WHERE EventID = %s AND UserID = %s AND RSVPStatus = 'Going'",
        (event_id, g.user["UserID"]),
        one=True,
    )
    if not rsvp_row:
        flash("You must RSVP 'Going' before checking in.", "error")
        return redirect(url_for("events.detail", event_id=event_id))

    already = query(
        "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
        (event_id, rsvp_row["RSVPID"]),
        one=True,
    )
    if already:
        flash("Already checked in.", "message")
        return redirect(url_for("events.detail", event_id=event_id))

    execute(
        "INSERT INTO Attendance (EventID, RSVPID, CheckInMethod) VALUES (%s, %s, 'SelfCheckIn')",
        (event_id, rsvp_row["RSVPID"]),
    )
    flash("Checked in.", "success")
    return redirect(url_for("events.detail", event_id=event_id))
