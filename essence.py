import urllib.request
import zipfile
from math import radians, cos, sin, asin, sqrt
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import sys
import csv
import os


_XML_SP95_TAG = "SP95"
_XML_SP98_TAG = "SP98"
_XML_E10_TAG = "E10"
_XML_GAZOLE_TAG = "Gazole"
_HOME_ASSISTANT_LOCATION = [{'lat': 50, 'lng': 3}]
_MAX_KM = 30


"""
     Station essence object
"""


class StationEssence(object):
    name = ""
    adress = ""
    id = 0
    gazoil = 0
    e95 = 0
    e98 = 0
    e10 = 0

    def __init__(self, name, adress, id, gazoil, e95, e98, e10):
        self.name = name
        self.adress = adress
        self.id = id
        self.gazoil = gazoil
        self.e95 = e95
        self.e98 = e98
        self.e10 = e10

    def __str__(self):
        return "StationEssence:\n [\n - name : %s \n - adress : %s \n - id : %s \n - gazoil : %s \n - e95 : %s  \n - e98 : %s  \n - e10 : %s \n ]" % (self.name, self.adress, self.id, self.gazoil, self.e95, self.e98, self.e10)


"""
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
"""


def distance(lon1, lat1, lon2, lat2):

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r


"""
    return true if the 'test_point' is near the 'center_point'
"""


def isNear(maxKM, center_point, test_point):
    logging.debug(center_point)
    logging.debug(test_point)

    lat1 = float(center_point[0]['lat'])
    lon1 = float(center_point[0]['lng'])
    lat2 = float(test_point[0]['lat']) / 100000
    lon2 = float(test_point[0]['lng']) / 100000
    a = distance(lon1, lat1, lon2, lat2)
    logging.debug('Distance (km) : %d km ', a)
    toReturn = a <= maxKM
    if toReturn:
        logging.debug('Inside the area')
    else:
        logging.debug('Outside the area')
    return toReturn


def downloadFile(url, file):
    logging.debug('Beginning file download with urllib2...')
    urllib.request.urlretrieve(url, file)


def unzipFile(source, dest):
    logging.debug('unzip ...')
    zip_ref = zipfile.ZipFile(source, 'r')
    zip_ref.extractall(dest)
    zip_ref.close()


def decodeXML(file, stations):
    nearStation = {}
    tree = ET.parse(file)
    root = tree.getroot()
    for child in root:
        try:
            isInTheArea = isNear(_MAX_KM, _HOME_ASSISTANT_LOCATION, [
                                 {'lat': child.attrib['latitude'], 'lng': child.attrib['longitude']}])
            if isInTheArea:
                logging.debug(stations[child.attrib['id']])
                #name, adress,id, gazoil, e95, e98,e10
                nearStation[child.attrib['id']] = StationEssence(
                    stations[child.attrib['id']][1],
                    stations[child.attrib['id']][3],
                    child.attrib['id'],
                    extractPrice(child, _XML_GAZOLE_TAG),
                    extractPrice(child, _XML_SP95_TAG),
                    extractPrice(child, _XML_SP98_TAG),
                    extractPrice(child, _XML_E10_TAG))
                logging.info(nearStation[child.attrib['id']])
        except:
            pass


def extractPrice(priceElement, type):
    valeur = 0
    try:
        xpath = ".//prix[@nom='" + type + "']"
        gazoilChild = priceElement.findall(xpath)
        valeur = gazoilChild[0].get("valeur")
    except:
        pass
    return float(valeur) / 1000


def loadStation(fileName):
    stations = {}
    file = open(fileName, "rt", encoding="utf-8")
    try:
        reader = csv.reader(file)
        for row in reader:
            stations[row[0]] = row
    finally:
        file.close()

    return stations


def removeFile(file):
    os.remove(file)


#####################
##      MAIN       ##
#####################
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
aDaybefore = datetime.today() - timedelta(days=1)
downloadFile('https://static.data.gouv.fr/resources/prix-des-carburants-en-france/20181117-111538/active-stations.csv', 'station.csv')
station = loadStation('station.csv')
downloadFile('https://donnees.roulez-eco.fr/opendata/jour',
             'PrixCarburants_instantane.zip')
unzipFile("PrixCarburants_instantane.zip", ".")
fileName = "PrixCarburants_quotidien_" + aDaybefore.strftime("%Y%m%d") + ".xml"
decodeXML(fileName, station)
removeFile('station.csv')
removeFile(fileName)
removeFile("PrixCarburants_instantane.zip")
