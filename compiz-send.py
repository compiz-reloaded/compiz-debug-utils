#!/usr/bin/env python3

from __future__ import print_function

import dbus

from argparse import ArgumentParser
from os import environ
import sys
import subprocess
from xml.dom import minidom


METHOD_ACTIVATE, METHOD_LIST, METHOD_GET = range(3)

booldict = {'true': True, 'false': False}


def destrify(s):
    '''Attempt to turn a string into an int, float, or bool'''
    value = None
    try:
        i = int(s, 0)
    except ValueError:
        try:
            f = float(s)
        except ValueError:
            value = booldict.get(s.lower(), s)
        else:
            value = f
    else:
        value = i
    return value

# Getting root window ID
try:
    rootwin = subprocess.Popen(['xwininfo', '-root'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
except OSError:
    raise SystemExit('Error: xwininfo not present')

try:
    rootwin_id = int(rootwin.split()[3], 0)
except IndexError:
    raise SystemExit('Error: unexpectedly short output from xwininfo')
except ValueError:
    raise SystemExit('Error: unable to convert "%s" to int', rootwin.split()[3])

disp = environ.get('DISPLAY')
if disp is None:
    print("Couldn't find a screen, check if DISPLAY is set right", file=sys.stderr)
    sys.exit(1)
screen_parts = disp.split(':')[-1].split('.')

if len(screen_parts) == 1:
    screen = '0'
else:
    screen = screen_parts[-1]

# dbus call setup
service = interface = 'org.freedesktop.compiz'
session_bus = dbus.SessionBus()

parser = ArgumentParser()
parser.set_defaults(method=METHOD_LIST)
group = parser.add_mutually_exclusive_group()
group.add_argument('--call', '-c', dest='method',
    action='store_const', const=METHOD_ACTIVATE)
group.add_argument('--get', '-g', dest='method',
    action='store_const', const=METHOD_GET)
parser.add_argument('--screen', '-s',
    action='store_true', default=False,
    help='Use the current screen for Compiz')

parser.add_argument('plugin', nargs='?')
parser.add_argument('plugin_args', nargs='*')

args_ns = parser.parse_args()

method = args_ns.method
plugin = args_ns.plugin
plugin_args = args_ns.plugin_args
screen_specific = args_ns.screen

if method == METHOD_LIST and plugin is None:
    proxy = session_bus.get_object(service, "/org/freedesktop/compiz")
    print("Available methods:", file=sys.stderr)
    xml = minidom.parseString(proxy.Introspect())
    print(xml.toprettyxml(), file=sys.stderr)
    sys.exit(0)

if method == METHOD_ACTIVATE:
    action = plugin_args.pop(0)
if method == METHOD_GET:
    prop = plugin_args.pop(0)

args = ['root', rootwin_id]

for k, v in zip(plugin_args[0::2], plugin_args[1::2]):
    args.append(k)
    args.append(destrify(v))

# D-Bus call
if method == METHOD_ACTIVATE:
    if screen_specific:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/screen%s/%s' %(plugin, screen, action))
    else:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/allscreens/%s' %(plugin, action))
    obj = dbus.Interface(proxy, interface)
    obj.activate(*args)
elif method == METHOD_LIST:
    if screen_specific:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/screen%s' %(plugin, screen))
    else:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/allscreens' %(plugin))
    obj = dbus.Interface(proxy, interface)
    res = obj.list()
    if res is not None:
        print('\n'.join(obj.list()))
elif method == METHOD_GET:
    if screen_specific:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/screen%s/%s' %(plugin, screen, prop))
    else:
        proxy = session_bus.get_object(
            service, '/org/freedesktop/compiz/%s/allscreens/%s' %(plugin, prop))

    obj = dbus.Interface(proxy, interface)
    res = obj.get()

    if isinstance(res, dbus.Array):
        for r in res:
            print(r)
    else:
        print(res)

# vim: et:sw=4:ts=4
