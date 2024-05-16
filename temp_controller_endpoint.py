import logging
import socket
import time
from wsgiref.simple_server import make_server

from lakeshore import InstrumentException, Model336
from prometheus_client import make_wsgi_app
from prometheus_client.core import REGISTRY, GaugeMetricFamily

logging.basicConfig(filename='instrument_manager.log', encoding='utf-8', level=logging.DEBUG)

class TempCollector:
    def __init__(self) -> None:
        self.name = 'lakeshore'
        self.ip_address = '192.168.4.3'
        self.connection = None
        self.kwargs = dict(timeout=1.0)

        self.connect()

    def connect(self, fail_time=60) -> None:
        start_time = time.time()
        while True:
            try:
                self.connection = Model336(ip_address=self.ip_address, **self.kwargs)
                print('Connected')
                break
            except (socket.timeout, OSError):
                if (time.time() - start_time) > fail_time:
                    print(f'Was not able to start connection with lakeshore after {fail_time}s of trying')
                    raise Exception('Was not able to start connection with lakeshore after {}s of trying'.format(fail_time))
                else:
                    time.sleep(1)

    def collect(self):
        try:
            self.connection.get_status_byte()
        except AttributeError:
            self.connect()
        except Exception as e:
            logging.exception('Could not get status bit connect')
            self.connect()

        try:
            temp = self.connection.get_kelvin_reading(1)
            setpoint = self.connection.get_control_setpoint(1)
            pid = self.connection.get_heater_pid(1)
            heater = self.connection.get_heater_output(1)
            heater_range = self.connection.get_heater_range(1)
        except (InstrumentException, socket.timeout) as e:
            logging.exception('Could not read from lakeshore')
            return

        yield GaugeMetricFamily(
                f'{self.name}_temperature',
                f'Temperature of {self.name} (K)', 
                value = temp
            )
        yield GaugeMetricFamily(
                f'{self.name}_setpoint',
                f'Setpoint temp of {self.name} (K)', 
                setpoint
            )
        yield GaugeMetricFamily(
                f'{self.name}_heater',
                f'Output of the heater (%)',
                heater
            )
        yield GaugeMetricFamily(
                f'{self.name}_heater',
                f'Output of the heater (%)',
                heater
            )
        yield GaugeMetricFamily(
                f'{self.name}_heater_range',
                f'Range of heater. Corresponds to an enum (OFF, LOW, MEDIUM, HIGH) to indicate heater output', 
                heater_range.value
            )
        # PID
        yield GaugeMetricFamily(
                f'{self.name}_heater_p',
                f'Proportional term of heater PID', 
                pid['gain']
            )
        yield GaugeMetricFamily(
                f'{self.name}_heater_i',
                f'Integral term of heater PID', 
                pid['integral']
            )
        yield GaugeMetricFamily(
                f'{self.name}_heater_d',
                f'Derivative term of heater PID', 
                pid['ramp_rate']
            )

REGISTRY.register(TempCollector())

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    app = make_wsgi_app()
    httpd = make_server('', 8001, app)
    httpd.serve_forever()
