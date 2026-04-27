"""
public.py

Unauthenticated browse endpoints: public club directory and public event list.
"""

from flask import Blueprint, jsonify, request

from db import query


bp = Blueprint("public", __name__)


@bp.get("/clubs")
def clubs():
    q = request.args.get("q", "").strip()
    sql = [
        "SELECT c.ClubID, c.ClubName, c.ClubDescription,",
        "       GROUP_CONCAT(DISTINCT cat.CategoryName ORDER BY cat.CategoryName SEPARATOR ', ') AS Categories",
        "FROM Club c",
        "LEFT JOIN ClubCategory cc ON cc.ClubID = c.ClubID",
        "LEFT JOIN Category cat   ON cat.CategoryID = cc.CategoryID",
    ]
    params = []
    if q:
        sql.append("WHERE c.ClubName LIKE %s")
        params.append(f"%{q}%")
    sql.append("GROUP BY c.ClubID, c.ClubName, c.ClubDescription")
    sql.append("ORDER BY c.ClubName")
    return jsonify(clubs=query(" ".join(sql), tuple(params)))


@bp.get("/events")
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
    return jsonify(events=query(" ".join(sql), tuple(params)))
