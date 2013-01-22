# -*- coding: utf-8 -*-
#
#  indentation_settings.py
#    ~ Separate indentation settings for different file types.
#
#  Copyright (C) 2012-2013 - Sergej Chodarev
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
from gi.repository import GObject, Gtk, Gedit, GtkSource, PeasGtk

import settings

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
        lang = self.document.get_language()
        if not lang: # No language set
            return
        lang_id = lang.get_id()
        indent = settings.get(lang_id)
        if indent == settings.TABS:
            self.view.set_insert_spaces_instead_of_tabs(False)
        else:
            self.view.set_insert_spaces_instead_of_tabs(True)
            self.view.set_tab_width(indent)

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
            self.settings_store.append(
                [lang_id, settings.indent_to_string(level), name])

    def save_language_settings(self):
        """Save selected indentation settings."""
        if not self.active:
            return
        lang_id = self.language_combo.get_active_id()
        if self.tabs_radio.get_active(): # Tabs
            settings.set(lang_id, settings.TABS)
        else: # Spaces
            num = self.num_spaces_spin.get_value_as_int()
            settings.set(lang_id, num)
    
    def settings_selection_changed(self, tree_selection):
        # Find out selected language
        model, itr = tree_selection.get_selected()
        lang_id = model.get_value(itr, 0)
        # Set all controls properly
        self.active = False # Stop saving settings
        self.language_combo.set_active_id(lang_id)
        indent = settings.get(lang_id)
        if indent == settings.TABS:
            self.tabs_radio.set_active(True)
        else:
            self.spaces_radio.set_active(True)
            self.num_spaces_spin.set_value(indent)
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
        itr = self.settings_store.append(["", "", ""])
        selection = self.settings_list.get_selection()
        selection.select_iter(itr)

    def remove_setting(self, button):
        selection = self.settings_list.get_selection()
        model, itr = selection.get_selected()
        lang_id = model.get_value(itr, 0)
        model.remove(itr)
        settings.remove(lang_id)
