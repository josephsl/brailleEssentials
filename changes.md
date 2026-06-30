# Braille Essentials Changelog

This document lists release changelogs for Braille Essentials add-on.

Note: forked from BrailleExtender in May 2026.

## Version 26.07

* Updated the add-on code to Braille Extender commit 550d652c (2026-06-16), introducing enhanced braille support for Microsoft Excel and localization updates.
* Changes from BrailleExtender:
	* No statement on add-on store based update process in add-on settings/general category (Braille Essentials does not have a self-updating mechanism).

## Version 26.05.4

* Updated the add-on code to be based on BrailleExtender commit adc4dca206f (2026-05-16). This resolves bugs including inability to open input braille table overview screen.
* Changes from BrailleExtender:
	* Removed "user guide" menu item (add-on user guide can be opened from add-on store under help menu item).
	* Some document formatting indicators on braille will resemble NVDA's own braille tags, including strikethrough and list items count in browse mode.
	* The add-on's document formatting settings option labels and order will closely resemble NVDA screen reader's own document formatting settings screen.
	* Strong emphasis braille tag is dots 12478/n/dots 14578.
	* In add-on settings, automatic braille input;output braill table selectionbased on current NVDA language will always be visible.

## Version 26.05.2

* NVDA 2025.3.3 or later is required.
* Removed add-on features, commands, and settings included in NVDA screen reader, including speech interrupt when scrolling on same line (2022.3), announce character when routing braille cursor (2024.4), and say current line while scrolling in (2025.1).
* Document formatting tags are now based on NVDA screen reader tags (⣋tag⣙/dots 1-2-4-7-8, tag, dots 1-4-5-7-8).
* Added an installation message informing that BrailleExtender must be disabled when installing Braille Essentials (these add-ons are incompatible).

## Version 26.05.1

* NVDA will no longer fail to report spelling errors and other font attributes in braille when using NVDA 2026.1.

## Version 26.05

* Initial forked add-on release.
* NVDA 2024.1 or later is required.
* Changes from BrailleExtender:
	* User interface and documentation now refers to "Braille Essentials".
	* Removed add-on version from "Braille Essentials" NVDA menu item.
	* Changed add-on homepage and source URL.
	* Removed add-on update check feature and update channel options (add-on updates done through the add-on store).
	* Remove "website" menu item (add-on website can be opened from add-on store).
	* Remove "translation pot file" menu item (no replacement).
