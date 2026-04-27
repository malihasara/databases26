"""
admin.py

Officer-facing club management endpoints: dashboard, members roster,
member-action requests (dual-approval by President + Vice President),
join request approval, event CRUD, and attendance check-in / no-show / reset.
"""

from datetime import datetime
from flask import Blueprint, g, jsonify, request

from auth import officer_required, role_in_club
from db import call_proc, execute, query, next_id


bp = Blueprint("admin", __name__)


ALLOWED_ACTIONS = {"Demote", "Remove", "PromoteOfficer", "PromoteVP", "PromotePresident"}
ALLOWED_ROLES = {"Member", "Officer", "VicePresident", "President"}


@bp.post("/members/<user_id>/role")
@officer_required()
def admin_set_member_role(club_id, user_id):
    if g.user.get("AccountType") != "Admin":
        return jsonify(error="admin access required"), 403
    body = request.get_json(silent=True) or {}
    role = body.get("role")
    if role not in ALLOWED_ROLES:
        return jsonify(error="invalid role"), 400
    target = query(
        "SELECT MembershipRole FROM ClubMembership "
        "WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active'",
        (club_id, user_id), one=True,
    )
    if not target:
        return jsonify(error="target is not an active member of this club"), 404
    try:
        if role == "President":
            execute(
                "UPDATE ClubMembership SET MembershipRole = 'Officer' "
                "WHERE ClubID = %s AND MembershipRole = 'President' AND NOT (UserID = %s)",
                (club_id, user_id),
            )
        execute(
            "UPDATE ClubMembership SET MembershipRole = %s "
            "WHERE ClubID = %s AND UserID = %s",
            (role, club_id, user_id),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


@bp.post("/members/<user_id>/remove")
@officer_required()
def admin_remove_member(club_id, user_id):
    if g.user.get("AccountType") != "Admin":
        return jsonify(error="admin access required"), 403
    try:
        execute(
            "DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s",
            (club_id, user_id),
        )
    except Exception as exc:
        return jsonify(error=str(exc).split(":")[-1].strip()), 400
    return jsonify(ok=True)


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
          (SELECT COUNT(*) FROM Announcement   WHERE ClubID=%s)                               AS posts,
          (SELECT COUNT(*) FROM MemberActionRequest WHERE ClubID=%s AND RequestStatus='Pending') AS actions
        """,
        (club_id, club_id, club_id, club_id, club_id), one=True,
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
        ORDER BY FIELD(cm.MembershipRole,'President','VicePresident','Officer','Member'), u.LastName
        """,
        (club_id,),
    )
    return jsonify(members=rows)


@bp.get("/member-actions")
@officer_required()
def list_member_actions(club_id):
    rows = query(
        """
        SELECT mar.RequestID, mar.ActionType, mar.TargetRole, mar.RequestStatus,
               mar.PresApproved, mar.VPApproved, mar.RequestTime,
               t.UserID AS TargetUserID, t.FirstName AS TargetFirstName, t.LastName AS TargetLastName,
               cm.MembershipRole AS TargetRoleNow,
               r.UserID AS RequesterUserID, r.FirstName AS RequesterFirstName, r.LastName AS RequesterLastName
        FROM MemberActionRequest mar
        JOIN User t ON t.UserID = mar.TargetUserID
        JOIN User r ON r.UserID = mar.RequestedByUserID
        LEFT JOIN ClubMembership cm ON cm.ClubID = mar.ClubID AND cm.UserID = mar.TargetUserID
        WHERE mar.ClubID = %s
        ORDER BY mar.RequestTime DESC
        """,
        (club_id,),
    )
    return jsonify(actions=rows)


@bp.post("/member-actions")
@officer_required()
def create_member_action(club_id):
    body = request.get_json(silent=True) or {}
    action = body.get("action")
    target = body.get("target_user_id")
    if action not in ALLOWED_ACTIONS:
        return jsonify(error="invalid action"), 400
    if not target:
        return jsonify(error="target_user_id required"), 400
    if g.user["UserID"] == target:
        return jsonify(error="you cannot request an action against yourself"), 400
    target_row = query(
        "SELECT MembershipRole FROM ClubMembership WHERE ClubID = %s AND UserID = %s "
        "AND MembershipStatus = 'Active'",
        (club_id, target), one=True,
    )
    if not target_row:
        return jsonify(error="target is not an active member of this club"), 404
    if query(
        "SELECT 1 FROM MemberActionRequest WHERE ClubID = %s AND TargetUserID = %s "
        "AND RequestStatus = 'Pending'",
        (club_id, target), one=True,
    ):
        return jsonify(error="a pending action already exists for this member"), 409

    new_id = next_id("MA", "MemberActionRequest", "RequestID")
    execute(
        "INSERT INTO MemberActionRequest "
        "(RequestID, ClubID, TargetUserID, ActionType, TargetRole, RequestedByUserID) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (new_id, club_id, target, action, body.get("target_role"), g.user["UserID"]),
    )
    return jsonify(ok=True, request_id=new_id)


