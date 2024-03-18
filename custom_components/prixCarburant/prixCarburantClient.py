import urllib.request
import zipfile
from math import radians, cos, sin, asin, sqrt
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import sys
import csv
import os
import shutil


"""
    PrixCarburantClient

"""


class PrixCarburantClient(object):

    version = ''
    xmlData = ""
    stations = {}
    homeAssistantLocation = [{'lat': 50, 'lng': 3}]
    maxKM = 0

    _XML_SP95_TAG = 'SP95'
    _XML_SP98_TAG = 'SP98'
    _XML_E10_TAG = 'E10'
    _XML_GAZOLE_TAG = 'Gazole'
    _XML_E85_TAG = 'E85'
    _XML_GPL_TAG = 'GPLc'

    def __init__(self, home_assistant_location, maxKM):
        self.homeAssistantLocation = home_assistant_location
        self.maxKM = maxKM
        self.lastUpdate = datetime.today()
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    def downloadFile(self, url, file):
        logging.debug("Downloading ...")
        logging.debug("   URL : " + url)
        urllib.request.urlretrieve(url, file)

    def unzipFile(self, source, dest):
        logging.debug("unziping ...")
        logging.debug("   source :" + source)
        zip_ref = zipfile.ZipFile(source, 'r')
        zip_ref.extractall(dest)
        zip_ref.close()

    def extractPrice(self, priceElement, type):
        valeur = 0
        maj= ""
        try:
            xpath = ".//prix[@nom='" + type + "']"
            gazoilChild = priceElement.findall(xpath)
            valeur = gazoilChild[0].get("valeur")
            maj = gazoilChild[0].get("maj")
        except BaseException:
            pass
        if valeur == 0:
            valeur = "-"
            maj = self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S')
        else:
            if isinstance(valeur, int):
                valeur = float(valeur) / 1000
        
        price = {
            'valeur': str(valeur),
            'maj': str(maj)
        }
        #logging.warning("[prixCarburantClientLoad] extractPrice : "+str(type)+" valeur : "+str(valeur)+" maj : "+str(maj))

        return price

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
        logging.debug("   " + str(center_point))
        logging.debug("   " + str(test_point))
        if test_point[0]['lat'] == "" and test_point[0]['lng'] == "":
            logging.debug(
                '   [isNear] Impossible to get lattitude or longitude, impossible to found the station')
            return False
        lat1 = float(center_point[0]['lat'])
        lon1 = float(center_point[0]['lng'])
        lat2 = float(test_point[0]['lat']) / 100000
        lon2 = float(test_point[0]['lng']) / 100000
        a = self.distance(lon1, lat1, lon2, lat2)
        logging.debug("   Distance (km) : %d km ", a)
        toReturn = a <= maxKM
        if toReturn:
            logging.debug("   Inside the area")
        else:
            logging.debug("   Outside the area")
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
        logging.debug("Removing tempory file ")
        logging.debug("   file : " + file)
        if os.path.exists(file):
          os.remove(file)

    def reloadIfNecessary(self):
        #logging.warning("[prixCarburantClientLoad] self.lastUpdate : "+str(self.lastUpdate))
        #logging.warning("[prixCarburantClientLoad] datetime.today().date() : "+str(datetime.today().date()))
        #today = datetime.today().date()
        #if today == self.lastUpdate:
        #    logging.debug("Informations are up-to-date")
        #    return False
        #else:
        #    logging.debug("Informations are outdated")
        self.load()
        return True

    def load(self):
        aDaybefore = datetime.today() - timedelta(days=1)
        try:
            #self.downloadFile(
            #     "https://static.data.gouv.fr/resources/prix-des-carburants-en-france/20181117-111538/active-stations.csv",
            #     "station.csv")
            self.stations = self.loadStation('./custom_components/prixCarburant/station.csv')
            #https://donnees.roulez-eco.fr/opendata/instantane
            #https://donnees.roulez-eco.fr/opendata/jour
            self.downloadFile("https://donnees.roulez-eco.fr/opendata/instantane",
                          "PrixCarburants_instantane.zip")
            self.unzipFile("PrixCarburants_instantane.zip", './PrixCarburantsData')
            #self.xmlData = "./PrixCarburantsData/PrixCarburants_quotidien_" + \
            #     aDaybefore.strftime("%Y%m%d") + ".xml"
            self.xmlData = "./PrixCarburantsData/PrixCarburants_instantane.xml"
            self.stationsXML = self.decodeXML(self.xmlData)
            self.lastUpdate = datetime.today()
        except:
            logging.warning("Failed to download new data, will be retry ")

    def extractSpecificStation(self, listToExtract):
        stationsExtracted = {}
        stationsXML = self.stationsXML
        for child in stationsXML:
            try:
                if child.attrib['id'] in listToExtract:
                    logging.debug("Need to be extracted")
                    stationsExtracted[child.attrib['id']
                                      ] = self.extractAndConstructStation(child)
                    logging.debug(stationsExtracted[child.attrib['id']])

            except Exception as e:
                logging.debug("[extractSpecificStation] : " + str(e))
                pass
        return stationsExtracted

    def extractAndConstructStation(self, elementxml):
        if elementxml.attrib['id'] in self.stations:
            logging.debug(self.stations[elementxml.attrib['id']])
            name = self.stations[elementxml.attrib['id']][1]
            address = self.stations[elementxml.attrib['id']][3]
        else:
            name = "undefined"
            address = elementxml.findall(
                ".//adresse")[0].text + " " + elementxml.findall(".//ville")[0].text
            #name, adress,id, gazoil, e95, e98,e10,e85, gplc
        object = StationEssence(
            name,
            address,
            elementxml.attrib['id'],
            self.extractPrice(elementxml, self._XML_GAZOLE_TAG),
            self.extractPrice(elementxml, self._XML_SP95_TAG),
            self.extractPrice(elementxml, self._XML_SP98_TAG),
            self.extractPrice(elementxml, self._XML_E10_TAG),
            self.extractPrice(elementxml, self._XML_E85_TAG),
            self.extractPrice(elementxml, self._XML_GPL_TAG))
        if object.isClose():
            logging.debug("station is closed")
            raise Exception('Station is closed')
        else:
            logging.debug("station is still opened")

        return object

    def foundNearestStation(self):
        nearStation = {}
        stationsXML = self.stationsXML
        for child in stationsXML:
            try:
                isInTheArea = self.isNear(self.maxKM, self.homeAssistantLocation, [
                    {'lat': child.attrib['latitude'], 'lng': child.attrib['longitude']}])
                if isInTheArea:
                    nearStation[child.attrib['id']
                                ] = self.extractAndConstructStation(child)
                    logging.debug(nearStation[child.attrib['id']])

            except Exception as e:
                logging.debug("[foundNearestStation]" + str(e))
                pass
        return nearStation

    def clean(self):
        #self.removeFile("station.csv")
        self.removeFile(self.xmlData)
        self.removeFile("PrixCarburants_instantane.zip")
        try:
          shutil.rmtree('./PrixCarburantsData')
        except OSError as e:
          logging.debug("Error: %s - %s." % (e.filename, e.strerror))


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
    gazoil = {}
    e95 = {}
    e98 = {}
    e10 = {}
    e85 = {}
    gpl = {}

    def __init__(self, name, adress, id, gazoil, e95, e98, e10, e85, gpl):
        self.name = name
        self.adress = adress
        self.id = id
        self.gazoil = gazoil
        self.e95 = e95
        self.e98 = e98
        self.e10 = e10
        self.e85 = e85
        self.gpl = gpl

    def isClose(self):
        boole=self.e95['valeur'] == "None" and self.e98['valeur'] == "None" and self.e10['valeur'] =="None" and self.gazoil['valeur'] == "None" and self.e85['valeur'] == "None" and self.gpl['valeur'] == "None"
        logging.debug(""+str(boole))
        return boole

    def __str__(self):
        return "StationEssence:\n [\n - name : %s \n - adress : %s \n - id : %s \n - gazoil : %s \n - e95 : %s  \n - e98 : %s  \n - e10 : %s \n - e85 : %s \n - gplc : %s \n]" % (
            self.name, self.adress, self.id, self.gazoil['valeur'], self.e95['valeur'], self.e98['valeur'], self.e10['valeur'], self.e85['valeur'], self.gpl['valeur'])
