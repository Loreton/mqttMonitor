#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17


import  sys; sys.dont_write_bytecode = True
import  os
from LnDict import LoretoDict
from LnTime import millisecs_to_HMS_ms
from datetime import timedelta, datetime



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

    # -------------------------------------------------
    # def getPowerStatus(relayNr: int, device: dict) -> str:
    def retrieveRelayStatus(relayNr):

        # verifica dello status più aggiornato
        stateTime=datetime.strptime(device['STATE.Time'], '%Y-%m-%dT%H:%M:%S')
        stsTime=datetime.strptime(device['STATUS11.StatusSTS.Time'], '%Y-%m-%dT%H:%M:%S')

        if stsTime.timestamp() > stateTime.timestamp():
            kp='STATUS11.StatusSTS.POWER'
        else:
            kp='STATE.POWER'

        status=device[kp]
        if not status:
            status=device[f'{kp}{relayNr}']

        return status
    # -------------------------------------------------


    if not 'STATE' in device and not 'sensors' in device:
        return "undiscovered"

    ### capture relay friendlyNames
    fn=device.getkp('sensors.fn')
    friendlyNames=[x for x in fn if (x != '' and x != None)]
    device['Loreto']['nRelays']=len(friendlyNames)
    _dict=LoretoDict()

    '''prendiamo in considerazione  new_value
        se viene passato come argomento'''
    key=None
    if new_value and isinstance(new_value, dict):
        key=next(k for k in new_value.keys() if 'POWER' in k) # get first POWERx key


    ### inseriamo comunque tutti i relays
    for index, name in enumerate(friendlyNames):
        power_status=retrieveRelayStatus(relayNr=index+1)
        if key:
            if index==0 and key in ['POWER', 'POWER1']:
                power_status=new_value[key] ### lo specifio lo cambiamo se necessario
            elif key in ['POWER{index+1}']:
                power_status=new_value[key] ### lo specifio lo cambiamo se necessario

        _dict.set_keypath(f"{name}.Power", value=power_status, create=True)


        ### Pulsetime
        pt_value, pt_remaining=getPulseTime(device, index)
        _dict.set_keypath(f"{name}.Pulsetime", value=pt_value, create=True)
        _dict.set_keypath(f"{name}.Remaining", value=pt_remaining, create=True)

        ### Timers
        # timers()

    return _dict


# -------------------------------------------------
def retrieveRelayStatus2(device, relayNr):

    # verifica dello status più aggiornato
    stateTime=datetime.strptime(device['STATE.Time'], '%Y-%m-%dT%H:%M:%S')
    stsTime=datetime.strptime(device['STATUS11.StatusSTS.Time'], '%Y-%m-%dT%H:%M:%S')

    if stsTime.timestamp() > stateTime.timestamp():
        kp='STATUS11.StatusSTS.POWER'
    else:
        kp='STATE.POWER'

    status=device[kp]
    if not status:
        status=device[f'{kp}{relayNr}']

    return status





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



def setPulseTime(device, inx):
    """da sviluppare"""

    def secondsToPulseTime(seconds: float) -> int:
        seconds=float(seconds)
        if seconds<=11.1:
            pulsetime_value=seconds*10
        else:
            pulsetime_value=int(seconds)+100

        return int(pulsetime_value)


    SET=device['RESULT.PulseTime.Set']
    REMAINING=device['RESULT.PulseTime.Remaining']
    pulsetime_value=pulseTimeToSeconds(SET[inx]) if SET else None
    pulsetime_remaining=pulseTimeToSeconds(REMAINING[inx]) if REMAINING else None

    return pulsetime_value, pulsetime_remaining





