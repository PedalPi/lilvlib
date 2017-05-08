
    # --------------------------------------------------------------------------------------------------------
    # get the proper modgui

    '''
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
        if not useAbsolutePath:
            # special build, use first modgui found
            break
        if os.path.expanduser("~") in lilv.lilv_uri_to_path(resdir.as_string()):
            # found a modgui in the home dir, stop here and use it
            break

    del nodes, it
    '''

    # --------------------------------------------------------------------------------------------------------
    # gui
    '''
    gui = {}

    if modguigui is None or modguigui.me is None:
        warnings.append("no modgui available")

    else:
        # resourcesDirectory *must* be present
        modgui_resdir = world.find_nodes(modguigui.me, ns_modgui.resourcesDirectory.me, None).get_first()

        if modgui_resdir.me is None:
            errors.append("modgui has no resourcesDirectory data")

        else:
            if useAbsolutePath:
                gui['resourcesDirectory'] = lilv.lilv_uri_to_path(modgui_resdir.as_string())

                # check if modgui is defined in a separate file
                gui['usingSeeAlso'] = os.path.exists(os.path.join(bundle, "modgui.ttl"))

                # check if the modgui definition is on its own file and in the user dir
                gui['modificableInPlace'] = bool((bundle not in gui['resourcesDirectory'] or gui['usingSeeAlso']) and
                                                os.path.expanduser("~") in gui['resourcesDirectory'])
            else:
                gui['resourcesDirectory'] = modgui_resdir.as_string().replace(bundleuri,"",1)

            # icon and settings templates
            modgui_icon  = world.find_nodes(modguigui.me, ns_modgui.iconTemplate    .me, None).get_first()
            modgui_setts = world.find_nodes(modguigui.me, ns_modgui.settingsTemplate.me, None).get_first()

            if modgui_icon.me is None:
                errors.append("modgui has no iconTemplate data")
            else:
                iconFile = lilv.lilv_uri_to_path(modgui_icon.as_string())
                if os.path.exists(iconFile):
                    gui['iconTemplate'] = iconFile if useAbsolutePath else iconFile.replace(bundle,"",1)
                else:
                    errors.append("modgui iconTemplate file is missing")
                del iconFile

            if modgui_setts.me is not None:
                settingsFile = lilv.lilv_uri_to_path(modgui_setts.as_string())
                if os.path.exists(settingsFile):
                    gui['settingsTemplate'] = settingsFile if useAbsolutePath else settingsFile.replace(bundle,"",1)
                else:
                    errors.append("modgui settingsTemplate file is missing")
                del settingsFile

            # javascript and stylesheet files
            modgui_script = world.find_nodes(modguigui.me, ns_modgui.javascript.me, None).get_first()
            modgui_style  = world.find_nodes(modguigui.me, ns_modgui.stylesheet.me, None).get_first()

            if modgui_script.me is not None:
                javascriptFile = lilv.lilv_uri_to_path(modgui_script.as_string())
                if os.path.exists(javascriptFile):
                    gui['javascript'] = javascriptFile if useAbsolutePath else javascriptFile.replace(bundle,"",1)
                else:
                    errors.append("modgui javascript file is missing")
                del javascriptFile

            if modgui_style.me is None:
                errors.append("modgui has no stylesheet data")
            else:
                stylesheetFile = lilv.lilv_uri_to_path(modgui_style.as_string())
                if os.path.exists(stylesheetFile):
                    gui['stylesheet'] = stylesheetFile if useAbsolutePath else stylesheetFile.replace(bundle,"",1)
                else:
                    errors.append("modgui stylesheet file is missing")
                del stylesheetFile

            # template data for backwards compatibility
            # FIXME remove later once we got rid of all templateData files
            modgui_templ = world.find_nodes(modguigui.me, ns_modgui.templateData.me, None).get_first()

            if modgui_templ.me is not None:
                warnings.append("modgui is using old deprecated templateData")
                templFile = lilv.lilv_uri_to_path(modgui_templ.as_string())
                if os.path.exists(templFile):
                    with open(templFile, 'r') as fd:
                        try:
                            data = json.loads(fd.read())
                        except:
                            data = {}
                        keys = list(data.keys())

                        if 'author' in keys:
                            gui['brand'] = data['author']
                        if 'label' in keys:
                            gui['label'] = data['label']
                        if 'color' in keys:
                            gui['color'] = data['color']
                        if 'knob' in keys:
                            gui['knob'] = data['knob']
                        if 'controls' in keys:
                            index = 0
                            ports = []
                            for ctrl in data['controls']:
                                ports.append({
                                    'index' : index,
                                    'name'  : ctrl['name'],
                                    'symbol': ctrl['symbol'],
                                })
                                index += 1
                            gui['ports'] = ports
                del templFile

            # screenshot and thumbnail
            modgui_scrn  = world.find_nodes(modguigui.me, ns_modgui.screenshot.me, None).get_first()
            modgui_thumb = world.find_nodes(modguigui.me, ns_modgui.thumbnail .me, None).get_first()

            if modgui_scrn.me is not None:
                gui['screenshot'] = lilv.lilv_uri_to_path(modgui_scrn.as_string())
                if not os.path.exists(gui['screenshot']):
                    errors.append("modgui screenshot file is missing")
                if not useAbsolutePath:
                    gui['screenshot'] = gui['screenshot'].replace(bundle,"",1)
            else:
                errors.append("modgui has no screnshot data")

            if modgui_thumb.me is not None:
                gui['thumbnail'] = lilv.lilv_uri_to_path(modgui_thumb.as_string())
                if not os.path.exists(gui['thumbnail']):
                    errors.append("modgui thumbnail file is missing")
                if not useAbsolutePath:
                    gui['thumbnail'] = gui['thumbnail'].replace(bundle,"",1)
            else:
                errors.append("modgui has no thumbnail data")

            # extra stuff, all optional
            modgui_brand = world.find_nodes(modguigui.me, ns_modgui.brand.me, None).get_first()
            modgui_label = world.find_nodes(modguigui.me, ns_modgui.label.me, None).get_first()
            modgui_model = world.find_nodes(modguigui.me, ns_modgui.model.me, None).get_first()
            modgui_panel = world.find_nodes(modguigui.me, ns_modgui.panel.me, None).get_first()
            modgui_color = world.find_nodes(modguigui.me, ns_modgui.color.me, None).get_first()
            modgui_knob  = world.find_nodes(modguigui.me, ns_modgui.knob .me, None).get_first()

            if modgui_brand.me is not None:
                gui['brand'] = modgui_brand.as_string()
            if modgui_label.me is not None:
                gui['label'] = modgui_label.as_string()
            if modgui_model.me is not None:
                gui['model'] = modgui_model.as_string()
            if modgui_panel.me is not None:
                gui['panel'] = modgui_panel.as_string()
            if modgui_color.me is not None:
                gui['color'] = modgui_color.as_string()
            if modgui_knob.me is not None:
                gui['knob'] = modgui_knob.as_string()

            # ports
            errpr = False
            sybls = []
            ports = []
            nodes = world.find_nodes(modguigui.me, ns_modgui.port.me, None)
            it    = lilv.lilv_nodes_begin(nodes.me)
            while not lilv.lilv_nodes_is_end(nodes.me, it):
                port = lilv.lilv_nodes_get(nodes.me, it)
                it   = lilv.lilv_nodes_next(nodes.me, it)
                if port is None:
                    break
                port_indx = world.find_nodes(port, ns_lv2core.index .me, None).get_first()
                port_symb = world.find_nodes(port, ns_lv2core.symbol.me, None).get_first()
                port_name = world.find_nodes(port, ns_lv2core.name  .me, None).get_first()

                if None in (port_indx.me, port_name.me, port_symb.me):
                    if not errpr:
                        errors.append("modgui has some invalid port data")
                        errpr = True
                    continue

                port_indx = port_indx.as_int()
                port_symb = port_symb.as_string()
                port_name = port_name.as_string()

                ports.append({
                    'index' : port_indx,
                    'symbol': port_symb,
                    'name'  : port_name,
                })

                if port_symb not in sybls:
                    sybls.append(port_symb)
                elif not errpr:
                    errors.append("modgui has some duplicated port symbols")
                    errpr = True

            # sort ports
            if len(ports) > 0:
                ports2 = {}

                for port in ports:
                    ports2[port['index']] = port
                gui['ports'] = [ports2[i] for i in ports2]

                del ports2

            # cleanup
            del ports, nodes, it
    '''