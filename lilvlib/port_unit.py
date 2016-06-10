#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lilv

from lilvlib import NS


class PortUnit:

    def __init__(self, world, port, portname, types):
        self.ns_rdfs = NS(world, lilv.LILV_NS_RDFS)
        self.ns_units = NS(world, "http://lv2plug.in/ns/extensions/units#")

        self.errors = []
        self.warnings = []

        self.world = world
        self.portname = portname

        self.units = self.generate_units(port, types)

    def register_error(self, message, params=()):
        self.errors.append('port %s has' % self.portname + message % params)

    def generate_units(self, port, types):
        label, render, symbol = self.unit_info(port, self.portname)

        if "Control" in types and label and render and symbol:
            return {
                'label': label,
                'render': render,
                'symbol': symbol,
            }
        else:
            return {}

    '''control ports might contain unit'''
    def unit_info(self, port, portname):
        unit = self.unit(port)

        if unit is not None:
            uri = lilv.lilv_node_as_uri(unit)

            if uri is not None and uri.startswith("http://lv2plug.in/ns/"):
                return self.pre_existing_lv2_unit(uri)
            else:
                return self.custom_unit(unit)

        return (None, None, None)

    def unit(self, port):
        port_value = port.get_value(self.ns_units.unit.me)
        return lilv.lilv_nodes_get_first(port_value)

    def pre_existing_lv2_unit(self, unit_uri):
        uri = unit_uri.replace("http://lv2plug.in/ns/extensions/units#", "", 1)
        alnum = uri.isalnum()

        if not alnum:
            self.register_error("wrong lv2 unit uri")
            uri = uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]

        label, render, symbol = self.get_port_unit(uri)

        if alnum and not (label and render and symbol):
            self.register_error(
                "unknown lv2 unit (our bug?, data is '%s', '%s', '%s')",
                (label, render, symbol)
            )

        return (label, render, symbol)

    def get_port_unit(self, miniuri):
        # using label, render, symbol
        units = {
            's': ["seconds", "%f s", "s"],
            'ms': ["milliseconds", "%f ms", "ms"],
            'min': ["minutes", "%f mins", "min"],
            'bar': ["bars", "%f bars", "bars"],
            'beat': ["beats", "%f beats", "beats"],
            'frame': ["audio frames", "%f frames", "frames"],
            'm': ["metres", "%f m", "m"],
            'cm': ["centimetres", "%f cm", "cm"],
            'mm': ["millimetres", "%f mm", "mm"],
            'km': ["kilometres", "%f km", "km"],
            'inch': ["inches", """%f\"""", "in"],
            'mile': ["miles", "%f mi", "mi"],
            'db': ["decibels", "%f dB", "dB"],
            'pc': ["percent", "%f%%", "%"],
            'coef': ["coefficient", "* %f", "*"],
            'hz': ["hertz", "%f Hz", "Hz"],
            'khz': ["kilohertz", "%f kHz", "kHz"],
            'mhz': ["megahertz", "%f MHz", "MHz"],
            'bpm': ["beats per minute", "%f BPM", "BPM"],
            'oct': ["octaves", "%f octaves", "oct"],
            'cent': ["cents", "%f ct", "ct"],
            'semitone12TET': ["semitones", "%f semi", "semi"],
            'degree': ["degrees", "%f deg", "deg"],
            'midiNote': ["MIDI note", "MIDI note %d", "note"],
        }
        if miniuri in units.keys():
            return units[miniuri]
        return ("","","")

    def custom_unit(self, unit):
        xlabel = self.find_first_node(unit, self.ns_rdfs.label.me)
        xrender = self.find_first_node(unit, self.ns_units.render.me)
        xsymbol = self.find_first_node(unit, self.ns_units.symbol.me)

        if xlabel.me is not None:
            label = xlabel.as_string()
        else:
            self.register_error("custom unit with no label")

        if xrender.me is not None:
            render = xrender.as_string()
        else:
            self.register_error("custom unit with no render")

        if xsymbol.me is not None:
            symbol = xsymbol.as_string()
        else:
            self.errors.append("custom unit with no symbol")

        return (label, render, symbol)

    def find_first_node(self, unit, subject):
        return self.world.find_nodes(unit, subject, None).get_first()
