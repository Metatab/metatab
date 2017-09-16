# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""
Root program for metapack programs

"""

from pkg_resources import iter_entry_points
import argparse

from metapack.cli.core import  cli_init


def mt():
    cli_init()

    parser = argparse.ArgumentParser(
        prog='metapack',
        description='Create and manipulate metatab data packages')

    subparsers = parser.add_subparsers(help='Commands')

    for ep in iter_entry_points(group='mt.subcommands'):

        f = ep.load()
        f(subparsers)

    args = parser.parse_args()

    args.run_command(args)

