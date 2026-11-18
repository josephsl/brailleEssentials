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

import enum

if not hasattr(enum, "StrEnum"):
	class StrEnum(str, enum.Enum):
		pass

	enum.StrEnum = StrEnum

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


class MockFieldCommand:
	def __init__(self, command, field):
		self.command = command
		self.field = field


sys.modules["textInfos"].FieldCommand = MockFieldCommand


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
		self.brlex_typeforms = {}
		self._len_brlex_typeforms = 0

	def _getTypeformFromFormatField(self, field, formatConfig=None):
		if isinstance(field, dict) and field.get("bold"):
			return louis.bold, 192
		if isinstance(field, dict) and field.get("italic"):
			return louis.italic, 64
		if isinstance(field, dict) and field.get("invalid-spelling"):
			return louis.plain_text, 192
		return louis.plain_text, 0

	def _addFieldText(self, text, contentPos, separate=True):
		self.rawText += text
		self.rawTextTypeforms.extend([louis.plain_text] * len(text))
		self._rawToContentPos.extend([contentPos] * len(text))

	def getTextInfoForBraillePos(self, braillePos):
		if not isinstance(self.brailleToRawPos, list) or braillePos >= len(self.brailleToRawPos):
			return None
		raw_pos = self.brailleToRawPos[braillePos]
		content_pos = patches._get_region_content_pos(self, raw_pos)
		info = MagicMock()
		info.contentPos = content_pos
		info.rawPos = raw_pos
		info.character = self.rawText[raw_pos] if raw_pos < len(self.rawText) else ""
		info.copy = lambda: info
		info.expand = MagicMock()
		return info


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
	test_conf["braille"]["speakOnRouting"] = False
	addoncfg.curBD = "test_display"
	if hasattr(sys.modules["speech"], "spellTextInfo"):
		sys.modules["speech"].spellTextInfo.reset_mock()
	if hasattr(sys.modules["speech"], "speakTextInfo"):
		sys.modules["speech"].speakTextInfo.reset_mock()


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


