#!/usr/bin/python
# coding=utf-8
from influxdb import InfluxDBClient
import time

class InfluxDB(object):

    def __init__(self, host, port, username, password,
                 database, metrics, path, data_center
                 ):
        """
        Init 
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.influx = self.get_influxdb_client()
        self.metrics = metrics
        self.path = path
        self.data_center = data_center

    def get_influxdb_client(self):
        """
        Return influxdb client
        """

        return InfluxDBClient(host=self.host, port=self.port,
                              username=self.username, password=self.password,
                              database=self.database)

    def send_metric(self):
        """
        Send metric to database
        """
        metrics = []
        time_stamp = time.time()
        # build metric 
        for m in self.metrics:
            metrics.append({
                "measurement": self.path,
                "tags": {
                    "data_center": self.data_center,
                    "ip": m['ip']
                },
                #"time": time_stamp,
                "fields": {
                    "value": m['time']
                }
            })
        self.influx.write_points(metrics)
        self.dis_connect()

    def dis_connect(self):
        self.influx = None
        
