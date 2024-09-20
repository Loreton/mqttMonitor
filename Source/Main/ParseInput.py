#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17
#
# updated by ...: Loreto Notarantonio
# Date .........: 14-07-2024 18.01.29
#

import  sys; sys.dont_write_bytecode = True
import  os
from pathlib import Path

import argparse


# -----------------------------
def check_log_dir(path):
    p = Path(path).resolve()
    if p.is_dir():
        return str(p)
    else:
        p.mkdir(parents=True, exist_ok=True)
        return str(p)


# -----------------------------
def check_db_dir(path):
    p = Path(base_device_db_dir) / path
    if (p).is_dir():
        return str(p.resolve())
    else:
        print(f"""\n    Input arg ERROR:  {p} doesn't exists.
            pleas enter on of the following directories
            under the path: {base_device_db_dir}\n""")

        files=os.listdir(base_device_db_dir)
        for file in files:
            if (base_device_db_dir / file).is_dir() and file.startswith("D20"):
                print("     -", file)
        print()
        sys.exit(1)


##############################################################
# - Parse Input
##############################################################
def ParseInput(version: str, db_dir: str):
    global base_device_db_dir
    base_device_db_dir = Path(db_dir)
    logger_levels=['trace', 'debug', 'notify', 'info', 'function', 'warning', 'error', 'critical']

    # -- add common options to all subparsers
    def subparser_common_options(subparsers):
        for name, subp in subparsers.choices.items():
            ### --- mi serve per avere la entry negli args e creare poi la entry "product"
            subp.add_argument('--{0}'.format(name), action='store_true', default=True)
            single_parser_common_options(subp)


    # -- add common options to all subparsers
    def single_parser_common_options(_parser):

        # _parser.add_argument('--go', help='specify if command must be executed. (dry-run is default)', action='store_true')
        _parser.add_argument('--display-args', action='store_true', help='''Display arguments\n\n''' )
        _parser.add_argument('--systemd', action='store_true', help='''It's a systemd process\n\n''' )
        _parser.add_argument('--clean-device-data', action='store_true', help='''Clean all devices data\n\n''' )
        # _parser.add_argument('--pid-file', type=str, required=False, default='/tmp/mqttmonitor/mqttmonitor.pid', help='''pid file\n\n''' )

        _parser.add_argument( "--console-logger-level",
                                metavar='<optional>',
                                type=str.lower,
                                required=False,
                                default='critical',
                                choices=logger_levels,
                                nargs="?", # just one entry
                                help=f"""set console logger level:
                                        {logger_levels}
                                        \n\n""".replace('  ', '')
                            )


        _parser.add_argument( "--file-logger-level",
                                metavar='<optionalr>',
                                type=str.lower,
                                required=False,
                                default='warning',
                                choices=logger_levels,
                                nargs="?", # just one entry
                                help=f"""set file logger level:
                                        {logger_levels}
                                        \n\n""".replace('  ', '')
                            )



        _parser.add_argument( "--logging-dir",
                                metavar='<logger_dir>',
                                type=check_log_dir,
                                required=True,
                                default=None,
                                help=f"""full path of logger directory. It will be created dinamically. \n\n""".replace('  ', '')
                            )





    # =============================================
    # = Parsing
    # =============================================
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    db_file=os.environ.get("DB_FILE")

    # parser=argparse.ArgumentParser(description='mqtt monitoring', formatter_class=argparse.RawTextHelpFormatter)
    # https://stackoverflow.com/questions/61324536/python-argparse-with-argumentdefaultshelpformatter-and-rawtexthelpformatter
    class UltimateHelpFormatter_xx(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter ): pass
    class UltimateHelpFormatter(argparse.RawTextHelpFormatter ): pass

    parser=argparse.ArgumentParser(epilog="first line\n second line", formatter_class=UltimateHelpFormatter)

    parser.add_argument('--version', action='version', version=version)



    parser.add_argument('--topics',
                                type=str,
                                metavar='topics',
                                required=True,
                                default=['+/#'],
                                # nargs='*',
                                nargs='+',
                                help="""topics to listen, delimited by spaces.
        Es: --topics topic1 topic2 +/#
            (default: %(default)s)
    """)


    parser.add_argument("--db-version-dir",
                            type=check_db_dir,
                            metavar='-',
                            required=True,
                            default=None,
                            help=f"""directory:
                                    under path: {base_device_db_dir}
                                    (default: %(default)s)
                    """ )




    parser.add_argument(
            '--broker-name',
            metavar='-',
            type=str,
            required=True,
            choices=['LnMqtt', "emq", 'hiveMQ'],
            help='MQTT broker alias name  (default: %(default)s)'
        )

    parser.add_argument('--clear-retained',
                        action='store_true',
                        help='''clear retained messages (topic +/# far all) (default: %(default)s)\n\n''')

    parser.add_argument('--retained',
                        action='store_true',
                        help='''display retained messages (default: %(default)s)\n\n''')

    parser.add_argument('--just-monitor',
                        action='store_true',
                        help='''just monitoring mqtt broker messages (default: %(default)s)\n\n''')

    parser.add_argument('--save-period',
                        required=False,
                        default=5, ### valore iniziale... poi nel programma verrà portato a 60
                        type=int,
                        help="period to save device data on file (default: %(default)s)\n\n")


    parser.add_argument('--telegram-group-name',
                        metavar='-',
                        required=True,
                        type=str,
                        default=None,
                        help='Telegram group_name related to this application (default: %(default)s)\n\n')






    single_parser_common_options(parser)

    args = parser.parse_args()


    if args.display_args:
        import json
        json_data = json.dumps(vars(args), indent=4, sort_keys=True)
        print('input arguments: {json_data}'.format(**locals()))
        sys.exit(0)


    return  args

