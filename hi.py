#!/usr/bin/python3

# Heat Index: https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
# Windchill: https://www.weather.gov/media/epz/wxcalc/windChill.pdf
# Dewpoint: http://bmcnoldy.rsmas.miami.edu/Humidity.html

from influxdb import InfluxDBClient
import math
import configparser
from pathlib import Path
import sys
import logging

def write_db(metric,station,value,ts,valid=True):
    lineout=metric+",station="+station+",module=calc,valid="+str(valid)+" value="+str(value)+" "+str(ts)
    logging.info("write_db writing: "+lineout)
    client.write_points(lineout,protocol='line')

# defaults for hi & windchill if not present
HI=-1
CHILL=999
hi_valid=False
chill_valid=False

config = configparser.ConfigParser()
try:
    config.read_file(open(str(Path.home())+'/.config/hi/hi.ini'))
    user=config['database']['user']
    password=config['database']['password']
    dbname=config['database']['dbname']
    host=config['database']['host']
    module=config['station']['module']
    station=config['station']['station']
    enable_debug=config['misc'].getboolean('debug')
except Exception as E:
    sys.exit("Could not read config file: "+str(E))

if enable_debug:
    logging.basicConfig(level=logging.INFO)

temp_query="select last(value) from temperature where module=~/Outdoor/"
hum_query="select last(value) from humidity where module=~/Outdoor/"
wind_query="select last(value) from windstrength where module=~/Wind Gauge/"

client = InfluxDBClient(host=host,username=user,password=password, database=dbname)

t=client.query(temp_query,epoch="ns")
h=client.query(hum_query,epoch="ns")

Tc=next(t.get_points())["last"]         # Temp in C, needed for dewpoint calculation
T=Tc*1.8+32                             # Temp in F, needed for everything else
timestamp=next(t.get_points())["time"]
RH=next(h.get_points())["last"]

# Dewpoint doesn't have limits like wind chill & heat index, so calculate that first

TD=243.04*(math.log(RH/100)+((17.625*Tc)/(243.04+Tc)))/(17.625-math.log(RH/100)-((17.625*Tc)/(243.04+Tc)))
logging.info("TD calc: %d %d %d %d", timestamp, T, RH, TD)
write_db("dewpoint",station,TD,timestamp)

if T < 50:                  # Calculate wind chill
    chill_valid=True
    w=client.query(wind_query,epoch="ns")
    W=next(w.get_points())["last"]
    CHILL=((35.74+(0.6215 * T) - (35.75 * W**0.16) + (0.4275 * T * W**0.16))-32)
    logging.info("Windchill calc: %d %d %d %d",timestamp, T, W, CHILL)

if RH>=40 and T>=80:      # Calculate heat index
    hi_valid=True
    HI_simple = 0.5 * (T + 61.0 + ((T-68.0)*1.2) + (RH*0.094))
    if (T+HI_simple)/2 > 80:
        HI = -42.379 + 2.04901523*T + 10.14333127*RH - .22475541*T*RH - .00683783*T*T - .05481717*RH*RH + .00122874*T*T*RH + .00085282*T*RH*RH - .00000199*T*T*RH*RH
    else:
        HI=HI_simple
        logging.info("HI calc: %d %d %d %d %d",timestamp, T, RH, HI,HI_simple)
    
write_db("chill",station,CHILL,timestamp,chill_valid)
write_db("hi",station,HI,timestamp,hi_valid)
