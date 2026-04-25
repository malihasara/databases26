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
    CONSTRAINT chk_membership_role   CHECK (MembershipRole   IN ('Owner','Officer','Member')),
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
    AnnouncementID    CHAR(5)      PRIMARY KEY,
    AnnouncementTitle VARCHAR(100) NOT NULL,
    AnnouncementBody  TEXT         NOT NULL,
    AnnouncementDate  DATE         NOT NULL,
    ClubID            CHAR(5)      NOT NULL,
    UserID            CHAR(5)      NOT NULL,
    FOREIGN KEY (ClubID) REFERENCES Club(ClubID),
    FOREIGN KEY (UserID) REFERENCES User(UserID)
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
    CONSTRAINT chk_rsvp_status CHECK (RSVPStatus IN ('Going','NotGoing','Tentative'))
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
