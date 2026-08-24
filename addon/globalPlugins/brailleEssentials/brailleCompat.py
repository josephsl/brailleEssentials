# -*- coding: UTF-8 -*-
"""Compatibility layer for NVDA's braille package reorganisation.

NVDA moved the regions, buffers, handler, labels, constants, display helpers and
the braille input handler out of the flat ``braille`` and ``brailleInput``
namespaces into sub-modules, leaving deprecated aliases behind. Every read of an
alias goes through the module ``__getattr__`` installed by ``utils._deprecate``,
which logs a WARNING and a full stack trace. This add-on reads those names on
practically every braille update, which floods the log.

Importing the symbols from their real homes keeps the add-on quiet on current
NVDA while staying compatible with builds that predate the split (the manifest
minimum is 2025.3.3), where the same names still live on the flat modules and
are not deprecated.

Symbols that are stable objects (classes, functions, constants, label mappings)
are re-exported directly. Two module aliases are kept instead:

``brailleInput``
	``handler`` is rebound at run time by braille initialise/terminate, so it has
	to be read through the module rather than captured here.
``regionsProperties``
	``patches.py`` both reads and replaces the field-formatting functions, which
	means it needs the module object to assign back to.
"""

try:
	# NVDA with the split braille package.
	from braille import input as brailleInput
	from braille.brailleHandler import BrailleHandler, formatCellsForLog
	from braille.buffers import BrailleBuffer
	from braille.constants import (
		INPUT_END_IND,
		INPUT_START_IND,
		SELECTION_SHAPE,
		TEXT_SEPARATOR,
	)
	from braille.display import getDisplayDrivers, getDisplayList, getSerialPorts
	from braille.input.inputHandler import BrailleInputHandler
	from braille.labels import (
		landmarkLabels,
		negativeStateLabels,
		positiveStateLabels,
		roleLabels,
	)
	from braille.regions import properties as regionsProperties
	from braille.regions.NVDAObject import NVDAObjectHasUsefulText, NVDAObjectRegion
	from braille.regions.base import Region, TextRegion
	from braille.regions.focus import getFocusContextRegions, getFocusRegions
	from braille.regions.textInfo import TextInfoRegion

	NEW_BRAILLE_LAYOUT = True
except ImportError:
	# NVDA before the split: every symbol still lives on the flat modules, and
	# reading them there is not deprecated.
	import braille as regionsProperties  # noqa: F401 - module alias, see docstring
	import brailleInput  # noqa: F401 - module alias, see docstring
	from braille import (  # noqa: F401
		INPUT_END_IND,
		INPUT_START_IND,
		SELECTION_SHAPE,
		TEXT_SEPARATOR,
		BrailleBuffer,
		BrailleHandler,
		NVDAObjectHasUsefulText,
		NVDAObjectRegion,
		Region,
		TextInfoRegion,
		TextRegion,
		formatCellsForLog,
		getDisplayDrivers,
		getDisplayList,
		getFocusContextRegions,
		getFocusRegions,
		getSerialPorts,
		landmarkLabels,
		negativeStateLabels,
		positiveStateLabels,
		roleLabels,
	)
	from brailleInput import BrailleInputHandler  # noqa: F401

	NEW_BRAILLE_LAYOUT = False


def _resolveLouisDotsIOStart() -> int:
	"""Offset liblouis expects on dot patterns handed to it in dotsIO mode.

	NVDA's deprecation table claims ``brailleInput.LOUIS_DOTS_IO_START`` moved to
	``braille.input.constants``, but that module never defines it; the value now
	lives in ``louisHelper._DOTS_IO_START``. Reading the documented alias raises
	AttributeError on current builds, so resolve it from where it actually is,
	then from the pre-split public name, and only then from the literal.
	"""
	try:
		import louisHelper

		return louisHelper._DOTS_IO_START
	except (ImportError, AttributeError):
		pass
	try:
		return brailleInput.LOUIS_DOTS_IO_START
	except AttributeError:
		# The dotsIO marker bit, fixed by the liblouis API.
		return 0x8000


#: See L{_resolveLouisDotsIOStart}.
LOUIS_DOTS_IO_START = _resolveLouisDotsIOStart()
