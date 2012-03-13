# -*- coding: utf-8 -*-
#
#  indentation_settings.py
#    ~ Separate indentation settings for different file types.
#
#  Copyright (C) 2012 - Sergej Chodarev
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import os
import glib
from gi.repository import GObject, Gedit

TABS = 0
SPACES = 1

class Settings(object):
    def __init__(self):
        self.filename = os.path.join(glib.get_user_config_dir(),
                                     "gedit", "custom-indent.conf")
        self.settings = {}

    def read(self):
        try:
            f = file(self.filename, "r")
        except IOError: # No settings
            self.settings = {"makefile": 0}
            return
        for line in f:
            try:
                key_value = self.read_line(line)
                if key_value:
                    self.settings[key_value[0]] = key_value[1]
            except ValueError:
                pass

    def read_line(self, line):
        line = line.strip()
        if line.startswith("#"): # Skip comment
            return None
        parts = line.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Malformed configuration line")
        lang = parts[0].strip()
        indent_s = parts[1].strip()
        if (indent_s == "tabs"):
            indent = 0
        else:
            indent = int(indent_s)
        return (lang, indent)

    def is_configured(self, lang):
        return lang in self.settings

    def indent_len(self, lang):
        if lang in self.settings and self.settings[lang] > 0:
            return self.settings[lang]
        else:
            return None

    def indent_type(self, lang):
        if lang in self.settings:
            if self.settings[lang] <= 0:
                return TABS
            else:
                return SPACES
        else:
            return None


# Global settings
settings = Settings()


class IndentationSettingsApp(GObject.Object, Gedit.AppActivatable):
    __gtype_name__ = "IndentationSettingsApp"

    app = GObject.property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        global settings
        settings.read()

    def do_deactivate(self):
        pass

class IndentationSettingsView(GObject.Object, Gedit.ViewActivatable):
    __gtype_name__ = "IndentationSettingsView"

    view = GObject.property(type=Gedit.View)

    def __init__(self):
        GObject.Object.__init__(self)

    def apply_settings(self):
        global settings
        buf = self.view.get_buffer()
        if not buf:
            return
        lang = buf.get_language()
        lang_id = lang.get_id()
        if settings.is_configured(lang_id):
            if settings.indent_type(lang_id) == TABS:
                self.view.set_insert_spaces_instead_of_tabs(False)
            else:
                self.view.set_insert_spaces_instead_of_tabs(True)
                self.view.set_tab_width(settings.indent_len(lang_id))

    def do_activate(self):
            self.apply_settings()

    def do_deactivate(self):
        pass

    def do_update_state(self):
        pass
