#!/usr/bin/env python2

import subprocess
import sys
from argparse import ArgumentParser

def cmd_quote(string):
	if sys.version_info < (3, 3):
		import pipes
		return pipes.quote(string)
	else:
		import shlex
		return shlex.quote(string)

def ex_wrapper(items):
	"""Places an -ex before each item in iterable"""
	for item in items:
		yield '-ex'
		yield item

def gdb_wrapper(setup_args, post_setup_args=[], prog=None, fname=None, examine=False):
	if prog is None:
		gdb_args = ['gdb', '-batch-silent']
	else:
		gdb_args = ['gdb', prog, '-batch-silent']
	gdb_args.extend(setup_args)

	if fname is not None:
		gdb_args.extend(ex_wrapper([
			'set logging file {0}'.format(cmd_quote(fname)),
			'set logging overwrite on',
			"set logging on"
		]))

	gdb_args.extend(ex_wrapper([
		"set pagination off",
		"handle SIG33 pass nostop noprint",
	]))
	gdb_args.extend(post_setup_args)
	gdb_args.extend(ex_wrapper([
		"echo backtrace:\n"
		"backtrace full"
	]))

	if fname is not None:
		gdb_args.extend(ex_wrapper([
			"set logging off"
		]))

	gdb_args.extend(ex_wrapper([
		"detach",
		"quit",
	]))

	if examine:
		print('\n'.join(gdb_args))
	else:
		subprocess.call(gdb_args)

def attach_and_save(args, cmd_args):
	pid = args.pid
	fname = args.file
	examine = args.examine

	gdb_wrapper(
		ex_wrapper(['attach {0}'.format(pid), 'c']),
		fname=fname,
		examine=examine
	)

def run_and_save(args, cmd_args):
	prog = args.prog
	prog_args = cmd_args
	fname = args.file
	examine = args.examine

	prog_args=' '.join([cmd_quote(a) for a in prog_args])

	gdb_wrapper(
		[],
		post_setup_args=ex_wrapper(['run {0}'.format(prog_args)]),
		fname=fname,
		prog=prog,
		examine=examine
	)

parser = ArgumentParser()
parser.add_argument('-f', '--file', help="Backtrace file")
parser.add_argument('-x', '--examine', help="Don't run gdb, just show the generated args", action='store_true', default=False)
subparsers = parser.add_subparsers(title='subcommands', help='additional help')

pid_parser = subparsers.add_parser('attach')
pid_parser.set_defaults(func=attach_and_save)
pid_parser.add_argument('pid', type=int)

run_parser = subparsers.add_parser('run')
run_parser.set_defaults(func=run_and_save)
run_parser.add_argument('prog', nargs='?', default='compiz')

args_ns, cmd_args = parser.parse_known_args()
print(args_ns, cmd_args)
args_ns.func(args_ns, cmd_args)
