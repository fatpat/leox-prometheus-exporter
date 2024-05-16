# leox exporter for Prometheus
Prometheus exporter for LEOX ONT's
## Usage
```
$ leox-prometheus-exporter --help

 Usage: leox-prometheus-exporter [OPTIONS]

╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --listen-addr           TEXT     [env var: LEOX_EXPORTER_LISTEN_ADDR] [default: 127.0.0.1]                                        │
│ --listen-port           INTEGER  [env var: LEOX_EXPORTER_LISTEN_PORT] [default: 9198]                                             │
│ --log-level             TEXT     [env var: LEOX_EXPORTER_LOG_LEVEL] [default: info]                                               │
│ --leox-ip               TEXT     [env var: LEOX_EXPORTER_LEOX_IP] [default: 192.168.100.1]                                        │
│ --leox-port             INTEGER  [env var: LEOX_EXPORTER_LEOX_PORT] [default: 80]                                                 │
│ --leox-login            TEXT     [env var: LEOX_EXPORTER_LEOX_LOGIN] [default: leox]                                              │
│ --leox-password         TEXT     [env var: LEOX_EXPORTER_LEOX_PASSWORD] [default: leolabs_7]                                      │
│ --metrics-prefix        TEXT     [env var: LEOX_EXPORTER_METRICS_PREFIX] [default: leox_]                                         │
│ --help                           Show this message and exit.                                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
