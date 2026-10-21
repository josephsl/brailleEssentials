# coding: utf-8
"""Automated unit tests for tab replacement with custom space widths in Braille Essentials."""

import builtins
import ctypes
import os
import sys
import types
from collections import defaultdict
from unittest.mock import MagicMock

import pytest

# Ensure translation functions and builtins exist in test environment
builtins._ = lambda s: s
builtins.pgettext = lambda c, s: s

# Setup comtypes mock structures before imports
comtypes = types.ModuleType("comtypes")


class GUID(ctypes.Structure):
	_fields_ = [("Data1", ctypes.c_ulong)]

	def __init__(self, val=None):
		super().__init__()


comtypes.GUID = GUID


class IUnknown(ctypes.Structure):
	pass


comtypes.IUnknown = IUnknown
comtypes.c_float = ctypes.c_float
comtypes.HRESULT = ctypes.c_long
comtypes.COMMETHOD = lambda *args: None
comtypes.STDMETHOD = lambda *args: None
comtypes.CoCreateInstance = MagicMock()
comtypes.CLSCTX_INPROC_SERVER = 1
sys.modules["comtypes"] = comtypes
sys.modules["comtypes.client"] = MagicMock()

# Setup configobj mock
import configobj
import validate

configobj.validate = validate

# NVDA core modules to mock
NVDA_MODULES = [
	"addonHandler",
	"api",
	"appModuleHandler",
	"braille",
	"brailleInput",
	"brailleTables",
	"buildVersion",
	"characterProcessing",
	"colors",
	"config",
	"controlTypes",
	"core",
	"cursorManager",
	"globalCommands",
	"globalPluginHandler",
	"globalVars",
	"gui",
	"inputCore",
	"keyLabels",
	"keyboardHandler",
	"languageHandler",
	"logHandler",
	"louisHelper",
	"nvwave",
	"queueHandler",
	"scriptHandler",
	"speech",
	"textInfos",
	"tones",
	"treeInterceptorHandler",
	"ui",
	"versionInfo",
	"virtualBuffers",
	"vision",
	"winUser",
	"wx",
	"NVDAObjects",
	"NVDAObjects.behaviors",
	"appModules",
	"appModules.brailleExtenderExcel",
]

for mod in NVDA_MODULES:
	if mod not in sys.modules:
		sys.modules[mod] = MagicMock()

sys.modules["globalVars"].appArgs.configPath = "/tmp"
sys.modules["addonHandler"].getAvailableAddons = lambda filterFunc=None: iter([])


class AutoDict(defaultdict):
	def __init__(self, *args, **kwargs):
		super().__init__(AutoDict, *args, **kwargs)
		self.spec = {}


test_conf = AutoDict()
test_conf["braille"]["expandAtCursor"] = True
test_conf["braille"]["translationTable"] = "en-ueb-g2.ctb"
test_conf["braille"]["showSelection"] = True
test_conf["braille"]["inputTable"] = "en-ueb-g2.ctb"
test_conf["brailleEssentials"]["advanced"]["fixCursorPositions"] = False
test_conf["brailleEssentials"]["tabSpace"] = False
test_conf["brailleEssentials"]["objectPresentation"]["selectedElement"] = 0

sys.modules["config"].conf = test_conf
sys.modules["braille"].handler = MagicMock()
sys.modules["braille"].handler.display.name = "noBraille"
sys.modules["braille"].TEXT_SEPARATOR = " "
sys.modules["braille"].dotsIO = 1

addon_path = os.path.abspath(
	os.path.join(os.path.dirname(__file__), "..", "addon", "globalPlugins")
)
if addon_path not in sys.path:
	sys.path.insert(0, addon_path)

from brailleEssentials import addoncfg, patches
import louis