def _try_apply(request_id):
    try:
        call_proc("sp_apply_member_action", (request_id,))
    except Exception:
        pass


@bp.post("/member-actions/<request_id>/approve")
@officer_required()
def approve_member_action(club_id, request_id):
    role = role_in_club(g.user["UserID"], club_id) if g.user["AccountType"] != "Admin" else "Admin"
    req = query(
        "SELECT RequestStatus, PresApproved, VPApproved, ClubID "
        "FROM MemberActionRequest WHERE RequestID = %s",
        (request_id,), one=True,
    )
    if not req or req["ClubID"] != club_id:
        return jsonify(error="request not found"), 404
    if req["RequestStatus"] != "Pending":
        return jsonify(error="request is not pending"), 400

    column = None
    if role == "President":
        column = "PresApproved"
    elif role == "VicePresident":
        column = "VPApproved"
    elif role == "Admin":
        column = "VPApproved" if req["PresApproved"] else "PresApproved"
    if not column:
        return jsonify(error="only the President or Vice President can approve this"), 403

    execute(f"UPDATE MemberActionRequest SET {column} = 1 WHERE RequestID = %s", (request_id,))
    _try_apply(request_id)
    return jsonify(ok=True)


@bp.post("/member-actions/<request_id>/reject")
@officer_required()
def reject_member_action(club_id, request_id):
    role = role_in_club(g.user["UserID"], club_id) if g.user["AccountType"] != "Admin" else "Admin"
    if role not in ("President", "VicePresident", "Admin"):
        return jsonify(error="only the President or Vice President can reject this"), 403
    execute(
        "UPDATE MemberActionRequest "
        "SET RequestStatus = 'Rejected', ResolvedTime = NOW() "
        "WHERE RequestID = %s AND ClubID = %s AND RequestStatus = 'Pending'",
        (request_id, club_id),
    )
    return jsonify(ok=True)


@bp.post("/member-actions/<request_id>/cancel")
@officer_required()
def cancel_member_action(club_id, request_id):
    req = query(
        "SELECT RequestedByUserID, RequestStatus FROM MemberActionRequest WHERE RequestID = %s",
        (request_id,), one=True,
    )
    if not req:
        return jsonify(error="request not found"), 404
    if req["RequestedByUserID"] != g.user["UserID"] and g.user["AccountType"] != "Admin":
        return jsonify(error="only the requester can cancel"), 403
    if req["RequestStatus"] != "Pending":
        return jsonify(error="request is not pending"), 400
    execute(
        "UPDATE MemberActionRequest "
        "SET RequestStatus = 'Cancelled', ResolvedTime = NOW() "
        "WHERE RequestID = %s",
        (request_id,),
    )
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
        "UPDATE RSVP SET RSVPStatus = 'Going' WHERE RSVPID = %s AND RSVPStatus = 'NoShow'",
        (rsvp_id,),
    )
    execute(
        "INSERT INTO Attendance (EventID, RSVPID, CheckInMethod) VALUES (%s, %s, 'Manual')",
        (event_id, rsvp_id),
    )
    return jsonify(ok=True)


@bp.post("/events/<event_id>/no-show/<rsvp_id>")
@officer_required()
def officer_no_show(club_id, event_id, rsvp_id):
    rsvp = query("SELECT EventID FROM RSVP WHERE RSVPID = %s", (rsvp_id,), one=True)
    if not rsvp or rsvp["EventID"] != event_id:
        return jsonify(error="rsvp not found for this event"), 404
    execute("DELETE FROM Attendance WHERE EventID = %s AND RSVPID = %s", (event_id, rsvp_id))
    execute("UPDATE RSVP SET RSVPStatus = 'NoShow' WHERE RSVPID = %s", (rsvp_id,))
    return jsonify(ok=True)


@bp.post("/events/<event_id>/reset/<rsvp_id>")
@officer_required()
def officer_reset_rsvp(club_id, event_id, rsvp_id):
    rsvp = query("SELECT EventID, RSVPStatus FROM RSVP WHERE RSVPID = %s", (rsvp_id,), one=True)
    if not rsvp or rsvp["EventID"] != event_id:
        return jsonify(error="rsvp not found for this event"), 404
    execute("DELETE FROM Attendance WHERE EventID = %s AND RSVPID = %s", (event_id, rsvp_id))
    if rsvp["RSVPStatus"] == "NoShow":
        execute("UPDATE RSVP SET RSVPStatus = 'Going' WHERE RSVPID = %s", (rsvp_id,))
    return jsonify(ok=True)
