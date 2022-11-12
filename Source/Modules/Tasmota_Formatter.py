#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os
from LnDict import LoretoDict
from LnTime import millisecs_to_HMS_ms



####################################################################
### preparazione stato WiFi
####################################################################
def wifi(device: dict):
    wifi=device.getkp(keypaths=['STATE.Wifi', 'STATUS11.StatusSTS.Wifi'], default={})
    if wifi:
        wifi.pop('AP', None)
        wifi.pop('Mode', None)
        wifi.pop('LinkCount', None)
        wifi.pop('DownTime', None)

    return wifi


####################################################################
### info varie
####################################################################
def deviceInfo(device: dict):
    infodata=LoretoDict()
    infodata['device_name']      = device.getkp('sensors.dn')
    infodata['ip_address']       = device.getkp('sensors.ip')
    infodata['firmware_version'] = device.getkp('sensors.sw')
    infodata['modello']          = device.getkp('sensors.md')
    infodata['host_name']        = device.getkp('sensors.hn')
    infodata['online offline']   = device.get('LWT')

    return infodata






####################################################################
### preparazione stato dei relè
# new_value potrebbe contenere:  {"POWER1":"OFF"}
# e quindi va in override su quanto letto da device
####################################################################
def relayStatus(device: dict, new_value: dict={}) -> dict:

    relays=[x for x in device.getkp('sensors.fn') if (x != '' and x != None)]
    _dict=LoretoDict()

    key='scramble@#,.$%$'
    if new_value and isinstance(new_value, dict):
        key=next(k for k in new_value.keys() if 'POWER' in k)

    for inx, name in enumerate(relays):
        if inx==0:
            power_status=device.getkp(keypaths=['RESULT.POWER', 'RESULT.POWER1', 'STATE.POWER', 'STATE.POWER1'], default='???')
            if key in ['POWER', 'POWER1']:
                power_status=new_value[key]
        else:
            power_status=device.getkp(keypaths=[f'RESULT.POWER{inx+1}', f'STATE.POWER{inx+1}'], default='???')
            if key in [f'POWER{inx+1}']:
                power_status=new_value[key]

        _dict.set_keypath(f"{name}.Power", value=power_status, create=True)

        ### Pulsetime
        pt_value, pt_remaining=getPulseTime(device, inx)
        _dict.set_keypath(f"{name}.Pulsetime", value=pt_value, create=True)
        _dict.set_keypath(f"{name}.Remaining", value=pt_remaining, create=True)

    return _dict


####################################################################
#
# {"PulseTime":{"Set":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"Remaining":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}}
#
#   PulseTime<x>:   Display the amount of PulseTime remaining on the corresponding Relay<x>
#           0 / OFF = disable use of PulseTime for Relay<x>
#           1..111 = set PulseTime for Relay<x> in 0.1 second increments
#           112..64900 = set PulseTime for Relay<x>, offset by 100, in 1 second increments.
#           Add 100 to desired interval in seconds, e.g.,
#           PulseTime 113 = 13 seconds and PulseTime 460 = 6 minutes (i.e., 360 seconds)
#           <value> Set the duration to keep Relay<x> ON when Power<x> ON command is issued.
#           After this amount of time, the power will be turned OFF.
#
####################################################################
def getPulseTime(device, inx):

    def secondsToPulseTime(seconds: float) -> int:
        seconds=float(seconds)
        if seconds<=11.1:
            pulsetime_value=seconds*10
        else:
            pulsetime_value=int(seconds)+100

        return int(pulsetime_value)

    def pulseTimeToSeconds(value: int) -> int:
        """Errori strani:
            remaining 1886060 invece di 132 - 1886192
            remaining 1885929 invece di 115 - 1886044
        """
        if value<=111:
            seconds=int(value/10)
            milliseconds=(value/10)*1000
        else:
            seconds=int(value-100)
            milliseconds=(value-100)*1000
        return millisecs_to_HMS_ms(milliseconds=milliseconds, strip_leading=True)


    SET=device['RESULT.PulseTime.Set']
    REMAINING=device['RESULT.PulseTime.Remaining']
    pulsetime_value=pulseTimeToSeconds(SET[inx]) if SET else None
    pulsetime_remaining=pulseTimeToSeconds(REMAINING[inx]) if REMAINING else None

    return pulsetime_value, pulsetime_remaining



