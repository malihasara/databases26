DROP TRIGGER IF EXISTS trg_rsvp_capacity_insert;
DELIMITER //
CREATE TRIGGER trg_rsvp_capacity_insert
BEFORE INSERT ON RSVP
FOR EACH ROW
BEGIN
    DECLARE current_going INT;
    DECLARE max_capacity  INT;

    IF NEW.RSVPStatus = 'Going' THEN
        SELECT EventCapacity INTO max_capacity
        FROM Event WHERE EventID = NEW.EventID;

        SELECT COUNT(*) INTO current_going
        FROM RSVP
        WHERE EventID = NEW.EventID AND RSVPStatus = 'Going';

        IF current_going >= max_capacity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot RSVP: event is at full capacity.';
        END IF;
    END IF;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_rsvp_capacity_update;
DELIMITER //
CREATE TRIGGER trg_rsvp_capacity_update
BEFORE UPDATE ON RSVP
FOR EACH ROW
BEGIN
    DECLARE current_going INT;
    DECLARE max_capacity  INT;

    IF NEW.RSVPStatus = 'Going' AND OLD.RSVPStatus <> 'Going' THEN
        SELECT EventCapacity INTO max_capacity
        FROM Event WHERE EventID = NEW.EventID;

        SELECT COUNT(*) INTO current_going
        FROM RSVP
        WHERE EventID = NEW.EventID AND RSVPStatus = 'Going';

        IF current_going >= max_capacity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot update RSVP: event is at full capacity.';
        END IF;
    END IF;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS fn_event_seats_remaining;
DELIMITER //
CREATE FUNCTION fn_event_seats_remaining(p_event_id CHAR(5))
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE cap INT;
    DECLARE going INT;

    SELECT EventCapacity INTO cap FROM Event WHERE EventID = p_event_id;
    SELECT COUNT(*) INTO going FROM RSVP
    WHERE EventID = p_event_id AND RSVPStatus = 'Going';

    RETURN cap - going;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_create_rsvp;
DELIMITER //
CREATE PROCEDURE sp_create_rsvp(
    IN p_rsvp_id CHAR(5),
    IN p_user_id CHAR(5),
    IN p_event_id CHAR(5),
    IN p_status   VARCHAR(10)
)
BEGIN
    DECLARE v_status     VARCHAR(15);
    DECLARE v_visibility VARCHAR(15);
    DECLARE v_club_id    CHAR(5);
    DECLARE v_existing   INT;
    DECLARE v_member     INT;

    SELECT EventStatus, EventVisibility, ClubID
      INTO v_status, v_visibility, v_club_id
    FROM Event WHERE EventID = p_event_id;

    IF v_status <> 'Scheduled' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot RSVP: event is not scheduled.';
    END IF;

    SELECT COUNT(*) INTO v_existing FROM RSVP
    WHERE UserID = p_user_id AND EventID = p_event_id;
    IF v_existing > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User already RSVP''d to this event.';
    END IF;

    IF v_visibility = 'MembersOnly' THEN
        SELECT COUNT(*) INTO v_member FROM ClubMembership
        WHERE UserID = p_user_id
          AND ClubID = v_club_id
          AND MembershipStatus = 'Active';
        IF v_member = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Members-only event: user is not an active member.';
        END IF;
    END IF;

    INSERT INTO RSVP (RSVPID, RSVPStatus, RSVPCreationDate, UserID, EventID)
    VALUES (p_rsvp_id, p_status, CURDATE(), p_user_id, p_event_id);
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_create_club_with_owner;
DROP PROCEDURE IF EXISTS sp_create_club_with_officer;
DELIMITER //
CREATE PROCEDURE sp_create_club_with_officer(
    IN p_club_id CHAR(5),
    IN p_name VARCHAR(80),
    IN p_desc TEXT,
    IN p_category_id CHAR(5),
    IN p_officer_user_id CHAR(5)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        INSERT INTO Club (ClubID, ClubName, ClubDescription, ClubCreationDate, CategoryID)
        VALUES (p_club_id, p_name, p_desc, CURDATE(), p_category_id);

        INSERT INTO ClubMembership
            (ClubID, UserID, MembershipRole, MembershipStatus, MembershipJoinDate)
        VALUES
            (p_club_id, p_officer_user_id, 'Officer', 'Active', CURDATE());
    COMMIT;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_approve_join_request;
DELIMITER //
CREATE PROCEDURE sp_approve_join_request(IN p_request_id CHAR(5))
BEGIN
    DECLARE v_user_id CHAR(5);
    DECLARE v_club_id CHAR(5);
    DECLARE v_status  VARCHAR(10);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SELECT UserID, ClubID, RequestStatus
      INTO v_user_id, v_club_id, v_status
    FROM JoinRequest WHERE RequestID = p_request_id;

    IF v_status <> 'Pending' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Join request is not pending.';
    END IF;

    START TRANSACTION;
        UPDATE JoinRequest SET RequestStatus = 'Approved'
        WHERE RequestID = p_request_id;

        INSERT INTO ClubMembership
            (ClubID, UserID, MembershipRole, MembershipStatus, MembershipJoinDate)
        VALUES
            (v_club_id, v_user_id, 'Member', 'Active', CURDATE())
        ON DUPLICATE KEY UPDATE
            MembershipStatus = 'Active';
    COMMIT;
END //
DELIMITER ;

DROP TRIGGER IF EXISTS trg_protect_last_owner_delete;
DROP TRIGGER IF EXISTS trg_protect_last_officer_delete;
DELIMITER //
CREATE TRIGGER trg_protect_last_officer_delete
BEFORE DELETE ON ClubMembership
FOR EACH ROW
BEGIN
    DECLARE remaining_officers INT;
    DECLARE other_members INT;

    IF OLD.MembershipRole = 'Officer' THEN
        SELECT COUNT(*) INTO other_members
        FROM ClubMembership
        WHERE ClubID = OLD.ClubID AND NOT (UserID = OLD.UserID);

        IF other_members > 0 THEN
            SELECT COUNT(*) INTO remaining_officers
            FROM ClubMembership
            WHERE ClubID = OLD.ClubID
              AND MembershipRole = 'Officer'
              AND NOT (UserID = OLD.UserID);

            IF remaining_officers = 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot remove the last Officer while members remain.';
            END IF;
        END IF;
    END IF;
END //
DELIMITER ;
