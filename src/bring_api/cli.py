from .api import BringApi
import logging
import argparse
import os
import sys


from bring_api import __version__

_logger = logging.getLogger(__name__)


def lists(api, args):
    relevant_lists = _relevant_lists(api, args)
    for l in relevant_lists:
        print(l)
        purchase_items = l.purchase_items()
        recently_items = l.recently_items()
        if purchase_items:
            print("Purchase:")
            for item in purchase_items:
                print("- {0}".format(item))
        if args.show_recently and recently_items:
            for item in recently_items:
                print("- {0}".format(item))


def _relevant_lists(args, api):
    all_lists = api.lists()
    if args.list:
        return [l for l in all_lists if l.name in args.list]
    else:
        return all_lists


def add(api, args):
    pass


def purchase(api, args):
    pass


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--email', type=str,
                        default=os.environ.get('BRING_EMAIL'))
    parser.add_argument('-p', '--password', type=str,
                        default=os.environ.get('BRING_PASSWORD'))
    parser.add_argument('-v', '--verbose',
                        dest="loglevel", help="set loglevel to INFO",
                        action='store_const', const=logging.INFO)
    parser.add_argument(
        '--version',
        action='version',
        version='bring {0}'.format(__version__))

    subparsers = parser.add_subparsers()

    parser_list = subparsers.add_parser('lists')
    parser_list.add_argument('-l', '--list', nargs='*')
    parser_list.add_argument('-r', '--show-recently', action='store_true')
    parser_list.set_defaults(func=lists)

    parser_add = subparsers.add_parser('add')
    parser_add.set_defaults(func=add)

    parser_purchase = subparsers.add_parser('purchase')
    parser_purchase.set_defaults(func=purchase)

    parsed_args = parser.parse_args(args)

    if not parsed_args.email or not parsed_args.password:
        exit(parser.print_usage())

    return parser.parse_args(args)


def setup_logging(loglevel):
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def main(args):
    args = parse_args(args)
    setup_logging(args.loglevel)
    api = BringApi.authenticate(args.email, args.password)
    args.func(api, args)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
