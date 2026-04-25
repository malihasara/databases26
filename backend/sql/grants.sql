DROP USER IF EXISTS 'club_dev'@'%';
CREATE USER 'club_dev'@'%' IDENTIFIED BY 'CHANGE_ME_DEV_PASSWORD';
GRANT ALL PRIVILEGES ON club_organizations.* TO 'club_dev'@'%';

DROP USER IF EXISTS 'club_app'@'%';
CREATE USER 'club_app'@'%' IDENTIFIED BY 'CHANGE_ME_APP_PASSWORD';

GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.User           TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.Club           TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.ClubMembership TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.JoinRequest    TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.Announcement   TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.Event          TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.RSVP           TO 'club_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON club_organizations.Attendance     TO 'club_app'@'%';

GRANT SELECT ON club_organizations.Category  TO 'club_app'@'%';
GRANT SELECT ON club_organizations.Location  TO 'club_app'@'%';
GRANT SELECT ON club_organizations.EventType TO 'club_app'@'%';

GRANT EXECUTE ON PROCEDURE club_organizations.sp_create_rsvp            TO 'club_app'@'%';
GRANT EXECUTE ON PROCEDURE club_organizations.sp_create_club_with_owner TO 'club_app'@'%';
GRANT EXECUTE ON PROCEDURE club_organizations.sp_approve_join_request   TO 'club_app'@'%';
GRANT EXECUTE ON FUNCTION  club_organizations.fn_event_seats_remaining  TO 'club_app'@'%';

FLUSH PRIVILEGES;
