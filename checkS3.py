import os
import re
import sys
import yaml
import json
import logging
import datetime
import argparse
from pythonping import ping
import urllib.request

class DNS(object):
    """
    This class contains methods to find access time for S3 CloudFront edge server.
    """

    def __init__(self):
        """
        Defines variables to share across methods, sets up logging, Shotgun
        connections, and runs _generate and _export class methods.
        """

        # Initialize shared variables. By default, use the last month for the
        # date range.
        self._dnsservers = {}
        self._set_up_logging()
        # Be generous and run the generate code if we've only got date args.
        

        # Grab our user settings and barf if something is wrong.
        logging.info("Reading set.yml...\n")
        if os.path.exists("set.yml"):
            try:
                with open("set.yml", "r") as fh:
                    self._dnsservers = yaml.load(fh, Loader=yaml.FullLoader)
            except Exception as e:
                logging.info("Could not parse set.yml: %s" % e)
                return
        else:
            logging.error("Did not find set.yml. See README.md for details.")
            return
        if not self._dnsservers:
            logging.error("Settings dict is empty (bad \"set.yml\" file?), exiting.")
            return

        # Generate, export, and print the report.
        try:
          self._start()
        except Exception as e:
          logging.error("FAIL!: %s" % str(e))

    def _set_up_logging(self):
        """
        Creates logs directory and sets up logger-related stuffs.
        """

        # Create a logs directory if it doesn't exist.
        if not os.path.exists("logs"):
            os.makedirs("logs")


        # Create a datestamp var for stamping the logs.
        datestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H-%M-%S")

        # Create a log file path.
        log = os.path.join("logs", "%s.log" % datestamp)

        # Set the logging level.
        logging_level = logging.INFO

        # Set up our logging.
        logging.basicConfig(
            filename=log,
            level=logging_level,
            format="%(levelname)s: %(asctime)s: %(message)s",
        )
        logging.getLogger().addHandler(logging.StreamHandler())

    def _dig(self, s3_url, location, dnsserver):
        '''
        Use dig command to get IP from specific DNS server.
        '''
        cmd_dig = "dig %s @%s +short" % (s3_url, dnsserver)
        ip_list = os.popen(cmd_dig).read().split("\n")
        logging.info("DNS Server Location: %s, DNS Server IP: %s" % (location, dnsserver))
        return ip_list[0]

    def _get_ip_location(self, ip):
        '''
        Get geo location of a give IPv4 address.
        '''
        with urllib.request.urlopen("https://geolocation-db.com/jsonp/" + ip) as url:
            data = url.read().decode()
            data = data.split("(")[1].strip(")")
            loc =json.loads(data)
            logging.info("country_code: %s, city: %s"%(loc["country_code"], loc["city"]))
            return loc

    def _ping(self, ip):
        '''
        Ping to get latency of a given IP.
        '''
        try:
            response_list = ping(ip, size=10, count=3)
            logging.info("ip: %s, min: %s, max: %s, avg: %s \n" % (ip, str(response_list.rtt_min_ms), str(response_list.rtt_max_ms), str(response_list.rtt_avg_ms)))
        except Exception as e:
            logging.error("%s isn't reachable.\n" %(ip))

    def _start(self):
        '''
        Start to check
        '''
        for s3_url in self._dnsservers.keys():
            logging.info("%s\n"%s3_url)
            for dns_servers in self._dnsservers[s3_url].keys():
                s = self._dnsservers[s3_url][dns_servers]
                ip = self._dig(s3_url, dns_servers, s)
                loc = self._get_ip_location(ip)
                self._ping(ip)


if __name__ == "__main__":
  d = DNS()