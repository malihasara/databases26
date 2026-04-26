from datetime import datetime
from flask import Blueprint, jsonify, request

from auth import officer_required
from db import call_proc, execute, query, next_id


bp = Blueprint("admin", __name__)


@bp.get("/")
@officer_required()
def dashboard(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    counts = query(
        """
        SELECT
          (SELECT COUNT(*) FROM ClubMembership WHERE ClubID=%s AND MembershipStatus='Active') AS members,
          (SELECT COUNT(*) FROM JoinRequest    WHERE ClubID=%s AND RequestStatus='Pending')   AS pending,
          (SELECT COUNT(*) FROM Event          WHERE ClubID=%s AND EventStatus='Scheduled')   AS events,
          (SELECT COUNT(*) FROM Announcement   WHERE ClubID=%s)                               AS posts
        """,
        (club_id, club_id, club_id, club_id), one=True,
    )
    return jsonify(club=club, counts=counts)


@bp.get("/members")
@officer_required()
def members(club_id):
    rows = query(
        """
        SELECT cm.UserID, cm.MembershipRole, cm.MembershipStatus, cm.MembershipJoinDate,
               u.FirstName, u.LastName, u.Email
        FROM ClubMembership cm JOIN User u ON u.UserID = cm.UserID
        WHERE cm.ClubID = %s
        ORDER BY FIELD(cm.MembershipRole,'Officer','Member'), u.LastName
        """,
        (club_id,),
    )
    return jsonify(members=rows)


@bp.post("/members/<user_id>/role")
@officer_required()
def update_member_role(club_id, user_id):
    body = request.get_json(silent=True) or {}
    role = body.get("role")
    if role not in ("Officer", "Member"):
        return jsonify(error="invalid role"), 400
    execute(
        "UPDATE ClubMembership SET MembershipRole = %s WHERE ClubID = %s AND UserID = %s",
        (role, club_id, user_id),
    )
    return jsonify(ok=True)


@bp.post("/members/<user_id>/remove")
@officer_required()
def remove_member(club_id, user_id):
    try:
        execute(
            "DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s",
            (club_id, user_id),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.get("/requests")
@officer_required()
def requests_view(club_id):
    rows = query(
        """
        SELECT jr.RequestID, jr.RequestStatus, jr.RequestTime,
               u.UserID, u.FirstName, u.LastName, u.Email
        FROM JoinRequest jr JOIN User u ON u.UserID = jr.UserID
        WHERE jr.ClubID = %s
        ORDER BY jr.RequestTime DESC
        """,
        (club_id,),
    )
    return jsonify(requests=rows)


@bp.post("/requests/<request_id>/approve")
@officer_required()
def approve_request(club_id, request_id):
    try:
        call_proc("sp_approve_join_request", (request_id,))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.post("/requests/<request_id>/reject")
@officer_required()
def reject_request(club_id, request_id):
    execute(
        "UPDATE JoinRequest SET RequestStatus = 'Rejected' WHERE RequestID = %s AND ClubID = %s",
        (request_id, club_id),
    )
    return jsonify(ok=True)


@bp.get("/events")
@officer_required()
def events_view(club_id):
    rows = query(
        """
        SELECT e.EventID, e.EventTitle, e.EventStartTime, e.EventStatus, e.EventVisibility,
               e.EventCapacity,
               (SELECT COUNT(*) FROM RSVP r       WHERE r.EventID = e.EventID AND r.RSVPStatus='Going') AS going,
               (SELECT COUNT(*) FROM Attendance a WHERE a.EventID = e.EventID)                          AS attended
        FROM Event e WHERE e.ClubID = %s
        ORDER BY e.EventStartTime DESC
        """,
        (club_id,),
    )
    return jsonify(events=rows)


@bp.get("/event-form-options")
@officer_required()
def event_form_options(club_id):
    locations = query("SELECT LocationID, BuildingName, RoomNumber FROM Location ORDER BY BuildingName")
    types = query("SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName")
    return jsonify(locations=locations, types=types)


@bp.post("/events")
@officer_required()
def create_event(club_id):
    body = request.get_json(silent=True) or {}
    try:
        new_id = next_id("EV", "Event", "EventID")
        execute(
            """
            INSERT INTO Event (EventID, EventTitle, EventDescription, EventStartTime, EventEndTime,
                               EventCapacity, EventStatus, EventVisibility, LocationID, EventTypeID, ClubID)
            VALUES (%s,%s,%s,%s,%s,%s,'Scheduled',%s,%s,%s,%s)
            """,
            (
                new_id,
                body.get("title", "").strip(),
                body.get("description", "").strip(),
                datetime.fromisoformat(body["start"]),
                datetime.fromisoformat(body["end"]),
                int(body["capacity"]),
                body.get("visibility", "Public"),
                body["location_id"],
                body["type_id"],
                club_id,
            ),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True, event_id=new_id)


@bp.get("/events/<event_id>")
@officer_required()
def event_detail(club_id, event_id):
    event = query("SELECT * FROM Event WHERE EventID = %s AND ClubID = %s", (event_id, club_id), one=True)
    if not event:
        return jsonify(error="event not found"), 404
    return jsonify(event=event)


@bp.post("/events/<event_id>")
@officer_required()
def update_event(club_id, event_id):
    body = request.get_json(silent=True) or {}
    try:
        execute(
            """
            UPDATE Event SET EventTitle=%s, EventDescription=%s, EventStartTime=%s, EventEndTime=%s,
                             EventCapacity=%s, EventVisibility=%s, LocationID=%s, EventTypeID=%s,
                             EventStatus=%s
            WHERE EventID=%s AND ClubID=%s
            """,
            (
                body.get("title", "").strip(),
                body.get("description", "").strip(),
                datetime.fromisoformat(body["start"]),
                datetime.fromisoformat(body["end"]),
                int(body["capacity"]),
                body.get("visibility", "Public"),
                body["location_id"],
                body["type_id"],
                body.get("status", "Scheduled"),
                event_id,
                club_id,
            ),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.post("/events/<event_id>/delete")
@officer_required()
def delete_event(club_id, event_id):
    try:
        execute("DELETE FROM Attendance WHERE EventID = %s", (event_id,))
        execute("DELETE FROM RSVP WHERE EventID = %s", (event_id,))
        execute("DELETE FROM Event WHERE EventID = %s AND ClubID = %s", (event_id, club_id))
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.get("/events/<event_id>/attendance")
@officer_required()
def attendance(club_id, event_id):
    event = query(
        "SELECT EventID, EventTitle FROM Event WHERE EventID = %s AND ClubID = %s",
        (event_id, club_id), one=True,
    )
    if not event:
        return jsonify(error="event not found"), 404
    rsvps = query(
        """
        SELECT r.RSVPID, r.RSVPStatus, u.FirstName, u.LastName, u.Email,
               a.CheckInTime, a.CheckInMethod
        FROM RSVP r JOIN User u ON u.UserID = r.UserID
        LEFT JOIN Attendance a ON a.RSVPID = r.RSVPID AND a.EventID = r.EventID
        WHERE r.EventID = %s
        ORDER BY r.RSVPStatus, u.LastName
        """,
        (event_id,),
    )
    return jsonify(event=event, rsvps=rsvps)


@bp.post("/events/<event_id>/checkin/<rsvp_id>")
@officer_required()
def officer_check_in(club_id, event_id, rsvp_id):
    if query(
        "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
        (event_id, rsvp_id), one=True,
    ):
        return jsonify(ok=True, already=True)
    execute(
        "INSERT INTO Attendance (EventID, RSVPID, CheckInMethod) VALUES (%s, %s, 'Manual')",
        (event_id, rsvp_id),
    )
    return jsonify(ok=True)
