#!/bin/bash
# ------------------------------------
# updated by ...: Loreto Notarantonio
# Date .........: 14-07-2024 18.00.55
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



function start() {
    cmd="/usr/bin/python ${program} \
                --console-logger-level $LOG_LEVEL \
                --file-logger-level critical \
                --logging-dir ${log_dir} \
                --broker-name LnMqtt \
                --db-version-dir ${db_version_dir} \
                --telegram-group-name ${tgGroup} \
                --topics +/# "

}

# create zip file /tmp/compiled/mqttMonitor.zip
bash /home/loreto/lnProfile/liveProduction/python_ZipProject.lnk.sh

tgGroup="Ln_MqttMonitor_Client"
log_dir="/tmp/mqttmonitor"


LOG_LEVEL="info"
db_version_dir="D20240626"

program="/tmp/compiled/mqttMonitor.zip"
program="/home/loreto//GIT-REPO/Python/mqttMonitor/__main__.py"


args=$*
echo "${TAB}script args:   $args"
word='--go'; [[ " $args " == *" $word "* ]] && args=${args//$word/} && g_fEXECUTE=1 && g_DRY_RUN=''
g_Args=$(echo $args) # remove BLANKs
echo "${TAB}application args:   $g_Args"


start # set command
cd /tmp
echo -e "\n" $cmd $g_Args
[[ "$g_fEXECUTE" == "1" ]] && $cmd $g_Args || echo -e '\n     entrer --go to execute\n'