class DummyRegion:
	"""Mock braille region for testing _addTextWithFields and update_region."""

	def __init__(self):
		self.rawText = ""
		self.rawTextTypeforms = []
		self._rawToContentPos = []
		self._currentContentPos = 0
		self.cursorPos = None
		self.selectionStart = None
		self.selectionEnd = None
		self._endsWithField = False
		self._isFormatFieldAtStart = True
		self._skipFieldsNotAtStartOfNode = False
		self.brailleCells = []
		self.brailleToRawPos = []
		self.rawToBraillePos = []
		self.brailleCursorPos = None


class DummyTextInfo:
	def __init__(self, commands, is_collapsed=False):
		self._commands = commands
		self.isCollapsed = is_collapsed
		self.obj = MagicMock()

	def getTextWithFields(self, formatConfig=None):
		return self._commands


@pytest.fixture(autouse=True)
def reset_test_config():
	test_conf["brailleEssentials"]["advanced"]["fixCursorPositions"] = False
	test_conf["brailleEssentials"]["tabSpace"] = False
	test_conf["brailleEssentials"]["objectPresentation"]["selectedElement"] = 0
	addoncfg.curBD = "test_display"


class TestTabSizeConfig:
	"""Tests for getTabSize retrieval and fallback handling."""

	def test_default_tab_size(self):
		addoncfg.curBD = "noBraille"
		test_conf["brailleEssentials"].pop("tabSize_noBraille", None)
		assert addoncfg.getTabSize() == 2

	def test_custom_tab_sizes(self):
		addoncfg.curBD = "focus"
		test_conf["brailleEssentials"]["tabSize_focus"] = 4
		assert addoncfg.getTabSize() == 4

		test_conf["brailleEssentials"]["tabSize_focus"] = 8
		assert addoncfg.getTabSize() == 8

		test_conf["brailleEssentials"]["tabSize_focus"] = 1
		assert addoncfg.getTabSize() == 1

	def test_invalid_and_nonpositive_tab_sizes_fallback_to_two(self):
		addoncfg.curBD = "focus"
		test_conf["brailleEssentials"]["tabSize_focus"] = 0
		assert addoncfg.getTabSize() == 2

		test_conf["brailleEssentials"]["tabSize_focus"] = -4
		assert addoncfg.getTabSize() == 2

		test_conf["brailleEssentials"]["tabSize_focus"] = "invalid"
		assert addoncfg.getTabSize() == 2


