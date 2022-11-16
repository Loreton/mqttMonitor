#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 2021-09-17
#
# updated by ...: Loreto Notarantonio
# Date .........: 16-11-2022 21.23.48
#

import  sys; sys.dont_write_bytecode = True
import  os


##############################################################
# - Parse Input
##############################################################
def ParseInput():
    import argparse
    logger_levels=['trace', 'debug', 'notify', 'info', 'function', 'warning', 'error', 'critical']

    # -- add common options to all subparsers
    def single_parser_common_options(_parser):
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


        _parser.add_argument( "--file-logger-level",   ##  MI DA ERRORE
                                metavar='<file_logger>',
                                type=str.lower,
                                required=False,
                                default='warning',
                                choices=logger_levels,
                                nargs="?", # just one entry
                                help=f"""set file logger level:
                                        {logger_levels}
                                        \n\n""".replace('  ', '')
                            )

        _parser.add_argument('--go', help='specify if command must be executed. (dry-run is default)', action='store_true')
        _parser.add_argument('--display-args', action='store_true', help='''Display arguments\n\n''' )
        _parser.add_argument('--systemd', action='store_true', help='''It's a systemd process\n\n''' )



    # -- add common options to all subparsers
    def subparser_common_options(subparsers):
        for name, subp in subparsers.choices.items():
            ### --- mi serve per avere la entry negli args e creare poi la entry "product"
            subp.add_argument('--{0}'.format(name), action='store_true', default=True)
            single_parser_common_options(subp)

    # =============================================
    # = Parsing
    # =============================================
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    parser=argparse.ArgumentParser(description='mqtt monitoring', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--topics',
                                metavar='',
                                required=True,
                                default=['+/#'],
                                # nargs='*',
                                nargs='+', type=str,
                                help="""topics to listen, delimited by spaces.
        Es: --topics vescovi-Power Vescovi-Control
            default: +/#
    """)
    parser.add_argument('--clear-retained', action='store_true', help='''clear retained messages (topic +/# far all)\n\n''')
    parser.add_argument('--retained', action='store_true', help='''display retaied messages (topic +/# far all)\n\n''')
    parser.add_argument('--monitor', action='store_true', help='''just monitoring mqtt broker messages (topic +/# far all)\n\n''')





    single_parser_common_options(parser)

    args = parser.parse_args()


    if args.display_args:
        import json
        json_data = json.dumps(vars(args), indent=4, sort_keys=True)
        print('input arguments: {json_data}'.format(**locals()))
        sys.exit(0)


    return  args

