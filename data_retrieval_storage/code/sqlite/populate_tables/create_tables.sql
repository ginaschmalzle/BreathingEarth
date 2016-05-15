-- Create coordinate table
DROP TABLE IF EXISTS coordinates;
CREATE TABLE coordinates (
   site TEXT PRIMARY KEY UNIQUE,
   lat NUMBER,
   lng NUMBER
);

-- Create position table
DROP TABLE IF EXISTS positions;
CREATE TABLE positions (
   site TEXT,
   Date TEXT,
   Up NUMBER,
   Sig NUMBER
);

-- Create medians table
DROP TABLE IF EXISTS medians;
CREATE TABLE medians (
   site TEXT,
   Date TEXT,
   rolling_median NUMBER
);
