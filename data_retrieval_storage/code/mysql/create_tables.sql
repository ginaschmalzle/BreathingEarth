USE breathingearth;

-- Create coordinate table
DROP TABLE IF EXISTS coordinates;
CREATE TABLE coordinates (
   site VARCHAR(10) PRIMARY KEY UNIQUE,
   lat FLOAT,
   lng FLOAT
);

-- Create position table
DROP TABLE IF EXISTS positions;
CREATE TABLE positions (
   site VARCHAR(10),
   Date VARCHAR(20),
   Up FLOAT,
   Sig FLOAT
);

-- Create medians table
DROP TABLE IF EXISTS medians;
CREATE TABLE medians (
   site VARCHAR(10),
   Date VARCHAR(20),
   rolling_median FLOAT
);

-- Create weather table
DROP TABLE IF EXISTS weather;
CREATE TABLE weather (
  PST VARCHAR(20) PRIMARY KEY UNIQUE,
  MaxTemperatureF FLOAT,
  MeanTemperatureF FLOAT,
  MinTemperatureF FLOAT,
  MaxDewPointF FLOAT,
  MeanDewPointF FLOAT,
  MinDewpointF FLOAT,
  MaxHumidity FLOAT,
  MeanHumidity FLOAT,
  MinHumidity FLOAT,
  MaxSeaLevelPressureIn FLOAT,
  MeanSeaLevelPressureIn FLOAT,
  MinSeaLevelPressureIn FLOAT,
  MaxVisibilityMiles FLOAT,
  MeanVisibilityMiles FLOAT,
  MinVisibilityMiles FLOAT,
  MaxWindSpeedMPH FLOAT,
  MeanWindSpeedMPH FLOAT,
  MaxGustSpeedMPH FLOAT,
  PrecipitationIn FLOAT,
  CloudCover FLOAT,
  Events VARCHAR(20),
  WindDirDegrees FLOAT
);
