# Unterstützung für "Punktum"

import api
import braille
import globalCommands
import globalPluginHandler
import threading

def setCursorAndClick(routingIndex):
	braille.handler.routeTo(routingIndex)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def script_braille_routeTo(self, gesture):
		routingIndex = gesture.routingIndex
		region = braille.handler.mainBuffer
		cursorIndex = region.cursorPos
		braille.handler.routeTo(routingIndex)
		if cursorIndex != routingIndex:
			fg = api.getForegroundObject()
			FormClassName = fg.windowClassName
			obj = api.getFocusObject()
			MemoClassName = obj.windowClassName
			if FormClassName == "TAT_Text_Dlg" and MemoClassName == "TMemo":
				Timer = threading.Timer(0.050, setCursorAndClick, args=(routingIndex, ))
				Timer.start()

globalCommands.GlobalCommands.script_braille_routeTo = GlobalPlugin().script_braille_routeTo
