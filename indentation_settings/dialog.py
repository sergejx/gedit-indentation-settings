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
from contextlib import contextmanager
from gi.repository import Gtk, GtkSource

import settings

class IndentationSettingsDialog(object):
    def __init__(self, datadir):
        # State of the dialog: in active state all changes are immediately saved
        # Should be set to False in code modifying controls
        # Managed using self.inactive context manager
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
        self.languages_filter = builder.get_object("languages_filter")
        self.settings_store = builder.get_object("settings_store")
        self.settings_selection = self.settings_list.get_selection()

        builder.get_object("toolbar").get_style_context() \
                .add_class("inline-toolbar")

        self.init_settings_list()
        self.init_languages_list()
        self.disable_settings_pane()
        self.remove_button.set_sensitive(False)

        builder.connect_signals(self)
        self.active = True

    def get_panel(self):
        return self.panel

    @contextmanager
    def inactive(self):
        """Perform actions without settings saving."""
        state = self.active
        self.active = False
        yield
        self.active = state

    def init_languages_list(self):
        manager = GtkSource.LanguageManager.get_default()
        lang_ids = manager.get_language_ids()
        for id in lang_ids:
            name = manager.get_language(id).get_name()
            self.languages_store.append([id, name])
        self.languages_filter.set_visible_func(self.language_list_filter_func)

    def init_settings_list(self):
        manager = GtkSource.LanguageManager.get_default()
        for (lang_id, level) in settings.list_settings():
            name = manager.get_language(lang_id).get_name()
            self.settings_store.append(
                [lang_id, settings.indent_to_string(level), name])

    def language_list_filter_func(self, store, itr, data):
        """Filter function for hiding languages that are already configured."""
        settings_model, settings_itr = self.settings_selection.get_selected()
        selected_id = settings_model.get_value(settings_itr, 0)
        lang_id = store[itr][0]
        return not settings.is_configured(lang_id) or lang_id == selected_id

    def disable_settings_pane(self):
        """
        Disable indentation settings for cases where no language is selected.
        """
        for control in [self.language_combo, self.tabs_radio, self.spaces_radio,
                        self.num_spaces_spin]:
            control.set_sensitive(False)
        # Unselect language
        with self.inactive():
            self.language_combo.set_active_id(None)

    def fill_language_settings(self, lang_id):
        """Setup indentation settings pane controls for a language."""
        # Enable controls
        self.language_combo.set_sensitive(True)
        self.tabs_radio.set_sensitive(True)
        self.spaces_radio.set_sensitive(True)
        # Set all controls properly
        with self.inactive():
            self.languages_filter.refilter()
            self.language_combo.set_active_id(lang_id)
            indent = settings.get(lang_id)
            if indent == settings.TABS:
                self.tabs_radio.set_active(True)
            else:
                self.spaces_radio.set_active(True)
                self.num_spaces_spin.set_value(indent)
                self.num_spaces_spin.set_sensitive(True)

    def save_language_settings(self):
        """Save selected indentation settings."""
        if not self.active:
            return
        # Gather data
        # language from settings list
        s_model, s_itr = self.settings_selection.get_selected()
        selected_lang_id = s_model.get_value(s_itr, 0)
        # language from languges combobox
        l_itr = self.language_combo.get_active_iter()
        lang_id, lang_name = self.languages_filter[l_itr]
        # indentation
        if self.tabs_radio.get_active():
            indent = settings.TABS
        else: # Spaces
            indent = self.num_spaces_spin.get_value_as_int()

        # Update settings
        settings.set(lang_id, indent)
        if lang_id != selected_lang_id and selected_lang_id: # Language changed
            settings.remove(selected_lang_id)

        # Update settings list
        s_model[s_itr] = (lang_id, settings.indent_to_string(indent), lang_name)

    def settings_selection_changed(self, tree_selection):
        model, itr = tree_selection.get_selected()
        if itr is not None:
            lang_id = model.get_value(itr, 0)
            self.fill_language_settings(lang_id)
            self.remove_button.set_sensitive(True)
        else: # Nothing selected
            self.disable_settings_pane()
            self.remove_button.set_sensitive(False)
        
    def language_changed(self, combobox):
        self.save_language_settings()

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
        self.settings_selection.select_iter(itr)

    def remove_setting(self, button):
        model, itr = self.settings_selection.get_selected()
        lang_id = model.get_value(itr, 0)
        model.remove(itr)
        settings.remove(lang_id)
