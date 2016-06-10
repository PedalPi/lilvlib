import lilv

from .lilvlib import NS


class PluginAuthor:

    def __init__(self, world, plugin, bundleuri, ns_doap):
        self.ns_doap = ns_doap
        self.ns_foaf = NS(world, lilv.LILV_NS_FOAF)

        self.world = world
        self.bundleuri = bundleuri

        self.errors = []
        self.warnings = []

    @property
    def author(self):
        return {
            'name': self.name,
            'homepage': self.homepage,
            'email': self.email,
        }

    @property
    def name(self):
        name = self.plugin.get_author_name().as_string() or ""

        if name is '':
            self.errors.append("plugin author name is missing")

        return name

    @property
    def homepage(self):
        homepage = self.plugin.get_author_homepage().as_string() or ''

        if homepage != '':
            return homepage

        prj = self.plugin_get_first_value(self.ns_lv2core.project)
        lv2maintainer = None
        lv2homepage = None

        if prj.me is not None:
            lv2maintainer = self.lv2maintaner(prj)

            if lv2maintainer is not None:
                lv2homepage = self.lv2homepage(lv2maintainer)

                if lv2homepage is not None:
                    homepage = lilv.lilv_node_as_string(lv2homepage)

        del lv2homepage
        del lv2maintainer
        del prj

        if homepage is None or homepage is '':
            self.warnings.append("plugin author homepage is missing")

        return homepage

    def lv2maintaner(self, prj):
        return lilv.lilv_world_get(
            self.world.me,
            prj.me,
            self.ns_doap.maintainer.me,
            None
        )

    def lv2homepage(self, maintainer):
        return lilv.lilv_world_get(
            self.world.me,
            maintainer,
            self.ns_foaf.homepage.me,
            None
        )

    @property
    def email(self):
        email = self.plugin.get_author_name().as_string() or ""

        if email is '':
            pass
        elif email.startswith(self.bundleuri):
            email = email.replace(self.bundleuri, "", 1)
            self.warnings.append("plugin author email entry is missing 'mailto:' prefix")

        elif email.startswith("mailto:"):
            email = email.replace("mailto:", "", 1)

        return email