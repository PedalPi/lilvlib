#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------------------------------
# Imports

import lilv
import os


# ------------------------------------------------------------------------------------------------------------
# Utilities

def LILV_FOREACH(collection, func):
    itr = collection.begin()
    while itr:
        yield func(collection.get(itr))
        itr = collection.next(itr)

class NS(object):
    def __init__(self, world, base):
        self.world = world
        self.base = base
        self._cache = {}

    def __getattr__(self, attr):
        if attr.endswith("_"):
            attr = attr[:-1]
        if attr not in self._cache:
            self._cache[attr] = lilv.Node(self.world.new_uri(self.base+attr))
        return self._cache[attr]

def is_integer(string):
    return string.strip().lstrip("-+").isdigit()

# ------------------------------------------------------------------------------------------------------------

def get_category(nodes):
    category_indexes = {
        'DelayPlugin': ['Delay'],
        'DistortionPlugin': ['Distortion'],
        'WaveshaperPlugin': ['Distortion', 'Waveshaper'],
        'DynamicsPlugin': ['Dynamics'],
        'AmplifierPlugin': ['Dynamics', 'Amplifier'],
        'CompressorPlugin': ['Dynamics', 'Compressor'],
        'ExpanderPlugin': ['Dynamics', 'Expander'],
        'GatePlugin': ['Dynamics', 'Gate'],
        'LimiterPlugin': ['Dynamics', 'Limiter'],
        'FilterPlugin': ['Filter'],
        'AllpassPlugin': ['Filter', 'Allpass'],
        'BandpassPlugin': ['Filter', 'Bandpass'],
        'CombPlugin': ['Filter', 'Comb'],
        'EQPlugin': ['Filter', 'Equaliser'],
        'MultiEQPlugin': ['Filter', 'Equaliser', 'Multiband'],
        'ParaEQPlugin': ['Filter', 'Equaliser', 'Parametric'],
        'HighpassPlugin': ['Filter', 'Highpass'],
        'LowpassPlugin': ['Filter', 'Lowpass'],
        'GeneratorPlugin': ['Generator'],
        'ConstantPlugin': ['Generator', 'Constant'],
        'InstrumentPlugin': ['Generator', 'Instrument'],
        'OscillatorPlugin': ['Generator', 'Oscillator'],
        'ModulatorPlugin': ['Modulator'],
        'ChorusPlugin': ['Modulator', 'Chorus'],
        'FlangerPlugin': ['Modulator', 'Flanger'],
        'PhaserPlugin': ['Modulator', 'Phaser'],
        'ReverbPlugin': ['Reverb'],
        'SimulatorPlugin': ['Simulator'],
        'SpatialPlugin': ['Spatial'],
        'SpectralPlugin': ['Spectral'],
        'PitchPlugin': ['Spectral', 'Pitch Shifter'],
        'UtilityPlugin': ['Utility'],
        'AnalyserPlugin': ['Utility', 'Analyser'],
        'ConverterPlugin': ['Utility', 'Converter'],
        'FunctionPlugin': ['Utility', 'Function'],
        'MixerPlugin': ['Utility', 'Mixer'],
    }

    def fill_in_category(node):
        category = node.as_string().replace("http://lv2plug.in/ns/lv2core#","")
        if category in category_indexes.keys():
            return category_indexes[category]
        return []
    categories = []
    for cat in [cat for catlist in LILV_FOREACH(nodes, fill_in_category) for cat in catlist]:
        if cat not in categories:
            categories.append(cat)
    return categories

# ------------------------------------------------------------------------------------------------------------
# get_bundle_dirname

def get_bundle_dirname(bundleuri):
    bundle = lilv.lilv_uri_to_path(bundleuri)

    if not os.path.exists(bundle):
        raise IOError(bundleuri)
    if os.path.isfile(bundle):
        bundle = os.path.dirname(bundle)

    return bundle

# ------------------------------------------------------------------------------------------------------------
# get_pedalboard_info

