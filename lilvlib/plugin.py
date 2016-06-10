#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lilv
import os

from lilvlib import NS, get_category
from port import Port
from plugin_author import PluginAuthor


class Plugin:
    LABEL_NAME_SIZE = 16

    def __init__(self, world, plugin, useAbsolutePath=True):
        self.world = world
        self.plugin = plugin
        self.useAbsolutePath = useAbsolutePath

        self.ns_doap = NS(world, lilv.LILV_NS_DOAP)
        self.ns_lv2core = NS(world, lilv.LILV_NS_LV2)
        self.ns_rdfs = NS(world, lilv.LILV_NS_RDFS)
        self.ns_rdf = NS(world, lilv.LILV_NS_RDF)

        self.ns_morph = NS(world, "http://lv2plug.in/ns/ext/morph#")
        self.ns_pset = NS(world, "http://lv2plug.in/ns/ext/presets#")
        self.ns_mod = NS(world, "http://moddevices.com/ns/mod#")
        self.ns_modgui = NS(world, "http://moddevices.com/ns/modgui#")

        self.errors = []
        self.warnings = []

        self.bundleuri = self.plugin.get_bundle_uri().as_string()
        self.bundle = lilv.lilv_uri_to_path(self.bundleuri)

        self.author = self.generate_author(
            world,
            plugin,
            self.bundleuri
        )

        self.uri = self.generate_uri()
        self.name = self.generate_name()

        self.binary = self.generate_binary(self.bundle)
        self.brand = self.generate_brand(self.author)
        self.label = self.generate_label()
        self.theLicense = self.generate_license()
        self.comment = self.generate_comment()

        self.version, self.minorVersion, self.microVersion = \
            self.generate_version_data()

        self.stability = self.generate_stability(
            self.minorVersion,
            self.microVersion
        )

        self.bundles = self.generate_bundles()

        self.ports = self.generate_ports()

        self.data = {
            'uri': self.uri,
            'name': self.name,

            'binary': self.binary,
            'brand': self.brand,
            'label': self.label,
            'license': self.theLicense,
            'comment': self.comment,

            'category': get_category(plugin.get_value(self.ns_rdf.type_)),
            'microVersion': self.microVersion,
            'minorVersion': self.minorVersion,

            'version': self.version,
            'stability': self.stability,

            'author': self.author,
            'bundles': self.bundles,
            'gui': None,  # gui,
            'ports': self.ports,
            'presets': [],  # presets,

            'errors': self.errors,
            'warnings': self.warnings,
        }

    def plugin_get_first_value_as_string(self, subject):
        return self.plugin_get_first_value(subject).as_string() \
            or ""

    def plugin_get_first_value(self, subject):
        return self.plugin.get_value(subject).get_first()

    def generate_author(self, world, plugin, bundleuri):
        author = PluginAuthor(world, plugin, bundleuri)

        self.errors += author.errors
        self.warnings += author.warnings

        return author.author

    def generate_uri(self):
        uri = self.plugin.get_uri().as_string() or ""

        if not uri:
            self.errors.append("plugin uri is missing or invalid")

        elif uri.startswith("file:"):
            self.errors.append("plugin uri is local, and thus not suitable for redistribution")
        #elif not (uri.startswith("http:") or uri.startswith("https:")):
            #warnings.append("plugin uri is not a real url")

        return uri

    def generate_name(self):
        name = self.plugin.get_name().as_string() or ""

        if not name:
            self.errors.append("plugin name is missing")

        return name

    def generate_binary(self, bundle):
        binary = lilv.lilv_uri_to_path(
            self.plugin.get_library_uri().as_string() or ""
        )

        if not binary:
            self.errors.append("plugin binary is missing")
        elif not self.useAbsolutePath:
            binary = binary.replace(bundle, "", 1)

        return binary

    def generate_brand(self, author):
        brand = self.plugin_get_first_value_as_string(self.ns_mod.brand)

        if not brand:
            brand = author['name'].split(" - ", 1)[0].split(" ", 1)[0]
            brand = brand.rstrip(",").rstrip(";")
            if len(brand) > 11:
                brand = brand[:11]
            self.warnings.append("plugin brand is missing")

        elif len(brand) > 11:
            brand = brand[:11]
            self.errors.append("plugin brand has more than 11 characters")

        return brand

    def generate_label(self):
        name = self.name
        label = self.plugin_get_first_value_as_string(self.ns_mod.label)

        if not label:
            if len(name) <= Plugin.LABEL_NAME_SIZE:
                label = name
            else:
                labels = name.split(" - ", 1)[0].split(" ")
                if labels[0].lower() in self.bundle.lower() \
                   and len(labels) > 1 \
                   and not labels[1].startswith(("(", "[")):
                    label = labels[1]
                else:
                    label = labels[0]

                if len(label) > Plugin.LABEL_NAME_SIZE:
                    label = label[:Plugin.LABEL_NAME_SIZE]

                self.warnings.append("plugin label is missing")
                del labels

        elif len(label) > Plugin.LABEL_NAME_SIZE:
            label = label[:Plugin.LABEL_NAME_SIZE]
            self.errors.append("plugin label has more than 16 characters")

        return label

    def generate_license(self):
        lic = self.plugin_get_first_value_as_string(self.ns_doap.license)

        if not lic:
            prj = self.plugin.get_value(self.ns_lv2core.project).get_first()
            if prj.me is not None:
                licsnode = lilv.lilv_world_get(
                    self.world.me,
                    prj.me,
                    self.ns_doap.license.me,
                    None
                )
                if licsnode is not None:
                    lic = lilv.lilv_node_as_string(licsnode)
                del licsnode
            del prj

        if not lic:
            self.errors.append("plugin license is missing")

        elif lic.startswith(self.bundleuri):
            lic = lic.replace(self.bundleuri, "", 1)
            self.warnings.append("plugin license entry is a local path instead of a string")

        return lic

    def generate_comment(self):
        comment = self.plugin_get_first_value_as_string(self.ns_rdfs.comment)

        if not comment:
            self.errors.append("plugin comment is missing")

        return comment

    def generate_version_data(self):
        microver = self.plugin_get_first_value(self.ns_lv2core.microVersion)
        minorver = self.plugin_get_first_value(self.ns_lv2core.minorVersion)

        if microver.me is None and minorver.me is None:
            self.errors.append("plugin is missing version information")
            minorVersion = 0
            microVersion = 0

        else:
            if minorver.me is None:
                self.errors.append("plugin is missing minorVersion")
                minorVersion = 0
            else:
                minorVersion = minorver.as_int()

            if microver.me is None:
                self.errors.append("plugin is missing microVersion")
                microVersion = 0
            else:
                microVersion = microver.as_int()

        del minorver
        del microver

        version = "%d.%d" % (minorVersion, microVersion)

        return version, minorVersion, microVersion

    def generate_stability(self, minorVersion, microVersion):
        # 0.x is experimental
        if minorVersion == 0:
            stability = "experimental"

        # odd x.2 or 2.x is testing/development
        elif minorVersion % 2 != 0 or microVersion % 2 != 0:
            stability = "testing"

        # otherwise it's stable
        else:
            stability = "stable"

        return stability

    def generate_bundles(self):
        if not self.useAbsolutePath:
            return []

        bundles = []
        bnodes = lilv.lilv_plugin_get_data_uris(self.plugin.me)

        it = lilv.lilv_nodes_begin(bnodes)
        while not lilv.lilv_nodes_is_end(bnodes, it):
            bnode = lilv.lilv_nodes_get(bnodes, it)
            it = lilv.lilv_nodes_next(bnodes, it)

            if bnode is None:
                continue
            if not lilv.lilv_node_is_uri(bnode):
                continue

            bpath = os.path.abspath(
                os.path.dirname(
                    lilv.lilv_uri_to_path(lilv.lilv_node_as_uri(bnode))
                )
            )

            if not bpath.endswith(os.sep):
                bpath += os.sep

            if bpath not in bundles:
                bundles.append(bpath)

        if self.bundle not in bundles:
            bundles.append(self.bundle)

        del bnodes, it

        return bundles

    def generate_ports(self):
        index = 0
        ports = {
            'audio': {'input': [], 'output': []},
            'control': {'input': [], 'output': []},
            'midi': {'input': [], 'output': []}
        }

        for i in range(self.plugin.get_num_ports()):
            p = self.plugin.get_port_by_index(i)

            port = Port(self.world, p, index)
            types, info = port.data

            self.errors += port.errors
            self.warnings += port.warnings

            info['index'] = index
            index += 1

            isInput = "Input" in types
            types.remove("Input" if isInput else "Output")

            for typ in [typl.lower() for typl in types]:
                if typ not in list(ports.keys()):
                    ports[typ] = {'input': [], 'output': []}
                ports[typ]["input" if isInput else "output"].append(info)

        return ports

        '''
        portsymbols = []
        portnames   = []

        # check for duplicate names
        if portname in portsymbols:
            self.warnings.append("port name '%s' is not unique" % portname)
        else:
            portnames.append(portname)

        # check for duplicate symbols
        if portsymbol in portsymbols:
            self.errors.append("port symbol '%s' is not unique" % portsymbol)
        else:
            portsymbols.append(portsymbol)
        '''
