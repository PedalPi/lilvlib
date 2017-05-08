#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint

import lilv
import os

from plugin import Plugin


def get_all_plugins():
    world = lilv.World()
    world.load_all()
    plugins = world.get_all_plugins()

    return [Plugin(world, p, False).data for p in plugins]


'''
Get plugin-related info from a list of lv2 bundles

@param bundles is a list of strings, consisting of directories in the
               filesystem (absolute pathnames).
'''
def get_plugins_info(bundles):
    if len(bundles) == 0:
        raise Exception('get_plugins_info() - no bundles provided')

    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    # (these functions are not exposed via World yet)
    lilv.lilv_world_load_specifications(world.me)
    lilv.lilv_world_load_plugin_classes(world.me)

    # load all bundles
    for bundle in bundles:
        # lilv wants the last character as the separator
        bundle = os.path.abspath(bundle)
        if not bundle.endswith(os.sep):
            bundle += os.sep

        # convert bundle string into a lilv node
        bundlenode = lilv.lilv_new_file_uri(world.me, None, bundle)

        # load the bundle
        world.load_bundle(bundlenode)

        # free bundlenode, no longer needed
        lilv.lilv_node_free(bundlenode)

    plugins = world.get_all_plugins()

    if plugins.size() == 0:
        raise Exception('get_plugins_info() - selected bundles have no plugins')

    return [Plugin(world, p, False) for p in plugins]

'''
if __name__ == '__main__':
    from sys import argv  # , exit
    from pprint import pprint
    #get_plugins_info(argv[1:])
    #for i in get_plugins_info(argv[1:]): pprint(i)
    #exit(0)
    for i in get_plugins_info(argv[1:]):
        warnings = i['warnings'].copy()

        if 'plugin brand is missing' in warnings:
            i['warnings'].remove('plugin brand is missing')

        if 'plugin label is missing' in warnings:
            i['warnings'].remove('plugin label is missing')

        if 'no modgui available' in warnings:
            i['warnings'].remove('no modgui available')

        for warn in warnings:
            if "has no short name" in warn:
                i['warnings'].remove(warn)

        pprint({
            'uri': i['uri'],
            'errors': i['errors'],
            'warnings': i['warnings']
        }, width=200)
'''


if __name__ == "__main__":
    pprint(get_all_plugins(), width=200)
