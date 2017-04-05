#!/usr/bin/env python3

from itertools import chain, product
import sys

# I like lxml because it functions sanely
from lxml import etree

binds = {
    'key': {},
    'button': {},
    'edge': {},
}

binding_xpaths = [
    '//option[@type="{0}"]'.format(k)
    for k in binds.keys()
]

ignore = {
    # all are only applicable when showing scale results
    'scaleaddons': None,

    # these are bindings that're relative to expo's mode
    'expo': {
        'dnd_button',
        'exit_button',
        'next_vp_button',
        'prev_vp_button',
    },

    # window move context
    'wobbly': {
        'snap_key',
    },

    # I still want to factor this out into providing a custom context
    # any plugin can setup bindings in 8|
    'vpswitch': {
        'initiate_button',
    },

    # since these are for the caps,
    # I think they operate in the same context
    # as the cube's next/prev slide key
    'cube': {
        'next_slide_key',
        'prev_slide_key',
    },

    'cubeaddon': {
        '_'.join(items) for
        items in product(
            ('top', 'bottom'),
            ('next', 'prev'),
            ('key', 'button')
        )
    }
}

for fname in sys.argv[1:]:
    items = etree.parse(fname)
    plugin_name = items.xpath('//plugin')[0]

    # ignore if all 
    context_sensitive_actions = ignore.get(plugin_name, {})
    if context_sensitive_actions is None:
        continue

    for b_xpath in binding_xpaths:
        features = { item.text for item in items.xpath('.//feature') }
        for opt in items.xpath(b_xpath):
            dflt_binding = opt.xpath('./default')

            if opt.attrib['name'] in context_sensitive_actions:
                continue

            if not dflt_binding:
                continue

            dflt_binding = dflt_binding[0]
            
            if dflt_binding.text is None:
                continue

            if dflt_binding.text.strip() in {'none', ''}:
                continue


            # caveat: we don't have anything in metadata
            # that indicates that a binding is context-sensitive
            # meaning it really only applies when the plugin is active
            # so the modless-Button related ones are false positives

            # For now, hardcode which plugins have context sensitive bindings

            binds[opt.attrib['type']].setdefault(
                dflt_binding.text,
                []
            ).append(
                '{0}:{1}'.format(
                    plugin_name.attrib['name'],
                    opt.attrib['name']
                )
            )

for section in binds:
    for bind, plugins in binds[section].items():
        if len(plugins) <= 1:
            continue
        print(bind, "is shared in")

        for p in plugins:
            print('\t{0}'.format(p))
        print()
