
from PMS import Plugin
from PMS.Objects import *
from PMS.Shortcuts import *
import os
	
####################################################################################################

APPLICATIONS_PREFIX = "/applications/Airfoil"
NAME = "Airfoil"

ART		   = 'Airfoil.png'
ICON		  = 'Airfoil.png'


####################################################################################################

def Start():

	Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, ApplicationsMainMenu, L('ApplicationsTitle'), ART, ICON)
        Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)

def GetLocalhostSpeakerName():
	buffer = execShellCommand("defaults read com.rogueamoeba.AirfoilSpeakers serverName")
	if buffer.find("does not exist") != -1:
		return execShellCommand("hostname").replace(".local", "")
	return buffer

def toArray(arrayStr):
	return arrayStr.split(", ")	
	
def SetAudioSource():
	execAppleScript("""on setAudioSource()""", """tell application "Airfoil\"""", """set pathToApp to (POSIX path of (path to application "Plex"))""", """set newSource to make new application source""", """set application file of newSource to pathToApp""", """set current audio source to newSource""", """end tell""", """end setAudioSource""", """""", """try""", """tell application "Airfoil\"""", """""", """if name of current audio source is not equal to "Plex" then""", """setAudioSource()""", """end if""", """""", """end tell""", """on error""", """setAudioSource()""", """end try""")


def GetSpeakers():
	applescript = """tell application "Airfoil" to return id of every speaker"""
	return toArray(execAppleScript(applescript))

def GetSpeakerName(speakerID):
	applescript = """tell application "Airfoil" to return name of every speaker whose id is \"""" + speakerID + """\""""
	return execAppleScript(applescript)

def GetSpeakerStatus(speakerID):
	applescript = """tell application "Airfoil" to return connected of every speaker whose id is \"""" + speakerID + """\""""
	return execAppleScript(applescript) == "true"

def ConnectToSpeaker(speakerID):
	applescript = """tell application "Airfoil" to connect to every speaker whose id is \"""" + speakerID + """\""""
	execAppleScript(applescript)

def DisconnectFromSpeaker(speakerID):
	applescript = """tell application "Airfoil" to disconnect from every speaker whose id is \"""" + speakerID + """\""""
	execAppleScript(applescript)

def execShellCommand(cmd):
	f = os.popen(cmd)
	output = f.readlines()
	if len(output) > 0:
		result = output[0].replace("\n", "")
		return result
	return ""

def execAppleScript(*applescripts):	
	cmd = "osascript"
	for applescript in applescripts:
		cmd += " -e '" +  applescript + "'"
	return execShellCommand(cmd)
	
def GetApplicationVersion(application):
	applescript = """tell application \"""" + application + """\" to return version"""
	return 	execAppleScript(applescript)

def IsApplicationExists(applicationID):
	return execAppleScript("""tell application "Finder\"""", "try", """exists application file id \"""" + applicationID + """\"""", "true", "on error", "false", "end try", "end tell") == "true"

def IsAirfoilSpeakersRunning():
	applescript = """tell application "System Events" to count (every process whose name is "Airfoil Speakers")"""
	return execAppleScript(applescript) == "1"
	
def QuitArfoiSpeakers():
	applescript = """tell application "Airfoil Speakers" to quit"""
	execAppleScript(applescript)

def LaunchAirfoilSpeakers():
	applescript = """tell application "Airfoil Speakers" to run"""
	execAppleScript(applescript)

def AddErrorItem(dir, title, error, image):
	item = DirectoryItem(
		ErrorCallback,
		title,
		description=error,
		thumb=image,
		art=R(ART)
	)
	dir.Append(Function(item, error=error))

