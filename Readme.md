#### CDN Research

All resource about cdn what we research in KMA

##### How to install

- Requirements
  - influxdb-server
  - redis-server

- Install python library

```sh
pip install -r requirements.txt
```

- Install fping toool

  On Ubuntu

```
apt-get install -y fping
```
  On CentOS, RHEL

```sh
yum install -f fping
```

Example Config file '/etc/ping.conf'

```
[DEFAULT]
dc_name = Ha-Noi
process = 8

[influxdb]
host = influxdb.sapham.net
database = ping3
username = ping
password = xxxxx

[redis]
host = 45.124.93.137
password = xxxxx
```

##### How to run

- Simple command

```sh
python ping.py
```
