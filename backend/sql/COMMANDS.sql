-- ============================================================================
--  VioletConnect (Campus Club Management & Event Platform)
--  Single-file SQL bundle for Milestone 3 / Milestone 4 submission.
--
--  Sections:
--   1. Schema (CREATE DATABASE / CREATE TABLE + CHECK constraints)
--   2. Advanced PL/SQL (triggers, function, stored procedures)
--   3. Seed data (>=10 rows per table, realistic)
--   4. Database-level security (developer + application accounts; GRANTs)
--   5. Application-level SQL (every SELECT / INSERT / UPDATE / DELETE the
--      Flask backend issues, grouped by feature, with parameterized values
--      shown as %s).
--
--  Run order (fresh DB):
--    sections 1 -> 2 -> 3 -> 4
--  Section 5 is reference; the app issues these at runtime.
-- ============================================================================


-- ============================================================================
-- 1. SCHEMA
-- ============================================================================

DROP DATABASE IF EXISTS club_organizations;
CREATE DATABASE club_organizations;
USE club_organizations;

CREATE TABLE User (
    UserID              CHAR(5)         PRIMARY KEY,
    FirstName           VARCHAR(40)     NOT NULL,
    LastName            VARCHAR(40)     NOT NULL,
    Email               VARCHAR(100)    NOT NULL UNIQUE,
    PasswordHash        CHAR(60)        NOT NULL,
    AccountCreationDate DATE            NOT NULL,
    AccountStatus       VARCHAR(10)     NOT NULL DEFAULT 'Active',
    AccountType         VARCHAR(10)     NOT NULL DEFAULT 'Student',
    FacultyRequestStatus VARCHAR(10)    NOT NULL DEFAULT 'None',
    FacultyRequestTime  TIMESTAMP       NULL,
    CONSTRAINT chk_user_status   CHECK (AccountStatus       IN ('Active','Inactive')),
    CONSTRAINT chk_user_type     CHECK (AccountType         IN ('Student','Faculty')),
    CONSTRAINT chk_faculty_req   CHECK (FacultyRequestStatus IN ('None','Pending','Approved','Rejected'))
);

