"""
my_clubs.py

The signed-in user's club roster, split into clubs they lead vs. clubs they're
a member of, plus their pending join + club-creation requests.
"""

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
               cm.MembershipRole, cm.MembershipStatus,
               GROUP_CONCAT(DISTINCT cat.CategoryName ORDER BY cat.CategoryName SEPARATOR ', ') AS Categories
        FROM ClubMembership cm
        JOIN Club c ON c.ClubID = cm.ClubID
        LEFT JOIN ClubCategory cc ON cc.ClubID = c.ClubID
        LEFT JOIN Category cat   ON cat.CategoryID = cc.CategoryID
        WHERE cm.UserID = %s AND cm.MembershipStatus = 'Active'
        GROUP BY c.ClubID, c.ClubName, c.ClubDescription, cm.MembershipRole, cm.MembershipStatus
        ORDER BY c.ClubName
        """,
        (g.user["UserID"],),
    )
    leaders = ("President", "VicePresident", "Officer")
    managing = [r for r in rows if r["MembershipRole"] in leaders]
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
    pending_clubs = query(
        """
        SELECT RequestID, ProposedName, RequestStatus, RequestTime
        FROM ClubCreationRequest
        WHERE RequestedByUserID = %s AND RequestStatus = 'Pending'
        ORDER BY RequestTime DESC
        """,
        (g.user["UserID"],),
    )
    return jsonify(managing=managing, member=member, pending=pending, pending_clubs=pending_clubs)