class TestFormattingMarkersTabSynchronization:
	"""Tests verifying style formatting markers and typeforms stay synchronized across tabs."""

	def test_format_field_after_tab_aligns_marker_position(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		commands = [
			"\t",
			MockFieldCommand("formatChange", {"bold": True}),
			"StyledText",
			MockFieldCommand("formatChange", {"bold": False}),
			"After",
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		# 4 spaces replacing tab, followed by 'StyledText', then 'After'
		assert region.rawText == "    StyledTextAfter"
		# Format marker for bold must be placed at raw index 4 (after 4 spaces), NOT at content pos 1
		assert 4 in region.brlex_typeforms
		assert region.brlex_typeforms[4] == 192  # Bold dots
		# Format marker turning off bold must be at raw index 4 + len('StyledText') = 14
		assert 14 in region.brlex_typeforms
		assert region.brlex_typeforms[14] == 0
		# rawTextTypeforms must have plain text for the 4 spaces and bold for StyledText
		assert region.rawTextTypeforms[:4] == [louis.plain_text] * 4
		assert region.rawTextTypeforms[4:14] == [louis.bold] * 10
		assert region.rawTextTypeforms[14:] == [louis.plain_text] * 5

	def test_format_field_spanning_tabs_maintains_typeforms_and_spans(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		commands = [
			MockFieldCommand("formatChange", {"italic": True}),
			"def\tfoo():",
			MockFieldCommand("formatChange", {}),
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		expected_text = "def    foo():"
		assert region.rawText == expected_text
		# Italic typeform applied across all characters including the 4 tab spaces
		assert region.rawTextTypeforms == [louis.italic] * len(expected_text)
		assert region.brlex_typeforms[0] == 64
		assert region.brlex_typeforms[len(expected_text)] == 0

	def test_multiple_format_transitions_with_tabs(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		commands = [
			"\t",
			MockFieldCommand("formatChange", {"bold": True}),
			"one\t",
			MockFieldCommand("formatChange", {"italic": True}),
			"two",
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		assert region.rawText == "  one  two"
		# First formatChange (bold) at offset 2 (after 2 leading spaces)
		assert 2 in region.brlex_typeforms
		assert region.brlex_typeforms[2] == 192
		# Second formatChange (italic) after 'one  ' (length 5) -> offset 7
		assert 7 in region.brlex_typeforms
		assert region.brlex_typeforms[7] == 64

	def test_update_region_shifts_brlex_typeforms_markers(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		region.rawText = "\tHello\tWorld"
		region.rawTextTypeforms = [0] * len(region.rawText)
		region._rawToContentPos = list(range(len(region.rawText)))
		# In unexpanded text: 0='\t', 1='H', 6='\t', 7='W'
		region.brlex_typeforms = {0: 0, 1: 192, 6: 0, 7: 64}
		region._len_brlex_typeforms = 7

		mock_translate_result = ([0] * 18, list(range(18)), list(range(18)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    Hello    World"
		# Tab at pos 0 expands by 3 -> pos 1 shifts to 1+3=4
		# Tab at pos 6 (in old text) -> pos 6 shifts to 6+3=9
		# Pos 7 (in old text) has 2 preceding tabs -> shifts to 7+6=13
		assert region.brlex_typeforms[0] == 0
		assert region.brlex_typeforms[4] == 192
		assert region.brlex_typeforms[9] == 0
		assert region.brlex_typeforms[13] == 64
		assert region._len_brlex_typeforms == 13

	def test_update_region_expands_raw_text_typeforms_across_tabs(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		region.rawText = "A\tB"
		region.rawTextTypeforms = [louis.plain_text, louis.bold, louis.italic]

		mock_translate_result = ([0] * 6, list(range(6)), list(range(6)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "A    B"
		# Tab at pos 1 was bold; all 4 spaces must be bold
		assert region.rawTextTypeforms == [
			louis.plain_text,
			louis.bold,
			louis.bold,
			louis.bold,
			louis.bold,
			louis.italic,
		]

	def test_multiple_tabs_inside_format_run(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 3

		region = DummyRegion()
		commands = [
			"\t",
			MockFieldCommand("formatChange", {"bold": True}),
			"\tbold\ttext\t",
			MockFieldCommand("formatChange", {}),
			"\tafter",
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		# Leading tab: 3 spaces (plain)
		# Bold run: 3 spaces + "bold" + 3 spaces + "text" + 3 spaces = 17 chars
		# Bold ends at 3 + 17 = 20
		# After run: 3 spaces + "after" = 8 chars
		assert region.rawText == "   " + "   bold   text   " + "   after"
		assert region.brlex_typeforms[3] == 192
		assert region.brlex_typeforms[20] == 0
		assert region.rawTextTypeforms[:3] == [louis.plain_text] * 3
		assert region.rawTextTypeforms[3:20] == [louis.bold] * 17
		assert region.rawTextTypeforms[20:] == [louis.plain_text] * 8

	def test_tab_size_one_formatting_markers(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 1

		region = DummyRegion()
		commands = [
			"\t",
			MockFieldCommand("formatChange", {"bold": True}),
			"\tword",
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		assert region.rawText == "  word"
		assert region.brlex_typeforms[1] == 192
		assert region.rawTextTypeforms[:1] == [louis.plain_text]
		assert region.rawTextTypeforms[1:] == [louis.bold] * 5

	def test_update_region_marker_on_tab_character(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		region.rawText = "\t"
		region.rawTextTypeforms = [louis.bold]
		region.brlex_typeforms = {0: 192}

		mock_translate_result = ([0] * 4, list(range(4)), list(range(4)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    "
		assert region.rawTextTypeforms == [louis.bold] * 4
		assert region.brlex_typeforms == {0: 192}


class TestTabReplacementPerformanceAndBatching:
	"""Tests verifying batch slice extensions and high-performance tab replacement."""

	def test_consecutive_tabs_batch_expansion(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["\t\t\t"]), {})

		assert region.rawText == " " * 12
		assert len(region.rawTextTypeforms) == 12
		assert region._rawToContentPos == [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]
		assert region._currentContentPos == 3

	def test_mixed_tabs_and_words_content_pos_mapping(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["func(\targ1,\targ2\t)"]), {})

		expected_text = "func(  arg1,  arg2  )"
		assert region.rawText == expected_text
		assert len(region._rawToContentPos) == len(expected_text)
		assert region._currentContentPos == len("func(\targ1,\targ2\t)")

	def test_large_line_with_many_tabs_performance(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		num_tabs = 100
		command = "\tcode" * num_tabs
		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo([command]), {})

		assert region.rawText == "    code" * num_tabs
		assert len(region.rawText) == 8 * num_tabs
		assert len(region.rawTextTypeforms) == len(region.rawText)
		assert len(region._rawToContentPos) == len(region.rawText)
		assert region._currentContentPos == len(command)


class TestRegionSubclassesScope:
	"""Tests verifying monkey patch cleanly supports any Region subclass without assuming TextInfoRegion internals."""

	def test_base_region_without_textinfo_internals(self):
		"""A plain Region subclass without _rawToContentPos or TextInfo methods."""
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		class BaseRegionMock:
			def __init__(self):
				self.rawText = "\tSimple\tRegion"
				self.cursorPos = None
				self.selectionStart = None
				self.selectionEnd = None
				self.brailleCells = []
				self.rawToBraillePos = []
				self.brailleToRawPos = []
				self.brailleCursorPos = None

		region = BaseRegionMock()
		mock_translate_result = ([0] * 19, list(range(19)), list(range(19)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    Simple    Region"
		# Region has no _rawToContentPos or rawTextTypeforms; no AttributeError raised
		assert not hasattr(region, "_rawToContentPos")

	def test_region_with_typeforms_only(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		class TypeformsOnlyRegion:
			def __init__(self):
				self.rawText = "\tHi"
				self.rawTextTypeforms = [louis.bold, louis.italic, louis.plain_text]
				self.cursorPos = None
				self.selectionStart = None
				self.selectionEnd = None
				self.brailleCells = []
				self.rawToBraillePos = []
				self.brailleToRawPos = []
				self.brailleCursorPos = None

		region = TypeformsOnlyRegion()
		mock_translate_result = ([0] * 4, list(range(4)), list(range(4)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "  Hi"
		assert region.rawTextTypeforms == [louis.bold, louis.bold, louis.italic, louis.plain_text]

	def test_region_with_cursor_and_selection_offsets(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		class GenericRegion:
			def __init__(self):
				self.rawText = "\tA\tB"
				self.cursorPos = 1  # on 'A'
				self.selectionStart = 0
				self.selectionEnd = 3  # on 'B'
				self.brailleCells = []
				self.rawToBraillePos = []
				self.brailleToRawPos = []
				self.brailleCursorPos = None

		region = GenericRegion()
		mock_translate_result = ([0] * 8, list(range(8)), list(range(8)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    A    B"
		# Cursor was at 1 (after 1 tab) -> 1 + 3 = 4 (at 'A')
		assert region.cursorPos == 4
		assert region.selectionStart == 0
		# SelectionEnd was at 3 (after 2 tabs) -> 3 + 2*3 = 9 (after 'B')
		assert region.selectionEnd == 9

	def test_region_with_no_cursor_or_selection(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		class NoCursorRegion:
			def __init__(self):
				self.rawText = "\tNoCursor"
				self.cursorPos = None
				self.selectionStart = None
				self.selectionEnd = None
				self.brailleCells = []
				self.rawToBraillePos = []
				self.brailleToRawPos = []
				self.brailleCursorPos = None

		region = NoCursorRegion()
		mock_translate_result = ([0] * 12, list(range(12)), list(range(12)), 0)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "    NoCursor"
		assert region.cursorPos is None
		assert region.selectionStart is None
		assert region.selectionEnd is None


class TestCursorRoutingOnTabSpaces:
	"""Tests for cursor routing on intermediate spaces of tabs and initial position alignment."""

	def _setup_routing_env(self, region, mode=patches.RC_EMULATE_ARROWS_SILENT):
		test_conf["brailleEssentials"]["tabSpace"] = True
		test_conf["brailleEssentials"]["routingCursorsEditFields"] = mode

		obj = sys.modules["api"].getNavigatorObject()
		obj.appModule = MagicMock(spec=[])
		obj.hasFocus = True
		obj.role = patches.get_control_type("ROLE_EDITABLETEXT")

		sys.modules["braille"].handler.getTether.return_value = 0
		sys.modules["braille"].handler.buffer = sys.modules["braille"].handler.mainBuffer = region
		sys.modules["braille"].handler.buffer.windowStartPos = 0

		sent_keys = []

		def mock_from_name(key):
			m = MagicMock()
			m.send = lambda: sent_keys.append(key)
			return m

		sys.modules["keyboardHandler"].KeyboardInputGesture.fromName = mock_from_name
		return sent_keys

	def test_routing_on_intermediate_spaces_maps_to_tab_content_position(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})

		# "j" followed by 4 spaces and "p" -> len 6
		assert region.rawText == "j    p"
		assert region._rawToContentPos == [0, 1, 1, 1, 1, 2]

		# Any space of the tab (indices 1, 2, 3, 4) must map to content offset 1 (the tab)
		for raw_idx in (1, 2, 3, 4):
			assert patches._get_region_content_pos(region, raw_idx) == 1

	def test_cursor_on_tab_snaps_to_initial_tab_cell(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		# Region with cursor positioned at intermediate space cell 3 of tab
		region = DummyRegion()
		region.rawText = "j    p"
		region._rawToContentPos = [0, 1, 1, 1, 1, 2]
		region.cursorPos = 3  # third space of tab

		# Call _expand_region_tabs (or simulate update snapping)
		# Directly verify snapping logic when cursorPos is in intermediate tab spacing
		target_content = region._rawToContentPos[region.cursorPos]
		initial_raw = region._rawToContentPos.index(target_content)
		assert initial_raw == 1

		# Verify update_region with tab expansion snaps cursorPos to initial cell 1
		region_update = DummyRegion()
		region_update.rawText = "j\tp"
		region_update.cursorPos = 1  # on tab
		region_update._rawToContentPos = [0, 1, 2]

		mock_translate_result = ([0] * 6, list(range(6)), list(range(6)), 1)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region_update)
		assert region_update.rawText == "j    p"
		assert region_update.cursorPos == 1  # Initial cell of the tab

	def test_arrow_emulation_routing_on_intermediate_space_sends_single_step(self):
		region = DummyRegion()
		region.rawText = "j    p"
		region._rawToContentPos = [0, 1, 1, 1, 1, 2]
		region._currentContentPos = 3
		region.cursorPos = 0  # At 'j'
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		sent_keys = self._setup_routing_env(region)

		# Route to cell 1 (beginning of tab)
		g1 = MagicMock()
		g1.routingIndex = 1
		patches.script_braille_routeTo(None, g1)
		assert sent_keys == ["rightarrow"]

		# Route to cell 2 (second space of tab)
		sent_keys.clear()
		g2 = MagicMock()
		g2.routingIndex = 2
		patches.script_braille_routeTo(None, g2)
		assert sent_keys == ["rightarrow"]

		# Route to cell 4 (fourth space of tab)
		sent_keys.clear()
		g4 = MagicMock()
		g4.routingIndex = 4
		patches.script_braille_routeTo(None, g4)
		assert sent_keys == ["rightarrow"]

		# Route to cell 5 ('p')
		sent_keys.clear()
		g5 = MagicMock()
		g5.routingIndex = 5
		patches.script_braille_routeTo(None, g5)
		assert sent_keys == ["rightarrow", "rightarrow"]

	def test_arrow_emulation_routing_on_same_tab_sends_zero_steps(self):
		region = DummyRegion()
		region.rawText = "j    p"
		region._rawToContentPos = [0, 1, 1, 1, 1, 2]
		region._currentContentPos = 3
		region.cursorPos = 1  # Already on tab
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		sent_keys = self._setup_routing_env(region)

		# Route to cell 3 (third space of same tab)
		g = MagicMock()
		g.routingIndex = 3
		patches.script_braille_routeTo(None, g)
		assert sent_keys == []

	def test_arrow_emulation_beep_mode_triggers_beeps(self):
		region = DummyRegion()
		region.rawText = "j    p"
		region._rawToContentPos = [0, 1, 1, 1, 1, 2]
		region._currentContentPos = 3
		region.cursorPos = 0
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		self._setup_routing_env(region, mode=patches.RC_EMULATE_ARROWS_BEEP)
		sys.modules["tones"].beep.reset_mock()

		g = MagicMock()
		g.routingIndex = 1
		patches.script_braille_routeTo(None, g)
		assert sys.modules["tones"].beep.call_count == 2


class TestTrailingTabsRoutingAndBoundaries:
	"""Tests specifically covering trailing tabs such as 'j\\tp\\t' and boundary triggers."""

	def _setup_routing_env(self, region):
		test_conf["brailleEssentials"]["tabSpace"] = True
		test_conf["brailleEssentials"]["routingCursorsEditFields"] = patches.RC_EMULATE_ARROWS_SILENT

		obj = sys.modules["api"].getNavigatorObject()
		obj.appModule = MagicMock(spec=[])
		obj.hasFocus = True
		obj.role = patches.get_control_type("ROLE_EDITABLETEXT")

		sys.modules["braille"].handler.getTether.return_value = 0
		sys.modules["braille"].handler.buffer = sys.modules["braille"].handler.mainBuffer = region
		sys.modules["braille"].handler.buffer.windowStartPos = 0

		sent_keys = []

		def mock_from_name(key):
			m = MagicMock()
			m.send = lambda: sent_keys.append(key)
			return m

		sys.modules["keyboardHandler"].KeyboardInputGesture.fromName = mock_from_name
		return sent_keys

	def test_trailing_tab_string_content_mapping(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp\t"]), {})

		assert region.rawText == "j  p  "
		assert region._rawToContentPos == [0, 1, 1, 2, 3, 3]
		assert region._currentContentPos == 4

		# Neither trailing tab space should map to 0 (which would jump to start of line)
		assert patches._get_region_content_pos(region, 4) == 3
		assert patches._get_region_content_pos(region, 5) == 3

	def test_trailing_tab_size_calculation(self):
		region = DummyRegion()
		region.rawText = "j  p  "
		region._rawToContentPos = [0, 1, 1, 2, 3, 3]
		region._currentContentPos = 4

		# Content size must be 4 (end of line position), not 3 (trailing tab)
		assert patches._get_region_content_size(region) == 4

	def test_routing_to_trailing_tab_spaces_from_p(self):
		region = DummyRegion()
		region.rawText = "j  p  "
		region._rawToContentPos = [0, 1, 1, 2, 3, 3]
		region._currentContentPos = 4
		region.cursorPos = 3  # at 'p' (content pos 2)
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		sent_keys = self._setup_routing_env(region)

		# Route to cell 4 (space 1 of trailing tab) -> must send 1 rightarrow, NOT 'end'
		g4 = MagicMock()
		g4.routingIndex = 4
		patches.script_braille_routeTo(None, g4)
		assert sent_keys == ["rightarrow"]

		# Route to cell 5 (space 2 of trailing tab) -> must send 1 rightarrow, NOT 'end'
		sent_keys.clear()
		g5 = MagicMock()
		g5.routingIndex = 5
		patches.script_braille_routeTo(None, g5)
		assert sent_keys == ["rightarrow"]

	def test_routing_beyond_trailing_tab_sends_end(self):
		region = DummyRegion()
		region.rawText = "j  p  "
		region._rawToContentPos = [0, 1, 1, 2, 3, 3]
		region._currentContentPos = 4
		region.cursorPos = 0
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		sent_keys = self._setup_routing_env(region)

		# Route to cell 6 (beyond display cells of text) -> sends 'end'
		g = MagicMock()
		g.routingIndex = 6
		patches.script_braille_routeTo(None, g)
		assert sent_keys == ["end"]

	def test_routing_from_trailing_tab_backward(self):
		region = DummyRegion()
		region.rawText = "j  p  "
		region._rawToContentPos = [0, 1, 1, 2, 3, 3]
		region._currentContentPos = 4
		region.cursorPos = 4  # on trailing tab (content pos 3)
		region.brailleToRawPos = [0, 1, 2, 3, 4, 5]

		sent_keys = self._setup_routing_env(region)

		# Route to cell 3 ('p')
		g3 = MagicMock()
		g3.routingIndex = 3
		patches.script_braille_routeTo(None, g3)
		assert sent_keys == ["leftarrow"]

		# Route to cell 1 (tab 1)
		sent_keys.clear()
		g1 = MagicMock()
		g1.routingIndex = 1
		patches.script_braille_routeTo(None, g1)
		assert sent_keys == ["leftarrow", "leftarrow"]

		# Route to cell 0 ('j') -> sends 'home'
		sent_keys.clear()
		g0 = MagicMock()
		g0.routingIndex = 0
		patches.script_braille_routeTo(None, g0)
		assert sent_keys == ["home"]

	def test_multiple_trailing_tabs(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp\t\t"]), {})

		assert region.rawText == "j  p    "
		assert region._rawToContentPos == [0, 1, 1, 2, 3, 3, 4, 4]
		assert region._currentContentPos == 5
		assert patches._get_region_content_pos(region, 6) == 4
		assert patches._get_region_content_pos(region, 7) == 4

	def test_trailing_tab_in_expand_region_tabs_does_not_fall_back_to_zero(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		class RegionWithContentPos:
			def __init__(self):
				self.rawText = "j\tp\t"
				self._rawToContentPos = [0, 1, 2, 3]
				self.cursorPos = 3
				self.selectionStart = None
				self.selectionEnd = None
				self.brailleCells = []
				self.rawToBraillePos = []
				self.brailleToRawPos = []
				self.brailleCursorPos = None

		region = RegionWithContentPos()
		mock_translate_result = ([0] * 6, list(range(6)), list(range(6)), 4)
		sys.modules["louisHelper"].translate = MagicMock(return_value=mock_translate_result)

		patches.update_region(region)

		assert region.rawText == "j  p  "
		assert region._rawToContentPos == [0, 1, 1, 2, 3, 3]
		# Trailing tab cursorPos was 3 -> 3 + 1 = 4 (initial cell of trailing tab)
		assert region.cursorPos == 4


class TestDynamicFormattingMarkersAndSpellingErrors:
	"""Tests verifying dynamic formatting markers (such as spelling errors) are preserved without distortion."""

	def test_dynamic_spelling_error_appearance_and_removal(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		# 1. Spelling error dynamically present
		region_err = DummyRegion()
		commands_err = [
			"\t",
			MockFieldCommand("formatChange", {"invalid-spelling": True}),
			"mispelled",
			MockFieldCommand("formatChange", {"invalid-spelling": False}),
			" normal",
		]
		patches._addTextWithFields(region_err, DummyTextInfo(commands_err), defaultdict(bool))

		assert region_err.rawText == "    mispelled normal"
		assert 4 in region_err.brlex_typeforms
		# Error mask is active starting at raw offset 4 (after 4 tab spaces)
		assert region_err.brlex_typeforms[4] != 0
		# Error mask turns off at 4 + len("mispelled") = 13
		assert 13 in region_err.brlex_typeforms
		assert region_err.brlex_typeforms[13] == 0

		# 2. Spelling error fixed dynamically
		region_fixed = DummyRegion()
		commands_fixed = [
			"\t",
			MockFieldCommand("formatChange", {"invalid-spelling": False}),
			"corrected",
			" normal",
		]
		patches._addTextWithFields(region_fixed, DummyTextInfo(commands_fixed), defaultdict(bool))
		assert region_fixed.rawText == "    corrected normal"
		# No active error masks
		for mask in region_fixed.brlex_typeforms.values():
			assert mask == 0

	def test_spelling_error_spanning_tab(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		commands = [
			MockFieldCommand("formatChange", {"invalid-spelling": True}),
			"bad\tword",
			MockFieldCommand("formatChange", {"invalid-spelling": False}),
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		assert region.rawText == "bad  word"
		assert 0 in region.brlex_typeforms
		assert region.brlex_typeforms[0] != 0
		assert 9 in region.brlex_typeforms
		assert region.brlex_typeforms[9] == 0

	def test_spelling_error_on_trailing_tab(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		commands = [
			"prefix ",
			MockFieldCommand("formatChange", {"invalid-spelling": True}),
			"err\t",
			MockFieldCommand("formatChange", {"invalid-spelling": False}),
		]
		patches._addTextWithFields(region, DummyTextInfo(commands), defaultdict(bool))

		assert region.rawText == "prefix err  "
		assert 7 in region.brlex_typeforms
		assert region.brlex_typeforms[7] != 0
		assert 12 in region.brlex_typeforms
		assert region.brlex_typeforms[12] == 0

	def test_ia2_dynamic_spelling_format_field_normalization(self):
		field = {"invalid": "spelling"}
		patches._prepare_format_field_for_braille(field)
		assert field.get("invalid-spelling") is True


class MockBrailleBuffer:
	"""Mock of NVDA's BrailleBuffer containing regions and bufferPosToRegionPos mapping."""

	def __init__(self, regions):
		self.regions = regions
		self.windowStartPos = 0
		self.cursorPos = None
		self.brailleCells = []
		self.rawText = ""
		start = 0
		for r in regions:
			self.rawText += getattr(r, "rawText", "")
			cells = getattr(r, "brailleCells", [])
			if not cells and getattr(r, "rawText", ""):
				cells = [0] * len(r.rawText)
				r.brailleCells = cells
			self.brailleCells.extend(cells)
			if getattr(r, "brailleCursorPos", None) is not None:
				self.cursorPos = start + r.brailleCursorPos
			elif getattr(r, "cursorPos", None) is not None:
				if getattr(r, "rawToBraillePos", None) and 0 <= r.cursorPos < len(r.rawToBraillePos):
					self.cursorPos = start + r.rawToBraillePos[r.cursorPos]
				else:
					self.cursorPos = start + r.cursorPos
			start += len(cells)

	def bufferPosToRegionPos(self, bufferPos: int):
		start = 0
		for r in self.regions:
			cells = getattr(r, "brailleCells", [])
			end = start + len(cells)
			if end > bufferPos:
				return r, bufferPos - start
			start = end
		raise LookupError("No such position")

	def getTextInfoForWindowPos(self, windowPos: int):
		pos = self.windowStartPos + windowPos
		try:
			region, reg_pos = self.bufferPosToRegionPos(pos)
			if hasattr(region, "getTextInfoForBraillePos"):
				return region.getTextInfoForBraillePos(reg_pos)
		except LookupError:
			pass
		return None

	@property
	def brailleToRawPos(self):
		res = []
		start = 0
		for r in self.regions:
			b2r = getattr(r, "brailleToRawPos", [])
			if not b2r and getattr(r, "rawText", ""):
				b2r = list(range(len(r.rawText)))
			res.extend([p + start for p in b2r])
			start += len(getattr(r, "rawText", ""))
		return res


class TestAlternativeRoutingInTerminalsAndEditFields:
	"""Tests verifying alternative arrow key routing in ROLE_TERMINAL and ROLE_EDITABLETEXT with full buffer structures."""

	def _setup_terminal_env(self, region, mode=patches.RC_EMULATE_ARROWS_SILENT, role="ROLE_TERMINAL"):
		test_conf["brailleEssentials"]["tabSpace"] = True
		test_conf["brailleEssentials"]["routingCursorsEditFields"] = mode

		obj = sys.modules["api"].getNavigatorObject()
		obj.appModule = MagicMock(spec=[])
		obj.hasFocus = True
		obj.role = patches.get_control_type(role)

		buffer = MockBrailleBuffer([region])
		sys.modules["braille"].handler.getTether.return_value = 0
		sys.modules["braille"].handler.buffer = sys.modules["braille"].handler.mainBuffer = buffer
		sys.modules["braille"].handler.getTextInfoForWindowPos = buffer.getTextInfoForWindowPos

		sent_keys = []

		def mock_from_name(key):
			m = MagicMock()
			m.send = lambda: sent_keys.append(key)
			return m

		sys.modules["keyboardHandler"].KeyboardInputGesture.fromName = mock_from_name
		return buffer, sent_keys

	def test_terminal_routing_on_intermediate_spaces_maps_to_tab(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0  # At 'j'
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		buffer, sent_keys = self._setup_terminal_env(region)

		# Route to cell 1 (beginning of tab)
		g1 = MagicMock()
		g1.routingIndex = 1
		patches.script_braille_routeTo(None, g1)
		assert sent_keys == ["rightarrow"]

		# Route to cell 2 (second space of tab) from 'j'
		sent_keys.clear()
		g2 = MagicMock()
		g2.routingIndex = 2
		patches.script_braille_routeTo(None, g2)
		assert sent_keys == ["rightarrow"]

		# Now move cursor to tab (initial raw cell 1)
		region.cursorPos = 1
		buffer.cursorPos = 1
		sent_keys.clear()
		# Route to cell 3 (third space of same tab) -> 0 steps
		g3 = MagicMock()
		g3.routingIndex = 3
		patches.script_braille_routeTo(None, g3)
		assert sent_keys == []

		# Now move cursor to 'p' (cell 5, content pos 2)
		region.cursorPos = 5
		buffer.cursorPos = 5
		sent_keys.clear()
		# Route to cell 2 (second space of tab) -> sends 1 leftarrow
		patches.script_braille_routeTo(None, g2)
		assert sent_keys == ["leftarrow"]

	def test_terminal_routing_on_trailing_tabs(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 2

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp\t"]), {})
		# rawText: "j  p  ", _rawToContentPos: [0, 1, 1, 2, 3, 3]
		region.cursorPos = 0  # At 'j'
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		buffer, sent_keys = self._setup_terminal_env(region)

		# Route from 'j' to cell 4 (first space of trailing tab) -> sends 3 rightarrows
		g4 = MagicMock()
		g4.routingIndex = 4
		patches.script_braille_routeTo(None, g4)
		assert sent_keys == ["rightarrow", "rightarrow", "rightarrow"]

		# Now cursor is on trailing tab (initial cell 4, content pos 3)
		region.cursorPos = 4
		buffer.cursorPos = 4
		sent_keys.clear()
		# Route to cell 5 (second space of same trailing tab) -> sends 0 steps
		g5 = MagicMock()
		g5.routingIndex = 5
		patches.script_braille_routeTo(None, g5)
		assert sent_keys == []

		# Route beyond trailing tab (cell 6) -> sends end
		sent_keys.clear()
		g6 = MagicMock()
		g6.routingIndex = 6
		patches.script_braille_routeTo(None, g6)
		assert sent_keys == ["end"]

		# Route backward from trailing tab (cell 4) to cell 3 ('p', content pos 2) -> sends leftarrow
		sent_keys.clear()
		g3 = MagicMock()
		g3.routingIndex = 3
		patches.script_braille_routeTo(None, g3)
		assert sent_keys == ["leftarrow"]

	def test_terminal_plain_spaces_arrow_emulation(self):
		"""In terminals where text has literal spaces without tabs, arrow steps match column count."""
		region = DummyRegion()
		region.rawText = "ls    -l"
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		buffer, sent_keys = self._setup_terminal_env(region)

		# Route from 0 to column 3 (space 2)
		g3 = MagicMock()
		g3.routingIndex = 3
		patches.script_braille_routeTo(None, g3)
		assert sent_keys == ["rightarrow", "rightarrow", "rightarrow"]

		# From column 3 to column 0 -> sends home
		region.cursorPos = 3
		buffer.cursorPos = 3
		sent_keys.clear()
		g0 = MagicMock()
		g0.routingIndex = 0
		patches.script_braille_routeTo(None, g0)
		assert sent_keys == ["home"]

		# From column 3 to end of line (column 8) -> sends end
		sent_keys.clear()
		g8 = MagicMock()
		g8.routingIndex = 8
		patches.script_braille_routeTo(None, g8)
		assert sent_keys == ["end"]

	def test_edit_field_alternative_routing_with_mock_buffer(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["code\tblock"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		_buffer, sent_keys = self._setup_terminal_env(region, role="ROLE_EDITABLETEXT")

		# Route to cell 6 (third space of tab) -> sends 4 rightarrows (from 'c' at 0 to '\t' at content index 4)
		g6 = MagicMock()
		g6.routingIndex = 6
		patches.script_braille_routeTo(None, g6)
		assert len(sent_keys) == 4
		assert all(k == "rightarrow" for k in sent_keys)


class TestRoutingSpeechAnnouncements:
	"""Tests verifying NVDA's speakOnRouting setting triggers character speech after alternative routing."""

	def _setup_speech_env(self, region, speak_on_routing=True, mode=patches.RC_EMULATE_ARROWS_SILENT):
		test_conf["brailleEssentials"]["tabSpace"] = True
		test_conf["brailleEssentials"]["routingCursorsEditFields"] = mode
		test_conf["braille"]["speakOnRouting"] = speak_on_routing

		obj = sys.modules["api"].getNavigatorObject()
		obj.appModule = MagicMock(spec=[])
		obj.hasFocus = True
		obj.role = patches.get_control_type("ROLE_TERMINAL")

		buffer = MockBrailleBuffer([region])
		sys.modules["braille"].handler.getTether.return_value = 0
		sys.modules["braille"].handler.buffer = sys.modules["braille"].handler.mainBuffer = buffer
		sys.modules["braille"].handler.getTextInfoForWindowPos = buffer.getTextInfoForWindowPos

		sent_keys = []
		sys.modules["keyboardHandler"].KeyboardInputGesture.fromName = lambda key: MagicMock(
			send=lambda: sent_keys.append(key)
		)
		sys.modules["speech"].spellTextInfo.reset_mock()
		sys.modules["speech"].speakTextInfo.reset_mock()
		return buffer, sent_keys

	def test_speech_called_when_speak_on_routing_enabled(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=True)

		g = MagicMock()
		g.routingIndex = 2  # intermediate tab space
		patches.script_braille_routeTo(None, g)

		assert sys.modules["speech"].spellTextInfo.call_count == 1
		called_info = sys.modules["speech"].spellTextInfo.call_args[0][0]
		called_info.expand.assert_called_with(sys.modules["textInfos"].UNIT_CHARACTER)

	def test_speech_not_called_when_speak_on_routing_disabled(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=False)

		g = MagicMock()
		g.routingIndex = 2
		patches.script_braille_routeTo(None, g)

		assert sys.modules["speech"].spellTextInfo.call_count == 0
		assert sys.modules["speech"].speakTextInfo.call_count == 0

	def test_speech_speaks_correct_character_on_tab_routing(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=True)

		# Route to cell 3 (third space of tab) -> character is space/tab
		g = MagicMock()
		g.routingIndex = 3
		patches.script_braille_routeTo(None, g)

		assert sys.modules["speech"].spellTextInfo.call_count == 1
		info = sys.modules["speech"].spellTextInfo.call_args[0][0]
		assert info.contentPos == 1  # tab content offset

	def test_speech_speaks_correct_character_on_text_routing(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=True)

		# Route to cell 5 ('p')
		g = MagicMock()
		g.routingIndex = 5
		patches.script_braille_routeTo(None, g)

		assert sys.modules["speech"].spellTextInfo.call_count == 1
		info = sys.modules["speech"].spellTextInfo.call_args[0][0]
		assert info.character == "p"
		assert info.contentPos == 2

	def test_speech_with_beep_mode(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=True, mode=patches.RC_EMULATE_ARROWS_BEEP)
		sys.modules["tones"].beep.reset_mock()

		g = MagicMock()
		g.routingIndex = 1
		patches.script_braille_routeTo(None, g)

		assert sys.modules["tones"].beep.call_count == 2
		assert sys.modules["speech"].spellTextInfo.call_count == 1

	def test_speech_graceful_when_config_key_absent(self):
		test_conf["brailleEssentials"]["tabSpace"] = True
		addoncfg.curBD = "test_display"
		test_conf["brailleEssentials"][f"tabSize_{addoncfg.curBD}"] = 4

		region = DummyRegion()
		patches._addTextWithFields(region, DummyTextInfo(["j\tp"]), {})
		region.cursorPos = 0
		region.brailleCells = [0] * len(region.rawText)
		region.brailleToRawPos = list(range(len(region.rawText)))
		region.rawToBraillePos = list(range(len(region.rawText)))

		self._setup_speech_env(region, speak_on_routing=False)
		test_conf["braille"].pop("speakOnRouting", None)

		g = MagicMock()
		g.routingIndex = 1
		patches.script_braille_routeTo(None, g)
		assert sys.modules["speech"].spellTextInfo.call_count == 0