def ApplicationsMainMenu():
	SetAudioSource()
	dir = MediaContainer(noCache=True, replaceParent=True)
	hasAirfoilSpeakers = IsApplicationExists("com.rogueamoeba.AirfoilSpeakers")
	if hasAirfoilSpeakers:
		if GetApplicationVersion("Airfoil Speakers") < "3.5.0":
			AddErrorItem(dir, L("Airfoil_Speakers_Error"), L("Airfoil_Speakers_Version_Error"), R("AirfoilSpeakers-error.png"))
		else:
			if IsAirfoilSpeakersRunning():
				status = " (" + L("Running") + ")"
				image = R("AirfoilSpeakers.png")
			else:
				status = " (" + L("Not_Running") + ")"
				image = R("AirfoilSpeakers-disabled.png")

			item = PopupDirectoryItem(
				AirfoilSPeakersCallback,
				"Airfoil Speakers"+status,
				thumb=image	,
				art=R(ART)
			)
			dir.Append(Function(item))
	
	hasAirfoil = IsApplicationExists("com.rogueamoeba.Airfoil")
	if hasAirfoilSpeakers:
		if GetApplicationVersion("Airfoil") < "3.5.0":
			AddErrorItem(dir, L("Airfoil_Error"), L("Airfoil_Version_Error"), R("Airfoil-error.png"))
		else:
			localSpeakerName = execShellCommand("hostname").replace(".local", "")
			Speakers = GetSpeakers()	
			for speakerId in Speakers:

				if speakerId == "com.rogueamoeba.airfoil.LocalSpeaker":
					# This is the local speaker => instead of computer, airfoil speaker name is set
					name = localSpeakerName
				else:
					name = GetSpeakerName(speakerId)
					if name == "" or name == localSpeakerName:
						# this is a remote speaker running on this computer (skip it)
						continue

				if GetSpeakerStatus(speakerId):
					status = " ("+L("Connected") + ")"
					image = Resource.ExternalPath(name+".png")
					if not isinstance(image, str):
						image = R("default-speaker.png")
				else:
					status = ""
					image = Resource.ExternalPath(name+"-disabled.png")	
					if not isinstance(image, str):
						image = R("default-speaker-disabled.png")

				item = PopupDirectoryItem(
					SpeakerCallback,
					name+status,
					subtitle="",
					summary="",
					thumb=image	,
					art=R(ART)
				)
				dir.Append(Function(item, speakerId = speakerId))
			
	if not hasAirfoilSpeakers and not hasAirfoil:
		AddErrorItem(dir, L("No_Airfoil_found"), L("Install_Airfoil_Error"), R("Airfoil-error.png"))
	return dir


def AirfoilSPeakersCallback(sender):
	dir = MediaContainer(noHistory=True, replaceParent=True)
	if IsAirfoilSpeakersRunning():
		dir.Append(Function(DirectoryItem(QuitAirfoilSpeakersCallback, L("Quit"))))
	else:
		dir.Append(Function(DirectoryItem(LaunchAirfoilSpeakersCallback, L("Launch"))))
	return dir


def SpeakerCallback(sender, speakerId):
	dir = MediaContainer(noHistory=True, replaceParent=True)
	if GetSpeakerStatus(speakerId):
		dir.Append(Function(DirectoryItem(DisconnectCallback, L("Disconnect")), speakerId = speakerId))
	else:
		dir.Append(Function(DirectoryItem(ConnectCallback, L("Connect")), speakerId = speakerId))
	return dir
  

def QuitAirfoilSpeakersCallback(sender):
	QuitArfoiSpeakers()
	return ApplicationsMainMenu()
	
def LaunchAirfoilSpeakersCallback(sender):
	LaunchAirfoilSpeakers()
	return ApplicationsMainMenu()

def DisconnectCallback(sender, speakerId):
	DisconnectFromSpeaker(speakerId)
	return ApplicationsMainMenu()

def ConnectCallback(sender, speakerId):
	ConnectToSpeaker(speakerId)
	return ApplicationsMainMenu()
	
def ErrorCallback(sender, error):
	return MessageContainer(sender.itemTitle, error)

	
