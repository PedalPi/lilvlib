#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lilv
import os

from .lilvlib import NS
from .port import Port


class Plugin:

    def __init__(self, world, plugin, useAbsolutePath=True):
        self.world = world
        self.plugin = plugin
        self.useAbsolutePath = useAbsolutePath

        self.ns_doap = NS(world, lilv.LILV_NS_DOAP)
        self.ns_foaf = NS(world, lilv.LILV_NS_FOAF)
        self.ns_rdf = NS(world, lilv.LILV_NS_RDF)
        #self.ns_rdfs = NS(world, lilv.LILV_NS_RDFS)
        self.ns_lv2core = NS(world, lilv.LILV_NS_LV2)
        self.ns_atom = NS(world, "http://lv2plug.in/ns/ext/atom#")
        self.ns_midi = NS(world, "http://lv2plug.in/ns/ext/midi#")
        self.ns_morph = NS(world, "http://lv2plug.in/ns/ext/morph#")
        self.ns_pprops = NS(world, "http://lv2plug.in/ns/ext/port-props#")
        self.ns_pset = NS(world, "http://lv2plug.in/ns/ext/presets#")
        #self.ns_units = NS(world, "http://lv2plug.in/ns/extensions/units#")
        self.ns_mod = NS(world, "http://moddevices.com/ns/mod#")
        self.ns_modgui = NS(world, "http://moddevices.com/ns/modgui#")

        self.errors = []
        self.warnings = []

        self.bundleuri = self.plugin.get_bundle_uri().as_string()
        self.bundle = lilv.lilv_uri_to_path(self.bundleuri)


    def plugin_get_first_value(self, subject):
        return self.plugin.get_value(subject).get_first()

    def plugin_get_first_value_as_string(self, subject):
        return self.plugin_get_first_value(subject).get_first().as_string() \
            or ""

    @property
    def uri(self):
        uri = self.plugin.get_uri().as_string() or ""

        if not uri:
            self.errors.append("plugin uri is missing or invalid")

        elif uri.startswith("file:"):
            self.errors.append("plugin uri is local, and thus not suitable for redistribution")
        #elif not (uri.startswith("http:") or uri.startswith("https:")):
            #warnings.append("plugin uri is not a real url")

        return uri

    @property
    def name(self):
        name = self.plugin.get_name().as_string() or ""

        if not name:
            self.errors.append("plugin name is missing")

        return name

    @property
    def binary(self):
        binary = lilv.lilv_uri_to_path(
            self.plugin.get_library_uri().as_string() or ""
        )

        if not binary:
            self.errors.append("plugin binary is missing")
        elif not self.useAbsolutePath:
            binary = binary.replace(self.bundle, "", 1)

        return binary

    @property
    def license(self):
        lic = self.plugin_get_first_value_as_string(self.ns_doap.license)

        if not lic:
            prj = self.plugin.get_value(self.ns_lv2core.project).get_first()
            if prj.me is not None:
                licsnode = lilv.lilv_world_get(self.world.me, prj.me, self.ns_doap.license.me, None)
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

    @property
    def comment(self):
        comment = self.plugin_get_first_value_as_string(self.ns_rdfs.comment)

        if not comment:
            self.errors.append("plugin comment is missing")

        return comment

    @property
    def version(self):
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

        # 0.x is experimental
        if minorVersion == 0:
            stability = "experimental"

        # odd x.2 or 2.x is testing/development
        elif minorVersion % 2 != 0 or microVersion % 2 != 0:
            stability = "testing"

        # otherwise it's stable
        else:
            stability = "stable"

        return (version, minorVersion, microVersion, stability)

    @property
    def author(self):
        author = {
            'name': self.plugin.get_author_name().as_string() or "",
            'homepage': self.plugin.get_author_homepage().as_string() or "",
            'email': self.plugin.get_author_email().as_string() or "",
        }

        if not author['name']:
            self.errors.append("plugin author name is missing")

        if not author['homepage']:
            prj = self.plugin.get_value(self.ns_lv2core.project).get_first()
            if prj.me is not None:
                maintainer = lilv.lilv_world_get(self.world.me, prj.me, self.ns_doap.maintainer.me, None)
                if maintainer is not None:
                    homepage = lilv.lilv_world_get(self.world.me, maintainer, self.ns_foaf.homepage.me, None)
                    if homepage is not None:
                        author['homepage'] = lilv.lilv_node_as_string(homepage)
                    del homepage
                del maintainer
            del prj

        if not author['homepage']:
            warnings.append("plugin author homepage is missing")

        if not author['email']:
            pass
        elif author['email'].startswith(self.bundleuri):
            author['email'] = author['email'].replace(self.bundleuri,"",1)
            self.warnings.append("plugin author email entry is missing 'mailto:' prefix")
        elif author['email'].startswith("mailto:"):
            author['email'] = author['email'].replace("mailto:","",1)

        return author

    @property
    def brand(self, author):
        brand = self.get_plugin_first_value_as_string(self.ns_mod.brand)

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

    @property
    def label(self):
        name = self.name
        label = self.get_plugin_first_value_as_string(self.ns_mod.label)

        if not label:
            if len(name) <= 16:
                label = name
            else:
                labels = name.split(" - ", 1)[0].split(" ")
                if labels[0].lower() in self.bundle.lower() \
                   and len(labels) > 1 \
                   and not labels[1].startswith(("(", "[")):
                    label = labels[1]
                else:
                    label = labels[0]

                if len(label) > 16:
                    label = label[:16]

                self.warnings.append("plugin label is missing")
                del labels

        elif len(label) > 16:
            label = label[:16]
            self.errors.append("plugin label has more than 16 characters")

    @property
    def bundles(self):
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

    def ports(self):
        index = 0
        ports = {
            'audio': {'input': [], 'output': []},
            'control': {'input': [], 'output': []},
            'midi': {'input': [], 'output': []}
        }

        portsymbols = []
        portnames   = []

        for i in range(self.plugin.get_num_ports()):
            p = self.plugin.get_port_by_index(i)

            types, info = Port(self.world, p, index).data

            info['index'] = index
            index += 1

            isInput = "Input" in types
            types.remove("Input" if isInput else "Output")

            for typ in [typl.lower() for typl in types]:
                if typ not in list(ports.keys()):
                    ports[typ] = {'input': [], 'output': []}
                ports[typ]["input" if isInput else "output"].append(info)
