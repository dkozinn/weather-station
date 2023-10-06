# grafana-netatmo
Netatmo Weather Station dashboard for Grafana

https://grafana.com/grafana/dashboards/12378

![Screenshot](https://raw.githubusercontent.com/florianbeer/grafana-netatmo/master/screenshot.png)

## Installation

##### TODO - Update required configuration

* Create a [Netatmo developer account](https://dev.netatmo.com/apidocumentation) and fill in your CLIENT_ID, CLIENT_SECRET, USERNAME and PASSWORD in the script.
* This script assumes you have InfluxDB running on the same machine as this script and it uses no authentication.
* Create a cron job to run the script periodically e.g.

```
# cat /etc/cron.d/netatmo
*/5 * * * * root  /usr/local/bin/netatmo_influx.py > /dev/null 2>&1
```

## Calculated values

Running ```hi.py``` via cron will calculate dewpoint and optionally heat index or wind chill if the temperature and humidity fall into the valid ranges. By default, these values will be inserted into Influx from a module named **calc** with measurement names **dewpoint**, **hi**, and **windchill**.

Configuration to run ```netatmo_influx.py``` and ```hi.py``` must be provided in the ```hi.ini``` file which must be located at ```$HOME/.config/hi/hi.ini```.

### Known issues

* The calculated values are computed and saved in the db inconsistently. Heat index is stored in degrees C, dewpoint and wind chill are stored in degrees F. Issue [#3](https://github.com/dkozinn/weather-station/issues/3) will eventually fix this.