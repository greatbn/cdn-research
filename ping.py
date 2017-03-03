#!/usr/bin/python
"""
Author: Sa Pham Dang
Email: saphi070@gmail.com
"""
# coding=utf-8
import logging
import time
import re
from logging import handlers
from multiprocessing import Pool
import copy_reg
import types
from send_metric import InfluxDB
import netaddr
import subprocess
import redis
import ConfigParser

LOG = logging.getLogger("ping-subnet")
handler = handlers.SysLogHandler(address='/dev/log')
LOG.addHandler(handler)
LOG.setLevel(logging.DEBUG)


def _pickle_method(m):
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)


copy_reg.pickle(types.MethodType, _pickle_method)


class PingSubnet(object):
    """
    Ping subnet use multiprocessing
    """

    def __init__(self, subnet, num_process):
        self.subnet = subnet
        self.num_process = num_process

    def fping(self, subnet):
        """
        Ping all IP in a subnet
        """
        fping_output = ""
        try:
            fping_command = ['fping', '-a', '-q', '-e', '-g', subnet]
            fping_output = subprocess.Popen(fping_command,
                                            stdout=subprocess.PIPE).stdout.read()
        except Exception as e:
            LOG.error("Can't ping subnet: %s with an error: %s",
                      subnet,
                      e.message)
            return False
        fping_output = fping_output.splitlines()
        total_res_time = 0
        for res in fping_output:
            ip, res_time = self.parse(res)
            total_res_time += float(res_time)
        avg_time = 0
        if total_res_time != 0:
            avg_time = float(total_res_time/len(fping_output))
        metrics = {
            "subnet": subnet,
            "avg_time": avg_time
        }

        LOG.debug("Subnet: {0}, Avg Time: {1}".format(subnet,
                                                      str(avg_time)))
        return metrics

    def parse(self, string):
        """Parse result in ping"""
        parse = re.match("^((?:[0-9]{1,3}\.){3}[0-9]{1,3})\s\(((?:\d)*\.(?:\d)*|(?:\d)*)\sms\)$", string)
        parse_result = parse.groups()
        return parse_result[0], parse_result[1]

    def subnetting(self):
        """Subnet NetAddr to /24"""
        ip = netaddr.IPNetwork(addr=self.subnet)
        subnets = list(ip.subnet(prefixlen=24))
        list_subnets = [str(subnet) for subnet in subnets]
        return list_subnets

    def process(self):
        """Process list subnet"""
        list_subnets = self.subnetting()
        LOG.debug("Number of subnet: "+str(len(list_subnets)))
        p = Pool(self.num_process)
        start_time = time.time()
        result_ping = p.map(self.fping, list_subnets)
        end_time = time.time()
        LOG.debug("Result ping: " + str(result_ping))
        p.close()
        p.join()
        total_time = end_time - start_time
        LOG.debug("Total time: "+str(total_time))
        return result_ping


def get_config(config_file):
    """
    Get config from file
    example config file

    """
    config = ConfigParser.RawConfigParser()
    try:
        config.read(config_file)
    except:
        LOG.error("File ping.conf not found")
    data_center = config.get('DEFAULT', 'dc_name')
    num_process = config.get('DEFAULT', 'process')
    default = {}
    default = {
        "data_center": data_center,
        "num_process": num_process
    }
    influx_host = config.get('influxdb', 'host')
    influx_port = 8086
    try:
        influx_port = config.get('influxdb', 'port')
    except:
        pass
    influx_username = config.get('influxdb', 'username')
    influx_password = config.get('influxdb', 'password')
    influx_database = config.get('influxdb', 'database')
    influxdb_creds = {}
    influxdb_creds = {
        "host": influx_host,
        "port": influx_port,
        "database": influx_database,
        "username": influx_username,
        "password": influx_password
    }
    redis_creds = {}
    redis_host = config.get('redis', 'host')
    redis_port = 6379
    try:
        redis_port = config.get('redis', 'port')
    except:
        pass
    redis_password = config.get('redis', 'password')
    redis_creds = {
        "host": redis_host,
        "port": redis_port,
        "password": redis_password,
    }
    return default, influxdb_creds, redis_creds


def main():
    """
    Main function
    """
    config_file = "/etc/ping.conf"
    default, influxdb_creds, redis_creds = get_config(config_file)

    influx_path = 'ping'
    data_center = default['data_center']
    num_process = default['num_process']
    list_ip_file_name = "VN.zone"
    redis_key = data_center
    try:
        with open(list_ip_file_name, "r") as f:
            subnets = f.readlines()
            start_time = time.time()
            for subnet in subnets:
                ping = PingSubnet(subnet, num_process=int(num_process))

                out = ping.process()
                r = redis.Redis(host=redis_creds['host'],
                                port=redis_creds['port'],
                                password=redis_creds['password'])
                r.rpush(redis_key, out)
            end_time = time.time()
            total_time = end_time - start_time
            LOG.info("Total time: "+str(total_time))
            r = redis.Redis(host=redis_creds['host'],
                            port=redis_creds['port'],
                            password=redis_creds['password'])
            influx = InfluxDB(host=influxdb_creds['host'],
                              port=influxdb_creds['port'],
                              username=influxdb_creds['username'],
                              password=influxdb_creds['password'],
                              database=influxdb_creds['database'])
            for i in range(r.llen(redis_key)):
                influx.send_metric(metrics=r.lpop(redis_key),
                                   path=influx_path,
                                   data_center=data_center)
            LOG.info('Ping done')
    except Exception as e:
        LOG.error('Open file range IP failed: ' + e.message)


if __name__ == '__main__':
    main()