class TestAddTextWithFieldsTabReplacement:
	"""Tests for tab replacement inside _addTextWithFields buffer hook."""

	def test_tab_replacement_disabled(self):
		test_conf["brailleEssentials"]["tabSpace"] = False
		region = DummyRegion()
		info = DummyTextInfo(["\tCallable"])

		patches._addTextWithFields(region, info, {})

		assert region.rawText == "\tCallable"
		assert len(region.rawTextTypeforms) == len("\tCallable")
		assert region._rawToContentPos == list(range(len("\tCallable")))
		assert region._currentContentPos == 9

	@pytest.mark.parametrize("space_width", [1, 2, 4, 8])
	def test_tab_replacement_enabled_with_custom_space_widths(self, space_width):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = space_width

		region = DummyRegion()
		info = DummyTextInfo(["\tCallable"])

		patches._addTextWithFields(region, info, {})

		expected_spaces = " " * space_width
		expected_text = expected_spaces + "Callable"
		assert region.rawText == expected_text
		assert len(region.rawText) == space_width + 8
		assert len(region.rawTextTypeforms) == len(expected_text)

		# Content position 0 (the tab character) must be repeated for all space cells
		assert region._rawToContentPos[:space_width] == [0] * space_width
		# Following characters must map to original document content offsets
		assert region._rawToContentPos[space_width:] == list(range(1, 9))
		assert region._currentContentPos == 9

	def test_multiple_tabs_in_command(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		info = DummyTextInfo(["\tdef\tfoo():"])

		patches._addTextWithFields(region, info, {})

		expected_text = "    def    foo():"
		assert region.rawText == expected_text
		assert len(region._rawToContentPos) == len(expected_text)
		assert region._rawToContentPos[:4] == [0, 0, 0, 0]
		assert region._rawToContentPos[4:7] == [1, 2, 3]  # 'def'
		assert region._rawToContentPos[7:11] == [4, 4, 4, 4]  # second tab at content pos 4
		assert region._currentContentPos == len("\tdef\tfoo():")

	def test_selection_spanning_tab(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		info = DummyTextInfo(["\tCallable"])

		patches._addTextWithFields(region, info, {}, isSelection=True)

		assert region.selectionStart == 0
		assert region.selectionEnd == 12  # 4 spaces + 8 chars
		assert region.rawText == "    Callable"


class TestUpdateRegionTabReplacement:
	"""Tests for tab replacement inside update_region hook."""

	def test_update_region_replaces_tabs_when_enabled(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		region.rawText = "\tHello\tWorld"
		region.rawTextTypeforms = [0] * len(region.rawText)
		region._rawToContentPos = list(range(len(region.rawText)))
		region.cursorPos = 7  # on the second tab
		region.selectionStart = 0
		region.selectionEnd = 7

		# Mock louisHelper.translate
		mock_translate_result = (
			[0] * 18,
			list(range(18)),
			list(range(18)),
			0,
		)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    Hello    World"
		assert len(region.rawTextTypeforms) == len("    Hello    World")
		assert len(region._rawToContentPos) == len("    Hello    World")
		# String has '\tHello\tWorld' where indices are:
		# 0: '\t', 1-5: 'Hello', 6: '\t', 7: 'W'
		# cursorPos 7 is at 'W' after both tabs. Each tab expanded by 3 chars (+6 total).
		# In '    Hello    World', 'W' is at index 4 + 5 + 4 = 13.
		assert region.cursorPos == 13
		assert region.selectionStart == 0
		assert region.selectionEnd == 13

	def test_update_region_untouched_when_disabled(self):
		test_conf["brailleEssentials"]["tabSpace"] = False
		region = DummyRegion()
		region.rawText = "\tHello"
		region.rawTextTypeforms = [0] * len(region.rawText)

		mock_translate_result = ([0] * 6, list(range(6)), list(range(6)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "\tHello"


class TestDynamicTabReplacementBehavior:
	"""Tests dynamic toggling and immediate effect without restarts."""

	def test_toggle_without_restart(self):
		region1 = DummyRegion()
		test_conf["brailleEssentials"]["tabSpace"] = False
		patches._addTextWithFields(region1, DummyTextInfo(["\tTest"]), {})
		assert region1.rawText == "\tTest"

		# Immediately enable tab replacement
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 3

		region2 = DummyRegion()
		patches._addTextWithFields(region2, DummyTextInfo(["\tTest"]), {})
		assert region2.rawText == "   Test"

		# Immediately disable tab replacement again
		test_conf["brailleEssentials"]["tabSpace"] = False

		region3 = DummyRegion()
		patches._addTextWithFields(region3, DummyTextInfo(["\tTest"]), {})
		assert region3.rawText == "\tTest"

	def test_dynamic_space_width_change(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"

		# Set width to 2
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2
		region_width_2 = DummyRegion()
		patches._addTextWithFields(region_width_2, DummyTextInfo(["\tValue"]), {})
		assert region_width_2.rawText == "  Value"

		# Change width to 5 dynamically
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 5
		region_width_5 = DummyRegion()
		patches._addTextWithFields(region_width_5, DummyTextInfo(["\tValue"]), {})
		assert region_width_5.rawText == "     Value"


class TestLiblouisOutputVerification:
	"""Direct Liblouis translation test verifying tab replacement produces space cells."""

	def test_replaced_text_produces_blank_space_cells(self):
		tables = ["en-ueb-g2.ctb"]
		tab_size = 4
		replaced_text = (" " * tab_size) + "Callable"

		# Translate using dotsIO
		result, braille_to_raw, raw_to_braille, cursor = louis.translate(
			tables, replaced_text, mode=louis.dotsIO, cursorPos=0
		)

		cell_values = [ord(c) & 255 for c in result]

		# Verify first 4 cells are blank spaces (dot 0)
		assert cell_values[:4] == [0, 0, 0, 0]

		# Verify cursor at pos 0 maps to first blank cell
		assert cursor == 0

		# Verify characters for 'Callable' follow
		assert len(cell_values) > 4


class TestIssue4ReproductionSteps:
	"""Specific verification of the failure scenario reported in Issue 4."""

	def test_tab_characters_do_not_revert_on_cursor_move(self):
		"""Issue 4 note 1: Tab sign must not revert when cursor moves or selection changes."""
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		# 1. Cursor on tab (content pos 0)
		region_at_tab = DummyRegion()
		region_at_tab.cursorPos = 0
		patches._addTextWithFields(region_at_tab, DummyTextInfo(["\tCallable"]), {})
		assert region_at_tab.rawText == "  Callable"
		assert "\t" not in region_at_tab.rawText

		# 2. Cursor moved to 'Callable' (content pos 1)
		region_at_c = DummyRegion()
		# In update_TextInfoRegion: chunk before cursor is expanded first
		chunk_before = DummyTextInfo(["\t"])
		patches._addTextWithFields(region_at_c, chunk_before, {})
		# Cursor placed at end of chunk_before (index 2 in rawText)
		region_at_c.cursorPos = len(region_at_c.rawText)
		chunk_after = DummyTextInfo(["Callable"])
		patches._addTextWithFields(region_at_c, chunk_after, {})
		assert region_at_c.rawText == "  Callable"
		assert region_at_c.cursorPos == 2  # Points to 'C'
		assert "\t" not in region_at_c.rawText

		# 3. Selection with Shift+Right (selecting 'C')
		region_sel = DummyRegion()
		patches._addTextWithFields(region_sel, DummyTextInfo(["\t"]), {})
		# Selection on 'C'
		patches._addTextWithFields(region_sel, DummyTextInfo(["C"]), {}, isSelection=True)
		patches._addTextWithFields(region_sel, DummyTextInfo(["allable"]), {})
		assert region_sel.rawText == "  Callable"
		assert region_sel.selectionStart == 2
		assert region_sel.selectionEnd == 3
		assert "\t" not in region_sel.rawText

	def test_increasing_decreasing_space_count_takes_immediate_effect(self):
		"""Issue 4 note 2: Changing spaces per tab takes effect immediately."""
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"

		# Default 2
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2
		r2 = DummyRegion()
		patches._addTextWithFields(r2, DummyTextInfo(["\tCallable"]), {})
		assert r2.rawText == "  Callable"

		# Increase to 4
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4
		r4 = DummyRegion()
		patches._addTextWithFields(r4, DummyTextInfo(["\tCallable"]), {})
		assert r4.rawText == "    Callable"

		# Decrease to 1
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 1
		r1 = DummyRegion()
		patches._addTextWithFields(r1, DummyTextInfo(["\tCallable"]), {})
		assert r1.rawText == " Callable"

	def test_deactivating_setting_immediately_disables_without_restart(self):
		"""Issue 4 note 3: Deactivating setting immediately disables replacement."""
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		# Active
		test_conf["brailleEssentials"]["tabSpace"] = True
		r_active = DummyRegion()
		patches._addTextWithFields(r_active, DummyTextInfo(["\tCallable"]), {})
		assert r_active.rawText == "    Callable"

		# Deactivated: tabs immediately preserved
		test_conf["brailleEssentials"]["tabSpace"] = False
		r_inactive = DummyRegion()
		patches._addTextWithFields(r_inactive, DummyTextInfo(["\tCallable"]), {})
		assert r_inactive.rawText == "\tCallable"
