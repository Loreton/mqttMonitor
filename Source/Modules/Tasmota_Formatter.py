#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 01-12-2022 08.44.42

import  sys; sys.dont_write_bytecode = True
import  os
# import logging; logger=logging.getLogger(__name__)

from LoretoDict import LnDict
from LnTime import millisecs_to_HMS_ms
from datetime import timedelta, datetime
import time
from LnSunTime import sunTime_casetta



def setup(my_logger):
    global logger, italicB, italicE
    logger=my_logger
    italicB='<i>'; italicE='</i>'

def getBasePointer(d: dict, key_list: list):
    keys=d.keySearch(d=d,  key_patterns=key_list)


####################################################################
### preparazione stato WiFi
####################################################################
def wifi(data: dict):
    wifi={}
    # wifi["SSId"]=italicB +  data['SSId'] + italicE
    # wifi["BSSId"]=italicB +  data['BSSId'] + italicE
    # wifi["RSSI"]=italicB +  data['RSSI'] + italicE
    # wifi["Signal"]=italicB +  data['Signal'] + italicE

    wifi["SSId"]=f"{italicB}{data['SSId']}{italicE}"
    wifi["BSSId"]=f"{italicB}{data['BSSId']}{italicE}"
    wifi["RSSI"]=f"{italicB}{data['RSSI']}{italicE}"
    wifi["Signal"]=f"{italicB}{data['Signal']}{italicE}"


    return wifi


####################################################################
### info varie
####################################################################
def deviceInfo(data: dict):
    d=dict()
    iS='<i>'; iE='</i>'
    _date, _time=data['last_update'].split('T')

    d['device_name'] = italicB + data['device_name'] + italicE
    d['Last Update']= {
                "date": italicB + _date + italicE,
                "time": italicB + _time + italicE
                }
    d['firmware'] = italicB + data['firmware'] + italicE
    d['modello'] = italicB + data['modello']  + italicE

    # for key, value in d.items():
    #     d[key]=f"{iS}{value}{iE}"
    return d








############################################################################
# new_data --> {"POWER1":"OFF"}
############################################################################
def retrieveRelayStatus(data: dict, relayNr: int, new_data: dict={}) -> str:

    pwr_key=f'POWER{relayNr}'
    power_status=None

    '''prendiamo in considerazione  new_data se viene passato come argomento'''
    if new_data and isinstance(new_data, dict):
        power_status=new_data.get(pwr_key, None)

    # verifica dello status più aggiornato (nell'ordine)
    if not power_status:
        power_status=data.get_keypaths(keypaths=[f'STATE.{pwr_key}', f'STATUS11.{pwr_key}', f'RESULT.{pwr_key}'])


    if not power_status:
        power_status='N/A'

    return power_status





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
def getPulseTime(data: dict, relayNr: int):

    #----------------------------------------------
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
    #----------------------------------------------


    SET=data['PulseTime.Set']
    REMAINING=data['PulseTime.Remaining']

    pulsetime_value=pulseTimeToSeconds(SET[relayNr]) if SET else None
    pulsetime_remaining=pulseTimeToSeconds(REMAINING[relayNr]) if REMAINING else None

    return pulsetime_value, pulsetime_remaining
    # return f"{italicB}{pulsetime_value}{italicE}", f"{italicB}{pulsetime_remaining}{italicE}"



def setPulseTime(data, relayNr):
    """da sviluppare"""

    def secondsToPulseTime(seconds: float) -> int:
        seconds=float(seconds)
        if seconds<=11.1:
            pulsetime_value=seconds*10
        else:
            pulsetime_value=int(seconds)+100

        return int(pulsetime_value)


    SET=data['RESULT.PulseTime.Set']
    REMAINING=data['RESULT.PulseTime.Remaining']
    pulsetime_value=pulseTimeToSeconds(SET[relayNr]) if SET else None
    pulsetime_remaining=pulseTimeToSeconds(REMAINING[relayNr]) if REMAINING else None

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
def timers(data: dict, outputRelay: int=0, italic=False) -> dict:
    # if 'RESULT' in data:
        # data=data['RESULT']

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
    if outputRelay<1:
        outputRelay=list(range(1,16+1)) # possono essere massimo 16 timers
    else:
        outputRelay=[min(int(outputRelay), 16)] # per evitare > 16

    _action=['off', 'on', 'toggle', 'rule/blink']
    _mode=['clock time', 'sunrise', 'sunset']
    sunrise_time, sunset_time=sunTime_casetta(str_format='%H:%M')



    myTimers={}

    areEnabled=(data['Timers']=="ON")


    if areEnabled:

        for i in range(1, 17):
            # logger.notify('i: %s [%s]', i, type(i))
            timerx=data[f'Timer{i}']
            if timerx['Enable']==0:
                continue

            if int(timerx['Output']) not in outputRelay:
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

            # myTimers[f'T{i}']=f'{_time} {ACTION} {DAYS}{onTime} [{RELAY}]'
            if italic:
                myTimers[f'T{i}']=f'{italicB}{_time} {ACTION} {DAYS}{onTime}{italicE}' # italic
            else:
                myTimers[f'T{i}']=f'{_time} {ACTION} {DAYS}{onTime}'
    else:
        myTimers='Disabled'

    return myTimers



    #### TO BE DELETED

    '''
    myTimers={}
    # print(data.to_json())
    if 'timers' in data:
        basePtr=data['timers']
        # areEnabled=(data['timers']['Timers']=="ON")
    elif 'RESULT' in data:
        basePtr=data['RESULT']
        # areEnabled=(data['RESULE']['Timers']=="ON")
    else:
        basePtr=data
        # areEnabled=(data['Timers']=="ON")

    areEnabled=(basePtr['Timers']=="ON")

    if areEnabled:
        # if myTimers['Enabled']=='ON':
        # myTimers['Enabled']=data[f'{basePtr}Timers']

        for i in range(1, 17):
            timerx=basePtr[f'Timer{i}']
            if timerx['Enable']==0:
                continue

            if int(timerx['Output']) not in outputRelay:
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
    else:
        myTimers='Disabled'

    return myTimers
    '''