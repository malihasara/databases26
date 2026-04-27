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
    IN p_officer_user_id CHAR(5)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;
        INSERT INTO Club (ClubID, ClubName, ClubDescription, ClubCreationDate)
        VALUES (p_club_id, p_name, p_desc, CURDATE());

        INSERT INTO ClubMembership
            (ClubID, UserID, MembershipRole, MembershipStatus, MembershipJoinDate)
        VALUES
            (p_club_id, p_officer_user_id, 'President', 'Active', CURDATE());
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
DROP TRIGGER IF EXISTS trg_protect_last_president_delete;
DELIMITER //
CREATE TRIGGER trg_protect_last_president_delete
BEFORE DELETE ON ClubMembership
FOR EACH ROW
BEGIN
    DECLARE remaining_leaders INT;
    DECLARE other_members INT;

    IF OLD.MembershipRole = 'President' THEN
        SELECT COUNT(*) INTO other_members
        FROM ClubMembership
        WHERE ClubID = OLD.ClubID AND NOT (UserID = OLD.UserID);

        IF other_members > 0 THEN
            SELECT COUNT(*) INTO remaining_leaders
            FROM ClubMembership
            WHERE ClubID = OLD.ClubID
              AND MembershipRole IN ('President','VicePresident','Officer')
              AND NOT (UserID = OLD.UserID);

            IF remaining_leaders = 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot remove the last leader while members remain.';
            END IF;
        END IF;
    END IF;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS sp_apply_member_action;
DELIMITER //
CREATE PROCEDURE sp_apply_member_action(IN p_request_id CHAR(5))
BEGIN
    DECLARE v_status   VARCHAR(10);
    DECLARE v_pres     TINYINT(1);
    DECLARE v_vp       TINYINT(1);
    DECLARE v_action   VARCHAR(20);
    DECLARE v_role     VARCHAR(15);
    DECLARE v_club     CHAR(5);
    DECLARE v_target   CHAR(5);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SELECT RequestStatus, PresApproved, VPApproved, ActionType, TargetRole, ClubID, TargetUserID
      INTO v_status, v_pres, v_vp, v_action, v_role, v_club, v_target
    FROM MemberActionRequest WHERE RequestID = p_request_id;

    IF v_status <> 'Pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Request is not pending.';
    END IF;
    IF v_pres = 0 OR v_vp = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Both President and Vice President must approve.';
    END IF;

    START TRANSACTION;
        IF v_action = 'Remove' THEN
            DELETE FROM ClubMembership WHERE ClubID = v_club AND UserID = v_target;
        ELSEIF v_action = 'Demote' THEN
            UPDATE ClubMembership SET MembershipRole = 'Member'
            WHERE ClubID = v_club AND UserID = v_target;
        ELSEIF v_action = 'PromoteOfficer' THEN
            UPDATE ClubMembership SET MembershipRole = 'Officer'
            WHERE ClubID = v_club AND UserID = v_target;
        ELSEIF v_action = 'PromoteVP' THEN
            UPDATE ClubMembership SET MembershipRole = 'VicePresident'
            WHERE ClubID = v_club AND UserID = v_target;
        ELSEIF v_action = 'PromotePresident' THEN
            UPDATE ClubMembership
              SET MembershipRole = CASE WHEN MembershipRole = 'President' THEN 'Officer'
                                        ELSE MembershipRole END
            WHERE ClubID = v_club;
            UPDATE ClubMembership SET MembershipRole = 'President'
            WHERE ClubID = v_club AND UserID = v_target;
        END IF;

        UPDATE MemberActionRequest
        SET RequestStatus = 'Approved', ResolvedTime = NOW()
        WHERE RequestID = p_request_id;
    COMMIT;
END //
DELIMITER ;
