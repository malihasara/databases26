from datetime import datetime
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from auth import officer_required
from db import call_proc, execute, query, next_id


bp = Blueprint("admin", __name__, url_prefix="/admin/<club_id>")


@bp.route("/")
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
        (club_id, club_id, club_id, club_id),
        one=True,
    )
    return render_template("admin/dashboard.html", club=club, counts=counts)


@bp.route("/members")
@officer_required()
def members(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    rows = query(
        """
        SELECT cm.UserID, cm.MembershipRole, cm.MembershipStatus, cm.MembershipJoinDate,
               u.FirstName, u.LastName, u.Email
        FROM ClubMembership cm JOIN User u ON u.UserID = cm.UserID
        WHERE cm.ClubID = %s
        ORDER BY FIELD(cm.MembershipRole,'Owner','Officer','Member'), u.LastName
        """,
        (club_id,),
    )
    return render_template("admin/members.html", club=club, members=rows)


@bp.route("/members/<user_id>/role", methods=("POST",))
@officer_required()
def update_member_role(club_id, user_id):
    role = request.form.get("role")
    if role not in ("Owner", "Officer", "Member"):
        flash("Invalid role.", "error")
    else:
        execute(
            "UPDATE ClubMembership SET MembershipRole = %s WHERE ClubID = %s AND UserID = %s",
            (role, club_id, user_id),
        )
        flash("Role updated.", "success")
    return redirect(url_for("admin.members", club_id=club_id))


@bp.route("/members/<user_id>/remove", methods=("POST",))
@officer_required()
def remove_member(club_id, user_id):
    try:
        execute(
            "DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s",
            (club_id, user_id),
        )
        flash("Member removed.", "success")
    except Exception as exc:
        flash(str(exc).split(":")[-1].strip(), "error")
    return redirect(url_for("admin.members", club_id=club_id))


@bp.route("/requests")
@officer_required()
def requests_view(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
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
    return render_template("admin/requests.html", club=club, requests=rows)


@bp.route("/requests/<request_id>/approve", methods=("POST",))
@officer_required()
def approve_request(club_id, request_id):
    try:
        call_proc("sp_approve_join_request", (request_id,))
        flash("Request approved.", "success")
    except Exception as exc:
        flash(str(exc).split(":")[-1].strip(), "error")
    return redirect(url_for("admin.requests_view", club_id=club_id))


@bp.route("/requests/<request_id>/reject", methods=("POST",))
@officer_required()
def reject_request(club_id, request_id):
    execute(
        "UPDATE JoinRequest SET RequestStatus = 'Rejected' WHERE RequestID = %s AND ClubID = %s",
        (request_id, club_id),
    )
    flash("Request rejected.", "success")
    return redirect(url_for("admin.requests_view", club_id=club_id))


@bp.route("/events")
@officer_required()
def events_view(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    rows = query(
        """
        SELECT e.EventID, e.EventTitle, e.EventStartTime, e.EventStatus, e.EventVisibility,
               e.EventCapacity,
               (SELECT COUNT(*) FROM RSVP r WHERE r.EventID = e.EventID AND r.RSVPStatus='Going') AS going,
               (SELECT COUNT(*) FROM Attendance a WHERE a.EventID = e.EventID) AS attended
        FROM Event e WHERE e.ClubID = %s
        ORDER BY e.EventStartTime DESC
        """,
        (club_id,),
    )
    return render_template("admin/events.html", club=club, events=rows)


@bp.route("/events/new", methods=("GET", "POST"))
@officer_required()
def create_event(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    locations = query("SELECT LocationID, BuildingName, RoomNumber FROM Location ORDER BY BuildingName")
    types = query("SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName")

    if request.method == "POST":
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
                    request.form["title"].strip(),
                    request.form["description"].strip(),
                    datetime.fromisoformat(request.form["start"]),
                    datetime.fromisoformat(request.form["end"]),
                    int(request.form["capacity"]),
                    request.form["visibility"],
                    request.form["location_id"],
                    request.form["type_id"],
                    club_id,
                ),
            )
            flash("Event created.", "success")
            return redirect(url_for("admin.events_view", club_id=club_id))
        except Exception as exc:
            flash(str(exc).split(":")[-1].strip(), "error")

    return render_template(
        "admin/event_form.html",
        club=club,
        locations=locations,
        types=types,
        event=None,
    )


@bp.route("/events/<event_id>/edit", methods=("GET", "POST"))
@officer_required()
def edit_event(club_id, event_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    event = query("SELECT * FROM Event WHERE EventID = %s AND ClubID = %s", (event_id, club_id), one=True)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin.events_view", club_id=club_id))

    locations = query("SELECT LocationID, BuildingName, RoomNumber FROM Location ORDER BY BuildingName")
    types = query("SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName")

    if request.method == "POST":
        try:
            execute(
                """
                UPDATE Event SET EventTitle=%s, EventDescription=%s, EventStartTime=%s, EventEndTime=%s,
                                 EventCapacity=%s, EventVisibility=%s, LocationID=%s, EventTypeID=%s,
                                 EventStatus=%s
                WHERE EventID=%s AND ClubID=%s
                """,
                (
                    request.form["title"].strip(),
                    request.form["description"].strip(),
                    datetime.fromisoformat(request.form["start"]),
                    datetime.fromisoformat(request.form["end"]),
                    int(request.form["capacity"]),
                    request.form["visibility"],
                    request.form["location_id"],
                    request.form["type_id"],
                    request.form.get("status", "Scheduled"),
                    event_id,
                    club_id,
                ),
            )
            flash("Event updated.", "success")
            return redirect(url_for("admin.events_view", club_id=club_id))
        except Exception as exc:
            flash(str(exc).split(":")[-1].strip(), "error")

    return render_template(
        "admin/event_form.html",
        club=club,
        locations=locations,
        types=types,
        event=event,
    )


@bp.route("/events/<event_id>/delete", methods=("POST",))
@officer_required()
def delete_event(club_id, event_id):
    try:
        execute("DELETE FROM Attendance WHERE EventID = %s", (event_id,))
        execute("DELETE FROM RSVP WHERE EventID = %s", (event_id,))
        execute("DELETE FROM Event WHERE EventID = %s AND ClubID = %s", (event_id, club_id))
        flash("Event deleted.", "success")
    except Exception as exc:
        flash(str(exc).split(":")[-1].strip(), "error")
    return redirect(url_for("admin.events_view", club_id=club_id))


@bp.route("/events/<event_id>/attendance")
@officer_required()
def attendance(club_id, event_id):
    event = query(
        "SELECT EventID, EventTitle FROM Event WHERE EventID = %s AND ClubID = %s",
        (event_id, club_id),
        one=True,
    )
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin.events_view", club_id=club_id))

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
    return render_template("admin/attendance.html", club_id=club_id, event=event, rsvps=rsvps)


@bp.route("/events/<event_id>/checkin/<rsvp_id>", methods=("POST",))
@officer_required()
def officer_check_in(club_id, event_id, rsvp_id):
    exists = query(
        "SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s",
        (event_id, rsvp_id),
        one=True,
    )
    if exists:
        flash("Already checked in.", "message")
    else:
        execute(
            "INSERT INTO Attendance (EventID, RSVPID, CheckInMethod) VALUES (%s, %s, 'Manual')",
            (event_id, rsvp_id),
        )
        flash("Checked in.", "success")
    return redirect(url_for("admin.attendance", club_id=club_id, event_id=event_id))
