#!/usr/bin/python
# coding=utf-8
from influxdb import InfluxDBClient


class InfluxDB(object):
    """
    Connect to influxdb and send metric
    """

    def __init__(self, host, port, username,
                 password, database,):
        """
        Init
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.influx = self.get_influxdb_client()

    def get_influxdb_client(self):
        """
        Return influxdb client
        """

        return InfluxDBClient(host=self.host, port=self.port,
                              username=self.username, password=self.password,
                              database=self.database)

    def send_metric(self, metrics, path, data_center):
        """
        Send metric to database
        """
        metrics = []
        # build metric
        for m in metrics:
            metrics.append({
                "measurement": path,
                "tags": {
                    "data_center": data_center,
                    "subnet": m['subnet']
                },
                "fields": {
                    "value": float(m['avg_time'])
                }
            })
        self.influx.write_points(metrics)
        self.dis_connect()

    def dis_connect(self):
        self.influx = None
