#!/usr/bin/python
"""Query in influxdb and generate gdnsd config file"""

from influxdb import InfluxDBClient


class GdnsdConfig(object):
    """
    Connect to influxdb and send metric
    """

    def __init__(self, host, port, username, password,
                 database, path, dc_tag, subnet_tag, nets_file):
        """
        Init
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.path = path
        self.influx = self.get_influxdb_client()
        self.dc_tag = dc_tag
        self.subnet_tag = subnet_tag
        self.all_dc = self.get_all_dc()
        self.all_subnet = self.get_all_subnets()
        self.nets_file = nets_file

    def get_influxdb_client(self):
        """
        Return influxdb client
        """

        return InfluxDBClient(host=self.host, port=self.port,
                              username=self.username, password=self.password,
                              database=self.database)

    def get_all_subnets(self):
        """
        Return all subnet in database in 1 week
        """
        query = 'SHOW TAG VALUES FROM "{0}" WITH KEY = "{1}"'.format(self.path,
                                                                     self.subnet_tag)
        result = list(self.influx.query(query))
        return result[0]

    def get_all_dc(self):
        """
        Return all datacenter name in database
        """
        query = 'SHOW TAG VALUES FROM "{0}" WITH KEY = "{1}"'.format(self.path,
                                                                     self.dc_tag)
        result = list(self.influx.query(query))
        return result[0]

    def generate(self):
        """Perform Generate gnsd config file"""
        with open(self.nets_file, 'w') as f:
            for i in range(len(self.all_subnet)):
                subnet = self.all_subnet[i]['value']
                result = []
                for dc in self.all_dc:
                    query = "SELECT value FROM {0} where data_center = " \
                            "'{1}' and subnet = '{2}' and time > now() - 7d " \
                            "limit 1".format(self.path, dc['value'], subnet)
                    res = list(self.influx.query(query))
                    dc_time = {
                        "data_center": dc['value'],
                        "time": res[0][0]['value']
                        }
                    result.append(dc_time)
                arranged_result = sorted(result, key=lambda k: k['time'])
                arr_dc = ""
                time_dc = ""
                for dc in arranged_result:
                    arr_dc += dc['data_center'] + ", "
                    time_dc += str(dc['time']) + ", "
                f.writelines("%-18s   => [%-30s] #%-50s\n" %(subnet,
                                                           arr_dc,
                                                           time_dc))


def main():
    """
    Main function
    """
    influx_host = 'influxdb'
    influx_port = '8086'
    influx_username = 'xxxx'
    influx_password = 'xxxxx'
    influx_database = 'xxxxx'
    influx_path = 'ping'
    dc_tag = 'data_center'
    subnet_tag = 'subnet'
    nets_file = '/tmp/nets.1'
    gen = GdnsdConfig(host=influx_host, port=influx_port,
                      username=influx_username, password=influx_password,
                      database=influx_database, path=influx_path,
                      dc_tag=dc_tag, subnet_tag=subnet_tag,
                      nets_file=nets_file)
    gen.generate()


if __name__ == '__main__':
    main()
