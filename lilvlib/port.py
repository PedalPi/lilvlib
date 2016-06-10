#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lilv
from .port_unit import PortUnit


class Port:
    SHORT_NAME_SIZE = 16

    def __init__(self, world, port, index):
        self.errors = []
        self.warnings = []

        portname = self.portnames

        self.data = (types, {
            'name': portname,
            'symbol': self.portsymbol,
            'ranges': ranges,
            'units': PortUnit(world, portname).units,
            'designation': self.designation,
            'properties': self.properties,
            'rangeSteps': (
                self.get_port_data(self.port, self.ns_mod.rangeSteps) or \
                self.get_port_data(self.port, self.ns_pprops.rangeSteps) or [None] \
            )[0],
            'scalePoints': scalepoints,
            'shortName': self.psname,
        })

    @property
    def portname(self):
        portname = lilv.lilv_node_as_string(port.get_name()) or ""

        if not portname:
            portname = "_%i" % index
            self.errors.append("port with index %i has no name" % index)

        return portname

    @property
    def portsymbol(self):
        portsymbol = lilv.lilv_node_as_string(port.get_symbol()) or ""

        if not portsymbol:
            portsymbol = "_%i" % index
            self.errors.append("port with index %i has no symbol" % index)

        return portsymbol

    #FIXME - Move to plugin.py
    '''
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

    '''short name'''
    @property
    def psname(self):
        portname = self.portname

        psname = lilv.lilv_nodes_get_first(self.port.get_value(ns_lv2core.shortName.me))

        if psname is not None:
            psname = lilv.lilv_node_as_string(psname) or ""

        if not psname:
            psname = self.get_short_port_name(portname)
            if len(psname) > Port.SHORT_NAME_SIZE:
                self.warnings.append("port '%s' name is too big, reduce the name size or provide a shortName" % portname)

        elif len(psname) > Port.SHORT_NAME_SIZE:
            psname = psname[:Port.SHORT_NAME_SIZE]
            self.errors.append("port '%s' short name has more than %d characters" % portname, Port.SHORT_NAME_SIZE)

        # check for old style shortName
        if self.port.get_value(self.ns_lv2core.shortname.me) is not None:
            self.errors.append("port '%s' short name is using old style 'shortname' instead of 'shortName'" % portname)

        return psname

    def get_short_port_name(self, portName):
        if len(portName) <= Port.SHORT_NAME_SIZE:
            return portName

        portName = portName.split("/",1)[0].split(" (",1)[0].split(" [",1)[0].strip()

        # cut stuff if too big
        if len(portName) > Port.SHORT_NAME_SIZE:
            portName = portName[0] + portName[1:].replace("a","").replace("e","").replace("i","").replace("o","").replace("u","")

            if len(portName) > Port.SHORT_NAME_SIZE:
                portName = portName[:Port.SHORT_NAME_SIZE]

        return portName.strip()

    @property
    def types(self):
        types = [typ.rsplit("#",1)[-1].replace("Port","",1) for typ in self.get_port_data(self.port, ns_rdf.type_)]

        if "Atom" in types \
            and port.supports_event(ns_midi.MidiEvent.me) \
            and lilv.Nodes(port.get_value(ns_atom.bufferType.me)).get_first() == ns_atom.Sequence:
                types.append("MIDI")

        #if "Morph" in types:
            #morphtyp = lilv.lilv_nodes_get_first(port.get_value(ns_morph.supportsType.me))
            #if morphtyp is not None:
                #morphtyp = lilv.lilv_node_as_uri(morphtyp)
                #if morphtyp:
                    #types.append(morphtyp.rsplit("#",1)[-1].replace("Port","",1))

        return types

    @property
    def designation(self):
        designation = (self.get_port_data(self.port, self.ns_lv2core.designation) or [""])[0]

    def macarronada(self):
        properties = [
            typ.rsplit("#", 1)[-1]
            for typ in self.get_port_data(
                self.port,
                self.ns_lv2core.portProperty
            )
        ]

        types = self.types

        # data
        ranges = {}
        scalepoints = []

        # unit block
        ulabel = ""
        urender = ""
        usymbol = ""

        if "Control" in types or "CV" in types:
            self.control_with_range(properties, types)
        if "Control" in types:
            self.control_port_with_unit()

    '''control and cv must contain ranges, might contain scale points'''
    def control_with_range(self, properties, types):
        isInteger = "integer" in properties

        if isInteger and "CV" in types:
            self.errors.append("port '%s' has integer property and CV type" % portname)

        xdefault = lilv.lilv_nodes_get_first(port.get_value(self.ns_mod.default.me)) or \
                   lilv.lilv_nodes_get_first(port.get_value(self.ns_lv2core.default.me))
        xminimum = lilv.lilv_nodes_get_first(port.get_value(self.ns_mod.minimum.me)) or \
                   lilv.lilv_nodes_get_first(port.get_value(self.ns_lv2core.minimum.me))
        xmaximum = lilv.lilv_nodes_get_first(port.get_value(self.ns_mod.maximum.me)) or \
                   lilv.lilv_nodes_get_first(port.get_value(self.ns_lv2core.maximum.me))

        if xminimum is not None and xmaximum is not None:
            if isInteger:
                if is_integer(lilv.lilv_node_as_string(xminimum)):
                    ranges['minimum'] = lilv.lilv_node_as_int(xminimum)
                else:
                    ranges['minimum'] = lilv.lilv_node_as_float(xminimum)
                    if fmod(ranges['minimum'], 1.0) == 0.0:
                        warnings.append("port '%s' has integer property but minimum value is float" % portname)
                    else:
                        errors.append("port '%s' has integer property but minimum value has non-zero decimals" % portname)
                    ranges['minimum'] = int(ranges['minimum'])

                if is_integer(lilv.lilv_node_as_string(xmaximum)):
                    ranges['maximum'] = lilv.lilv_node_as_int(xmaximum)
                else:
                    ranges['maximum'] = lilv.lilv_node_as_float(xmaximum)
                    if fmod(ranges['maximum'], 1.0) == 0.0:
                        warnings.append("port '%s' has integer property but maximum value is float" % portname)
                    else:
                        errors.append("port '%s' has integer property but maximum value has non-zero decimals" % portname)
                    ranges['maximum'] = int(ranges['maximum'])

            else:
                ranges['minimum'] = lilv.lilv_node_as_float(xminimum)
                ranges['maximum'] = lilv.lilv_node_as_float(xmaximum)

                if is_integer(lilv.lilv_node_as_string(xminimum)):
                    self.warnings.append("port '%s' minimum value is an integer" % portname)

                if is_integer(lilv.lilv_node_as_string(xmaximum)):
                    self.warnings.append("port '%s' maximum value is an integer" % portname)

            if ranges['minimum'] >= ranges['maximum']:
                ranges['maximum'] = ranges['minimum'] + (1 if isInteger else 0.1)
                errors.append("port '%s' minimum value is equal or higher than its maximum" % portname)

            if xdefault is not None:
                if isInteger:
                    if is_integer(lilv.lilv_node_as_string(xdefault)):
                        ranges['default'] = lilv.lilv_node_as_int(xdefault)
                    else:
                        ranges['default'] = lilv.lilv_node_as_float(xdefault)
                        if fmod(ranges['default'], 1.0) == 0.0:
                            self.warnings.append("port '%s' has integer property but default value is float" % portname)
                        else:
                            errors.append("port '%s' has integer property but default value has non-zero decimals" % portname)
                        ranges['default'] = int(ranges['default'])
                else:
                    ranges['default'] = lilv.lilv_node_as_float(xdefault)

                    if is_integer(lilv.lilv_node_as_string(xdefault)):
                        self.warnings.append("port '%s' default value is an integer" % portname)

                testmin = ranges['minimum']
                testmax = ranges['maximum']

                if "sampleRate" in properties:
                    testmin *= 48000
                    testmax *= 48000

                if not (testmin <= ranges['default'] <= testmax):
                    ranges['default'] = ranges['minimum']
                    errors.append("port '%s' default value is out of bounds" % portname)

            else:
                ranges['default'] = ranges['minimum']

                if "Input" in types:
                    errors.append("port '%s' is missing default value" % portname)

        else:
            if isInteger:
                ranges['minimum'] = 0
                ranges['maximum'] = 1
                ranges['default'] = 0
            else:
                ranges['minimum'] = -1.0 if "CV" in types else 0.0
                ranges['maximum'] = 1.0
                ranges['default'] = 0.0

            if "CV" not in types and designation != "http://lv2plug.in/ns/lv2core#latency":
                errors.append("port '%s' is missing value ranges" % portname)

        nodes = port.get_scale_points()

        if nodes is not None:
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
                            self.warnings.append("port '%s' has integer property but scalepoint '%s' value is float" % (portname, label))
                        else:
                            self.errors.append("port '%s' has integer property but scalepoint '%s' value has non-zero decimals" % (portname, label))
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