# cs480proj

CREATE TABLE Manager (
    ssn INT PRIMARY KEY,
    name TEXT,
    email TEXT
);

CREATE TABLE Manager (
    ssn INT PRIMARY KEY,
    name TEXT,
    email TEXT
);

CREATE TABLE Address (
    road_name TEXT,
    number INT,
    city TEXT,
    PRIMARY KEY (road_name, number, city)
);

CREATE TABLE LivesIn_Client (
    email TEXT REFERENCES Client(email),
    road_name TEXT,
    number INT,
    city TEXT,
    PRIMARY KEY (email, road_name, number, city),
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

-- DRIVER
CREATE TABLE Driver (
    name TEXT PRIMARY KEY,
    road_name TEXT,
    number INT,
    city TEXT,
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

CREATE TABLE Driver (
    name TEXT PRIMARY KEY,
    road_name TEXT,
    number INT,
    city TEXT,
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

CREATE TABLE CreditCard (
    card_num TEXT PRIMARY KEY,
    email TEXT REFERENCES Client(email),
    road_name TEXT,
    number INT,
    city TEXT,
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

CREATE TABLE Car (
    carid TEXT PRIMARY KEY,
    brand TEXT
);

CREATE TABLE Model (
    modelid TEXT PRIMARY KEY,
    carid TEXT REFERENCES Car(carid),
    color TEXT,
    construction_year INT,
    transmission TEXT
);

CREATE TABLE CanDrive (
    driver_name TEXT,
    modelid TEXT,
    PRIMARY KEY (driver_name, modelid),
    FOREIGN KEY (driver_name) REFERENCES Driver(name),
    FOREIGN KEY (modelid) REFERENCES Model(modelid)
);

CREATE TABLE Rent (
    rentid TEXT PRIMARY KEY,
    rent_date DATE,
    client_email TEXT REFERENCES Client(email),
    driver_name TEXT REFERENCES Driver(name),
    modelid TEXT REFERENCES Model(modelid)
);

CREATE TABLE Review (
    reviewid TEXT PRIMARY KEY,
    name TEXT REFERENCES Driver(name),
    message TEXT,
    rating INT CHECK (rating >= 0 AND rating <= 5)
);

CREATE TABLE Written_By (
    email TEXT REFERENCES Client(email),
    reviewid TEXT REFERENCES Review(reviewid),
    PRIMARY KEY (email, reviewid)
);