# Get info from an lv2 bundle
# @a bundle is a string, consisting of a directory in the filesystem (absolute pathname).
def get_pedalboard_info(bundle):
    # lilv wants the last character as the separator
    bundle = os.path.abspath(bundle)
    if not bundle.endswith(os.sep):
        bundle += os.sep

    # Create our own unique lilv world
    # We'll load a single bundle and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    # (these functions are not exposed via World yet)
    lilv.lilv_world_load_specifications(world.me)
    lilv.lilv_world_load_plugin_classes(world.me)

    # convert bundle string into a lilv node
    bundlenode = lilv.lilv_new_file_uri(world.me, None, bundle)

    # load the bundle
    world.load_bundle(bundlenode)

    # free bundlenode, no longer needed
    lilv.lilv_node_free(bundlenode)

    # get all plugins in the bundle
    plugins = world.get_all_plugins()

    # make sure the bundle includes 1 and only 1 plugin (the pedalboard)
    if plugins.size() != 1:
        raise Exception('get_pedalboard_info(%s) - bundle has 0 or > 1 plugin'.format(bundle))

    # no indexing in python-lilv yet, just get the first item
    plugin = None
    for p in plugins:
        plugin = p
        break

    if plugin is None:
        raise Exception('get_pedalboard_info(%s) - failed to get plugin, you are using an old lilv!'.format(bundle))

    # define the needed stuff
    ns_rdf      = NS(world, lilv.LILV_NS_RDF)
    ns_lv2core  = NS(world, lilv.LILV_NS_LV2)
    ns_ingen    = NS(world, "http://drobilla.net/ns/ingen#")
    ns_modpedal = NS(world, "http://moddevices.com/ns/modpedal#")

    # check if the plugin is a pedalboard
    def fill_in_type(node):
        return node.as_string()
    plugin_types = [i for i in LILV_FOREACH(plugin.get_value(ns_rdf.type_), fill_in_type)]

    if "http://moddevices.com/ns/modpedal#Pedalboard" not in plugin_types:
        raise Exception('get_pedalboard_info(%s) - plugin has no mod:Pedalboard type'.format(bundle))

    # let's get all the info now
    ingenarcs   = []
    ingenblocks = []

    info = {
        'name'  : plugin.get_name().as_string(),
        'uri'   : plugin.get_uri().as_string(),
        'author': plugin.get_author_name().as_string() or "", # Might be empty
        'hardware': {
            # we save this info later
            'audio': {
                'ins' : 0,
                'outs': 0
             },
            'cv': {
                'ins' : 0,
                'outs': 0
             },
            'midi': {
                'ins' : 0,
                'outs': 0
             }
        },
        'size': {
            'width' : plugin.get_value(ns_modpedal.width).get_first().as_int(),
            'height': plugin.get_value(ns_modpedal.height).get_first().as_int(),
        },
        'screenshot' : os.path.basename(plugin.get_value(ns_modpedal.screenshot).get_first().as_string() or ""),
        'thumbnail'  : os.path.basename(plugin.get_value(ns_modpedal.thumbnail).get_first().as_string() or ""),
        'connections': [], # we save this info later
        'plugins'    : []  # we save this info later
    }

    # connections
    arcs = plugin.get_value(ns_ingen.arc)
    it = arcs.begin()
    while not arcs.is_end(it):
        arc = arcs.get(it)
        it  = arcs.next(it)

        if arc.me is None:
            continue

        head = lilv.lilv_world_get(world.me, arc.me, ns_ingen.head.me, None)
        tail = lilv.lilv_world_get(world.me, arc.me, ns_ingen.tail.me, None)

        if head is None or tail is None:
            continue

        ingenarcs.append({
            "source": lilv.lilv_uri_to_path(lilv.lilv_node_as_string(tail)).replace(bundle,"",1),
            "target": lilv.lilv_uri_to_path(lilv.lilv_node_as_string(head)).replace(bundle,"",1)
        })

    # hardware ports
    handled_port_uris = []
    ports = plugin.get_value(ns_lv2core.port)
    it = ports.begin()
    while not ports.is_end(it):
        port = ports.get(it)
        it   = ports.next(it)

        if port.me is None:
            continue

        # check if we already handled this port
        port_uri = port.as_uri()
        if port_uri in handled_port_uris:
            continue
        if port_uri.endswith("/control_in") or port_uri.endswith("/control_out"):
            continue
        handled_port_uris.append(port_uri)

        # get types
        port_types = lilv.lilv_world_find_nodes(world.me, port.me, ns_rdf.type_.me, None)

        if port_types is None:
            continue

        portDir  = "" # input or output
        portType = "" # atom, audio or cv

        it2 = lilv.lilv_nodes_begin(port_types)
        while not lilv.lilv_nodes_is_end(port_types, it2):
            port_type = lilv.lilv_nodes_get(port_types, it2)
            it2 = lilv.lilv_nodes_next(port_types, it2)

            if port_type is None:
                continue

            port_type_uri = lilv.lilv_node_as_uri(port_type)

            if port_type_uri == "http://lv2plug.in/ns/lv2core#InputPort":
                portDir = "input"
            elif port_type_uri == "http://lv2plug.in/ns/lv2core#OutputPort":
                portDir = "output"
            elif port_type_uri == "http://lv2plug.in/ns/lv2core#AudioPort":
                portType = "audio"
            elif port_type_uri == "http://lv2plug.in/ns/lv2core#CVPort":
                portType = "cv"
            elif port_type_uri == "http://lv2plug.in/ns/ext/atom#AtomPort":
                portType = "atom"

        if not (portDir or portType):
            continue

        if portType == "audio":
            if portDir == "input":
                info['hardware']['audio']['ins'] += 1
            else:
                info['hardware']['audio']['outs'] += 1

        elif portType == "atom":
            if portDir == "input":
                info['hardware']['midi']['ins'] += 1
            else:
                info['hardware']['midi']['outs'] += 1

        elif portType == "cv":
            if portDir == "input":
                info['hardware']['cv']['ins'] += 1
            else:
                info['hardware']['cv']['outs'] += 1

    # plugins
    blocks = plugin.get_value(ns_ingen.block)
    it = blocks.begin()
    while not blocks.is_end(it):
        block = blocks.get(it)
        it    = blocks.next(it)

        if block.me is None:
            continue

        protouri1 = lilv.lilv_world_get(world.me, block.me, ns_lv2core.prototype.me, None)
        protouri2 = lilv.lilv_world_get(world.me, block.me, ns_ingen.prototype.me, None)

        if protouri1 is not None:
            proto = protouri1
        elif protouri2 is not None:
            proto = protouri2
        else:
            continue

        instance = lilv.lilv_uri_to_path(lilv.lilv_node_as_string(block.me)).replace(bundle,"",1)
        uri      = lilv.lilv_node_as_uri(proto)

        enabled  = lilv.lilv_world_get(world.me, block.me, ns_ingen.enabled.me, None)
        minorver = lilv.lilv_world_get(world.me, block.me, ns_lv2core.minorVersion.me, None)
        microver = lilv.lilv_world_get(world.me, block.me, ns_lv2core.microVersion.me, None)

        ingenblocks.append({
            "instance": instance,
            "uri"     : uri,
            "x"       : lilv.lilv_node_as_float(lilv.lilv_world_get(world.me, block.me, ns_ingen.canvasX.me, None)),
            "y"       : lilv.lilv_node_as_float(lilv.lilv_world_get(world.me, block.me, ns_ingen.canvasY.me, None)),
            "enabled" : lilv.lilv_node_as_bool(enabled) if enabled is not None else False,
            "minorVersion": lilv.lilv_node_as_int(minorver) if minorver else 0,
            "microVersion": lilv.lilv_node_as_int(microver) if microver else 0,
        })

    info['connections'] = ingenarcs
    info['plugins']     = ingenblocks

    return info

