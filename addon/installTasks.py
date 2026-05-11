# installTasks.py for Braille Essentials add-on which is a fork of BrailleExtender
# Makes sure Braille Essentials replaces or disables Braille Extender if it is installed so there is no conflict between them
# Copies Braille Extender's old configuration directory for Braille Essentials to use if necessary (forking leftovers needing migration)
# And, prevents Braille Essentials from being installed on older NVDA versions since we will be removing older patch support and switching to new API
#
# Copyright (C) 2026 by Dalen Bernaca, under GPL

from os import path
from versionInfo import version_year, version_major, version_minor
from logHandler import log
import addonHandler
import globalVars
import shutil
import wx

def getAddonByName (name):
	"""
	Returns addon object for requested add-on if present, None otherwise.
	It does not return the object for currently installing add-on, only installed add-ons are matched.
	"""
	this = addonHandler.getCodeAddon()
	try:
		return next(addonHandler.getAvailableAddons(
			filterFunc=lambda a:id(a)!=id(this) and a.name==name))
	except StopIteration:
		pass

# Get both addons if possible
brailleExtender   = getAddonByName("BrailleExtender")
brailleEssentials = getAddonByName("brailleEssentials")

def fixConfig ():
	"""
	This function makes sure all previous configuration mismatches
	caused by transition to a new fork are rectified.
	"""
	# Find whether previous brailleEssentials add-on was installed
	if brailleEssentials is None:
		# No previous installs, and this version has config fixed.
		# If BrailleExtender was installed in the past and then removed
		# it probably left its config behind, but we do not know
		# exactly when was it and whether all of it would be compatible with the forked version
		# If brailleEssentials was installed and removed, we cannot tell whose config was left on the disk
		# We may decide to offer user to accept the risk?!
		# But perhaps best just not to do the transfer for now.
		return
	# We check if we have older brailleEssentials and we find old config files
	installedVersion  = tuple(map(int, brailleEssentials.version.split(".")))
	installedVersion += (3-len(installedVersion))*(0,)
	if installedVersion > (26, 5, 1):
		# Config transfer is not necessary
		return
	oldConfigPath = path.join(globalVars.appArgs.configPath, "brailleExtender")
	if not path.isdir(oldConfigPath):
		# No old config, we are free!
		return
	# We need to copy it
	newConfigPath = path.join(globalVars.appArgs.configPath, brailleEssentials.name)
	# But first, let see whether someone played with brailleEssentials installs before
	if path.isdir(newConfigPath):
		# Do not go trumpling over it
		return
	# Everything clear. We have older brailleEssentials installed and config in brailleExtender directory
	# so, copy it into brailleEssentials directory, if possible
	log.info("Migrating old configuration...")
	try:
		shutil.copytree(oldConfigPath, newConfigPath)
		# If brailleExtender is not installed, then we can safely remove the old config directory
		if brailleExtender is None:
			shutil.rmtree(oldConfigPath, ignore_errors=True)
		log.info("Done!")
	except Exception as e:
		# If Windows weirdness prevents the action, just ignore it and don't bother the user
		log.info("Migration failed because of: %s" % str(e))

def onInstall ():
	if (version_year, version_major, version_minor) < (2025, 3, 3):
		# No incompatibility overrides for us
		# Applicable if attempting to install manually on older NVDA releases
		wx.MessageBox("We are sorry, but Braille Essentials add-on requires NVDA 2025.3.3 or newer.\nThe add-on will not be installed.\nYou can use original Braille Extender add-on instead.", "Installation Prevented", wx.ICON_ERROR|wx.OK|wx.CENTRE)
		raise RuntimeError("This add-on cannot be installed on this NVDA version")
	log.info("Braille Essentials add-on installation started")
	# try to fix config if necessary
	fixConfig()
	# Ensure no conflict with brailleExtender
	if brailleExtender is None:
		log.info("Installation prepared, awaiting restart...")
		return
	if brailleExtender.isEnabled or brailleExtender.isPendingEnable:
		message = "Braille Extender is present and enabled on this instance of NVDA.\nTo avoid conflicts, Braille Extender will be disabled.\nWe strongly recommend that you remove it to avoid any possible conflicts in the future."
	else:
		message = "Braille Extender add-on is installed on this instance of NVDA.\nIt is currently disabled and thus will not interfere with Braille Essentials.\nNevertheless, we strongly recommend that you remove it to avoid any possible conflicts in the future."
	brailleExtender.enable(False)
	wx.MessageBox(message, "Braille Extender Warning", wx.ICON_WARNING|wx.OK|wx.CENTRE)
	log.info("Installation prepared, awaiting restart...")
