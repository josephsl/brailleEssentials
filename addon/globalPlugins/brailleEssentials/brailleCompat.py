# coding: utf-8
# brailleCompat.py - Part of Braille Essentials Addon for NVDA
# Copyright 2026 Joseph Lee, André-Abush CLAUSE, released under GPL.

"""Compatibility layer for NVDA's braille package reorganisation.

NVDA 2026.1 split the ``braille`` and ``brailleInput`` modules into the ``braille``
and ``braille.input`` packages. The old top level names still resolve, through the
module level ``__getattr__`` installed by ``utils._deprecate``, but relying on them
has two costs:

* Every read logs a deprecation warning together with a full stack trace. Loading
  the add-on on NVDA 2026.1 writes around fifty of those before NVDA finishes
  starting, which buries anything else in the log.
* Reads are all the shim supports. Assigning to a moved name binds a new attribute
  on the old module instead of replacing the real one, so the add-on's patches of
  ``getPropertiesBraille``, ``getControlFieldBraille`` and ``getFormatFieldBraille``
  silently stop taking effect: NVDA core resolves those from
  ``braille.regions.properties`` (and from the modules that import them by name),
  never from ``braille``.

This module resolves each symbol the add-on needs from its new home when the
package layout is available, and falls back to the pre-2026.1 names otherwise, so
the add-on keeps working on every NVDA version it claims to support.
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

import braille


def _tryImport(name: str) -> ModuleType | None:
	try:
		return importlib.import_module(name)
	except ImportError:
		return None


NEW_BRAILLE_PACKAGE: bool = _tryImport("braille.regions.base") is not None
"""``True`` on NVDA 2026.1 and later, where ``braille`` is a package."""


if NEW_BRAILLE_PACKAGE:
	import braille.input as brailleInput  # noqa: F401 - re-exported, see below
	from braille.brailleHandler import BrailleHandler
	from braille.buffers import BrailleBuffer
	from braille.constants import (
		INPUT_END_IND,
		INPUT_START_IND,
		SELECTION_SHAPE,
		TEXT_SEPARATOR,
	)
	from braille.display import getDisplayList
	from braille.input.inputHandler import BrailleInputHandler
	from braille.labels import (
		landmarkLabels,
		negativeStateLabels,
		positiveStateLabels,
		roleLabels,
	)
	from braille.regions.NVDAObject import NVDAObjectHasUsefulText, NVDAObjectRegion
	from braille.regions.base import Region, TextRegion
	from braille.regions.focus import getFocusContextRegions, getFocusRegions
	from braille.regions.textInfo import TextInfoRegion
else:
	import brailleInput  # noqa: F401 - re-exported, see below

	BrailleHandler = braille.BrailleHandler
	BrailleBuffer = braille.BrailleBuffer
	INPUT_END_IND = braille.INPUT_END_IND
	INPUT_START_IND = braille.INPUT_START_IND
	SELECTION_SHAPE = braille.SELECTION_SHAPE
	TEXT_SEPARATOR = braille.TEXT_SEPARATOR
	getDisplayList = braille.getDisplayList
	BrailleInputHandler = brailleInput.BrailleInputHandler
	landmarkLabels = braille.landmarkLabels
	negativeStateLabels = braille.negativeStateLabels
	positiveStateLabels = braille.positiveStateLabels
	roleLabels = braille.roleLabels
	NVDAObjectHasUsefulText = braille.NVDAObjectHasUsefulText
	NVDAObjectRegion = braille.NVDAObjectRegion
	Region = braille.Region
	TextRegion = braille.TextRegion
	getFocusContextRegions = braille.getFocusContextRegions
	getFocusRegions = braille.getFocusRegions
	TextInfoRegion = braille.TextInfoRegion

# ``brailleInput`` above is deliberately re-exported under its historical name so that
# callers can keep writing ``brailleInput.handler``: the handler is a singleton that is
# rebound at initialise/terminate time, so it must be looked up on the module on every
# access rather than captured here.

LOUIS_DOTS_IO_START = 0x8000
"""Bit set on each cell passed to liblouis in ``dotsIO`` mode.

Removed from ``brailleInput`` in NVDA 2026.1 with no public replacement, so the add-on
carries its own copy for :func:`patches._translate`.
"""


# Modules that can hold a binding to a braille module level function, most specific first.
# NVDA 2026.1 defines them in ``braille.regions.properties`` but re-binds them by name in
# the modules that call them, e.g. ``braille.regions.NVDAObject`` does
# ``from .properties import getPropertiesBraille``. Patching only the defining module
# would leave those callers on the original implementation.
_FUNCTION_HOLDER_MODULES = (
	"braille.regions.properties",
	"braille.regions.NVDAObject",
	"braille.regions.textInfo",
	"braille",
)


def _holderModules(name: str) -> list[ModuleType]:
	"""Return every module whose own namespace binds ``name``.

	``vars()`` is used rather than :func:`getattr` so that the deprecation
	``__getattr__`` is not triggered, and so that modules which only re-export the
	name through that shim are not mistaken for real holders.
	"""
	holders = []
	for modName in _FUNCTION_HOLDER_MODULES:
		mod = _tryImport(modName)
		if mod is not None and name in vars(mod):
			holders.append(mod)
	return holders


def getBrailleFunction(name: str) -> Any:
	"""Return NVDA's current implementation of a braille module level function.

	:param name: Name of the function, e.g. ``"getPropertiesBraille"``.
	:raises AttributeError: If no known braille module provides it.
	"""
	holders = _holderModules(name)
	if not holders:
		raise AttributeError(f"no braille module provides {name!r}")
	return getattr(holders[0], name)


def patchBrailleFunction(name: str, func: Any) -> None:
	"""Replace a braille module level function everywhere NVDA looks it up.

	:param name: Name of the function, e.g. ``"getPropertiesBraille"``.
	:param func: Replacement implementation.
	:raises AttributeError: If no known braille module provides it.
	"""
	holders = _holderModules(name)
	if not holders:
		raise AttributeError(f"no braille module provides {name!r}")
	for mod in holders:
		setattr(mod, name, func)
