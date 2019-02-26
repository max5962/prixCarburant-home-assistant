import urllib.request
import zipfile
from math import radians, cos, sin, asin, sqrt
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import sys
import csv
import os


"""
    PrixCarburantClient

"""


class PrixCarburantClient(object):

    version = ""
    xmlData = ""
    stations = {}
    homeAssistantLocation = [{'lat': 50, 'lng': 3}]
    maxKM = 0

    _XML_SP95_TAG = "SP95"
    _XML_SP98_TAG = "SP98"
    _XML_E10_TAG = "E10"
    _XML_GAZOLE_TAG = "Gazole"

    def __init__(self, home_assistant_location, maxKM):
        self.homeAssistantLocation = home_assistant_location
        self.maxKM = maxKM
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    def downloadFile(self, url, file):
        logging.debug('Downloading ...')
        logging.debug('   URL : ' + url)
        urllib.request.urlretrieve(url, file)

    def unzipFile(self, source, dest):
        logging.debug('unziping ...')
        logging.debug('   source :' + source)
        zip_ref = zipfile.ZipFile(source, 'r')
        zip_ref.extractall(dest)
        zip_ref.close()

    def extractPrice(self, priceElement, type):
        valeur = 0
        try:
            xpath = ".//prix[@nom='" + type + "']"
            gazoilChild = priceElement.findall(xpath)
            valeur = gazoilChild[0].get("valeur")
        except:
            pass
        return float(valeur) / 1000

    def loadStation(self, fileName):
        stations = {}
        file = open(fileName, "rt", encoding="utf-8")
        try:
            reader = csv.reader(file)
            for row in reader:
                stations[row[0]] = row
        finally:
            file.close()

        return stations

    """
    return true if the 'test_point' is near the 'center_point'
    """

    def isNear(self, maxKM, center_point, test_point):
        logging.debug("Comparing : ")
        logging.debug('   ' + str(center_point))
        logging.debug('   ' + str(test_point))
        lat1 = float(center_point[0]['lat'])
        lon1 = float(center_point[0]['lng'])
        lat2 = float(test_point[0]['lat']) / 100000
        lon2 = float(test_point[0]['lng']) / 100000
        a = self.distance(lon1, lat1, lon2, lat2)
        logging.debug('   Distance (km) : %d km ', a)
        toReturn = a <= maxKM
        if toReturn:
            logging.debug('   Inside the area')
        else:
            logging.debug('   Outside the area')
        return toReturn

    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """

    def distance(self, lon1, lat1, lon2, lat2):

        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles
        return c * r

    def removeFile(self, file):
        logging.debug('Removing tempory file ')
        logging.debug('   file : ' + file)
        os.remove(file)

    def load(self):
        aDaybefore = datetime.today() - timedelta(days=1)
        self.downloadFile(
            'https://static.data.gouv.fr/resources/prix-des-carburants-en-france/20181117-111538/active-stations.csv', 'station.csv')
        self.stations = self.loadStation('station.csv')
        self.downloadFile('https://donnees.roulez-eco.fr/opendata/jour',
                          'PrixCarburants_instantane.zip')
        self.unzipFile("PrixCarburants_instantane.zip", ".")
        self.xmlData = "PrixCarburants_quotidien_" + \
            aDaybefore.strftime("%Y%m%d") + ".xml"

    def extractSpecificStation(self, listToExtract):
        stationsExtracted = {}
        stationsXML= self.decodeXML(self.xmlData)
        for child in stationsXML:
            try:
                if child.attrib['id'] in listToExtract:
                    logging.debug("Need to be extracted")
                    stationsExtracted[child.attrib['id']]=self.extractAndConstructStation(child)
                    logging.info(stationsExtracted[child.attrib['id']])

            except Exception as e:
                logging.error("erreur" + str(e))
                pass
        return stationsExtracted


    def extractAndConstructStation(self, elementxml ):
        if elementxml.attrib['id'] in self.stations:
            logging.debug(self.stations[elementxml.attrib['id']])
            name=self.stations[elementxml.attrib['id']][1]
            address=self.stations[elementxml.attrib['id']][3]
        else:
            name="undefined"
            address=elementxml.findall(".//adresse")[0].text + " " + elementxml.findall(".//ville")[0].text
            #name, adress,id, gazoil, e95, e98,e10
        return  StationEssence(
                name,
                address,
                elementxml.attrib['id'],
                self.extractPrice(elementxml, self._XML_GAZOLE_TAG),
                self.extractPrice(elementxml, self._XML_SP95_TAG),
                self.extractPrice(elementxml, self._XML_SP98_TAG),
                self.extractPrice(elementxml, self._XML_E10_TAG))

    def foundNearestStation(self):
        nearStation = {}
        stationsXML= self.decodeXML(self.xmlData)
        for child in stationsXML:
            try:
                isInTheArea = self.isNear(self.maxKM, self.homeAssistantLocation, [
                    {'lat': child.attrib['latitude'], 'lng': child.attrib['longitude']}])
                if isInTheArea:
                    nearStation[child.attrib['id']]=self.extractAndConstructStation(child)
                    logging.info(nearStation[child.attrib['id']])

            except Exception as e:
                logging.error("erreur" + str(e))
                pass
        return nearStation



    def clean(self):
        self.removeFile('station.csv')
        self.removeFile(self.xmlData)
        self.removeFile("PrixCarburants_instantane.zip")


    def decodeXML(self, file):
        tree = ET.parse(file)
        root = tree.getroot()
        return root
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


#####################
##      MAIN       ##
#####################
_HOME_ASSISTANT_LOCATION = [{'lat': 50.581864, 'lng': 3.025573}]
_MAX_KM = 30
exampleList=[]
exampleList.append("59000002")
exampleList.append("59000017")
client = PrixCarburantClient(_HOME_ASSISTANT_LOCATION,_MAX_KM)
client.load()
client.foundNearestStation()
client.extractSpecificStation(exampleList)
#client.clean()
