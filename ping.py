#!/usr/bin/python
"""
Author: Sa Pham Dang
Email: saphi070@gmail.com
"""
# coding=utf-8
import subprocess
import re
import logging
from logging import handlers
from multiprocessing import Pool
import time
import copy_reg
import types
from send_metric import InfluxDB

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

    def __init__(self, subnets, num_process):
        self.subnets = subnets
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
            LOG.error("Can't ping subnet: %s with an error: %s", subnet, e.message )
        return fping_output.splitlines()

    def parse(self, string):
        parse = re.match("^((?:[0-9]{1,3}\.){3}[0-9]{1,3})\s\(((?:\d)*\.(?:\d)*|(?:\d)*)\sms\)$", string)
        parse_result = parse.groups()
        return parse_result[0], parse_result[1]

    def process(self):
        """
        Return a list result.
        Pattern: IP*time
        example: 192.168.1.2*time
        """
        list_result = []
        result = {}
        p = Pool(self.num_process)
        start_time = time.time()
        result_ping = p.map(self.fping, self.subnets)
        end_time = time.time()
        LOG.debug("Result ping: " + str(result_ping))
        p.close()
        p.join()
        total_time = end_time - start_time
        LOG.debug("Total time: "+str(total_time))
        LOG.debug("ok")
        result_ping = result_ping[0]
        for res in result_ping:
            ip, res_time = self.parse(res)
            LOG.debug("IP: %s, time: %s", ip, res_time)
            result['ip'] = ip
            result['time'] = res_time
            list_result.append(result)
            result = {}
        LOG.debug("Result parse: " + str(list_result))
        return list_result


def main():
    """
    Main function
    """
    list_ip_file_name = "VN.zone"
    result = []
    try:
        with open(list_ip_file_name, "r") as f:
            subnets = f.readlines()
            remove_line = []
            for subnet in subnets:
                remove_line.append(subnet.strip())
        #    for subnet in f.readlines():
            ping = PingSubnet(remove_line)
            result = ping.process()
            LOG.info("Result: "+str(result))
    except Exception as e:
        LOG.error('Open file range IP failed: ' + e.message)
    host = 'x.x.x.x'
    port = '8086'
    username = 'ping'
    password = 'xx'
    database = 'pingmetrics'
    path = 'ping'
    data_center = "Ha-Noi"
    influx = InfluxDB(host=host, port=port,
                      username=username, password=password,
                      database=database, metrics=result, path=path,
                      data_center=data_center)
    influx.send_metric()


if __name__ == '__main__':
    main()