CREATE TABLE Category (
    CategoryID   CHAR(5)     PRIMARY KEY,
    CategoryName VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE Club (
    ClubID           CHAR(5)      PRIMARY KEY,
    ClubName         VARCHAR(80)  NOT NULL UNIQUE,
    ClubDescription  TEXT         NOT NULL,
    ClubCreationDate DATE         NOT NULL,
    CategoryID       CHAR(5)      NOT NULL,
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);

CREATE TABLE ClubMembership (
    ClubID             CHAR(5)     NOT NULL,
    UserID             CHAR(5)     NOT NULL,
    MembershipRole     VARCHAR(15) NOT NULL,
    MembershipStatus   VARCHAR(10) NOT NULL DEFAULT 'Active',
    MembershipJoinDate DATE        NOT NULL,
    PRIMARY KEY (ClubID, UserID),
    FOREIGN KEY (ClubID) REFERENCES Club(ClubID),
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    CONSTRAINT chk_membership_role   CHECK (MembershipRole   IN ('Officer','Member')),
    CONSTRAINT chk_membership_status CHECK (MembershipStatus IN ('Active','Inactive'))
);

CREATE TABLE JoinRequest (
    RequestID     CHAR(5)     PRIMARY KEY,
    RequestStatus VARCHAR(10) NOT NULL DEFAULT 'Pending',
    RequestTime   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ClubID        CHAR(5)     NOT NULL,
    UserID        CHAR(5)     NOT NULL,
    UNIQUE (ClubID, UserID, RequestStatus),
    FOREIGN KEY (ClubID) REFERENCES Club(ClubID),
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    CONSTRAINT chk_request_status CHECK (RequestStatus IN ('Pending','Approved','Rejected'))
);

CREATE TABLE Announcement (
    AnnouncementID         CHAR(5)      PRIMARY KEY,
    AnnouncementTitle      VARCHAR(100) NOT NULL,
    AnnouncementBody       TEXT         NOT NULL,
    AnnouncementDate       DATE         NOT NULL,
    AnnouncementVisibility VARCHAR(15)  NOT NULL DEFAULT 'Public',
    ClubID                 CHAR(5)      NOT NULL,
    UserID                 CHAR(5)      NOT NULL,
    FOREIGN KEY (ClubID) REFERENCES Club(ClubID),
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    CONSTRAINT chk_announce_vis CHECK (AnnouncementVisibility IN ('Public','MembersOnly'))
);

CREATE TABLE Location (
    LocationID   CHAR(5)      PRIMARY KEY,
    BuildingName VARCHAR(60)  NOT NULL,
    RoomNumber   VARCHAR(10)  NOT NULL,
    HomeAddress  VARCHAR(120) NOT NULL
);

CREATE TABLE EventType (
    EventTypeID   CHAR(5)     PRIMARY KEY,
    EventTypeName VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE Event (
    EventID          CHAR(5)      PRIMARY KEY,
    EventTitle       VARCHAR(100) NOT NULL,
    EventDescription TEXT         NOT NULL,
    EventStartTime   DATETIME     NOT NULL,
    EventEndTime     DATETIME     NOT NULL,
    EventCapacity    INT          NOT NULL,
    EventStatus      VARCHAR(15)  NOT NULL DEFAULT 'Scheduled',
    EventVisibility  VARCHAR(15)  NOT NULL DEFAULT 'Public',
    LocationID       CHAR(5)      NOT NULL,
    EventTypeID      CHAR(5)      NOT NULL,
    ClubID           CHAR(5)      NOT NULL,
    FOREIGN KEY (LocationID)  REFERENCES Location(LocationID),
    FOREIGN KEY (EventTypeID) REFERENCES EventType(EventTypeID),
    FOREIGN KEY (ClubID)      REFERENCES Club(ClubID),
    CONSTRAINT chk_event_status     CHECK (EventStatus     IN ('Scheduled','Cancelled','Completed')),
    CONSTRAINT chk_event_visibility CHECK (EventVisibility IN ('Public','MembersOnly')),
    CONSTRAINT chk_event_capacity   CHECK (EventCapacity > 0),
    CONSTRAINT chk_event_times      CHECK (EventEndTime > EventStartTime),
    INDEX idx_event_start (EventStartTime),
    INDEX idx_event_club (ClubID)
);

CREATE TABLE RSVP (
    RSVPID           CHAR(5)     PRIMARY KEY,
    RSVPStatus       VARCHAR(10) NOT NULL,
    RSVPCreationDate DATE        NOT NULL,
    EventID          CHAR(5)     NOT NULL,
    UserID           CHAR(5)     NOT NULL,
    UNIQUE (EventID, UserID),
    FOREIGN KEY (EventID) REFERENCES Event(EventID),
    FOREIGN KEY (UserID)  REFERENCES User(UserID),
    CONSTRAINT chk_rsvp_status CHECK (RSVPStatus IN ('Going','NotGoing','Tentative','NoShow'))
);

CREATE TABLE Attendance (
    EventID       CHAR(5)     NOT NULL,
    RSVPID        CHAR(5)     NOT NULL,
    CheckInTime   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CheckInMethod VARCHAR(20) NOT NULL DEFAULT 'Manual',
    PRIMARY KEY (EventID, RSVPID),
    FOREIGN KEY (RSVPID)  REFERENCES RSVP(RSVPID),
    FOREIGN KEY (EventID) REFERENCES Event(EventID),
    CONSTRAINT chk_checkin_method CHECK (CheckInMethod IN ('Manual','QRCode','SelfCheckIn'))
);


-- ============================================================================
-- 2. ADVANCED PL/SQL  (3 triggers, 1 function, 3 stored procedures)
-- ============================================================================

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


-- ============================================================================
-- 3. SEED DATA  (>=10 rows per table; bcrypt password hash is for "password123")
-- ============================================================================

INSERT INTO Category VALUES
('CA001','Sports'),
('CA002','Arts'),
('CA003','Academic'),
('CA004','Cultural'),
('CA005','Community Service'),
('CA006','Professional Development'),
('CA007','Hobbies'),
('CA008','Media'),
('CA009','Leadership'),
('CA010','STEM');

INSERT INTO User VALUES
('US001','Alice','Nguyen','alice@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-08-15','Active','Student','None',NULL),
('US002','Bob','Patel','bob@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-08-20','Active','Student','None',NULL),
('US003','Carol','Smith','carol@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-01','Active','Student','None',NULL),
('US004','David','Kim','david@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-05','Active','Student','None',NULL),
('US005','Emma','Lopez','emma@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-10','Active','Student','None',NULL),
('US006','Frank','Chen','frank@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-12','Active','Student','None',NULL),
('US007','Grace','Wong','grace@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-15','Active','Student','None',NULL),
('US008','Henry','Garcia','henry@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-20','Active','Student','None',NULL),
('US009','Ivy','Martinez','ivy@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-22','Active','Student','None',NULL),
('US010','Jack','Brown','jack@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-09-25','Active','Student','None',NULL),
('US011','Kara','Davis','kara@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-10-01','Active','Student','None',NULL),
('US012','Liam','Hall','liam@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-10-05','Active','Student','None',NULL),
('US013','Maliha','Admin','adminmaliha@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-08-01','Active','Faculty','None',NULL);

INSERT INTO Club VALUES
('CL001','Society of Asian Scientists & Engineers','Equips members with the skill set to succeed in professional environments.','2020-01-15','CA006'),
('CL002','Alpha Omega Epsilon','Professional and social sorority for women in engineering.','2019-09-10','CA009'),
('CL003','Business & Finance Group','Empowers Tandon students with comprehensive financial education.','2021-02-20','CA006'),
('CL004','Chemists Club','Bridges academia and industry in chemistry and chemical engineering.','2020-10-05','CA010'),
('CL005','oSTEM at NYU','Fosters a safe, supportive environment for all students in STEM.','2019-09-10','CA010'),
('CL006','Poly Anime Society','Promotes appreciation of Japanese culture and entertainment.','2021-01-25','CA007'),
('CL007','Poly Programming Club','Tandon competitive programming club.','2022-12-23','CA010'),
('CL008','Robotics Club','Relaxed learning environment for hands-on robotics.','2020-09-15','CA010'),
('CL009','Society of Women Engineers','Empowers women to succeed and advance in engineering.','2019-09-10','CA006'),
('CL010','Undergraduate Student Council','Primary student representatives and liaisons.','2018-09-11','CA009');

INSERT INTO ClubMembership VALUES
('CL001','US001','Officer','Active','2024-08-20'),
('CL001','US002','Officer','Active','2024-08-25'),
('CL001','US003','Member','Active','2024-09-02'),
('CL002','US005','Officer','Active','2024-09-12'),
('CL002','US007','Member','Active','2024-09-18'),
('CL003','US004','Officer','Active','2024-09-08'),
('CL004','US006','Officer','Active','2024-09-14'),
('CL005','US008','Officer','Active','2024-09-22'),
('CL005','US001','Member','Active','2024-09-25'),
('CL006','US009','Officer','Active','2024-09-25'),
('CL007','US010','Officer','Active','2024-09-28'),
('CL007','US002','Officer','Active','2024-10-01'),
('CL008','US011','Officer','Active','2024-10-03'),
('CL009','US012','Officer','Active','2024-10-07'),
('CL009','US003','Officer','Active','2024-10-08'),
('CL010','US001','Officer','Active','2024-10-10');

INSERT INTO JoinRequest (RequestID, RequestStatus, RequestTime, ClubID, UserID) VALUES
('JR001','Pending',  '2025-01-15 10:00:00','CL001','US004'),
('JR002','Approved', '2024-09-01 09:00:00','CL001','US003'),
('JR003','Pending',  '2025-01-16 11:00:00','CL003','US005'),
('JR004','Rejected', '2024-12-10 14:00:00','CL004','US007'),
('JR005','Pending',  '2025-01-18 13:00:00','CL007','US006'),
('JR006','Approved', '2024-10-05 10:00:00','CL007','US002'),
('JR007','Pending',  '2025-01-20 09:30:00','CL008','US001'),
('JR008','Pending',  '2025-01-21 16:00:00','CL009','US005'),
('JR009','Pending',  '2025-01-22 12:00:00','CL010','US008'),
('JR010','Pending',  '2025-01-23 15:00:00','CL002','US010');

INSERT INTO Location VALUES
('LO001','Rogers Hall','101','6 MetroTech Center, Brooklyn, NY 11201'),
('LO002','Jacobs Academic Building','674','370 Jay Street, Brooklyn, NY 11201'),
('LO003','Dibner Library','201','5 MetroTech Center, Brooklyn, NY 11201'),
('LO004','Tandon MakerSpace','100','6 MetroTech Center, Brooklyn, NY 11201'),
('LO005','Pfizer Auditorium','1','5 MetroTech Center, Brooklyn, NY 11201'),
('LO006','2 MetroTech Center','802','2 MetroTech Center, Brooklyn, NY 11201'),
('LO007','Rogers Hall','310','6 MetroTech Center, Brooklyn, NY 11201'),
('LO008','Jacobs Academic Building','473','370 Jay Street, Brooklyn, NY 11201'),
('LO009','Dibner Library','105','5 MetroTech Center, Brooklyn, NY 11201'),
('LO010','2 MetroTech Center','1001','2 MetroTech Center, Brooklyn, NY 11201');

INSERT INTO EventType VALUES
('ET001','Workshop'),
('ET002','Networking'),
('ET003','Social'),
('ET004','General Meeting'),
('ET005','Hackathon'),
('ET006','Seminar'),
('ET007','Competition'),
('ET008','Community Service'),
('ET009','Info Session'),
('ET010','Conference');

INSERT INTO Event VALUES
('EV001','SASE Networking Night','Connect with industry professionals and SASE alumni.','2026-05-15 18:00:00','2026-05-15 20:00:00',80,'Scheduled','Public','LO005','ET002','CL001'),
('EV002','AOE Sisters Social','A members-only social for current AOE sisters.','2026-05-20 17:00:00','2026-05-20 19:00:00',30,'Scheduled','MembersOnly','LO002','ET003','CL002'),
('EV003','BFG Stock Pitch Competition','Compete to deliver the best stock pitch to industry judges.','2026-06-05 14:00:00','2026-06-05 17:00:00',50,'Scheduled','Public','LO005','ET007','CL003'),
('EV004','Chem Club Lab Tour','Tour the chemistry research labs.','2026-04-28 11:00:00','2026-04-28 12:30:00',20,'Scheduled','MembersOnly','LO007','ET009','CL004'),
('EV005','oSTEM Study Session','Midterm study session, snacks provided.','2026-05-08 16:00:00','2026-05-08 19:00:00',40,'Scheduled','Public','LO003','ET003','CL005'),
('EV006','Anime Movie Night','Watch a classic Miyazaki film.','2026-06-12 19:00:00','2026-06-12 22:00:00',60,'Scheduled','Public','LO005','ET003','CL006'),
('EV007','PPC Weekly Practice','Weekly competitive programming practice.','2026-05-22 18:00:00','2026-05-22 20:00:00',35,'Scheduled','MembersOnly','LO008','ET004','CL007'),
('EV008','Robotics Arduino Workshop','Hands-on Arduino, build your first robot arm.','2026-06-01 13:00:00','2026-06-01 16:00:00',25,'Scheduled','Public','LO004','ET001','CL008'),
('EV009','SWE Resume Workshop','Get your resume reviewed by engineers.','2026-04-30 15:00:00','2026-04-30 17:00:00',45,'Scheduled','Public','LO002','ET001','CL009'),
('EV010','Student Council Town Hall','Open forum for students.','2026-05-01 12:00:00','2026-05-01 13:30:00',100,'Scheduled','Public','LO005','ET004','CL010'),
('EV011','SASE Hackathon 2026','24-hour hackathon, teams of up to 4.','2026-06-15 10:00:00','2026-06-16 10:00:00',120,'Scheduled','Public','LO006','ET005','CL001'),
('EV012','SWE Industry Panel','Hear from women engineers at top tech firms.','2026-06-20 17:00:00','2026-06-20 19:00:00',70,'Scheduled','Public','LO005','ET006','CL009');

INSERT INTO RSVP VALUES
('RS001','Going',    '2026-04-10','EV001','US001'),
('RS002','Going',    '2026-04-11','EV001','US002'),
('RS003','Tentative','2026-04-12','EV001','US003'),
('RS004','Going',    '2026-04-18','EV002','US005'),
('RS005','Going',    '2026-04-30','EV003','US004'),
('RS006','Going',    '2026-04-15','EV004','US006'),
('RS007','Going',    '2026-04-20','EV005','US008'),
('RS008','NotGoing', '2026-04-21','EV005','US001'),
('RS009','Going',    '2026-05-10','EV006','US009'),
('RS010','Going',    '2026-04-22','EV007','US010'),
('RS011','Tentative','2026-04-28','EV008','US011'),
('RS012','Going',    '2026-04-15','EV009','US012');

INSERT INTO Attendance VALUES
('EV001','RS001','2026-05-15 17:55:00','Manual'),
('EV001','RS002','2026-05-15 18:02:00','Manual'),
('EV002','RS004','2026-05-20 16:58:00','QRCode'),
('EV003','RS005','2026-06-05 13:50:00','Manual'),
('EV004','RS006','2026-04-28 10:55:00','QRCode'),
('EV005','RS007','2026-05-08 15:58:00','Manual'),
('EV006','RS009','2026-06-12 18:55:00','QRCode'),
('EV007','RS010','2026-05-22 17:50:00','Manual'),
('EV009','RS012','2026-04-30 14:55:00','QRCode'),
('EV001','RS003','2026-05-15 18:05:00','SelfCheckIn');

INSERT INTO Announcement VALUES
('AN001','Welcome!','Excited to welcome new members for the new semester.','2025-08-25','Public','CL001','US001'),
('AN002','Networking Night','Join us for a night of networking with industry professionals.','2025-09-10','Public','CL001','US001'),
('AN003','Volunteer Opportunity','Seeking volunteers for our community service event.','2025-09-20','Public','CL009','US012'),
('AN004','Study & Chill','Come hang out before finals.','2025-12-01','MembersOnly','CL001','US002'),
('AN005','Guest Speaker','Hosting a guest speaker from Google next week.','2025-10-15','Public','CL009','US003'),
('AN006','Hackathon Coming','Get ready for our hackathon. More details soon.','2025-11-01','Public','CL007','US010'),
('AN007','Mentor Day','Spend a day mentoring local high school students.','2025-10-05','Public','CL009','US012'),
('AN008','End of Semester Party','Food and drinks provided.','2025-12-15','MembersOnly','CL001','US001'),
('AN009','Resume Workshop','Resume workshop to help you prep for job search.','2025-09-30','Public','CL002','US005'),
('AN010','Arduino Workshop','Learn the basics of Arduino programming.','2025-10-20','Public','CL008','US011');


-- ============================================================================
-- 4. DATABASE-LEVEL SECURITY
--    Two MySQL accounts:
--      club_dev -> developers; full DDL/DML on club_organizations
--      club_app -> Flask app;  DML on user-touched tables, EXECUTE on routines,
--                              read-only on lookup tables, NO DDL.
-- ============================================================================

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

GRANT EXECUTE ON PROCEDURE club_organizations.sp_create_rsvp              TO 'club_app'@'%';
GRANT EXECUTE ON PROCEDURE club_organizations.sp_create_club_with_officer TO 'club_app'@'%';
GRANT EXECUTE ON PROCEDURE club_organizations.sp_approve_join_request     TO 'club_app'@'%';
GRANT EXECUTE ON FUNCTION  club_organizations.fn_event_seats_remaining    TO 'club_app'@'%';

FLUSH PRIVILEGES;


-- ============================================================================
-- 5. APPLICATION SQL  (everything the Flask backend issues at runtime).
--    Parameter values appear as %s; the app uses parameterized queries so
--    user input is never interpolated into the SQL string. Grouped by feature.
--
--    These statements are NOT executed when this file is run; they are listed
--    for the Milestone 3/4 "all SQL commands used by the app" requirement.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 5.1 Authentication & accounts  (auth.py)
-- ----------------------------------------------------------------------------

-- Load the logged-in user from the session cookie.
SELECT UserID, FirstName, LastName, Email, AccountType
FROM User WHERE UserID = %s;

-- Login: fetch user by email (only Active accounts can log in).
SELECT UserID, FirstName, LastName, Email, AccountType, PasswordHash
FROM User
WHERE Email = %s AND AccountStatus = 'Active';

-- Registration: ensure the email is not already taken.
SELECT 1 FROM User WHERE Email = %s;

-- Registration: create a Student account (default path).
INSERT INTO User
   (UserID, FirstName, LastName, Email, PasswordHash,
    AccountCreationDate, AccountStatus, AccountType)
VALUES (%s,%s,%s,%s,%s,%s,'Active','Student');

-- Registration: create a Student account that is requesting Faculty access.
INSERT INTO User
   (UserID, FirstName, LastName, Email, PasswordHash,
    AccountCreationDate, AccountStatus, AccountType,
    FacultyRequestStatus, FacultyRequestTime)
VALUES (%s,%s,%s,%s,%s,%s,'Active','Student','Pending', NOW());

-- Officer-required role check (used by @officer_required).
SELECT MembershipRole FROM ClubMembership
WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active';


-- ----------------------------------------------------------------------------
-- 5.2 My Clubs  (my_clubs.py)
-- ----------------------------------------------------------------------------

-- All active memberships for the logged-in user (split into managing/member
-- in the application layer based on MembershipRole).
SELECT c.ClubID, c.ClubName, c.ClubDescription,
       cm.MembershipRole, cm.MembershipStatus, cat.CategoryName
FROM ClubMembership cm
JOIN Club c       ON c.ClubID      = cm.ClubID
JOIN Category cat ON cat.CategoryID = c.CategoryID
WHERE cm.UserID = %s AND cm.MembershipStatus = 'Active'
ORDER BY c.ClubName;

-- Pending join requests for the logged-in user.
SELECT c.ClubID, c.ClubName, jr.RequestTime
FROM JoinRequest jr
JOIN Club c ON c.ClubID = jr.ClubID
WHERE jr.UserID = %s AND jr.RequestStatus = 'Pending'
ORDER BY jr.RequestTime DESC;


-- ----------------------------------------------------------------------------
-- 5.3 Club directory + detail  (clubs.py)
-- ----------------------------------------------------------------------------

-- Directory list with optional name filter, category filter, and sort
-- (sort is interpolated from a fixed allow-list, not user input).
SELECT c.ClubID, c.ClubName, c.ClubDescription, c.ClubCreationDate,
       cat.CategoryID, cat.CategoryName
FROM Club c
JOIN Category cat ON cat.CategoryID = c.CategoryID
WHERE 1=1
  AND c.ClubName  LIKE %s   -- only when q is provided
  AND c.CategoryID = %s     -- only when category is provided
ORDER BY c.ClubName;          -- or c.ClubCreationDate DESC

-- Categories drop-down.
SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName;

-- Club detail.
SELECT c.*, cat.CategoryName
FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID
WHERE c.ClubID = %s;

-- Membership status of the viewer for this club.
SELECT MembershipRole, MembershipStatus FROM ClubMembership
WHERE ClubID = %s AND UserID = %s;

-- Whether the viewer already has a pending join request.
SELECT 1 FROM JoinRequest
WHERE ClubID = %s AND UserID = %s AND RequestStatus = 'Pending';

-- Announcements visible to a member or to faculty.
SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody,
       AnnouncementDate, AnnouncementVisibility
FROM Announcement WHERE ClubID = %s
ORDER BY AnnouncementDate DESC LIMIT 10;

-- Announcements visible to non-members (Public only).
SELECT AnnouncementID, AnnouncementTitle, AnnouncementBody,
       AnnouncementDate, AnnouncementVisibility
FROM Announcement
WHERE ClubID = %s AND AnnouncementVisibility = 'Public'
ORDER BY AnnouncementDate DESC LIMIT 10;

-- Upcoming events visible to a member or to faculty.
SELECT EventID, EventTitle, EventStartTime, EventVisibility
FROM Event
WHERE ClubID = %s AND EventStatus = 'Scheduled' AND EventStartTime >= NOW()
ORDER BY EventStartTime;

-- Upcoming events visible to non-members (Public only).
SELECT EventID, EventTitle, EventStartTime, EventVisibility
FROM Event
WHERE ClubID = %s AND EventStatus = 'Scheduled'
  AND EventVisibility = 'Public' AND EventStartTime >= NOW()
ORDER BY EventStartTime;

-- "Already a member?" check before creating a join request.
SELECT 1 FROM ClubMembership
WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active';

-- "Already pending?" check.
SELECT 1 FROM JoinRequest
WHERE ClubID = %s AND UserID = %s AND RequestStatus = 'Pending';

-- Create a new join request.
INSERT INTO JoinRequest (RequestID, RequestStatus, ClubID, UserID)
VALUES (%s, 'Pending', %s, %s);

-- Leave a club.
DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s;


-- ----------------------------------------------------------------------------
-- 5.4 Events list, detail, RSVP, and check-in  (events.py)
-- ----------------------------------------------------------------------------

-- Events list for a faculty user (no visibility filter).
SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,
       e.EventEndTime, e.EventCapacity, e.EventStatus, e.EventVisibility,
       c.ClubID, c.ClubName, t.EventTypeName, l.BuildingName, l.RoomNumber
FROM Event e
JOIN Club c      ON c.ClubID      = e.ClubID
JOIN EventType t ON t.EventTypeID = e.EventTypeID
JOIN Location l  ON l.LocationID  = e.LocationID
WHERE e.EventStatus = 'Scheduled'
ORDER BY e.EventStartTime;

-- Events list for a non-faculty user (Public OR member of the hosting club).
SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,
       e.EventEndTime, e.EventCapacity, e.EventStatus, e.EventVisibility,
       c.ClubID, c.ClubName, t.EventTypeName, l.BuildingName, l.RoomNumber
FROM Event e
JOIN Club c      ON c.ClubID      = e.ClubID
JOIN EventType t ON t.EventTypeID = e.EventTypeID
JOIN Location l  ON l.LocationID  = e.LocationID
LEFT JOIN ClubMembership cm
       ON cm.ClubID = e.ClubID
      AND cm.UserID = %s
      AND cm.MembershipStatus = 'Active'
WHERE e.EventStatus = 'Scheduled'
  AND (e.EventVisibility = 'Public' OR cm.UserID IS NOT NULL)
ORDER BY e.EventStartTime;

-- Filter drop-downs for the events page.
SELECT ClubID, ClubName FROM Club ORDER BY ClubName;
SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName;

-- Event detail (uses fn_event_seats_remaining for the "seats left" counter).
SELECT e.*, c.ClubName, t.EventTypeName,
       l.BuildingName, l.RoomNumber, l.HomeAddress,
       fn_event_seats_remaining(e.EventID) AS SeatsLeft
FROM Event e
JOIN Club c      ON c.ClubID      = e.ClubID
JOIN EventType t ON t.EventTypeID = e.EventTypeID
JOIN Location l  ON l.LocationID  = e.LocationID
WHERE e.EventID = %s;

-- MembersOnly event: confirm the viewer is an active member of the host club.
SELECT 1 FROM ClubMembership
WHERE ClubID = %s AND UserID = %s AND MembershipStatus = 'Active';

-- The viewer's existing RSVP for this event (if any).
SELECT RSVPID, RSVPStatus FROM RSVP WHERE EventID = %s AND UserID = %s;

-- Gate RSVP creation/update on whether the event is still open.
SELECT EventEndTime, EventStatus FROM Event WHERE EventID = %s;

-- Has the viewer already checked in?
SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s;

-- "Going" RSVP count for an event.
SELECT COUNT(*) AS c FROM RSVP WHERE EventID = %s AND RSVPStatus = 'Going';

-- Update an existing RSVP's status.
UPDATE RSVP SET RSVPStatus = %s WHERE RSVPID = %s;

-- Create a new RSVP through the validating stored procedure.
CALL sp_create_rsvp(%s, %s, %s, %s);

-- The viewer's "Going" RSVP for this event (used by self check-in).
SELECT RSVPID FROM RSVP
WHERE EventID = %s AND UserID = %s AND RSVPStatus = 'Going';

-- Self check-in.
INSERT INTO Attendance (EventID, RSVPID, CheckInMethod)
VALUES (%s, %s, 'SelfCheckIn');


-- ----------------------------------------------------------------------------
-- 5.5 Officer / club-management portal  (admin.py)
-- ----------------------------------------------------------------------------

-- Club identity (for the dashboard header).
SELECT ClubID, ClubName FROM Club WHERE ClubID = %s;

-- Dashboard counts.
SELECT
  (SELECT COUNT(*) FROM ClubMembership WHERE ClubID=%s AND MembershipStatus='Active') AS members,
  (SELECT COUNT(*) FROM JoinRequest    WHERE ClubID=%s AND RequestStatus='Pending')   AS pending,
  (SELECT COUNT(*) FROM Event          WHERE ClubID=%s AND EventStatus='Scheduled')   AS events,
  (SELECT COUNT(*) FROM Announcement   WHERE ClubID=%s)                               AS posts;

-- Members table.
SELECT cm.UserID, cm.MembershipRole, cm.MembershipStatus, cm.MembershipJoinDate,
       u.FirstName, u.LastName, u.Email
FROM ClubMembership cm JOIN User u ON u.UserID = cm.UserID
WHERE cm.ClubID = %s
ORDER BY FIELD(cm.MembershipRole,'Officer','Member'), u.LastName;

-- Update a member's role.
UPDATE ClubMembership SET MembershipRole = %s WHERE ClubID = %s AND UserID = %s;

-- Remove a member (the trg_protect_last_officer_delete trigger guards the
-- "last officer with members remaining" case).
DELETE FROM ClubMembership WHERE ClubID = %s AND UserID = %s;

-- Join requests for a club (used by both officer and faculty views).
SELECT jr.RequestID, jr.RequestStatus, jr.RequestTime,
       u.UserID, u.FirstName, u.LastName, u.Email
FROM JoinRequest jr JOIN User u ON u.UserID = jr.UserID
WHERE jr.ClubID = %s
ORDER BY jr.RequestTime DESC;

-- Approve a join request (atomic via stored procedure).
CALL sp_approve_join_request(%s);

-- Reject a join request.
UPDATE JoinRequest SET RequestStatus = 'Rejected'
WHERE RequestID = %s AND ClubID = %s;

-- Club events with going / attended counts.
SELECT e.EventID, e.EventTitle, e.EventStartTime, e.EventStatus, e.EventVisibility,
       e.EventCapacity,
       (SELECT COUNT(*) FROM RSVP r       WHERE r.EventID = e.EventID AND r.RSVPStatus='Going') AS going,
       (SELECT COUNT(*) FROM Attendance a WHERE a.EventID = e.EventID)                          AS attended
FROM Event e
WHERE e.ClubID = %s
ORDER BY e.EventStartTime DESC;

-- Drop-down options for the event create/edit form.
SELECT LocationID, BuildingName, RoomNumber FROM Location ORDER BY BuildingName;
SELECT EventTypeID, EventTypeName FROM EventType ORDER BY EventTypeName;

-- Create a new event.
INSERT INTO Event (EventID, EventTitle, EventDescription, EventStartTime, EventEndTime,
                   EventCapacity, EventStatus, EventVisibility,
                   LocationID, EventTypeID, ClubID)
VALUES (%s,%s,%s,%s,%s,%s,'Scheduled',%s,%s,%s,%s);

-- Single-event fetch for the edit form.
SELECT * FROM Event WHERE EventID = %s AND ClubID = %s;

-- Edit an event.
UPDATE Event
SET EventTitle = %s, EventDescription = %s, EventStartTime = %s, EventEndTime = %s,
    EventCapacity = %s, EventVisibility = %s, LocationID = %s, EventTypeID = %s,
    EventStatus = %s
WHERE EventID = %s AND ClubID = %s;

-- Delete an event (cascades through Attendance and RSVP first).
DELETE FROM Attendance WHERE EventID = %s;
DELETE FROM RSVP       WHERE EventID = %s;
DELETE FROM Event      WHERE EventID = %s AND ClubID = %s;

-- Per-event attendance roster.
SELECT EventID, EventTitle FROM Event WHERE EventID = %s AND ClubID = %s;

SELECT r.RSVPID, r.RSVPStatus, u.FirstName, u.LastName, u.Email,
       a.CheckInTime, a.CheckInMethod
FROM RSVP r
JOIN User u ON u.UserID = r.UserID
LEFT JOIN Attendance a ON a.RSVPID = r.RSVPID AND a.EventID = r.EventID
WHERE r.EventID = %s
ORDER BY r.RSVPStatus, u.LastName;

-- Officer-driven manual check-in: marks the attendee Present. If they were
-- previously flagged NoShow we restore RSVPStatus to Going so the seat counts.
SELECT 1 FROM Attendance WHERE EventID = %s AND RSVPID = %s;
UPDATE RSVP SET RSVPStatus = 'Going'
WHERE RSVPID = %s AND RSVPStatus = 'NoShow';
INSERT INTO Attendance (EventID, RSVPID, CheckInMethod)
VALUES (%s, %s, 'Manual');

-- Officer marks an attendee as a no-show. We delete any stale Attendance row
-- and flip RSVPStatus to 'NoShow'; the capacity trigger only counts
-- RSVPStatus = 'Going', so the seat is freed for someone else.
SELECT EventID FROM RSVP WHERE RSVPID = %s;
DELETE FROM Attendance WHERE EventID = %s AND RSVPID = %s;
UPDATE RSVP SET RSVPStatus = 'NoShow' WHERE RSVPID = %s;

-- Officer resets an attendee back to "going, not yet checked in" — useful if
-- Present or NoShow was clicked by mistake.
SELECT EventID, RSVPStatus FROM RSVP WHERE RSVPID = %s;
DELETE FROM Attendance WHERE EventID = %s AND RSVPID = %s;
UPDATE RSVP SET RSVPStatus = 'Going'
WHERE RSVPID = %s;


-- ----------------------------------------------------------------------------
-- 5.6 Announcements  (announcements.py)
-- ----------------------------------------------------------------------------

-- Officer-side list (includes visibility for the role pill).
SELECT a.AnnouncementID, a.AnnouncementTitle, a.AnnouncementBody, a.AnnouncementDate,
       a.AnnouncementVisibility, u.FirstName, u.LastName
FROM Announcement a JOIN User u ON u.UserID = a.UserID
WHERE a.ClubID = %s
ORDER BY a.AnnouncementDate DESC;

-- Post a new announcement.
INSERT INTO Announcement (AnnouncementID, AnnouncementTitle, AnnouncementBody,
                          AnnouncementDate, AnnouncementVisibility, ClubID, UserID)
VALUES (%s, %s, %s, %s, %s, %s, %s);

-- Delete an announcement.
DELETE FROM Announcement WHERE AnnouncementID = %s AND ClubID = %s;


-- ----------------------------------------------------------------------------
-- 5.7 Faculty admin portal  (admin_portal.py)
-- ----------------------------------------------------------------------------

-- Platform-wide overview counts.
SELECT
  (SELECT COUNT(*) FROM User WHERE AccountStatus='Active')   AS users,
  (SELECT COUNT(*) FROM User WHERE AccountType='Faculty')    AS faculty,
  (SELECT COUNT(*) FROM Club)                                 AS clubs,
  (SELECT COUNT(*) FROM Event WHERE EventStatus='Scheduled') AS scheduled_events,
  (SELECT COUNT(*) FROM RSVP  WHERE RSVPStatus='Going')      AS going_rsvps,
  (SELECT COUNT(*) FROM Attendance)                          AS check_ins;

-- All clubs with rolled-up counts.
SELECT c.ClubID, c.ClubName, cat.CategoryName,
       (SELECT COUNT(*) FROM ClubMembership cm
          WHERE cm.ClubID = c.ClubID AND cm.MembershipStatus = 'Active')           AS members,
       (SELECT COUNT(*) FROM Event e
          WHERE e.ClubID = c.ClubID AND e.EventStatus = 'Scheduled')               AS events,
       (SELECT COUNT(*) FROM Attendance a JOIN Event e ON e.EventID = a.EventID
          WHERE e.ClubID = c.ClubID)                                                AS check_ins
FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID
ORDER BY c.ClubName;

-- All users with optional name/email search.
SELECT UserID, FirstName, LastName, Email,
       AccountType, AccountStatus, AccountCreationDate
FROM User
WHERE FirstName LIKE %s OR LastName LIKE %s OR Email LIKE %s   -- only when q
ORDER BY AccountType DESC, LastName;

-- Faculty-controlled mutations on user accounts.
UPDATE User SET AccountType   = %s WHERE UserID = %s;
UPDATE User SET AccountStatus = %s WHERE UserID = %s;

-- Pending faculty access requests.
SELECT UserID, FirstName, LastName, Email,
       FacultyRequestStatus, FacultyRequestTime
FROM User WHERE FacultyRequestStatus = 'Pending'
ORDER BY FacultyRequestTime;

-- Approve a faculty request.
SELECT FacultyRequestStatus FROM User WHERE UserID = %s;
UPDATE User SET AccountType = 'Faculty', FacultyRequestStatus = 'Approved'
WHERE UserID = %s;

-- Reject a faculty request.
UPDATE User SET FacultyRequestStatus = 'Rejected'
WHERE UserID = %s AND FacultyRequestStatus = 'Pending';

-- Cross-club attendance summary.
SELECT e.EventID, e.EventTitle, e.EventStartTime, c.ClubName,
       (SELECT COUNT(*) FROM RSVP r       WHERE r.EventID = e.EventID AND r.RSVPStatus='Going') AS going,
       (SELECT COUNT(*) FROM Attendance a WHERE a.EventID = e.EventID)                           AS attended,
       e.EventCapacity
FROM Event e JOIN Club c ON c.ClubID = e.ClubID
ORDER BY e.EventStartTime DESC LIMIT 100;

-- Create-club form options.
SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryName;
SELECT UserID, FirstName, LastName, Email FROM User
WHERE AccountStatus = 'Active' ORDER BY LastName, FirstName;

-- Create a club (atomically inserts the club and its initial Officer membership).
CALL sp_create_club_with_officer(%s, %s, %s, %s, %s);

-- Faculty deletion of a club: nuke dependent rows in topological order so
-- foreign keys and the trg_protect_last_officer_delete trigger are satisfied.
DELETE a FROM Attendance a
JOIN Event e ON e.EventID = a.EventID
WHERE e.ClubID = %s;

DELETE r FROM RSVP r
JOIN Event e ON e.EventID = r.EventID
WHERE e.ClubID = %s;

DELETE FROM Event        WHERE ClubID = %s;
DELETE FROM Announcement WHERE ClubID = %s;
DELETE FROM JoinRequest  WHERE ClubID = %s;

-- Demote all Officers to Member first so the last-officer trigger does not fire
-- while we tear the membership table down.
UPDATE ClubMembership SET MembershipRole = 'Member' WHERE ClubID = %s;
DELETE FROM ClubMembership WHERE ClubID = %s;

DELETE FROM Club WHERE ClubID = %s;


-- ----------------------------------------------------------------------------
-- 5.8 CSV exports  (export.py)
-- ----------------------------------------------------------------------------

-- Members CSV (officer or faculty).
SELECT u.UserID, u.FirstName, u.LastName, u.Email,
       cm.MembershipRole, cm.MembershipStatus, cm.MembershipJoinDate
FROM ClubMembership cm JOIN User u ON u.UserID = cm.UserID
WHERE cm.ClubID = %s
ORDER BY cm.MembershipRole, u.LastName;

-- Per-event attendance CSV.
SELECT u.UserID, u.FirstName, u.LastName, u.Email,
       r.RSVPStatus, a.CheckInTime, a.CheckInMethod
FROM RSVP r
JOIN User u ON u.UserID = r.UserID
LEFT JOIN Attendance a ON a.RSVPID = r.RSVPID AND a.EventID = r.EventID
WHERE r.EventID = %s
ORDER BY u.LastName;


-- ----------------------------------------------------------------------------
-- 5.9 Public (unauthenticated) browse  (public.py)
-- ----------------------------------------------------------------------------

-- Public club directory.
SELECT c.ClubID, c.ClubName, c.ClubDescription, cat.CategoryName
FROM Club c JOIN Category cat ON cat.CategoryID = c.CategoryID
WHERE c.ClubName LIKE %s   -- only when q
ORDER BY c.ClubName;

-- Public events list.
SELECT e.EventID, e.EventTitle, e.EventDescription, e.EventStartTime,
       c.ClubName, l.BuildingName, l.RoomNumber
FROM Event e
JOIN Club c     ON c.ClubID     = e.ClubID
JOIN Location l ON l.LocationID = e.LocationID
WHERE e.EventVisibility = 'Public' AND e.EventStatus = 'Scheduled'
  AND e.EventTitle LIKE %s   -- only when q
ORDER BY e.EventStartTime;


-- ----------------------------------------------------------------------------
-- 5.10 ID generation helper  (db.py: next_id)
-- ----------------------------------------------------------------------------

-- Read the largest existing ID with a given prefix; the application increments
-- the numeric portion and zero-pads back to width 3 (e.g., RS012 -> RS013).
SELECT %s AS id   -- placeholder; the actual call is shown below
FROM %s            -- table name is fixed in code (e.g., RSVP)
WHERE %s LIKE %s   -- column name + 'PREFIX%' literal
ORDER BY %s DESC LIMIT 1;
