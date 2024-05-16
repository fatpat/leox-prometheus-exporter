import typer
from typing_extensions import Annotated
from enum import Enum
import logging
import requests
from lxml import html
import time
import re
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server, disable_created_metrics, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

log = logging.getLogger()

LEOX_HTTP_METRICS = [
    {
        'metric': 'pon_bytes_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Bytes Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_bytes_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Bytes Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Packets Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Packets Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_unicast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Unicast Packets Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_unicast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Unicast Packets Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_multicast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Multicast Packets Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_multicast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Multicast Packets Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_broadcast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Broadcast Packets Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_broadcast_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Broadcast Packets Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_pause_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Pause Packets Sent:"]/../td/child::text()',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_pause_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Pause Packets Received:"]/../td/child::text()',
        'labels': {'direction': 'rx'},
    },

    {
        'metric': 'pon_dropped_packets_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="Packets Dropped:"]/../td/child::text()',
    },

    {
        'metric': 'pon_errors_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="FEC Errors:"]/../td/child::text()',
        'labels': {'type': 'fec'},
    },
    {
        'metric': 'pon_errors_total',
        'page': '/admin/pon-stats.asp',
        'xpath': '//div[@class="data_common data_common_notitle"]/table/tr/th[child::text()="HEC Errors:"]/../td/child::text()',
        'labels': {'type': 'hec'},
    },

    {
        'metric': 'pon_transceiver_temperature_celcius',
        'page': '/status_pon.asp',
        'xpath': '//div[@class="data_common"]/table/tr/th[child::text()="Temperature"]/../td/child::text()',
        'regex': r'(?P<value>\d+(?:\.\d+)?)',
    },
    {
        'metric': 'pon_transceiver_bias_current_amperes',
        'page': '/status_pon.asp',
        'xpath': '//div[@class="data_common"]/table/tr/th[child::text()="Voltage"]/../td/child::text()',
        'regex': r'(?P<value>\d+(?:\.\d+)?)',
        'ratio': 0.001,
    },
    {
        'metric': 'pon_transceiver_power_dbm',
        'page': '/status_pon.asp',
        'xpath': '//div[@class="data_common"]/table/tr/th[child::text()="Tx Power"]/../td/child::text()',
        'regex': r'(?P<value>\d+(?:\.\d+)?)',
        'labels': {'direction': 'tx'},
    },
    {
        'metric': 'pon_transceiver_power_dbm',
        'page': '/status_pon.asp',
        'xpath': '//div[@class="data_common"]/table/tr/th[child::text()="Rx Power"]/../td/child::text()',
        'regex': r'(?P<value>\d+(?:\.\d+)?)',
        'labels': {'direction': 'rx'},
    },
    {
        'metric': 'pon_onu_state',
        'page': '/status_pon.asp',
        'xpath': '//th[child::text()="ONU State"]/../td/child::text()',
        'regex': r'^O(?P<value>\d+)$',
    },

    {
        'metric': 'cpu_percent',
        'page': '/status.asp',
        'xpath': '//th[child::text()="CPU Usage"]/../td/child::text()',
        'regex': r'^(?P<value>\d+)%$',
    },
    {
        'metric': 'memory_percent',
        'page': '/status.asp',
        'xpath': '//th[child::text()="Memory Usage"]/../td/child::text()',
        'regex': r'^(?P<value>\d+)%$',
    },
]

class CustomCollector(object):
    def __init__(self, leox_ip, leox_port, leox_login, leox_password, metrics_prefix):
        self.leox_ip = leox_ip
        self.leox_port = leox_port
        self.leox_login = leox_login
        self.leox_password = leox_password
        self.metrics_prefix = metrics_prefix
        pass

    def collect(self):
        pages = {}
        yield GaugeMetricFamily('leox_last_scrape', '', value=time.time())
        for conf in LEOX_HTTP_METRICS:
            try:

                metric = conf.get('metric', None)
                if metric is None:
                    log.warning(f"metric not found in {conf}, skipping")
                    continue
                metric = self.metrics_prefix + metric

                page = conf.get('page', None)
                if page is None:
                    log.warning(f"[{metric}] page is not set, skipping")
                    continue

                xpath = conf.get('xpath', None)
                if xpath is None:
                    log.warning(f"[{metric}] xpath is not set, skipping")
                    continue

                # get page from cache or request leox
                tree = pages.get(page, None)
                if tree is None:
                    log.info(f"scrapping page {page}")
                    resp = requests.get(f"http://{self.leox_login}:{self.leox_password}@{self.leox_ip}:{self.leox_port}{page}")
                    if resp.status_code != 200:
                        log.error(f"[{metric}] page {page} returned {resp.status_code}, skipping")
                        continue
                    tree = html.fromstring(resp.content)
                    pages[page] = tree

                # extract value
                value = tree.xpath(xpath)
                log.debug(value)
                value = value[0]
                regex = conf.get('regex', None)
                if regex is not None:
                    m = re.search(regex, value)
                    if m is None:
                        log.warning(f"[{metric}] regex ({regex}) does not match value ({value}), skipping")
                        continue
                    value = m.group('value')

                # convert to float
                value = float(value)
                # apply ratio
                value *= conf.get('ratio', 1)
                log.info(f"[{metric}] value={value}")

                # send metrics
                labels = conf.get('labels', {})
                if len(labels) > 0:
                    c = GaugeMetricFamily(metric, conf.get('help', metric), labels=labels.keys())
                    c.add_metric(labels.values(), value)
                    yield(c)
                else:
                    yield GaugeMetricFamily(metric, conf.get('help', metric), value=value)
            except Exception as e:
                log.error(f"error while handing metric {metric}, skipping", e)


def main_typer(
    listen_addr: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_LISTEN_ADDR")] = '127.0.0.1',
    listen_port: Annotated[int, typer.Option(envvar="LEOX_EXPORTER_LISTEN_PORT")] = 9198,
    log_level: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_LOG_LEVEL")] = 'info',
    leox_ip: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_LEOX_IP")] = "192.168.100.1",
    leox_port: Annotated[int, typer.Option(envvar="LEOX_EXPORTER_LEOX_PORT")] = 80,
    leox_login: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_LEOX_LOGIN")] = "leox",
    leox_password: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_LEOX_PASSWORD")] = "leolabs_7",
    metrics_prefix: Annotated[str, typer.Option(envvar="LEOX_EXPORTER_METRICS_PREFIX")] = "leox_",
):
    logging.basicConfig(level=log_level.upper())
    log.info("starting ...")
    disable_created_metrics()
    REGISTRY.unregister(GC_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.register(CustomCollector(
        leox_ip=leox_ip,
        leox_port=leox_port,
        leox_login=leox_login,
        leox_password=leox_password,
        metrics_prefix=metrics_prefix,
    ))
    start_http_server(addr=listen_addr, port=listen_port)
    while True:
        time.sleep(1)

def main():
    typer.run(main_typer)

if __name__ == '__main__':
    main()
