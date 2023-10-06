#!/usr/bin/env python3
# encoding=utf-8

""" See github.com/dkozinn/weather-station for details """

import configparser
import sys
from pathlib import Path

import lnetatmo
from influxdb import InfluxDBClient

authorization = lnetatmo.ClientAuth()
config = configparser.ConfigParser()
try:
    with open(str(Path.home()) + "/.config/hi/hi.ini") as myConfig: # pylint: disable=unspecified-encoding
        config.read_file(myConfig)
    user = config["database"]["user"]
    password = config["database"]["password"]
    dbname = config["database"]["dbname"]
    host = config["database"]["host"]
except FileNotFoundError as E:
    sys.exit(f"Could not read config file: {str(E)}")

weatherData = lnetatmo.WeatherStationData(authorization)

client = InfluxDBClient(host=host, username=user, password=password)
if {"name": "netatmo"} not in client.get_list_database():
    client.create_database("netatmo")

for station in weatherData.stations:
    station_data = []
    module_data = []
    station = weatherData.stationById(station)
    station_name = station["station_name"]
    altitude = station["place"]["altitude"]
    country = station["place"]["country"]
    timezone = station["place"]["timezone"]
    longitude = station["place"]["location"][0]
    latitude = station["place"]["location"][1]
    for module, moduleData in weatherData.lastData(exclude=3600).items():
        for measurement in ["altitude", "country", "longitude", "latitude", "timezone"]:
            value = eval(measurement)  # pylint: disable=eval-used
            if isinstance(value, int):
                value = float(value)
            station_data.append(
                {
                    "measurement": measurement,
                    "tags": {"station": station_name, "module": module},
                    "time": moduleData["When"],
                    "fields": {"value": value},
                }
            )

        for sensor, value in moduleData.items():
            if sensor.lower() != "when":
                if isinstance(value, int):
                    value = float(value)
                module_data.append(
                    {
                        "measurement": sensor.lower(),
                        "tags": {"station": station_name, "module": module},
                        "time": moduleData["When"],
                        "fields": {"value": value},
                    }
                )

    client.write_points(station_data, time_precision="s", database="netatmo")
    client.write_points(module_data, time_precision="s", database="netatmo")
