import argparse
import sys
import textwrap

from colorama import Fore, Style

from tncli.modules.deploy_contract import ContractDeployer
from tncli.modules.projects import ProjectBootstrapper
from tncli.modules.utils.func.func import Func
from tncli.modules.utils.system.argparse_fix import argv_fix
from tncli.modules.utils.system.log import logger
from tncli.modules.utils.fift.cli_lib import process_build_cli_lib_command
from tncli.modules.utils.fift.fift import Fift
from tncli.modules.utils.lite_client.lite_client import LiteClient

gr = Fore.GREEN
bl = Fore.CYAN
rs = Style.RESET_ALL


def main():
    '''
    CLI interface definition

    :return:
    '''

    help_text = f'''{Fore.YELLOW}TON blockchain is the future 🦄
--------------------------------
Command list, e.g. usage: tncli start wallet

{bl}start - create new project structure based on example project  
{gr}   wallet - create project with v3 wallet example

{bl}deploy - deploy current project to blockchain

{bl}fift / f - interact with fift :)
{gr}   interactive - default, run interactive fift
{gr}   run - run fift file ([config/fift-lib/] will be auto passed to -I
{gr}   sendboc - run fift file and run sendfile in lite-client, to made this work you need to add `saveboc` at the end of file
             if it called in project root - will create build/boc/[filename].boc file, else will use temp dir

{bl}wallet - interact with deploy-wallet

{rs}
Each command have help e.g.: tncli deploy -h

Credits: disintar.io team
'''

    # TODO: add logging verbose

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_text))

    subparser = parser.add_subparsers()

    parser_project = subparser.add_parser('start',
                                          description='Create new project structure based on example project')
    parser_project.add_argument('project', default='wallet', choices=['wallet', 'external_data'],
                                help="Which default project to bootstrap")

    parser_project.add_argument("--name", "-n", default='wallet', type=str, help='New project folder name')

    parser_deploy = subparser.add_parser('deploy', description='Deploy project to blockchain')
    parser_deploy.add_argument("--net", "-n", default='testnet', type=str, choices=['testnet', 'mainnet'],
                               help='Network to deploy')
    parser_deploy.add_argument("--workchain", "-wc", default=0, type=int, help='Workchain deploy to')
    parser_deploy.add_argument("--ton", "-t", default=0.05, type=int, help='How much TON will be sent to new contract')
    parser_deploy.add_argument("--update", action='store_true', help='Update cached configs of net')

    fift_help = f'''positional arguments:
  {bl}command{rs}              Which mode to run, can be [interactive, run, sendboc]
  {gr}   interactive - default, run interactive fift
  {gr}   run - run fift file ([config/fift-lib/] will be auto passed to -I
  {gr}   sendboc - run fift file and run sendfile in lite-client, you need to set only BOC in the stack
               if it called in project root - will create build/boc/[filename].boc file, else will use temp dir
  {rs}
'''
    lite_client_help = f'''positional arguments:
      {bl}command{rs}             
      {gr}   interactive - default, run interactive lite_client
      {gr}   
      {gr}   OTHER - all other arguments will passed to lite_client e.g. tnctl lc help
      {rs}
    '''
    func_help = f'''positional arguments:
      {bl}command{rs}             
      {gr}   build - default, build func code in build/ folder, if no build 
      {gr}   
      {gr}   OTHER - all other arguments and kwargs will pass to fun command
      {rs}
    '''
    #
    # shortcuts
    #

    subparser.add_parser('f', help="Same as fift",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description=textwrap.dedent(fift_help))
    subparser.add_parser('fc', help="Same as func",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description=textwrap.dedent(func_help))
    subparser.add_parser('lc', help="Same as lite-client",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description=textwrap.dedent(lite_client_help))
    subparser.add_parser('run', help="Same as fift run",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description=textwrap.dedent(fift_help))
    subparser.add_parser('build', help="Same as func build",
                         formatter_class=argparse.RawDescriptionHelpFormatter,
                         description=textwrap.dedent(fift_help))

    #
    #  FIFT
    #

    parser_fift = subparser.add_parser('fift', help=fift_help,
                                       formatter_class=argparse.RawDescriptionHelpFormatter,
                                       description=textwrap.dedent(fift_help))
    parser_fift.add_argument("--net", "-n", default='testnet', type=str, choices=['testnet', 'mainnet'],
                             help='Network to deploy')
    parser_fift.add_argument("--workchain", "-wc", default=0, type=int, help='Workchain deploy to')
    parser_fift.add_argument("--update", action='store_true', default=False, help='Update cached configs of net')
    parser_fift.add_argument("--build", action='store_true', default=False, help='Build func code from func/ folder in project')
    parser_fift.add_argument("--fift-args", "-fa", type=str, default='',
                             help='Pass args and kwargs to fift command, e.g.: -fa "-v 4" - '
                                  'set verbose level, will overwrite default ones, '
                                  'if you want pass args after command just don\'t use flag, f.e.g. '
                                  '[tncli fift run wallet.fif 0 0 1 -v 4]')
    parser_fift.add_argument("--lite-client-args", "-la", type=str,
                             default='',
                             help='Pass args and kwargs to lite-client command in sendboc mode, '
                                  'e.g.: -la "-v 4" - set verbose level')

    #
    #  LITE CLIENT
    #

    parser_lite_client = subparser.add_parser('lite-client', help=lite_client_help,
                                              formatter_class=argparse.RawDescriptionHelpFormatter,
                                              description=textwrap.dedent(lite_client_help))
    parser_lite_client.add_argument("--net", "-n", default='testnet', type=str, choices=['testnet', 'mainnet'],
                                    help='Network to deploy')
    parser_lite_client.add_argument("--update", action='store_true', default=False, help='Update cached configs of net')
    parser_lite_client.add_argument("--lite-client-args", "-la", type=str,
                                    default='',
                                    help='Pass args and kwargs to lite-client command')

    #
    #  FUNC
    #

    parser_func = subparser.add_parser('func', help=func_help,
                                       formatter_class=argparse.RawDescriptionHelpFormatter,
                                       description=textwrap.dedent(func_help))
    parser_func.add_argument("--func-args", "-fca", type=str,
                             default='',
                             help='Pass arguments to func command')
    parser_func.add_argument("--fift-args", "-fa", type=str, default='',
                             help='Pass args and kwargs to fift command, e.g.: -fa "-v 4" - '
                                  'set verbose level, will overwrite default ones, '
                                  'if you want pass args after command just don\'t use flag, f.e.g. '
                                  '[tncli fift run wallet.fif 0 0 1 -v 4]')
    parser_func.add_argument("--run", "-r", action='store_true', default=False,
                             help='Run fift code that was generated in build mode')

    command = sys.argv[1] if len(sys.argv) > 1 else None

    # it's tricky one
    # we want to support arguments as by default is None
    # we can't do it with argparse
    # so we need to get all str flags to correctly parse kwargs after argument can be none by default
    string_kwargs = []

    group_actions = parser._subparsers._group_actions

    for group_action in group_actions:
        choices = group_action.choices

        for choice in choices:
            arguments = choices[choice]._option_string_actions

            for key in arguments:
                if arguments[key].type == str:
                    string_kwargs.append(key)

    # wtf I need to do this, need to change!
    # Parse fift
    if command and command in ['fift', 'f', 'run'] and len(sys.argv) >= 2:
        _, kwargs = argv_fix(sys.argv, string_kwargs)
        args = parser.parse_args(['fift', *kwargs])
    # Parse lite-client
    elif command in ['lite-client', 'lc']:
        _, kwargs = argv_fix(sys.argv, string_kwargs)
        args = parser.parse_args(['lite-client', *kwargs])
    elif command in ['func', 'fc', 'build']:
        _, kwargs = argv_fix(sys.argv, string_kwargs)
        args = parser.parse_args(['func', *kwargs])
    # Parse specific build-cli-lib
    elif command == 'build-cli-lib':
        process_build_cli_lib_command(sys.argv[2:])
    # Parse else
    else:
        args = parser.parse_args()

    # If no kwargs and no command just display help text
    if len(args._get_kwargs()) == 0 and not command:
        parser.print_help()
        sys.exit(0)

    if command == 'start':
        bootstrapper = ProjectBootstrapper(project_name=args.project, folder_name=args.name)
        bootstrapper.deploy()

    elif command == 'deploy':
        deployer = ContractDeployer(network=args.net, update_config=args.update, workchain=args.workchain, ton=args.ton)
        deployer.publish()

    elif command in ['fift', 'f', 'run']:
        # get real args
        real_args, _ = argv_fix(sys.argv, string_kwargs)

        # Add support of tncli run ...
        if command != 'run':
            # Parse command (fift [command])
            command = real_args[2] if len(real_args) > 2 else None
            args_to_pass = real_args[3:]
        else:
            args_to_pass = real_args[2:]

        # Parse kwargs by argparse
        kwargs = dict(args._get_kwargs())

        # If use run command instead of f run - need to change start arg parse position
        fift = Fift(command, kwargs=kwargs, args=args_to_pass)
        fift.run()

    elif command in ['lite-client', 'lc']:
        real_args, _ = argv_fix(sys.argv, string_kwargs)
        args_to_pass = real_args[3:]

        # Parse kwargs by argparse
        kwargs = dict(args._get_kwargs())

        # Parse command
        command = real_args[2] if len(real_args) > 2 else None

        # If use run command instead of f run - need to change start arg parse position
        lite_client = LiteClient(command, kwargs=kwargs, args=args_to_pass)
        lite_client.run()
    elif command in ['func', 'fc', 'build']:
        real_args, _ = argv_fix(sys.argv, string_kwargs)

        # Parse kwargs by argparse
        kwargs = dict(args._get_kwargs())

        # Add support of tncli run ...
        if command != 'build':
            # Parse command (func [command])
            command = real_args[2] if len(real_args) > 2 else None
            args_to_pass = real_args[3:]
        else:
            args_to_pass = real_args[2:]

        # If use run command instead of f run - need to change start arg parse position
        func = Func(command, kwargs=kwargs, args=args_to_pass)
        func.run()
    else:
        logger.error("🔎 Can't find such command")
        sys.exit()


if __name__ == '__main__':
    main()
