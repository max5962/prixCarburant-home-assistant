from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from .essence import PrixCarburantClient
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_ELEVATION, CONF_MONITORED_CONDITIONS,
    ATTR_ATTRIBUTION, CONF_NAME)
import voluptuous as vol
import logging
import sys

ATTR_ID = "Station ID"
ATTR_GASOIL = "Gasoil"
ATTR_E95 =  "E95"
ATTR_E98 = "E98"
ATTR_E10 = "E10"
ATTR_ADDRESS = "Station Address"
ATTR_NAME="Station name"

CONF_MAX_KM="maxDistance"

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_MAX_KM, default=10): cv.positive_int,
    vol.Optional(CONF_LATITUDE): cv.latitude,
    vol.Optional(CONF_LONGITUDE): cv.longitude
})

def setup_platform(hass, config, add_devices, discovery_info=None):

    """Setup the sensor platform."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)

    homeLocation = [{
        'lat': str(latitude),
        'lng': str(longitude)
    }]

    maxDistance = config.get(CONF_MAX_KM)
    exampleList=[]
    exampleList.append("59000002")
    exampleList.append("59000017")

    client = PrixCarburantClient(homeLocation,maxDistance)
    client.load()
    stations=client.foundNearestStation()
    #stations=client.extractSpecificStation(exampleList)
    client.clean()
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    for station in stations:
        add_devices([PrixCarburant(stations.get(station))])

class PrixCarburant(Entity):
    """Representation of a Sensor."""

    def __init__(self,station):
        """Initialize the sensor."""
        self._state = None
        self.station=station

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'PrixCarburant'+self.station.id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "€"
   
    @property
    def device_state_attributes(self):
        """Return the device state attributes of the last update."""

        attrs = {
            ATTR_ID: self.station.id,
            ATTR_GASOIL: self.station.gazoil,
            ATTR_E95: self.station.e95,
            ATTR_E98: self.station.e98,
            ATTR_E10: self.station.e10,
            ATTR_ADDRESS: self.station.adress,
            ATTR_NAME: self.station.name
        }
        return attrs

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._state = self.station.gazoil
