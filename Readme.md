#### CDN Research

All resource about cdn what we research in KMA

##### How to use

- Requirements
  - influxdb
  - redis

Example Config file '/etc/ping.conf'

```
[DEFAULT]
dc_name = Ha-Noi
num_process = 8

[influxdb]
host = influxdb.sapham.net
database = ping3
username = ping
password = xxxxx

[redis]
host = 45.124.93.137
passsword = xxxxx
```

##### How to run

- Simple command

```sh
python ping.py
```
