import logging
import random
import time
from prometheus_client import make_wsgi_app, Summary, Gauge, Enum
from wsgiref.simple_server import make_server

from gammaionctl import GammaIonPump
from instrument_wrapper import InstrumentWrapper

from prometheus_client.core import GaugeMetricFamily, InfoMetricFamily, CounterMetricFamily, StateSetMetricFamily, REGISTRY

logging.basicConfig(filename='instrument_manager.log', encoding='utf-8', level=logging.DEBUG)

pump_small = InstrumentWrapper(GammaIonPump, name='pump_small', \
                                host='192.168.4.10', timeout=1.0)

pump_large = InstrumentWrapper(GammaIonPump, name='pump_large', \
                                host='192.168.4.9', timeout=1.0)

class PumpCollector:
    def __init__(self, connection):
        self.connection = connection
        self.name = self.connection.name

    def collect(self):
        hv_status =         self.connection.getHighVoltageStatus(1)
        assert hv_status is not None, \
                'This is a bad part of the library, it should really raise an error if this is the case'

        voltage =           self.connection.getVoltage(1)
        current =           self.connection.getCurrent(1)
        pressure, units =   self.connection.getPressureWithUnits(1)

#         yield StateSetMetricFamily(
#                 f'{self.name}_high_voltage_status', 
#                 f'High voltage status indicates if high voltage is running',
#                 value = {
#                     'ON':  hv_status, 
#                     'OFF': (not hv_status)
#                 }
#             )
        yield GaugeMetricFamily(
                f'{self.name}_high_voltage_status',
                f'High voltage status indicates if high voltage is running', 
                value = hv_status
            )
        yield GaugeMetricFamily(
                f'{self.name}_voltage',
                f'Voltage output in V', 
                voltage
            )
        yield GaugeMetricFamily(
                f'{self.name}_current',
                f'Current output in A',
                current
            )
        yield GaugeMetricFamily(
                f'{self.name}_pressure',
                f'Pressure output in {units}', 
                pressure
            )

REGISTRY.register(PumpCollector(pump_small))
REGISTRY.register(PumpCollector(pump_large))

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    app = make_wsgi_app()
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
