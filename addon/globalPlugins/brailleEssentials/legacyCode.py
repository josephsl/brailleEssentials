# Part of Braille Essentials add-on
# Copyright (C) 2026 by Dalen Bernaca

"""
The purpose of this module is to aggregate all legacy code from Braille Extender that would, inevitably, be deprecated.
In order to adapt Braille Essentials to API from NVDA 2025.3.3 and later some reorganization and cleaning is needed.
Parts of code that need to be moved around during the restructuring can be temporarely put here.
A function or class that ends up here will either be rewritten from scratch and moved to appropriate module or discarded in the future.
"""

import versionInfo
import re

# From common.py:

# some stand-in for gettext() used in other modules, but exact purpose is unclear
N_ = lambda s: _(s)

# At the moment unnecessary. Will need something like this in the future for new features.
# Needs serious rework though.
def nvdaVersionAtLeast(year: int, major: int, minor: int = 0) -> bool:
	"""Check if current NVDA version is >= year.major.minor.
	Import from common for custom version checks, e.g. nvdaVersionAtLeast(2024, 4).
	"""
	try:
		parts = versionInfo.version.split(".", 2)
		def _intPart(s):
			m = re.search(r"\d+", s)
			return int(m.group()) if m else 0
		vYear = _intPart(parts[0]) if len(parts) > 0 else 0
		vMajor = _intPart(parts[1]) if len(parts) > 1 else 0
		vMinor = _intPart(parts[2]) if len(parts) > 2 else 0
		return (vYear, vMajor, vMinor) >= (year, major, minor)
	except (ValueError, IndexError, AttributeError):
		return False

# We do not need these constants any more since we run from 2025.3.3 only
# NVDA core features (from changelog), used for addon compatibility:
# - 2022.3: interruptSpeechWhileScrolling (speech interrupt when scrolling)
# - 2024.4: speakOnRouting (announce character when routing cursor)
# - 2025.1: speakOnNavigatingByUnit (NVDA braille), automatic braille table selection (inputTable/translationTable "auto")
# Braille Essentials speakScroll stays independent; turn off NVDA's "Speak when navigating by line or paragraph" to avoid duplicates.
NVDA_HAS_INTERRUPT_SPEECH_WHILE_SCROLLING = nvdaVersionAtLeast(2022, 3)
NVDA_HAS_SPEAK_ON_ROUTING = nvdaVersionAtLeast(2024, 4)
NVDA_HAS_AUTOMATIC_BRAILLE_TABLES = nvdaVersionAtLeast(2025, 1)
