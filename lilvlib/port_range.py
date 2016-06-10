#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import fmod

import lilv
from lilvlib import NS, is_integer


class PortRange:

    def __init__(self, world, port, properties):
        self.ns_lv2core = NS(world, lilv.LILV_NS_LV2)
        self.ns_mod = NS(world, "http://moddevices.com/ns/mod#")

        self.errors = []
        self.warnings = []

        self.port = port.port
        self.portname = port.portname
        self.types = port.types
        self.properties = properties
        self.designation = port.designation

        xdefault = self.get_first_port_node(self.ns_mod.default.me) or \
                   self.get_first_port_node(self.ns_lv2core.default.me)
        xminimum = self.get_first_port_node(self.ns_mod.minimum.me) or \
                   self.get_first_port_node(self.ns_lv2core.minimum.me)
        xmaximum = self.get_first_port_node(self.ns_mod.maximum.me) or \
                   self.get_first_port_node(self.ns_lv2core.maximum.me)

        self.ranges = self.generate_range(
            xminimum,
            xmaximum,
            xdefault
        )

    def register_error(self, message, params=()):
        self.errors.append('port %s ' % self.portname + message % params)

    def get_first_port_node(self, subject):
        return lilv.lilv_nodes_get_first(self.port.get_value(subject))

    def generate_range(self, xminimum, xmaximum, xdefault):
        isInteger = "integer" in self.properties

        if isInteger and "CV" in self.types:
            self.register_error("has integer property and CV type")

        rangeIsDeclared = xminimum is not None and xmaximum is not None

        if rangeIsDeclared:
            return self.generate_known_range(
                isInteger,
                xminimum,
                xmaximum,
                xdefault
            )

        else:
            return self.generate_unknown_range(isInteger)

    def generate_known_range(self, isInteger, xminimum, xmaximum, xdefault):
        ranges = self.generate_known_minimun_and_maximum(
            isInteger,
            xminimum,
            xmaximum
        )

        if xdefault is not None:
            ranges['default'] = self.generate_known_default(
                isInteger,
                xdefault,
                ranges['minimum'],
                ranges['maximum']
            )
        else:
            ranges['default'] = ranges['minimum']

            if "Input" in self.types:
                self.register_error("is missing default value")

        return ranges

    def generate_known_minimun_and_maximum(self, isInteger, xminimum, xmaximum):
        if isInteger:
            ranges = self.range_integer(xminimum, xmaximum)
        else:
            ranges = self.range_float(xminimum, xmaximum)

        if ranges['minimum'] >= ranges['maximum']:
            ranges['maximum'] = ranges['minimum'] + (1 if isInteger else 0.1)
            self.register_error("minimum value is equal or higher than its maximum")

        return ranges

    def range_integer(self, xminimum, xmaximum):
        return {
            'minimum': self.range_value_integer(xminimum, 'minimum'),
            'maximum': self.range_value_integer(xminimum, 'maximum')
        }

    def range_value_integer(self, subject, subject_name):
        value = 0

        if is_integer(lilv.lilv_node_as_string(subject)):
            value = lilv.lilv_node_as_int(subject)

        else:
            value = lilv.lilv_node_as_float(subject)
            if fmod(value, 1.0) == 0.0:
                self.warnings.append("port '%s' has integer property but %s value is float" % (self.portname, subject_name))
            else:
                self.register_error("has integer property but %s value has non-zero decimals", subject_name)
            value = int(value)

        return value

    def range_float(self, xminimum, xmaximum):
        return {
            'minimum': self.range_value_float(xminimum, 'minimum'),
            'maximum': self.range_value_float(xmaximum, 'maximum')
        }

    def range_value_float(self, subject, subject_name):
        value = lilv.lilv_node_as_float(subject)

        if is_integer(lilv.lilv_node_as_string(subject)):
            self.warnings.append("port '%s' %s value declared float but is an integer" % (self.portname, subject_name))

        return value

    def generate_known_default(self, isInteger, xdefault, minimum, maximum):
        default = 0
        if isInteger:
            default = self.range_value_integer(xdefault, 'default value')
        else:
            default = self.range_value_float(xdefault, 'default')

        testmin = minimum
        testmax = maximum

        if "sampleRate" in self.properties:
            testmin *= 48000
            testmax *= 48000

        if not (testmin <= default <= testmax):
            default = minimum
            self.register_error("default value is out of bounds")

        return default

    def generate_unknown_range(self, isInteger):
        ranges = {}

        if isInteger:
            ranges['minimum'] = 0
            ranges['maximum'] = 1
            ranges['default'] = 0
        else:
            ranges['minimum'] = -1.0 if "CV" in self.types else 0.0
            ranges['maximum'] = 1.0
            ranges['default'] = 0.0

        if "CV" not in self.types \
           and self.designation != "http://lv2plug.in/ns/lv2core#latency":
            self.register_error("is missing value ranges")

        return ranges
