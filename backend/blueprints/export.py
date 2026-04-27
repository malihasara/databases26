"""
export.py

CSV exports for club officers / admins: members roster and per-event
attendance.
"""

import csv
from io import StringIO
from flask import Blueprint, Response

from auth import officer_required
from db import query


bp = Blueprint("export", __name__)


def csv_response(rows, columns, filename):
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for r in rows:
        writer.writerow([r[c] for c in columns])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.route("/members.csv")
@officer_required()
def members_csv(club_id):
    rows = query(
        """
        SELECT u.UserID, u.FirstName, u.LastName, u.Email,
               cm.MembershipRole, cm.MembershipStatus, cm.MembershipJoinDate
        FROM ClubMembership cm JOIN User u ON u.UserID = cm.UserID
        WHERE cm.ClubID = %s
        ORDER BY cm.MembershipRole, u.LastName
        """,
        (club_id,),
    )
    cols = ["UserID", "FirstName", "LastName", "Email",
            "MembershipRole", "MembershipStatus", "MembershipJoinDate"]
    return csv_response(rows, cols, f"{club_id}_members.csv")


@bp.route("/events/<event_id>/attendance.csv")
@officer_required()
def attendance_csv(club_id, event_id):
    rows = query(
        """
        SELECT u.UserID, u.FirstName, u.LastName, u.Email,
               r.RSVPStatus, a.CheckInTime, a.CheckInMethod
        FROM RSVP r
        JOIN User u ON u.UserID = r.UserID
        LEFT JOIN Attendance a ON a.RSVPID = r.RSVPID AND a.EventID = r.EventID
        WHERE r.EventID = %s
        ORDER BY u.LastName
        """,
        (event_id,),
    )
    cols = ["UserID", "FirstName", "LastName", "Email",
            "RSVPStatus", "CheckInTime", "CheckInMethod"]
    return csv_response(rows, cols, f"{event_id}_attendance.csv")
