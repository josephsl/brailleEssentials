# Build customizations
# Change this file instead of sconstruct or manifest files, whenever possible.

from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries, SpeechDictionaries

# Since some strings in `addon_info` are translatable,
# we need to include them in the .po files.
# Gettext recognizes only strings given as parameters to the `_` function.
# To avoid initializing translations in this module we simply import a "fake" `_` function
# which returns whatever is given to it as an argument.
from site_scons.site_tools.NVDATool.utils import _


# Add-on information variables
addon_info = AddonInfo(
	# add-on Name/identifier, internal for NVDA
	addon_name="brailleEssentials",
	# Add-on summary/title, usually the user visible name of the add-on
	# Translators: Summary/title for this add-on
	# to be shown on installation and add-on information found in add-on store
	addon_summary=_("Braille Essentials"),
	# Add-on description
	# Translators: Long description to be shown for this add-on on add-on information from add-on store
	addon_description=_("""This add-on provides essential features for NVDA users relying on braille support. The following features, deriving from Braille Extender, are available:

* Reload two favorite braille display with shortcuts.
* Automatic review cursor tethering in terminal role like in PuTTY, Powershell, bash, cmd.
* Auto scroll.
* Switch between several input/output braille tables.
* Mark the text with special attributes through dot 7, dot 8 or both.
* Use two output braille tables simultaneously.
* Display tab signs as spaces.
* Reverse forward scroll and back scroll buttons.
* Say the current line during text scrolling either in review mode, or in focus mode or both.
* Translate text easily in Unicode braille and vice versa. E.g.: z <--> ⠵.
* Convert cell description to Unicode braille and vice versa. E.g.: 123 <--> ⠇.
* Lock braille keyboard.
* Launch an application/URL with gesture.
* Braille dictionaries.
* Type with one-hand from braille keyboard.
* Display undefined characters from braille tables (including emojis) using altenative representations.
* Enter any character from braille keyboard (including emojis).
* Skip blank lines during text scrolling.
* Speech History Mode.

And much more.

For some braille displays, it extends the braille display commands to provide:

* Offer complete gesture maps including function keys, multimedia keys, quick navigation, etc.
* Emulate modifier keys, and thus any keyboard shortcut
* Offer several keyboard configurations concerning the possibility to input dots 7 and 8, enter and backspace
* Add actions and quick navigation through a rotor"""),
	# version
	addon_version="26.05.4",
	# Brief changelog for this version
	# Translators: what's new content for the add-on version to be shown in the add-on store
	addon_changelog=_("""* Updated the add-on code to be based on BrailleExtender commit adc4dca206f (2026-05-16). This resolves bugs including inability to open input braille table overview screen.

Changes from BrailleExtender:

* Removed "user guide" menu item (add-on user guide can be opened from add-on store under help menu item).
* Some document formatting indicators on braille will resemble NVDA's own braille tags, including strikethrough and list items count in browse mode.
* The add-on's document formatting settings option labels and order will closely resemble NVDA screen reader's own document formatting settings screen.
* Strong emphasis braille tag is dots 12478/n/dots 14578.
* In add-on settings, automatic braille input;output braill table selectionbased on current NVDA language will always be visible."""),
	# Author(s)
	addon_author="Joseph Lee <joseph.lee22590@gmail.com> (originally André-Abush Clause <dev@andreabc.net> and other contributors)",
	# URL for the add-on documentation support
	addon_url="https://github.com/josephsl/brailleEssentials",
	# URL for the add-on repository where the source code can be found
	addon_sourceURL="https://github.com/josephsl/brailleEssentials",
	# Documentation file name
	addon_docFileName="readme.html",
	# Minimum NVDA version supported (e.g. "2019.3.0", minor version is optional)
	addon_minimumNVDAVersion="2025.3.3",
	# Last NVDA version supported/tested (e.g. "2024.4.0", ideally more recent than minimum version)
	addon_lastTestedNVDAVersion="2026.1.1",
	# Add-on update channel (default is None, denoting stable releases,
	# and for development releases, use "dev".)
	# Do not change unless you know what you are doing!
	addon_updateChannel=None,
	# Add-on license such as GPL 2
	addon_license="GPL v2",
	# URL for the license document the ad-on is licensed under
	addon_licenseURL="https://www.gnu.org/licenses/gpl-2.0.html",
)

# Define the python files that are the sources of your add-on.
# You can either list every file (using ""/") as a path separator,
# or use glob expressions.
# For example to include all files with a ".py" extension from the "globalPlugins" dir of your add-on
# the list can be written as follows:
# pythonSources = ["addon/globalPlugins/*.py"]
# For more information on SCons Glob expressions please take a look at:
# https://scons.org/doc/production/HTML/scons-user/apd.html
pythonSources: list[str] = ["addon/globalPlugins/brailleEssentials/*.py"]

# Files that contain strings for translation. Usually your python sources
i18nSources: list[str] = pythonSources + ["buildVars.py"]

# Files that will be ignored when building the nvda-addon file
# Paths are relative to the addon directory, not to the root directory of your addon sources.
# You can either list every file (using ""/") as a path separator,
# or use glob expressions.
excludedFiles: list[str] = []

# Base language for the NVDA add-on
# If your add-on is written in a language other than english, modify this variable.
# For example, set baseLanguage to "es" if your add-on is primarily written in spanish.
# You must also edit .gitignore file to specify base language files to be ignored.
baseLanguage: str = "en"

# Markdown extensions for add-on documentation
# Most add-ons do not require additional Markdown extensions.
# If you need to add support for markup such as tables, fill out the below list.
# Extensions string must be of the form "markdown.extensions.extensionName"
# e.g. "markdown.extensions.tables" to add tables.
markdownExtensions: list[str] = []

# Custom braille translation tables
# If your add-on includes custom braille tables (most will not), fill out this dictionary.
# Each key is a dictionary named according to braille table file name,
# with keys inside recording the following attributes:
# displayName (name of the table shown to users and translatable),
# contracted (contracted (True) or uncontracted (False) braille code),
# output (shown in output table list),
# input (shown in input table list).
brailleTables: BrailleTables = {}

# Custom speech symbol dictionaries
# Symbol dictionary files reside in the locale folder, e.g. `locale\en`, and are named `symbols-<name>.dic`.
# If your add-on includes custom speech symbol dictionaries (most will not), fill out this dictionary.
# Each key is the name of the dictionary,
# with keys inside recording the following attributes:
# displayName (name of the speech dictionary shown to users and translatable),
# mandatory (True when always enabled, False when not).
symbolDictionaries: SymbolDictionaries = {}

# Custom speech dictionaries (distinct from symbol dictionaries above)
# Speech dictionary files reside in the speechDicts folder and are named `name.dic`.
# If your add-on includes custom speech (pronunciation) dictionaries (most will not), fill out this dictionary.
# Each key is the name of the dictionary,
# with keys inside recording the following attributes:
# displayName (name of the speech dictionary shown to users and translatable),
# mandatory (True when always enabled, False when not).
speechDictionaries: SpeechDictionaries = {}
