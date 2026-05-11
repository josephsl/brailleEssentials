# coding: utf-8
# Part of Braille Essentials (forked from BrailleExtender) Addon for NVDA
# Copyright 2016-2026 Dalen Bernaca, Joseph Lee, André-Abush CLAUSE, released under GPL.

"""
Paths and add-on metadata.
Other code from here has been moved to constants.py and legacyCode.py.
"""

import os
import addonHandler
import globalVars
import languageHandler

addon = addonHandler.getCodeAddon()

# Paths
configDir   = os.path.join(globalVars.appArgs.configPath, addon.name)
baseDir     = os.path.dirname(__file__)
addonDir    = addon.path
profilesDir = os.path.join(baseDir, "Profiles")

# Metadata
addonName      = addon.name
addonSummary   = addon.manifest["summary"]
addonVersion   = addon.version
addonURL       = addon.manifest["url"]
addonGitHubURL = addonURL
addonAuthor    = addon.manifest["author"]
addonDesc      = addon.manifest["description"]

lang = languageHandler.getLanguage().split('_')[-1].lower()
punctuationSeparator = ' ' if 'fr' in lang else ''

