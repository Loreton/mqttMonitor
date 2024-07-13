#!/bin/bash
# ------------------------------------
# updated by ...: Loreto Notarantonio
# Date .........: 08-07-2024 17.12.20
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

args=$*
echo "${TAB}script args:   $args"
word='--go'; [[ " $args " == *" $word "* ]] && args=${args//$word/} && g_fEXECUTE=1 && g_DRY_RUN=''
g_Args=$(echo $args) # remove BLANKs
echo "${TAB}application args:   $g_Args"

main "notify" # set log level
echo -e "\n" $cmd $g_Args
[[ "$g_fEXECUTE" == "1" ]] && $cmd $g_Args || echo -e '\n     entrer --go to execute\n'