# ------------------------------------------------------------------------------------------------------------
# get_pedalboard_name

# Faster version of get_pedalboard_info when we just need to know the pedalboard name
# @a bundle is a string, consisting of a directory in the filesystem (absolute pathname).
def get_pedalboard_name(bundle):
    # lilv wants the last character as the separator
    bundle = os.path.abspath(bundle)
    if not bundle.endswith(os.sep):
        bundle += os.sep

    # Create our own unique lilv world
    # We'll load a single bundle and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    # (these functions are not exposed via World yet)
    lilv.lilv_world_load_specifications(world.me)
    lilv.lilv_world_load_plugin_classes(world.me)

    # convert bundle string into a lilv node
    bundlenode = lilv.lilv_new_file_uri(world.me, None, bundle)

    # load the bundle
    world.load_bundle(bundlenode)

    # free bundlenode, no longer needed
    lilv.lilv_node_free(bundlenode)

    # get all plugins in the bundle
    plugins = world.get_all_plugins()

    # make sure the bundle includes 1 and only 1 plugin (the pedalboard)
    if plugins.size() != 1:
        raise Exception('get_pedalboard_info(%s) - bundle has 0 or > 1 plugin'.format(bundle))

    # no indexing in python-lilv yet, just get the first item
    plugin = None
    for p in plugins:
        plugin = p
        break

    if plugin is None:
        raise Exception('get_pedalboard_info(%s) - failed to get plugin, you are using an old lilv!'.format(bundle))

    # define the needed stuff
    ns_rdf = NS(world, lilv.LILV_NS_RDF)

    # check if the plugin is a pedalboard
    def fill_in_type(node):
        return node.as_string()
    plugin_types = [i for i in LILV_FOREACH(plugin.get_value(ns_rdf.type_), fill_in_type)]

    if "http://moddevices.com/ns/modpedal#Pedalboard" not in plugin_types:
        raise Exception('get_pedalboard_info(%s) - plugin has no mod:Pedalboard type'.format(bundle))

    return plugin.get_name().as_string()

