#!/bin/bash
# ------------------------------------
# updated by ...: Loreto Notarantonio
# Date .........: 14-05-2024 16.57.02
# ------------------------------------

Environment="ln_ENVARS_DIR=/home/pi/lnProfile/envars"
Environment="ln_RUNTIME_DIR=/home/pi/ln_runtime"


function production() {
    /usr/bin/python /home/loreto/lnProfile/liveProduction/mqttMonitor.zip \
                --console-logger-level error \
                --file-logger-level warning \
                --logging-dir /tmp/mqttmonitor \
                --telegram-group-name Ln_MqttMonitor_Client \
                --topics +/#

}


function main() {
LOG_LEVEL=$1

    /usr/bin/python /home/loreto//GIT-REPO/Python/mqttMonitor/__main__.py \
                --console-logger-level $LOG_LEVEL \
                --file-logger-level critical \
                --logging-dir /tmp/mqttmonitor \
                --telegram-group-name Ln_MqttMonitor_Client \
                --topics +/#

}


main "info"