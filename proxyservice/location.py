import os
import sys
import re
import urllib.request
import json


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


class LocastDMAFinder():
    location = {
                "latitude": None,
                "longitude": None,
                "DMA": None,
                "city": None,
                "active": False
                }

    def __init__(self, config):
        print("Getting user location...")
        self.mock_location = config.config["location"]["mock_location"]
        self.zipcode = config.config["location"]["override_zipcode"]

        # Check for user's location

        # Find the users location via lat\long or zipcode if specified,(lat\lon
        # taking precedence if both are provided) otherwise use IP. Attempts to
        # mirror the geolocation found at locast.org\dma. Also allows for a
        # check that Locast reports the area as active.
        if self.find_location():
            print("Got location as {} - DMA {} - Lat\Lon {}\{}".format(self.location['city'],
                                                                       self.location['DMA'],
                                                                       self.location['latitude'],
                                                                       self.location['longitude'])
                  )
        else:
            clean_exit()
        # Check that Locast reports this market is currently active and available.
        if not self.location['active']:
            print("Locast reports that this DMA\Market area is not currently active!")
            clean_exit()

    def set_location(self, geoRes):
        self.location["latitude"] = str(geoRes['latitude'])
        self.location["longitude"] = str(geoRes['longitude'])
        self.location["DMA"] = str(geoRes['DMA'])
        self.location["active"] = geoRes['active']
        self.location["city"] = str(geoRes['name'])

    def find_location(self):
        '''
        Mirror the geolocation options found at locast.org/dma since we can't
        rely on browser geolocation. If the user provides override coords, or
        override_zipcode, resolve location based on that data. Otherwise check
        by external ip, (using ipinfo.io, as the site does).
        Calls to Locast return JSON in the following format:
        {
            u'DMA': str (DMA Number),
            u'large_url': str,
            u'name': str,
            u'longitude': lon,
            u'latitude': lat,
            u'active': bool,
            u'announcements': list,
            u'small_url': str
        }
        '''
        zip_format = re.compile(r'^[0-9]{5}$')
        # Check if the user provided override coords.
        if self.mock_location:
            return self.get_coord_location()
        # Check if the user provided an override zipcode, and that it's valid.
        elif self.zipcode and zip_format.match(self.zipcode):
            return self.get_zip_location()
        else:
            # If no override zip, or not a valid ZIP, fallback to IP location.
            return self.get_ip_location()

    def get_zip_location(self):
        print("Getting location via provided zipcode {}".format(self.zipcode))
        # Get geolocation via Locast, based on user provided zipcode.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/zip/{}'.format(self.zipcode))
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        resp.close()
        self.set_location(geoRes)
        return True

    def get_ip_location(self):
        print("Getting location via IP Address.")
        # Get geolocation via Locast. Mirror their website and use https://ipinfo.io/ip to get external IP.
        ip_resp = urllib.request.urlopen('https://ipinfo.io/ip')
        ip = ip_resp.read().strip()
        ip_resp.close()

        print("Got external IP {}.".format(ip.decode('utf-8')))

        # Query Locast by IP, using a 'client_ip' header.
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/ip')
        req.add_header('client_ip', ip)
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        resp.close()
        self.set_location(geoRes)
        return True

    def get_coord_location(self):
        print("Getting location via provided lat\lon coordinates.")
        # Get geolocation via Locast, using lat\lon coordinates.
        lat = self.mock_location['latitude']
        lon = self.mock_location['longitude']
        req = urllib.request.Request('https://api.locastnet.org/api/watch/dma/{}/{}'.format(lat, lon))
        req.add_header('Content-Type', 'application/json')
        resp = urllib.request.urlopen(req)
        geoRes = json.load(resp)
        resp.close()
        self.set_location(geoRes)
        return True
