#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lilv
from .lilv import is_integer
from .lilvlib import NS
from .port_unit import PortUnit
from .port_range import PortRange


class Port:
    SHORT_NAME_SIZE = 16

    def __init__(self, world, port, index, ns_lv2core, ns_mod):
        self.ns_lv2core = ns_lv2core
        self.ns_mod = ns_mod

        self.ns_midi = NS(world, "http://lv2plug.in/ns/ext/midi#")
        self.ns_atom = NS(world, "http://lv2plug.in/ns/ext/atom#")
        self.ns_rdf = NS(world, lilv.LILV_NS_RDF)

        self.errors = []
        self.warnings = []

        self.portname = self.generate_portname(index)
        self.portsymbol = self.generate_portsymbol(index)
        self.pname = self.generate_psname()
        self.types = self.generate_types()
        self.designation = self.generate_designation()

        #FIXME macarronada

        self.data = (
            self.types,
            {
                'name': self.portname,
                'symbol': self.portsymbol,
                'ranges': self.ranges,
                'units': self.units,
                'designation': self.designation,
                'properties': self.properties,
                'rangeSteps': (
                    self.get_port_data(self.port, self.ns_mod.rangeSteps) or \
                    self.get_port_data(self.port, self.ns_pprops.rangeSteps) or [None] \
                )[0],
                'scalePoints': scalepoints,
                'shortName': self.psname,
            }
        )

    def generate_portname(self, index):
        portname = lilv.lilv_node_as_string(self.port.get_name()) or ""

        if not portname:
            portname = "_%i" % index
            self.errors.append("port with index %i has no name" % index)

        return portname

    def generate_portsymbol(self, index):
        portsymbol = lilv.lilv_node_as_string(self.port.get_symbol()) or ""

        if not portsymbol:
            portsymbol = "_%i" % index
            self.errors.append("port with index %i has no symbol" % index)

        return portsymbol

    def register_error(self, message, params=()):
        self.errors.append('port %s' % self.portname + message % params)

    '''short name'''
    def generate_psname(self):
        portname = self.portname

        psname = lilv.lilv_nodes_get_first(
            self.port.get_value(self.ns_lv2core.shortName.me)
        )

        if psname is not None:
            psname = lilv.lilv_node_as_string(psname) or ""

        if not psname:
            psname = self.get_short_port_name(portname)
            if len(psname) > Port.SHORT_NAME_SIZE:
                self.warnings.append("port '%s' name is too big, reduce the name size or provide a shortName" % portname)

        elif len(psname) > Port.SHORT_NAME_SIZE:
            psname = psname[:Port.SHORT_NAME_SIZE]
            self.register_error("short name has more than %d characters", Port.SHORT_NAME_SIZE)

        # check for old style shortName
        if self.port.get_value(self.ns_lv2core.shortname.me) is not None:
            self.register_error("short name is using old style 'shortname' instead of 'shortName'")

        return psname

    def get_short_port_name(self, portName):
        if len(portName) <= Port.SHORT_NAME_SIZE:
            return portName

        portName = portName.split("/", 1)[0] \
            .split(" (", 1)[0] \
            .split(" [", 1)[0] \
            .strip()

        if len(portName) > Port.SHORT_NAME_SIZE:
            portName = portName[0] + self.remove_vogals(portName[1:])

        if len(portName) > Port.SHORT_NAME_SIZE:
            portName = portName[:Port.SHORT_NAME_SIZE]

        return portName.strip()

    def remove_vogals(self, text):
        for vogal in ['a', 'e', 'i', 'o', 'u']:
            text = text.replace(vogal, '')

        return text

    def generate_types(self):
        types = [
            typ.rsplit("#", 1)[-1].replace("Port", "", 1)
            for typ in self.get_port_data(self.port, self.ns_rdf.type_)
        ]

        atomBufferTypeIsSequence = self.port_get_first_node(self.ns_atom.bufferType.me) == self.ns_atom.Sequence
        supportsMidiEvent = self.port.supports_event(self.ns_midi.MidiEvent.me)

        if "Atom" in types and supportsMidiEvent and atomBufferTypeIsSequence:
            types.append("MIDI")

        #if "Morph" in types:
            #morphtyp = lilv.lilv_nodes_get_first(port.get_value(ns_morph.supportsType.me))
            #if morphtyp is not None:
                #morphtyp = lilv.lilv_node_as_uri(morphtyp)
                #if morphtyp:
                    #types.append(morphtyp.rsplit("#",1)[-1].replace("Port","",1))

        return types

    def port_get_first_node(self, subject):
        return lilv.Nodes(self.port.get_value(subject)).get_first()

    def generate_designation(self):
        return (
            self.get_port_data(self.port, self.ns_lv2core.designation)
             or [""]
        )[0]

    def macarronada(self, world):
        properties = [
            typ.rsplit("#", 1)[-1]
            for typ in self.get_port_data(
                self.port,
                self.ns_lv2core.portProperty
            )
        ]

        # data
        ranges = {}
        scalepoints = []
        units = {}

        if "Control" in self.types or "CV" in self.types:
            portRange = PortRange(world, self)

            self.errors += portRange.errors
            self.warnings += portRange.warnings

            ranges = portRange.ranges

            self.control_with_range2()
            self.control_with_range3()

        if "Control" in self.types:
            portUnit = PortUnit(world, self.portname)

            self.errors += portUnit.errors
            self.warnings += portUnit.warnings

            units = portUnit.units

    '''control and cv must contain ranges, might contain scale points'''
    def control_with_range2(self):
        nodes = self.port.get_scale_points()

        if nodes is None:
            return

        scalepoints_unsorted = []

        it = lilv.lilv_scale_points_begin(nodes)
        while not lilv.lilv_scale_points_is_end(nodes, it):
            sp = lilv.lilv_scale_points_get(nodes, it)
            it = lilv.lilv_scale_points_next(nodes, it)

            if sp is None:
                continue

            label = lilv.lilv_scale_point_get_label(sp)
            value = lilv.lilv_scale_point_get_value(sp)

            if label is None:
                self.errors.append("a port scalepoint is missing its label")
                continue

            label = lilv.lilv_node_as_string(label) or ""

            if not label:
                self.errors.append("a port scalepoint is missing its label")
                continue

            if value is None:
                self.errors.append("port scalepoint '%s' is missing its value" % label)
                continue

            if isInteger:
                if is_integer(lilv.lilv_node_as_string(value)):
                    value = lilv.lilv_node_as_int(value)
                else:
                    value = lilv.lilv_node_as_float(value)
                    if fmod(value, 1.0) == 0.0:
                        self.warnings.append("port '%s' has integer property but scalepoint '%s' value is float" % (self.portname, label))
                    else:
                        self.register_error("has integer property but scalepoint '%s' value has non-zero decimals" label)
                    value = int(value)
            else:
                if is_integer(lilv.lilv_node_as_string(value)):
                    self.warnings.append("port '%s' scalepoint '%s' value is an integer" % (portname, label))
                value = lilv.lilv_node_as_float(value)

            if ranges['minimum'] <= value <= ranges['maximum']:
                scalepoints_unsorted.append((value, label))
            else:
                self.errors.append(("port scalepoint '%s' has an out-of-bounds value:\n" % label) +
                              ("%d < %d < %d" if isInteger else "%f < %f < %f") % (ranges['minimum'], value, ranges['maximum']))

        if len(scalepoints_unsorted) != 0:
            unsorted = dict(s for s in scalepoints_unsorted)
            values   = list(v for v, l in scalepoints_unsorted)
            values.sort()
            scalepoints = list({ 'value': v, 'label': unsorted[v] } for v in values)
            del unsorted, values

        del scalepoints_unsorted

    def control_with_range3(self):
        if "enumeration" in properties and len(scalepoints) <= 1:
            self.errors.append("port '%s' wants to use enumeration but doesn't have enough values" % portname)
            properties.remove("enumeration")

    def get_port_data(self, port, subj):
        nodes = port.get_value(subj.me)
        data = []

        it = lilv.lilv_nodes_begin(nodes)
        while not lilv.lilv_nodes_is_end(nodes, it):
            dat = lilv.lilv_nodes_get(nodes, it)
            it = lilv.lilv_nodes_next(nodes, it)
            if dat is None:
                continue
            data.append(lilv.lilv_node_as_string(dat))

        return data