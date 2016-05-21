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

-- Create weather table
DROP TABLE IF EXISTS weather;
CREATE TABLE weather (
  PST TEXT PRIMARY KEY UNIQUE,
  MaxTemperatureF NUMBER,
  MeanTemperatureF NUMBER,
  MinTemperatureF NUMBER,
  MaxDewPointF NUMBER,
  MeanDewPointF NUMBER,
  MinDewpointF NUMBER,
  MaxHumidity NUMBER,
  MeanHumidity NUMBER,
  MinHumidity NUMBER,
  MaxSeaLevelPressureIn NUMBER,
  MeanSeaLevelPressureIn NUMBER,
  MinSea LevelPressureIn NUMBER,
  MaxVisibilityMiles NUMBER,
  MeanVisibilityMiles NUMBER,
  MinVisibilityMiles NUMBER,
  MaxWindSpeedMPH NUMBER,
  MeanWindSpeedMPH NUMBER,
  MaxGustSpeedMPH NUMBER,
  PrecipitationIn NUMBER,
  CloudCover NUMBER,
  Events TEXT,
  WindDirDegrees NUMBER
);
