

air_pressure_col = ["air_pressure_local", "air_pressure_sea"]

humidity_col = ["humidity_mean", "humidity_min"]

weather_col = ["weather_noon", "weather_night"]

daily_columns_s1 = ["day", *air_pressure_col, "precipitation_sum", "precipitation_hourly_max",
                    "precipitation_10min_max", "temperature_mean", "temperature_max", "temperature_min", *humidity_col,
                    "wind_speed_mean", "wind_speed_max", "wind_speed_max_direction",
                    "wind_instantaneous_speed_max", "wind_instantaneous_speed_direction", "day_length", "snow_sum",
                    "snow_max_depth", *weather_col]

daily_columns_a1 = [col for col in daily_columns_s1 if col not in [*air_pressure_col, *humidity_col, *weather_col]]

hourly_columns_s1 = ["hour", *air_pressure_col, "precipitation", "temperature", "dew_point_temperature",
                     "vapor_pressure", "humidity", "wind_speed", "wind_direction", "day_length",
                     "globa_solar_radiation", "snow_fall", "fallen_snow", "weather", "cloud_cover", "visibility"]

