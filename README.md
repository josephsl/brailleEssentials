# Braille Essentials

* Authors: Joseph Lee

IMPORTANT: this is a fork of BrailleExtender.

This add-on provides essential features for NVDA users relying on braille support. The following features, deriving from Braille Extender, are available:

* Reload two favorite braille displays with shortcuts.
* Automatic review cursor tethering in terminal role like in PuTTY, Powershell, bash, cmd.
* Auto scroll.
* Switch between several input/output braille tables.
* Mark the text with special attributes through dot 7, dot 8 or both.
* Use two output braille tables simultaneously.
* Display tab signs as spaces.
* Reverse forward scroll and back scroll buttons.
* Say the current line during text scrolling either in review mode, or in focus mode or both.
* Translate text easily in Unicode braille and vice versa. E.g.: z <\--> ⠵.
* Convert cell description to Unicode braille and vice versa. E.g.: 123 <\--> ⠇.
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

* Offer complete gesture maps including function keys, multimedia keys, quick navigation, etc.;
* Emulate modifier keys, and thus any keyboard shortcut;
* Offer several keyboard configurations concerning the possibility to input dots 7 and 8, enter and backspace;
* Add actions and quick navigation through a rotor.

For a list of changes made between each add-on releases, refer to [changelogs for add-on releases][1] document.

## Features overview

### Speech History Mode

This mode allows you to review the recent announcements spoken by NVDA. To enable this mode, use NVDA+Control+t command or equivalent gestures on your braille displays (like ⡞+space). In this mode, you can use:

* The first routing cursor to copy the current announcement to the Clipboard.
* The last routing cursor to show the current announcement in a browseable message.
* Other routing cursors to navigate through history entries.

Please note that specific settings are available for this feature under the "Speech History Mode" settings category.

### Undefined character representation

The add-on allows you to customize how an undefined character should be
represented within a braille table. To do so, go to the — Representation of
undefined characters — settings. You can choose between the following
representations:

* Use braille table behavior (no description possible)
* Dots 1-8 (⣿)
* Dots 1-6 (⠿)
* Empty cell (⠀)
* Other dot pattern (e.g.: 6-123456)
* Question mark (depending on output table)
* Other sign/pattern (e.g.: ??)
* Hexadecimal
* Hexadecimal, HUC8
* Hexadecimal, HUC6
* Decimal
* Octal
* Binary

You can also combine this option with the “describe the character if possible” setting.

Notes:

* To distinguish the undefined set of characters while maximizing space, the best combination is the usage of the HUC8 representation without checking the “Show punctuation/symbol name for undefined characters if available” option.
* To learn more about the HUC (Hexadecimal Unicode characters) representation, see <https://danielmayr.at/huc/>
* Keep in mind that definitions in tables and those in your table dictionaries take precedence over character descriptions, which also take precedence over the chosen representation for undefined characters.

### Getting Current Character Info

This feature allows you to obtain various information regarding the character under the cursor using the current input braille table, such as: the HUC8 and HUC6 representations; the hexadecimal, decimal, octal or binary values; A description of the character if possible; the Unicode braille representation and the braille pattern dots.

Pressing the defined gesture associated to this function once shows you the information in a flash message and a double-press displays the same information in a virtual NVDA buffer. On supported displays the defined gesture is ⡉+space. No system gestures are defined by default.

For example, for the '.' character, you will get the following information:

>
>     .: 0x2e, 46, 0o56, 0b101110
>     dot (FULL STOP [Po])
>     ⠲ (256)
>     ⣥⣺⢃, ⠿⠺⠏⠔

### Advanced braille input

This feature allows you to enter any character from its HUC8 representation or its hexadecimal/decimal/octal/binary value. Moreover, it allows you to develop abbreviations. To use this function, enter the advanced input mode and then enter the desired pattern. Default gestures: NVDA+Windows+i or ⡊+space (on supported displays). Press the same gesture to exit this mode. Alternatively, an option allows you to automatically exit this mode after entering a single pattern.

If you want to enter a character from its HUC8 representation, simply enter the HUC8 pattern. Since a HUC8 sequence must fit on 3 or 4 cells, the interpretation will be performed each time 3 or 4 dot combinations are entered. If you wish to enter a character from its hexadecimal, decimal, octal or binary value, do the following:

1. Enter ⠼
2. Specify the basis as follows:
	* ⠭ or ⠓: for a hexadecimal value
	* ⠙: for a decimal value
	* ⠕: for an octal value
	* ⠃: for a binary value
3. Enter the value of the character according to the previously selected basis.
4. Press Space to validate.

For abbreviations, you must first add them in the dialog box — Advanced input mode dictionary —. Then, you just have to enter your abbreviation and press space to expand it. For example, you can define the following abbreviations: "⠎⠺" with "sandwich", "⠋⠛⠋⠗" to "🇫🇷".

Here are some examples of sequences to be entered for given characters:

Character| HUC8| Hexadecimal| Decimal| Octal| Binary  
---|---|---|---|---|---  
👍 (thumbs up)| ⣭⢤⡙| ⠭1f44d or ⠓1f44d| ⠙128077| ⠕372115| ⠃11111010001001101  
😀 (grinning face)| ⣭⡤⣺| ⠭1f600 or ⠓1f600| ⠙128512| ⠕373000| ⠃11111011000000000  
🍑 (peach)| ⣭⠤⠕| ⠭1f351 or ⠓1f351| ⠙127825| ⠕371521| ⠃11111001101010001  
🌊 (water wave)| ⣭⠤⠺| ⠭1f30a or ⠓1f30a| ⠙127754| ⠕371412| ⠃11111001100001010  

Note: the HUC6 input is currently not supported.

### One-hand mode

This feature allows you to compose a cell in several steps. This can be activated in the general settings of the extension's preferences or on the fly using NVDA+Windows+h gesture by default (⡂+space on supported displays). Three input methods are available.

#### Method 1: fill a cell in 2 stages on both sides

With this method, type the left side dots, then the right side dots. If one side is empty, type the dots correspondig to the opposite side twice, or type the dots corresponding to the non-empty side in 2 steps. For example:

* For ⠛: press dots 1-2 then dots 4-5.
* For ⠃: press dots 1-2 then dots 1-2, or dot 1 then dot 2.
* For ⠘: press 4-5 then 4-5, or dot 4 then dot 5.

#### Method 2: fill a cell in two stages on one side (Space = empty side)

Using this method, you can compose a cell with one hand, regardless of which side of the Braille keyboard you choose. The first step allows you to enter dots 1-2-3-7 and the second one 4-5-6-8. If one side is empty, press space. An empty cell will be obtained by pressing the space key twice. For example:

* For ⠛: press dots 1-2 then dots 1-2, or dots 4-5 then dots 4-5.
* For ⠃: press dots 1-2 then space, or 4-5 then space.
* For ⠘: press space then 1-2, or space then dots 4-5.

#### Method 3: fill a cell dots by dots (each dot is a toggle, press Space to validate the character)

In this mode, each dot is a toggle. You must press the space key as soon as the cell you have entered is the desired one to input the character. Thus, the more dots are contained in the cell, the more ways you have to enter the character. For example, for ⠛, you can compose the cell in the following ways:

* Dots 1-2, then dots 4-5, then space.
* Dots 1-2-3, then dot 3 (to correct), then dots 4-5, then space.
* Dot 1, then dots 2-4-5, then space.
* Dots 1-2-4, then dot 5, then space.
* Dot 2, then dot 1, then dot 5, then dot 4, and then space.

And so on.

[1]: https://github.com/josephsl/brailleEssentials/blob/main/changes.md
