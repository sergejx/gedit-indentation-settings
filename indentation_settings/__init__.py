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


from gi.repository import GObject, Gedit, PeasGtk

import settings
from dialog import IndentationSettingsDialog

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


