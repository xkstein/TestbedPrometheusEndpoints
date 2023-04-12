import logging
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

from gammaionctl import GammaIonPump
from instrument_wrapper import InstrumentWrapper

from prometheus_client.core import GaugeMetricFamily, REGISTRY

logging.basicConfig(filename='instrument_manager.log', encoding='utf-8', level=logging.DEBUG)

pump_small = InstrumentWrapper(GammaIonPump, name='pump_small', \
                                host='192.168.4.10', timeout=1.0)

pump_large = InstrumentWrapper(GammaIonPump, name='pump_large', \
                                host='192.168.4.9', timeout=1.0)

class PumpCollector:
    def __init__(self, connection) -> None:
        self.connection = connection
        self.name: str = self.connection.name

    def collect(self):
        try:
            hv_status = self.connection.getHighVoltageStatus(1)
            voltage =  self.connection.getVoltage(1)
            current =  self.connection.getCurrent(1)
            pressure, units =   self.connection.getPressureWithUnits(1)

            if None in (hv_status, voltage, current, pressure):
                raise ConnectionError
        except Exception as e:
            print(e)
            logging.error(e)
            return

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
