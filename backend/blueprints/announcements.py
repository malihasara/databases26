from datetime import date
from flask import Blueprint, g, jsonify, request

from auth import officer_required
from db import execute, query, next_id


bp = Blueprint("announcements", __name__)


@bp.get("/")
@officer_required()
def list_view(club_id):
    rows = query(
        """
        SELECT a.AnnouncementID, a.AnnouncementTitle, a.AnnouncementBody, a.AnnouncementDate,
               u.FirstName, u.LastName
        FROM Announcement a JOIN User u ON u.UserID = a.UserID
        WHERE a.ClubID = %s
        ORDER BY a.AnnouncementDate DESC
        """,
        (club_id,),
    )
    return jsonify(announcements=rows)


@bp.post("/")
@officer_required()
def create(club_id):
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    text = (body.get("body") or "").strip()
    if not (title and text):
        return jsonify(error="title and body required"), 400
    new_id = next_id("AN", "Announcement", "AnnouncementID")
    execute(
        "INSERT INTO Announcement (AnnouncementID, AnnouncementTitle, AnnouncementBody, "
        "AnnouncementDate, ClubID, UserID) VALUES (%s, %s, %s, %s, %s, %s)",
        (new_id, title, text, date.today(), club_id, g.user["UserID"]),
    )
    return jsonify(ok=True, announcement_id=new_id)


@bp.post("/<announcement_id>/delete")
@officer_required()
def delete(club_id, announcement_id):
    execute(
        "DELETE FROM Announcement WHERE AnnouncementID = %s AND ClubID = %s",
        (announcement_id, club_id),
    )
    return jsonify(ok=True)
