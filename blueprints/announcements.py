from datetime import date
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from auth import officer_required
from db import execute, query, next_id


bp = Blueprint("announcements", __name__, url_prefix="/admin/<club_id>/announcements")


@bp.route("/")
@officer_required()
def list_view(club_id):
    club = query("SELECT ClubID, ClubName FROM Club WHERE ClubID = %s", (club_id,), one=True)
    rows = query(
        """
        SELECT a.AnnouncementID, a.AnnouncementTitle, a.AnnouncementDate,
               u.FirstName, u.LastName
        FROM Announcement a JOIN User u ON u.UserID = a.UserID
        WHERE a.ClubID = %s
        ORDER BY a.AnnouncementDate DESC
        """,
        (club_id,),
    )
    return render_template("admin/announcements.html", club=club, announcements=rows)


@bp.route("/new", methods=("POST",))
@officer_required()
def create(club_id):
    title = request.form["title"].strip()
    body = request.form["body"].strip()
    if not (title and body):
        flash("Title and body are required.", "error")
        return redirect(url_for("announcements.list_view", club_id=club_id))
    new_id = next_id("AN", "Announcement", "AnnouncementID")
    execute(
        "INSERT INTO Announcement (AnnouncementID, AnnouncementTitle, AnnouncementBody, "
        "AnnouncementDate, ClubID, UserID) VALUES (%s, %s, %s, %s, %s, %s)",
        (new_id, title, body, date.today(), club_id, g.user["UserID"]),
    )
    flash("Announcement posted.", "success")
    return redirect(url_for("announcements.list_view", club_id=club_id))


@bp.route("/<announcement_id>/delete", methods=("POST",))
@officer_required()
def delete(club_id, announcement_id):
    execute(
        "DELETE FROM Announcement WHERE AnnouncementID = %s AND ClubID = %s",
        (announcement_id, club_id),
    )
    flash("Announcement deleted.", "success")
    return redirect(url_for("announcements.list_view", club_id=club_id))
