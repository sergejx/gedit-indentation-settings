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
"""
Custom indentation settings storage.
Indentation mode is stored as number of spaces or special number TABS.
"""

import os
from gi.repository import Gio, GLib

SETTINGS_KEY = "org.gnome.gedit.preferences.editor"
TABS = 0

# Initialze module
filename = os.path.join(GLib.get_user_config_dir(),
                             "gedit", "indentation-settings")
settings = {}
gedit_settings = Gio.Settings(SETTINGS_KEY)


def indent_to_string(indent):
    if indent == TABS:
        return "tabs"
    else:
        return str(indent) + " spaces"

def indent_from_string(string):
    """
    Read indentation mode from string specification.
    Specification is either number of spaces or word "tabs".
    The function would raise ValueError for incorrect inputs.
    """
    if string == "tabs":
        return TABS
    else:
        return int(string)

def read():
    """Read configuration file."""
    try:
        f = open(filename, "r")
    except IOError: # No settings
        settings['makefile'] = TABS
        return
    for line in f:
        try:
            key_value = read_line(line)
            if key_value:
                settings[key_value[0]] = key_value[1]
        except ValueError:
            pass

def write():
    f = open(filename, "w")
    for lang, indent in sorted(settings.items()):
        indent_s = str(indent) if indent > 0 else "tabs"
        f.write(lang + ":" + indent_s + "\n")

def read_line(line):
    line = line.strip()
    if line.startswith("#"): # Skip comment
        return None
    parts = line.split(":", 1)
    if len(parts) != 2:
        raise ValueError("Malformed configuration line")
    lang = parts[0].strip()
    indent_s = parts[1].strip()
    indent = indent_from_string(indent_s)
    return (lang, indent)

def is_configured(lang):
    return lang in settings

def default_mode():
    if gedit_settings.get_boolean("insert-spaces"):
        return gedit_settings.get_uint("tabs-size")
    else:
        return TABS

def get(lang):
    if lang in settings:
        return settings[lang]
    else:
        return default_mode()

def set(lang, indent):
    settings[lang] = indent
    write()

def remove(lang):
    """Remove language from settings list"""
    del settings[lang]
    write()

def list_settings():
    """
    Return list of all settings as a tuples (language_code, mode)
    where mode is instance of IndentationMode.
    """
    return sorted(settings.items())
