from flask import Blueprint, g, jsonify

from auth import login_required
from db import query


bp = Blueprint("my_clubs", __name__)


@bp.get("/")
@login_required
def list_my_clubs():
    rows = query(
        """
        SELECT c.ClubID, c.ClubName, c.ClubDescription,
               cm.MembershipRole, cm.MembershipStatus, cat.CategoryName
        FROM ClubMembership cm
        JOIN Club c       ON c.ClubID      = cm.ClubID
        JOIN Category cat ON cat.CategoryID = c.CategoryID
        WHERE cm.UserID = %s AND cm.MembershipStatus = 'Active'
        ORDER BY c.ClubName
        """,
        (g.user["UserID"],),
    )
    managing = [r for r in rows if r["MembershipRole"] == "Officer"]
    member   = [r for r in rows if r["MembershipRole"] == "Member"]

    pending = query(
        """
        SELECT c.ClubID, c.ClubName, jr.RequestTime
        FROM JoinRequest jr
        JOIN Club c ON c.ClubID = jr.ClubID
        WHERE jr.UserID = %s AND jr.RequestStatus = 'Pending'
        ORDER BY jr.RequestTime DESC
        """,
        (g.user["UserID"],),
    )
    return jsonify(managing=managing, member=member, pending=pending)
