from flask import Blueprint, g, render_template

from auth import login_required
from db import query


bp = Blueprint("my_clubs", __name__, url_prefix="/my-clubs")


@bp.route("/")
@login_required
def index():
    memberships = query(
        """
        SELECT c.ClubID, c.ClubName, c.ClubDescription,
               cm.MembershipRole, cm.MembershipStatus, cat.CategoryName
        FROM ClubMembership cm
        JOIN Club c        ON c.ClubID = cm.ClubID
        JOIN Category cat  ON cat.CategoryID = c.CategoryID
        WHERE cm.UserID = %s
        ORDER BY c.ClubName
        """,
        (g.user["UserID"],),
    )
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
    return render_template("my_clubs.html", memberships=memberships, pending=pending)
