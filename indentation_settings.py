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
from gi.repository import GObject, Gedit, Gio

SETTINGS_KEY = "org.gnome.gedit.preferences.editor"

TABS = 0
SPACES = 1

class Settings(object):
    """Custom indentation settings storage."""
    def __init__(self):
        self.filename = os.path.join(glib.get_user_config_dir(),
                                     "gedit", "indentation-settings")
        self.settings = {}
        self.gedit_settings = Gio.Settings(SETTINGS_KEY)

    def read(self):
        """Read configuration file."""
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
            return self.gedit_settings.get_uint("tabs-size")

    def indent_type(self, lang):
        if lang in self.settings:
            if self.settings[lang] <= 0:
                return TABS
            else:
                return SPACES
        else:
            if self.gedit_settings.get_boolean("insert-spaces"):
                return SPACES
            else:
                return TABS


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
    """Indenation settings applicator for a view."""
    __gtype_name__ = "IndentationSettingsView"

    view = GObject.property(type=Gedit.View)

    def __init__(self):
        GObject.Object.__init__(self)

    def apply_settings(self, *args):
        global settings
        if self.modeline_used(): # Modeline settings have higher precedence
            return
        lang = self.document.get_language()
        if not lang: # No language set
            return
        lang_id = lang.get_id()
        if settings.indent_type(lang_id) == TABS:
            self.view.set_insert_spaces_instead_of_tabs(False)
        else:
            self.view.set_insert_spaces_instead_of_tabs(True)
            self.view.set_tab_width(settings.indent_len(lang_id))

    def modeline_used(self):
        """Was indentation set by modeline?"""
        # Inspired by Auto Tab plugin
        modeline = self.view.get_data("ModelineOptions")
        if modeline:
            if modeline.has_key("tabs-width") or modeline.has_key("use-tabs"):
                return True
        return False

    def do_activate(self):
        self.document = self.view.get_buffer()
        self.apply_settings()
        self.handlers = [
                self.document.connect("notify::language", self.apply_settings)]

    def do_deactivate(self):
        for handler in self.handlers:
            self.document.disconnect(handler)

    def do_update_state(self):
        pass
