import telnetlib
import time
import re

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server, disable_created_metrics, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

LEOX_COMMANDS = [
    {
        'command': 'diag gpon get onu-state',
        're': re.compile(r'ONU state: Operation State\(O(?P<value>\d+)\)'),
        'metric': 'gpon_onu_state',
    },
    {
        'command': 'diag pon get transceiver tx-power',
        're': re.compile(r'Tx Power:\s+(?P<value>-?\d+(?:\.\d+)?)\s+dBm'),
        'metric': 'pon_transceiver_power_dbm',
        'labels': {
            'type': 'tx',
        }
    },
    {
        'command': 'diag pon get transceiver rx-power',
        're': re.compile(r'Rx Power:\s+(?P<value>-?\d+(?:\.\d+)?)\s+dBm'),
        'metric': 'pon_transceiver_power_dbm',
        'labels': {
            'type': 'rx',
        }
    },
    {
        'command': 'diag pon get transceiver bias-current',
        're': re.compile(r'Bias Current:\s+(?P<value>-?\d+(?:\.\d+)?)\s+mA'),
        'metric': 'pon_transceiver_bias_current_amperes',
        'ratio': 0.001, # mA -> A
    },
    {
        'command': 'diag pon get transceiver temperature',
        're': re.compile(r'Temperature:\s+(?P<value>-?\d+(?:\.\d+)?)\s+C'),
        'metric': 'pon_transceiver_temperature_celcius',
    },
    {
        'command': 'diag pon get transceiver voltage',
        're': re.compile(r'Voltage:\s+(?P<value>-?\d+(?:\.\d+)?)\s+V'),
        'metric': 'pon_transceiver_voltave_volts',
    },
]

LEOX_IP = "192.168.100.1"
LEOX_PORT = 23
LEOX_LOGIN = "leox"
LEOX_PASSWORD ="leolabs_7"
LEOX_TIMEOUT_COMMAND = 2

class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        tn = telnetlib.Telnet(LEOX_IP)
#        tn.set_debuglevel(1)
        tn.read_until(b"login: ", timeout=LEOX_TIMEOUT_COMMAND)
        tn.write(LEOX_LOGIN.encode('ascii') + b"\n")
        tn.read_until(b"Password: ", timeout=LEOX_TIMEOUT_COMMAND)
        tn.write(LEOX_PASSWORD.encode('ascii') + b"\n")
        tn.read_until(b'# ').decode('ascii')
        for command in LEOX_COMMANDS:
            #time.sleep(0.1)
            cmd = command.get('command', None)
            regex = command.get('re', None)
            if cmd is None or regex is None:
                continue

            metric = command.get('metric', re.sub(r'[^a-z0-9_]', '', re.sub(r'[-\s]+', '_', cmd.lower())))
            print(f"*** command:'{cmd}' metric:'{metric}' ***")

            cmd += "\n"
            tn.write(cmd.encode('ascii'))
            output = tn.read_until(b'# ').decode('ascii')
            m = re.search(regex, output)
            if m is None:
                print(output)
                print("output not found, skipping")
                continue
            value = float(m.group('value'))
            value *= command.get('ratio', 1)
            yield GaugeMetricFamily(metric, command.get('help', metric), value=value)
        tn.write(b"exit\n")
        tn.read_all()
#        finally:
#            if tn is not None:
#        tn.close()
        return

#    'diag pon get transceiver part-number',
#    'diag pon get transceiver vendor-name',
#    'diag l2-table get entry address valid',

def main():
    start_http_server(8000)
    disable_created_metrics()
    REGISTRY.unregister(GC_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.register(CustomCollector())
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