# ------------------------------------------------------------------------------------------------------------
# plugin_has_modgui

# Check if a plugin has modgui
def plugin_has_modgui(world, plugin):
    # define the needed stuff
    ns_modgui = NS(world, "http://moddevices.com/ns/modgui#")

    # --------------------------------------------------------------------------------------------------------
    # get the proper modgui

    modguigui = None

    nodes = plugin.get_value(ns_modgui.gui)
    it    = nodes.begin()
    while not nodes.is_end(it):
        mgui = nodes.get(it)
        it   = nodes.next(it)
        if mgui.me is None:
            continue
        resdir = world.find_nodes(mgui.me, ns_modgui.resourcesDirectory.me, None).get_first()
        if resdir.me is None:
            continue
        modguigui = mgui
        if os.path.expanduser("~") in lilv.lilv_uri_to_path(resdir.as_string()):
            # found a modgui in the home dir, stop here and use it
            break

    del nodes, it

    # --------------------------------------------------------------------------------------------------------
    # check selected modgui

    if modguigui is None or modguigui.me is None:
        return False

    # resourcesDirectory *must* be present
    modgui_resdir = world.find_nodes(modguigui.me, ns_modgui.resourcesDirectory.me, None).get_first()

    if modgui_resdir.me is None:
        return False

    return os.path.exists(lilv.lilv_uri_to_path(modgui_resdir.as_string()))

# ------------------------------------------------------------------------------------------------------------
# get_plugin_info

# Get info from a lilv plugin
# This is used in get_plugins_info below and MOD-SDK
'''
    # --------------------------------------------------------------------------------------------------------
    # presets

    def get_preset_data(preset):
        world.load_resource(preset.me)

        uri   = preset.as_string() or ""
        label = world.find_nodes(preset.me, ns_rdfs.label.me, None).get_first().as_string() or ""

        if not uri:
            errors.append("preset with label '%s' has no uri" % (label or "<unknown>"))
        if not label:
            errors.append("preset with uri '%s' has no label" % (uri or "<unknown>"))

        return (uri, label)

    presets = []

    presets_related = plugin.get_related(ns_pset.Preset)
    presets_data    = list(LILV_FOREACH(presets_related, get_preset_data))

    if len(presets_data) != 0:
        unsorted = dict(p for p in presets_data)
        uris     = list(unsorted.keys())
        uris.sort()
        presets  = list({ 'uri': p, 'label': unsorted[p] } for p in uris)
        del unsorted, uris

    del presets_related
'''
