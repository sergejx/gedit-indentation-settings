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
from gi.repository import GObject, Gio, Gtk, Gedit, GtkSource, PeasGtk

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
                
    def write(self):
        f = file(self.filename, "w")
        for lang, indent in self.settings.items():
            indent_s = str(indent) if indent > 0 else "tabs"
            f.write(lang + ":" + indent_s + "\n")

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

    def set_tabs(self, lang):
        self.settings[lang] = 0
        self.write()

    def set_spaces(self, lang, num):
        self.settings[lang] = num
        self.write()

    def list_settings(self):
        """
        Return list of all settings as a tuples (language_code, indentation)
        where indentation is either number of spaces or 0 for tabs.
        """
        return self.settings.items()


# Global settings
settings = Settings()


class IndentationSettingsApp(GObject.Object, Gedit.AppActivatable,
                             PeasGtk.Configurable):
    __gtype_name__ = "IndentationSettingsApp"

    app = GObject.property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        settings.read()

    def do_deactivate(self):
        pass

    def do_create_configure_widget(self):
        datadir = self.plugin_info.get_data_dir()
        dialog = IndentationSettingsDialog(datadir)
        return dialog.get_panel()


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

class IndentationSettingsDialog(object):
    def __init__(self, datadir):
        # Stave of the dialog: in active state all changes are immediately saved
        # Should be set to False in code modifying controls
        self.active = False
        
        # Read UI definition
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(datadir, "settings.ui"))

        # Get references to UI widgets
        self.panel = builder.get_object("settings_panel")
        self.settings_list = builder.get_object("settings_list")
        self.add_button = builder.get_object("add_button")
        self.remove_button = builder.get_object("remove_button")
        self.language_combo = builder.get_object("language_combo")
        self.tabs_radio = builder.get_object("tabs_radio")
        self.spaces_radio = builder.get_object("spaces_radio")
        self.num_spaces_spin = builder.get_object("num_spaces_spin")
        self.languages_store = builder.get_object("languages_store")
        self.settings_store = builder.get_object("settings_store")
        
        builder.get_object("toolbar").get_style_context() \
                .add_class("inline-toolbar")

        self.init_settings_list()
        self.init_languages_list()

        builder.connect_signals(self)
        self.active = True

    def get_panel(self):
        return self.panel

    def init_languages_list(self):
        manager = GtkSource.LanguageManager.get_default()
        lang_ids = manager.get_language_ids()
        for id in lang_ids:
            name = manager.get_language(id).get_name()
            self.languages_store.append([id, name])

    def init_settings_list(self):
        manager = GtkSource.LanguageManager.get_default()
        for (lang_id, level) in settings.list_settings():
            name = manager.get_language(lang_id).get_name()
            self.settings_store.append([lang_id, level, name])

    def save_language_settings(self):
        """Save selected indentation settings."""
        if not self.active:
            return
        lang_id = self.language_combo.get_active_id()
        if self.tabs_radio.get_active(): # Tabs
            settings.set_tabs(lang_id)
        else: # Spaces
            num = self.num_spaces_spin.get_value_as_int()
            settings.set_spaces(lang_id, num)
    
    def settings_selection_changed(self, tree_selection):
        # Find out selected language
        model, itr = tree_selection.get_selected()
        lang_id = model.get_value(itr, 0)
        # Set all controls properly
        self.active = False # Stop saving settings
        self.language_combo.set_active_id(lang_id)
        indent_type = settings.indent_type(lang_id)
        if indent_type == TABS:
            self.tabs_radio.set_active(True)
        elif indent_type == SPACES:
            self.spaces_radio.set_active(True)
            self.num_spaces_spin.set_value(settings.indent_len(lang_id))
        self.active = True

    def language_changed(self, combobox):
        pass

    def tabs_toggled(self, button):
        self.num_spaces_spin.set_sensitive(self.spaces_radio.get_active())
        self.save_language_settings()

    def spaces_toggled(self, button):
        self.num_spaces_spin.set_sensitive(self.spaces_radio.get_active())
        # Don't save settings, it was be done in tabs handler

    def num_spaces_changed(self, button):
        self.save_language_settings()

    def add_setting(self, button):
        pass

    def remove_setting(self, button):
        pass
