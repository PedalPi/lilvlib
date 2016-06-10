import lilv

from lilvlib import NS


class PluginAuthor:

    def __init__(self, world, plugin, bundleuri):
        self.ns_doap = NS(world, lilv.LILV_NS_DOAP)
        self.ns_foaf = NS(world, lilv.LILV_NS_FOAF)
        self.ns_lv2core = NS(world, lilv.LILV_NS_LV2)

        self.world = world

        self.errors = []
        self.warnings = []

        self.author = self.generate_author(plugin, bundleuri)

    def generate_author(self, plugin, bundleuri):
        return {
            'name': self.generate_name(plugin),
            'homepage': self.generate_homepage(plugin),
            'email': self.generate_email(plugin, bundleuri),
        }

    def generate_name(self, plugin):
        name = plugin.get_author_name().as_string() or ""

        if name is '':
            self.errors.append("plugin author name is missing")

        return name

    def generate_homepage(self, plugin):
        homepage = plugin.get_author_homepage().as_string() or ''

        if homepage != '':
            return homepage

        prj = plugin.get_value(self.ns_lv2core.project).get_first()
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

    def generate_email(self, plugin, bundleuri):
        email = plugin.get_author_name().as_string() or ""

        if email is '':
            pass
        elif email.startswith(bundleuri):
            email = email.replace(bundleuri, "", 1)
            self.warnings.append("plugin author email entry is missing 'mailto:' prefix")

        elif email.startswith("mailto:"):
            email = email.replace("mailto:", "", 1)

        return email
