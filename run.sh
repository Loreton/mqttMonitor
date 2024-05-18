#!/bin/bash
# ------------------------------------
# updated by ...: Loreto Notarantonio
# Date .........: 17-05-2024 14.18.48
# ------------------------------------

Environment="ln_ENVARS_DIR=/home/pi/lnProfile/envars"
Environment="ln_RUNTIME_DIR=/home/pi/ln_runtime"


function production() {
    cmd="/usr/bin/python /home/loreto/lnProfile/liveProduction/mqttMonitor.zip \
                --console-logger-level error \
                --file-logger-level warning \
                --logging-dir /tmp/mqttmonitor \
                --telegram-group-name Ln_MqttMonitor_Client \
                --topics +/#"

}


function main() {
LOG_LEVEL=$1

    cmd="/usr/bin/python /home/loreto//GIT-REPO/Python/mqttMonitor/__main__.py \
                --console-logger-level $LOG_LEVEL \
                --file-logger-level critical \
                --logging-dir /tmp/mqttmonitor \
                --telegram-group-name Ln_MqttMonitor_Client \
                --topics +/# "

}


main "info"
echo $cmd $@
$cmd $@
