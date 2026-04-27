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
('US013','Maliha','Admin','adminmaliha@nyu.edu','$2b$12$kf7YoZyG1sbvrPXvBvsFs.OkUgtKW9fdcCSNXzTnqCP8NPi1Q0Jpu','2024-08-01','Active','Admin','None',NULL);

INSERT INTO Club VALUES
('CL001','Society of Asian Scientists & Engineers','Equips members with the skill set to succeed in professional environments.','2020-01-15'),
('CL002','Alpha Omega Epsilon','Professional and social sorority for women in engineering.','2019-09-10'),
('CL003','Business & Finance Group','Empowers Tandon students with comprehensive financial education.','2021-02-20'),
('CL004','Chemists Club','Bridges academia and industry in chemistry and chemical engineering.','2020-10-05'),
('CL005','oSTEM at NYU','Fosters a safe, supportive environment for all students in STEM.','2019-09-10'),
('CL006','Poly Anime Society','Promotes appreciation of Japanese culture and entertainment.','2021-01-25'),
('CL007','Poly Programming Club','Tandon competitive programming club.','2022-12-23'),
('CL008','Robotics Club','Relaxed learning environment for hands-on robotics.','2020-09-15'),
('CL009','Society of Women Engineers','Empowers women to succeed and advance in engineering.','2019-09-10'),
('CL010','Undergraduate Student Council','Primary student representatives and liaisons.','2018-09-11');

INSERT INTO ClubCategory VALUES
('CL001','CA006'),('CL001','CA010'),
('CL002','CA009'),('CL002','CA006'),
('CL003','CA006'),('CL003','CA003'),
('CL004','CA010'),('CL004','CA003'),
('CL005','CA010'),('CL005','CA005'),
('CL006','CA007'),('CL006','CA004'),
('CL007','CA010'),('CL007','CA003'),
('CL008','CA010'),('CL008','CA007'),
('CL009','CA006'),('CL009','CA009'),
('CL010','CA009'),('CL010','CA005');

INSERT INTO ClubMembership VALUES
('CL001','US001','President','Active','2024-08-20'),
('CL001','US002','VicePresident','Active','2024-08-25'),
('CL001','US003','Member','Active','2024-09-02'),
('CL002','US005','President','Active','2024-09-12'),
('CL002','US007','Member','Active','2024-09-18'),
('CL003','US004','President','Active','2024-09-08'),
('CL004','US006','President','Active','2024-09-14'),
('CL005','US008','President','Active','2024-09-22'),
('CL005','US001','Member','Active','2024-09-25'),
('CL006','US009','President','Active','2024-09-25'),
('CL007','US010','President','Active','2024-09-28'),
('CL007','US002','VicePresident','Active','2024-10-01'),
('CL008','US011','President','Active','2024-10-03'),
('CL009','US012','President','Active','2024-10-07'),
('CL009','US003','VicePresident','Active','2024-10-08'),
('CL010','US001','President','Active','2024-10-10');

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