####################################################################
# "RESULT": {
#         "Timers": "ON",
#         "Timer1": {
#             "Enable": 1,
#             "Mode": 0,
#             "Time": "01:00",
#             "Window": 0,
#             "Days": "1111111",
#             "Repeat": 1,
#             "Output": 1,
#             "Action": 0
#         },
#
# voglamo tradurlo in:
#    Timers:
#       T1: 17:21 on LMMGVSD sS
#       T2: 22:30 off LMMGVSD
####################################################################
def timers(device: dict, payload: dict) -> dict:

    # -----------------------------------
    def _convertWeekDays(val):
        _it_days='DLMMGVS' # tasmota days start from Sunday
        _en_days='SMTWTFS' # tasmota days start from Sunday
        _data=''
        for i in range(0, 7):
            _data+=_en_days[i] if val[i]=='1' else '_ '
        return _data[1:] + _data[0] # lets start from Monday



    # -----------------------------------
    def sum_offset(t0_time, offset):
        offset_HH, offset_MM=offset.split(':')
        offset_minutes=abs(int(offset_HH))*60+int(offset_MM)
        if offset_minutes==0:
            return t0_time

        t0_HH, t0_MM=t0_time.split(':')
        t0=timedelta(hours=int(t0_HH), minutes=int(t0_MM))
        ofs=timedelta(hours=int(offset_HH), minutes=int(offset_MM))

        if offset[0]=='-':
            new_time=t0-ofs
        else:
            new_time=t0+ofs

        return time.strftime("%H:%M", time.gmtime(new_time.total_seconds()))

    # -----------------------------------


    myTimers={}
    _action=['off', 'on', 'toggle', 'rule/blink']
    _mode=['clock time', 'sunrise', 'sunset']

    myTimers['Enabled']=payload['Timers']
    if myTimers['Enabled']=='ON':

        for i in range(1, 17):
            timerx=payload[f'Timer{i}']
            if timerx['Enable']==0:
                continue

            MODE=_mode[int(timerx['Mode'])]
            ACTION=_action[int(timerx['Action'])]
            REPEAT='YES' if timerx['Repeat']=='1' else 'NO'
            offset=timerx["Time"]
            DAYS=_convertWeekDays(timerx['Days'])
            RELAY=timerx['Output']

            if MODE == 'sunset':
                onTime=' sS'
                offset=timerx["Time"]
                _time=sum_offset(t0_time=sunset_time,offset=offset)

            elif MODE == 'sunrise':
                onTime=' sR'
                _time=sum_offset(t0_time=sunrise_time,offset=offset)

            else:
                onTime=''
                _time=timerx["Time"]

            myTimers[f'T{i}']=f'{_time} {RELAY}.{ACTION} {DAYS}{onTime}'

    return myTimers





####################################################################
# "RESULT": {
#         "Timers": "ON",
#         "Timer1": {
#             "Enable": 1,
#             "Mode": 0,
#             "Time": "01:00",
#             "Window": 0,
#             "Days": "1111111",
#             "Repeat": 1,
#             "Output": 1,
#             "Action": 0
#         },
#
# voglamo tradurlo in:
#    Timers:
#       T1: 17:21 on LMMGVSD sS
#       T2: 22:30 off LMMGVSD
####################################################################
def timers2(device: dict, output: int) -> dict:

    # -----------------------------------
    def _convertWeekDays(val):
        _it_days='DLMMGVS' # tasmota days start from Sunday
        _en_days='SMTWTFS' # tasmota days start from Sunday
        _data=''
        for i in range(0, 7):
            _data+=_en_days[i] if val[i]=='1' else '_ '
        return _data[1:] + _data[0] # lets start from Monday



    # -----------------------------------
    def sum_offset(t0_time, offset):
        offset_HH, offset_MM=offset.split(':')
        offset_minutes=abs(int(offset_HH))*60+int(offset_MM)
        if offset_minutes==0:
            return t0_time

        t0_HH, t0_MM=t0_time.split(':')
        t0=timedelta(hours=int(t0_HH), minutes=int(t0_MM))
        ofs=timedelta(hours=int(offset_HH), minutes=int(offset_MM))

        if offset[0]=='-':
            new_time=t0-ofs
        else:
            new_time=t0+ofs

        return time.strftime("%H:%M", time.gmtime(new_time.total_seconds()))

    # -----------------------------------


    myTimers={}
    _action=['off', 'on', 'toggle', 'rule/blink']
    _mode=['clock time', 'sunrise', 'sunset']

    basePtr='timers'
    myTimers['Enabled']=device['timers.Timers']

    if myTimers['Enabled']=='ON':

        for i in range(1, 17):
            timerx=device[f'timers.Timer{i}']
            if timerx['Enable']==0:
                continue

            if timerx['Output']!=output:
                continue

            MODE=_mode[int(timerx['Mode'])]
            ACTION=_action[int(timerx['Action'])]
            REPEAT='YES' if timerx['Repeat']=='1' else 'NO'
            offset=timerx["Time"]
            DAYS=_convertWeekDays(timerx['Days'])
            RELAY=timerx['Output']

            if MODE == 'sunset':
                onTime=' sS'
                offset=timerx["Time"]
                _time=sum_offset(t0_time=sunset_time,offset=offset)

            elif MODE == 'sunrise':
                onTime=' sR'
                _time=sum_offset(t0_time=sunrise_time,offset=offset)

            else:
                onTime=''
                _time=timerx["Time"]

            myTimers[f'T{i}']=f'{_time} {RELAY}.{ACTION} {DAYS}{onTime}'

    return myTimers
