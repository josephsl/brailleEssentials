# Part of Braille Essentials (forked from BrailleExtender) Addon for NVDA
# Copyright 2016-2026 Dalen Bernaca, Joseph Lee, André-Abush CLAUSE, released under GPL.

"""
All constants in one place.
Most of them are extracted from Braille Extender's old common.py module.
Some are from other places.
"""

from controlTypes import IsCurrent

IS_CURRENT_NO = IsCurrent.NO

CHOICE_none = "none"

# text attributes
CHOICE_liblouis   = "liblouis"
CHOICE_dot7       = "dot7"
CHOICE_dot8       = "dot8"
CHOICE_dots78     = "dots78"
CHOICE_tags       = "tags"
CHOICE_spacing    = "spacing"
TAG_SEPARATOR     = chr(5)
CHOICE_likeSpeech = '0'
CHOICE_enabled    = '1'
CHOICE_disabled   = '2'

REPLACE_TEXT  = 0
INSERT_AFTER  = 1
INSERT_BEFORE = 2

ADDON_ORDER_PROPERTIES = "states,cellCoordsText,value,name,roleText,description,keyboardShortcut,positionInfo,positionInfoLevel,current,placeholder"

ROLE_LABEL = 0
FORMATTING_LABEL = 1

# auto scroll
DEFAULT_AUTO_SCROLL_DELAY = 3000
MIN_AUTO_SCROLL_DELAY = 200
MAX_AUTO_SCROLL_DELAY = 42000
DEFAULT_STEP_DELAY_CHANGE = 100
MIN_STEP_DELAY_CHANGE = 25
MAX_STEP_DELAY_CHANGE = 7000

# Routing cursors behavior in edit fields
RC_NORMAL = "normal"
RC_EMULATE_ARROWS_BEEP = "arrows_beeps"
RC_EMULATE_ARROWS_SILENT = "arrows_silent"

# From old version of addoncfg.py
CHOICE_braille = "braille"
CHOICE_speech = "speech"
CHOICE_speechAndBraille = "speechAndBraille"
CHOICE_focus = "focus"
CHOICE_review = "review"
CHOICE_focusAndReview = "focusAndReview"
