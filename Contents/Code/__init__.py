# -*- coding: utf-8 -*-
#
#
#
# NOTES:
#   1. Info.plist:  <PlexPluginCodePolicy> currently set to "Elevated"
#      ==> This plugin queries the metadata from the PMS server.
#          This gives a permission denied unless the security is set to "Elevated"
#
# TODO:
#   1. Write nicely formatted xml files.
#        Currently using: lxml.etree.ElementTree(<element>).write(<filename>, pretty_print = True)
#        but outcome is not exactly what I call pretty
#
# FEATURE WISHLIST:
#   Some playlist funtionality ideas:
#       = Keep track of total duration && ratingKey for a playlist
#       = Shuffle mode (also store as setting in the playlist.xml)
#           [DONE] Static: e.g. Populate the track list in a random order when playlist is opened for playback 
#           Dynamic: e.g. Building an URL service for playing the playlist. The service would determine the next track to play
#       = Support Smart playlists, like:
#           a. specify and store one or more search queries in stead of tracks
#           b. play "top <x>" rated songs of each/selected  album/artist
#       = Sort of 'On Deck' functionality for running playlist
#           Requires knowledge of what's happening in the player (e.g. like callbacks when song is done )
#           or maybe replace the standard TrackObject for playing tracks with our own URL service for starting the songs
#       = Create more advanced external tools for managing playlist, 
#
#
# QUESTIONS:
#   1. How to correctly use different ViewGroups?
#   2. How to differentiate for different users?
#   3. How to set the correct album art per track in the list (is that even possible)?
#
#

#######################################################################################################################
# URL's for managing playlist
#
#[PMS-IP:PMS-PORT]/music/playlists/playlists
#[PMS-IP:PMS-PORT]/music/playlists/playlists/list?key=<playlist key>
#
#[PMS-IP:PMS-PORT]/music/playlists/playlists/create?title=<title>&pltype=<SIMPLE|SMART>&description=<description>
#[PMS-IP:PMS-PORT]/music/playlists/playlists/delete?key=<playlist key>
#[PMS-IP:PMS-PORT]/music/playlists/playlists/rename?key=<playlist key>&newname=<new name>
#
#[PMS-IP:PMS-PORT]/music/playlists/tracks/add?playlistkey=<playlist key>&key=<track key>
#[PMS-IP:PMS-PORT]/music/playlists/tracks/remove?playlistkey=<playlist key>&key=<track key>
#[PMS-IP:PMS-PORT]/music/playlists/tracks/move?playlistkey=<playlist key>&key=<track key>&to=<new position>
#######################################################################################################################


import json
import os
from lxml import etree
from random import shuffle
#Not using objectify for now: Using SubElement requires version 3.2 of lxml
#from lxml import objectify

NAME = 'Playlists'
PREFIX = '/music/playlists'
PLUGIN_DIR = 'com.plexapp.plugins.playlist'
LIBRARY_SECTIONS = '/library/sections/'
URL_MUSIC_PLAYLIST = 'http://com.plexapp.plugins.playlist/track'
ART = 'art-default.png'
ICON = 'icon-default.png'

# File version
CURRENT_VERSION_ALL = "1"
CURRENT_VERSION_SINGLE = "1"

# Preferences
PREFS__USERNAME = 'username'
PREFS__PLEXIP = 'plexip'
PREFS__PLEXPORT = 'plexport'
PREFS__CONFIRM_DELETE_PL = 'confirm_delete_playlist'
PREFS__CONFIRM_REMOVE_TR = 'confirm_remove_track'
PREFS__USE_ONDECK = 'use_ondeck'
PREFS__ONDECK_PLAYED = 'time_ondeck'

DICT_KEY_PLAYING = 'playing'
DICT_PLAYING_KEY = 'key'
DICT_PLAYING_EXPIRE = 'expire'
DICT_PLAYING_KEY_EXPIRED = 'keyexpired'

#Request Header
REQUEST_HEADER_CLIENTID = 'X-Plex-Client-Identifier'
# Client / User information
CLIENT_UNKNOWN = 'Unknown'
CLIENT_USER_LIST = 'client_user_list'
DICT_KEY_CLIENT_LIST = CLIENT_USER_LIST

# XML 
PLAYLIST_ALL_ROOT = 'playlists'
PLAYLIST_ROOT = 'playlist'

# XML Attribute names
ATTR_VERSION = 'version'
ATTR_KEY = 'key'
ATTR_TITLE = 'title'
ATTR_RATINGKEY = 'ratingKey'
ATTR_DURATION = 'duration'
ATTR_THUMB = 'thumb'
ATTR_ART = 'art'
ATTR_PARTKEY = 'partkey'
ATTR_BITRATE = 'bitrate'
ATTR_AUDIOCHANNELS = 'audioChannels'
ATTR_AUDIOCODEC = 'audioCodec'
ATTR_CONTAINER = 'container'
ATTR_VIEWGROUP = 'viewGroup'
ATTR_SEARCH = 'search'
ATTR_PROMPT = 'prompt'
ATTR_PLTYPE = 'playlisttype'
ATTR_DESCR = 'description'
ATTR_PMS_URL = 'pmsurl'

# Create new playlist / maintenance
NEW_PL_TITLE = 'title'
NEW_PL_DESCRIPTION = 'description'
NEW_PL_TYPE = 'playlist_type'
PL_TYPE_SIMPLE = 'SIMPLE'
PL_TYPE_SMART = 'SMART'
PL_TYPES = [PL_TYPE_SIMPLE, PL_TYPE_SMART]
PL_MODE_PLAY = 'play'
PL_MODE_PLAY_SHUFFLE = 'playshuffle'
PL_MODE_PLAY_ONDECK = 'ondeck'
PL_MODE_DELETE = 'delete'
PL_MODE_MOVE = 'move'
PL_MODE_ASK = 'maintain'
CANCEL_MODE_DELETE_PL = 'delete_playlist'
CANCEL_MODE_REMOVE_TR = 'remove_track'
CANCEL_MODE_EDIT_PLAYLIST = 'edit_playlist'
CANCEL_MODE_ASK_ACTION = 'ask_action'
FILE_SUFFIX_ONDECK = '[On deck]'
FILE_SUFFIX_STARTED = '[Started]'

FILE_ALLPLAYLIST_SUFFIX = '_allPlaylists.xml'

# Track XPath
PL_XPATH_PLAYLIST = '/playlists/playlist'
PL_XPATH_TRACK = '/playlist/Track'
PMS_XPATH_DIRECTORY = '//Directory'
PMS_XPATH_TRACK = '//Track'
PMS_XPATH_MEDIA = '//Media'
PMS_XPATH_PART = '//Part'


# Resource stings
TEXT_MAIN_TITLE = "MAIN_TITLE"
TEXT_PREFERENCES = "PREFERENCES"

TEXT_MENU_ACTION_PLAYLIST_MAINTENANCE = "MENU_ACTION_PLAYLIST_MAINTENANCE"
TEXT_MENU_ACTION_CREATE_PLAYLIST = "MENU_ACTION_CREATE_PLAYLIST"
TEXT_MENU_ACTION_ADD_TRACKS = "MENU_ACTION_ADD_TRACKS"
TEXT_MENU_ACTION_REMOVE_TRACKS = "MENU_ACTION_REMOVE_TRACKS"
TEXT_MENU_ACTION_REMOVE_TRACK = "MENU_ACTION_REMOVE_TRACK"
TEXT_MENU_ACTION_MOVE_TRACK = "MENU_ACTION_MOVE_TRACK"
TEXT_MENU_ACTION_DELETE_PLAYLIST = "MENU_ACTION_DELETE_PLAYLIST"
TEXT_MENU_ACTION_EDIT_PLAYLIST = "MENU_ACTION_EDIT_PLAYLIST"
TEXT_MENU_ACTION_RENAME_PLAYLIST = "MENU_ACTION_RENAME_PLAYLIST"
TEXT_MENU_ACTION_SET_CLIENT_USER = "MENU_ACTION_SET_CLIENT_USER"
TEXT_MENU_SET_CLIENT_USER_PROMPT = "MENU_SET_CLIENT_USER_PROMPT"
TEXT_MENU_ACTION_PLAY_MODE_NORMAL ="MENU_ACTION_PLAY_MODE_NORMAL"
TEXT_MENU_ACTION_PLAY_MODE_SHUFFLED = "MENU_ACTION_PLAY_MODE_SHUFFLED"
TEXT_MENU_ACTION_PLAY_MODE_ONDECK = "MENU_ACTION_PLAY_MODE_ONDECK"
TEXT_MENU_ACTION_EDIT_MODE_REMOVE = "MENU_ACTION_EDIT_MODE_REMOVE"
TEXT_MENU_ACTION_EDIT_MODE_MOVE = "MENU_ACTION_EDIT_MODE_MOVE"
TEXT_MENU_ACTION_EDIT_MODE_ASK = "MENU_ACTION_EDIT_MODE_ASK"
TEXT_MENU_TITLE_SET_CLIENT_USER = "MENU_TITLE_SET_CLIENT_USER"
TEXT_MENU_TITLE_TRACK_ACTIONS = "MENU_TITLE_TRACK_ACTIONS"
TEXT_MENU_TITLE_TRACK_REMOVE = "MENU_TITLE_TRACK_REMOVE"
TEXT_MENU_TITLE_TRACK_MOVE = "MENU_TITLE_TRACK_MOVE"
TEXT_MENU_TITLE_TRACK_ASK = "MENU_TITLE_TRACK_ASK"
TEXT_MENU_TITLE_EDIT_ASK = "MENU_TITLE_EDIT_ASK"
TEXT_MENU_EDITPL_MOVE_PROMPT = "MENU_EDITPL_MOVE_PROMPT"

TEXT_MENU_CREATEPL_ENTER_TITLE = "MENU_CREATEPL_ENTER_TITLE"
TEXT_MENU_CREATEPL_ENTER_DESCR = "MENU_CREATEPL_ENTER_DESCR"
TEXT_MENU_CREATEPL_SELECT_TYPE = "MENU_CREATEPL_SELECT_TYPE"
TEXT_MENU_CREATEPL_ENTER_TITLE_PROMPT = "MENU_CREATEPL_ENTER_TITLE_PROMPT"
TEXT_MENU_CREATEPL_ENTER_DESCR_PROMPT = "MENU_CREATEPL_ENTER_DESCR_PROMPT"
TEXT_MENU_CREATEPL_SELECT_TYPE_PROMPT = "MENU_CREATEPL_SELECT_TYPE_PROMPT"
TEXT_MENU_CREATEPL_CREATE_LIST = "MENU_CREATEPL_CREATE_LIST"
TEXT_MENU_RENAMEPL_PROMPT = "MENU_RENAMEPL_PROMPT"

TEXT_TITLE_ADD_TO_PLAYLIST = "TITLE_ADD_TO_PLAYLIST"
TEXT_TITLE_CONFIRM_DELETE = "TITLE_CONFIRM_DELETE"
TEXT_TITLE_DELETE_CANCELED = "TITLE_DELETE_CANCELED"
TEXT_TITLE_ACTION_CANCELED = "TITLE_ACTION_CANCELED"
TEXT_TITLE_CANCEL = "TITLE_CANCEL"
TEXT_TITLE_SELECT_PLAYMODE = "TITLE_SELECT_PLAYMODE"
TEXT_TITLE_SELECT_EDITMODE = "TITLE_SELECT_EDITMODE"

TEXT_MSG_EMPTY_PLAYLIST = "MSG_EMPTY_PLAYLIST"
TEXT_MSG_TRACK_ALREADY_IN_PLAYLIST = "MSG_TRACK_ALREADY_IN_PLAYLIST"
TEXT_MSG_TRACK_ADDED_TO_PLAYLIST = "MSG_TRACK_ADDED_TO_PLAYLIST"
TEXT_MSG_TRACK_REMOVED_FROM_PLAYLIST = "MSG_TRACK_REMOVED_FROM_PLAYLIST"
TEXT_MSG_TRACK_MOVED_TO = "MSG_TRACK_MOVED_TO"
TEXT_MSG_TRACK_NOT_MOVED = "MSG_TRACK_NOT_MOVED"
TEXT_MSG_PLAYLIST_CREATED = "MSG_PLAYLIST_CREATED"
TEXT_MSG_PLAYLIST_RENAMED = "MSG_PLAYLIST_RENAMED"
TEXT_MSG_PLAYLIST_DELETED = "MSG_PLAYLIST_DELETED"

TEXT_ERROR_NO_METADATA = "ERROR_NO_METADATA"
TEXT_ERROR_NO_TRACK_FOUND = "ERROR_NO_TRACK_FOUND"
TEXT_ERROR_NO_MEDIA_FOR_TRACK = "ERROR_NO_MEDIA_FOR_TRACK"
TEXT_ERROR_NO_TRACK_DATA = "ERROR_NO_TRACK_DATA"
TEXT_ERROR_TRACK_NOT_ADDED = "ERROR_TRACK_NOT_ADDED"
TEXT_ERROR_PLAYLIST_EXISTS = "ERROR_PLAYLIST_EXISTS"
TEXT_ERROR_MISSING_TITLE = "ERROR_MISSING_TITLE"
TEXT_ERROR_EMPTY_SEARCH_QUERY = "ERROR_EMPTY_SEARCH_QUERY"
TEXT_ERROR_NO_FREE_KEYS = "ERROR_NO_FREE_KEYS"

####################################################################################################
def Start():
    
    Plugin.AddPrefixHandler(PREFIX, MainMenu, NAME)
    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
    Plugin.AddViewGroup('Maintenance', viewMode='List', mediaType='items')

    ObjectContainer.title1 = L(TEXT_MAIN_TITLE)
    ObjectContainer.view_group = 'List'
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)    
    
    Dict.Reset()
    LoadGlobalUsers()
    
    global expireThreadRunning
    expireThreadRunning = False


####################################################################################################
def ValidatePrefs():
    try:
        played_percent = int(Prefs[PREFS__ONDECK_PLAYED])
        if played_percent < 0 or played_percent > 100:
            return showMessage("Percentage between 0 and 100 requied")
    except Exception:
        return showMessage("Remove from 'On deck' must be a number")
    pass 

  
####################################################################################################
#@handler(PREFIX, NAME)
def MainMenu():   
    oc = ObjectContainer(no_cache = True)
    oc.title1 = L(TEXT_MAIN_TITLE) + '[%s]' % getUser()
        
    allPlaylists = LoadGlobalPlaylists()
    for playlistkey in allPlaylists.keys():
        listtitle = playlistTitle(playlist_dict = allPlaylists[playlistkey], include_duration = True)
        oc.add(PopupDirectoryObject(key = Callback(OpenPlaylistMenu, title = listtitle, playlistkey = playlistkey),
                                    title = listtitle))
      
    oc.add(DirectoryObject(key = Callback(MaintenanceMenu, title = L(TEXT_MENU_ACTION_PLAYLIST_MAINTENANCE)), title = L(TEXT_MENU_ACTION_PLAYLIST_MAINTENANCE)))  

    oc.add(PrefsObject(title = L(TEXT_PREFERENCES)))

    return oc


####################################################################################################
## Playlists
####################################################################################################


#@route(PREFIX +'/openplaylistoption')
def OpenPlaylistMenu(title, playlistkey):
    oc = ObjectContainer(title1 = L(TEXT_TITLE_SELECT_PLAYMODE), no_cache = True, no_history = True)

    oc.add(DirectoryObject(key = Callback(PlaylistMenu, title = title, playlistkey = playlistkey, mode = PL_MODE_PLAY),
                           title = L(TEXT_MENU_ACTION_PLAY_MODE_NORMAL)))    

    oc.add(DirectoryObject(key = Callback(PlaylistMenu, title = title, playlistkey = playlistkey, mode = PL_MODE_PLAY_SHUFFLE),
                           title = L(TEXT_MENU_ACTION_PLAY_MODE_SHUFFLED)))

    if Prefs[PREFS__USE_ONDECK] == True:
        full_filename = GetPlaylistFileName(playlistkey = playlistkey, suffix = FILE_SUFFIX_ONDECK)
        if os.path.isfile(full_filename):
            oc.add(DirectoryObject(key = Callback(PlaylistMenu, title = title, playlistkey = playlistkey, mode = PL_MODE_PLAY_ONDECK),
                                   title = L(TEXT_MENU_ACTION_PLAY_MODE_ONDECK)))
    return oc    


#@route(PREFIX +'/playlistmenu')
def PlaylistMenu(title, playlistkey, mode):
    oc = ObjectContainer(title2 = title, view_group='List', art = R('icon-default.png'),                         
                         no_cache = True)
    oc.content = ContainerContent.Tracks
    
    # load the playlist
    # This is an: etree.Element XML Element 
    pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
    suffix = ""
    if mode == PL_MODE_PLAY_ONDECK:
        suffix = FILE_SUFFIX_ONDECK
    playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False, suffix = suffix)
    if playlist != None:
        tracks = playlist.xpath(PL_XPATH_TRACK)
        # Load shuffled
        if len(tracks) > 1 and mode == PL_MODE_PLAY_SHUFFLE:
            shuffle(tracks)
        track_nr = 0
        for track in tracks:
            track_nr += 1
            oc.add(createTrackObject(track = track, index = track_nr, pms_url = pms_url, playlistkey = playlistkey))
        if Prefs[PREFS__USE_ONDECK] == True:
            if mode != PL_MODE_PLAY_ONDECK:
                SaveSinglePlaylist(playlistkey = playlistkey, playlist = playlist, suffix = FILE_SUFFIX_STARTED)
            else:
                DeleteSinglePlaylist(playlistkey = playlistkey, suffix = FILE_SUFFIX_STARTED)
        return oc
                    
    return showMessage(message_text = L(TEXT_MSG_EMPTY_PLAYLIST) )


def createTrackObjectURL(track, index, pms_url, playlistkey):
    title = trackTitle(title = track.get(ATTR_TITLE), index = index)
    key = track.get(ATTR_KEY)
    url = URL_MUSIC_PLAYLIST + '?playlistkey=%s&trackkey=%s' % (playlistkey, key)
    trackObject = TrackObject(url = url,
                              title = title,
                              duration = attributeAsInt(track.get(ATTR_DURATION))
                              )
    if track.get(ATTR_THUMB) != None:
        trackObject.thumb = pms_url + track.get(ATTR_THUMB)
    return trackObject


def createTrackObject(track, index, pms_url, playlistkey):
    title = trackTitle(title = track.get(ATTR_TITLE), index = index)
    key = track.get(ATTR_KEY)
    ratingKey = track.get(ATTR_RATINGKEY)
    if track.get(ATTR_PMS_URL) != None:
        pms_url = track.get(ATTR_PMS_URL)
    trackObject = TrackObject(title = title, key = pms_url + key, rating_key = ratingKey)
    trackObject.duration = attributeAsInt(track.get(ATTR_DURATION))
    #if track.get('art') != None:
    #    to.art = track.get('art')
    if track.get(ATTR_THUMB) != None:
        trackObject.thumb = pms_url + track.get(ATTR_THUMB)
    partkey = track.get(ATTR_PARTKEY)    
    if not partkey.startswith('http'):
        partkey = pms_url + partkey
    if Client.Platform == ClientPlatform.Windows:
        mediaObject = MediaObject( parts = [PartObject(key = partkey)] )
    else:
        mediaObject = MediaObject( parts = [PartObject(key = Callback(playSingleTrack,
                                                                      track_url = partkey,
                                                                      trackkey = key,
                                                                      index = str(index),
                                                                      playlistkey = playlistkey,
                                                                      duration = trackObject.duration))] )
    mediaObject.duration = trackObject.duration
    mediaObject.bitrate = attributeAsInt(track.get(ATTR_BITRATE))
    mediaObject.audio_channels = attributeAsInt(track.get(ATTR_AUDIOCHANNELS))
    if track.get(ATTR_AUDIOCODEC) != None:
        mediaObject.audio_codec = track.get(ATTR_AUDIOCODEC)
    if track.get(ATTR_CONTAINER) != None:
        mediaObject.container = track.get(ATTR_CONTAINER)           
    trackObject.add(mediaObject)
    return trackObject


#@indirect
@route(PREFIX + '/playtrack', duration=int)
def playSingleTrack(track_url, trackkey, index, playlistkey, duration):
    #   For on deck funcionality
    Log.Debug('playSingleTrack: %s' % track_url)
    # Load the current OnDeck file
    if Prefs[PREFS__USE_ONDECK] == True:
        # Check if this is the first new song played
        setPlaying(playlistkey = playlistkey, trackkey = trackkey, duration = duration)
        global expireThreadRunning
        if expireThreadRunning == False:
            expireThreadRunning = True
            Thread.CreateTimer(interval = 10, f = updateOnDeck)
            
    return Redirect(track_url)
    pass


def setPlaying(playlistkey, trackkey, duration):
    user = getUser()
    if user != None and len(user) > 0:        
        playing = Dict[DICT_KEY_PLAYING]
        if playing == None:
            playing = {}
        if user in playing.keys():
            user_playing = playing[user]
        else:
            user_playing = {}
        if playlistkey in user_playing.keys():
            # Check if the current key is already expired 
            now_playing = user_playing[playlistkey]
            if Datetime.Now() >= now_playing[DICT_PLAYING_EXPIRE]:
                if DICT_PLAYING_KEY_EXPIRED in now_playing.keys():
                    expiredkeys = now_playing[DICT_PLAYING_KEY_EXPIRED]
                    expiredkeys.append(now_playing[DICT_PLAYING_KEY])
                else:
                    expiredkeys = [now_playing[DICT_PLAYING_KEY]]                
                now_playing[DICT_PLAYING_KEY_EXPIRED] = expiredkeys
        else:
            now_playing = {}                
        now_playing[DICT_PLAYING_KEY] = trackkey
        # convert duration to seconds
        duration = duration // 1000
        try:
            played_percent = int(Prefs[PREFS__ONDECK_PLAYED])
            if played_percent > 0:
                if played_percent < 100:
                    duration =  (duration * played_percent) // 100
            else:
                duration = 1 
            now_playing[DICT_PLAYING_EXPIRE] = Datetime.Now() + Datetime.Delta(seconds = duration)
            Log.Debug("Create now playing %s " % now_playing[DICT_PLAYING_KEY])
            user_playing[playlistkey] = now_playing
            playing[user] = user_playing
            Dict[DICT_KEY_PLAYING] = playing
            Dict.Save()
        except Exception:
            pass


def updateOnDeck():
    # This is executed as a new Thread.
    # Check if this is the first new song played
    global expireThreadRunning
    anything_playing = False
    playing = Dict[DICT_KEY_PLAYING]
    if playing != None:        
        for user in playing.keys():
            user_playing = playing[user]
            for playlistkey in user_playing.keys():
                now_playing = user_playing[playlistkey]
                    
                # Check for already expired tracks
                if DICT_PLAYING_KEY_EXPIRED in now_playing.keys():
                    expiredkeys = now_playing[DICT_PLAYING_KEY_EXPIRED]
                else:
                    expiredkeys = []
                current_is_expired = Datetime.Now() >= now_playing[DICT_PLAYING_EXPIRE]
                
                if current_is_expired:
                    expiredkeys.append(now_playing[DICT_PLAYING_KEY])
                else:
                    anything_playing = True
                    
                if len(expiredkeys) > 0: 
                    #This song is playing long enough to remove it from the OnDeck                            
                    playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False, suffix = FILE_SUFFIX_STARTED)
                    if playlist == None:
                        # No newly started file present yet, check for existing OnDeck
                        playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False, suffix = FILE_SUFFIX_ONDECK)
                    else:
                        DeleteSinglePlaylist(playlistkey = playlistkey, suffix = FILE_SUFFIX_STARTED)
                    if playlist != None:
                        for key in expiredkeys:                               
                            Log.Debug("Remove key from OnDeck: %s" % key)
                            tracks = playlist.xpath('%s[@key="%s"]' % (PL_XPATH_TRACK, key))
                            for track in tracks:
                                playlist.remove(track)
                        if current_is_expired:
                            del user_playing[playlistkey]
                        else:
                            del now_playing[DICT_PLAYING_KEY_EXPIRED]
                        # Save to OnDeck
                        tracks = playlist.xpath('%s' % PL_XPATH_TRACK)
                        if len(tracks) > 0:
                            SaveSinglePlaylist(playlistkey = playlistkey, playlist = playlist, suffix = FILE_SUFFIX_ONDECK)
                        else:
                            DeleteSinglePlaylist(playlistkey = playlistkey, suffix = FILE_SUFFIX_ONDECK)
                            
            if len(user_playing) == 0:
                del playing[user]
        Dict.Save()
        
    if anything_playing == True:
        Thread.CreateTimer(interval = 10, f = updateOnDeck)
    else:
        expireThreadRunning = False
    pass
        

####################################################################################################
# Playlist maintenance
####################################################################################################

#@route(PREFIX +'/maintenance')
def MaintenanceMenu(title):
    oc = ObjectContainer(title2 = title, view_group='List')

    allPlaylists = LoadGlobalPlaylists()
    newsetting = { NEW_PL_TITLE : 'New playlist', NEW_PL_TYPE : PL_TYPE_SIMPLE, NEW_PL_DESCRIPTION : ''}
    playlists_present = (allPlaylists != None and len(allPlaylists) > 0)
    if playlists_present:
        oc.add(DirectoryObject(key = Callback(BrowseMusicMenu, title = L(TEXT_MENU_ACTION_ADD_TRACKS)), title = L(TEXT_MENU_ACTION_ADD_TRACKS)))  
        oc.add(DirectoryObject(key = Callback(MaintainTracksMenu, title = L(TEXT_MENU_ACTION_EDIT_PLAYLIST)), title = L(TEXT_MENU_ACTION_EDIT_PLAYLIST)))  
        oc.add(DirectoryObject(key = Callback(RenamePlaylistMenu, title = L(TEXT_MENU_ACTION_RENAME_PLAYLIST)), title = L(TEXT_MENU_ACTION_RENAME_PLAYLIST)))
    oc.add(DirectoryObject(key = Callback(CreatePlaylistMenu, settings = newsetting), title = L(TEXT_MENU_ACTION_CREATE_PLAYLIST)))  
    if playlists_present:
        oc.add(DirectoryObject(key = Callback(DeletePlaylistMenu, title = L(TEXT_MENU_ACTION_DELETE_PLAYLIST)), title = L(TEXT_MENU_ACTION_DELETE_PLAYLIST)))
    client_id = getClientIdentifier()
    if client_id != CLIENT_UNKNOWN and client_id != None:
        oc.add(DirectoryObject(key = Callback(SelectUserMenu), title = L(TEXT_MENU_TITLE_SET_CLIENT_USER)))
    
    return oc


#
# Edit playlist
#

#@route(PREFIX +'/maintainplaylist')
def MaintainTracksMenu(title):
    oc = ObjectContainer(title2 = title, no_cache = True, no_history = True)

    allPlaylists = LoadGlobalPlaylists()
    for playlistkey in allPlaylists.keys():
        listtitle = playlistTitle(playlist_dict = allPlaylists[playlistkey], include_duration = True)
        oc.add(PopupDirectoryObject(key = Callback(SelectModeTrackMenu, playlistkey = playlistkey, listtitle = listtitle),
                                    title = listtitle))
    return oc


#@route(PREFIX +'/selecteditmode')
def SelectModeTrackMenu(playlistkey, listtitle):
    oc = ObjectContainer(title1 = L(TEXT_TITLE_SELECT_EDITMODE), no_cache = True, no_history = True)

    oc.add(DirectoryObject(key = Callback(PlaylistEditMenu,
                                          title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_REMOVE, listtitle),
                                          key = playlistkey,
                                          mode = PL_MODE_DELETE,
                                          replace_parent = False),
                           title = L(TEXT_MENU_ACTION_EDIT_MODE_REMOVE)))      

    oc.add(DirectoryObject(key = Callback(PlaylistEditMenu,
                                          title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_MOVE, listtitle),
                                          key = playlistkey,
                                          mode = PL_MODE_MOVE,
                                          replace_parent = False),
                           title = L(TEXT_MENU_ACTION_EDIT_MODE_MOVE)))      

    oc.add(DirectoryObject(key = Callback(PlaylistEditMenu,
                                          title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_ASK, listtitle),
                                          key = playlistkey,
                                          mode = PL_MODE_ASK,
                                          replace_parent = False),
                           title = L(TEXT_MENU_ACTION_EDIT_MODE_ASK)))
    
    oc.add(DirectoryObject(key = Callback(CancelAction, title = '', mode = CANCEL_MODE_EDIT_PLAYLIST),
                           title = L(TEXT_TITLE_CANCEL)))      
    return oc


#@route(PREFIX +'/playlistedit')
def PlaylistEditMenu(title, key, mode, replace_parent = True):
    oc = ObjectContainer(title2 = title, view_group='List', art = R('icon-default.png'),
                         no_cache = True,
                         replace_parent = replace_parent)
    
    # load the playlist
    # This is an: etree.Element XML Element 
    playlist = LoadSinglePlaylist(playlistkey = key)
    if playlist != None:
        track_nr = 0
        tracks = playlist.xpath(PL_XPATH_TRACK)
        for track in tracks:
            track_nr += 1
            oc.add(createMaintainTrackObject(track = track, index = track_nr, playlistkey = key, mode = mode))
        return oc
                    
    return showMessage(message_text = L(TEXT_MSG_EMPTY_PLAYLIST) )


@route(PREFIX +'/createedittrack', index=int)
def createMaintainTrackObject(track, index, playlistkey, mode):
    title = trackTitle(title = track.get(ATTR_TITLE), index = index)
    key = track.get(ATTR_KEY)    
    if mode == PL_MODE_DELETE:
        # Delete tracks from list
        if Prefs[PREFS__CONFIRM_REMOVE_TR] == True:
            return PopupDirectoryObject(key = Callback(ConfirmRemoveTrackMenu, playlistkey = playlistkey, key = key, tracktitle = title),
                                        title = title)
        
        return DirectoryObject(key = Callback(removeFromPlaylist, playlistkey = playlistkey, key = key, tracktitle = title),
                               title = title)
    elif mode == PL_MODE_MOVE:
        return InputDirectoryObject(key = Callback(moveTrack, playlistkey = playlistkey, trackkey = key,
                                                   mode = PL_MODE_MOVE),
                                    title = title,
                                    prompt = L(TEXT_MENU_EDITPL_MOVE_PROMPT))
    elif mode == PL_MODE_ASK:
        # Note: Not using PopuDirectoryObject her, because InputDirectoryObject does not work from within PopuDirectoryObject
        return DirectoryObject(key = Callback(AskActionTrackMenu, playlistkey = playlistkey, key = key, tracktitle = title, trackindex = index),
                               title = title)
    # Should not happen !


#@route(PREFIX +'/confirmremovetrack')
def ConfirmRemoveTrackMenu(playlistkey, key, tracktitle):
    oc = ObjectContainer(title1 = L(TEXT_TITLE_CONFIRM_DELETE), no_cache = True, no_history = True)

    oc.add(DirectoryObject(key = Callback(removeFromPlaylist, playlistkey = playlistkey, key = key,
                                          tracktitle = tracktitle,
                                          mode = PL_MODE_DELETE),
                           title = L(TEXT_MENU_ACTION_REMOVE_TRACK)))
    cancelParams = {'playlistkey' : playlistkey}
    oc.add(DirectoryObject(key = Callback(CancelAction, title = L(TEXT_TITLE_DELETE_CANCELED), mode = CANCEL_MODE_REMOVE_TR, params = cancelParams),
                           title = L(TEXT_TITLE_CANCEL)))      
    return oc


@route(PREFIX +'/askactiontrack', trackindex=int)
def AskActionTrackMenu(playlistkey, key, tracktitle, trackindex):
    oc = ObjectContainer(title1 = L(TEXT_MENU_TITLE_EDIT_ASK), no_cache = True, no_history = True)

    oc.add(DirectoryObject(key = Callback(removeFromPlaylist, playlistkey = playlistkey, key = key,
                                          tracktitle = tracktitle,
                                          mode = PL_MODE_ASK),
                           title = L(TEXT_MENU_ACTION_REMOVE_TRACK)))

    oc.add(InputDirectoryObject(key = Callback(moveTrack, playlistkey = playlistkey, trackkey = key,
                                               mode = PL_MODE_ASK),
                                title = L(TEXT_MENU_ACTION_MOVE_TRACK),
                                prompt = L(TEXT_MENU_EDITPL_MOVE_PROMPT)))    
    
    cancelParams = {'playlistkey' : playlistkey}
    oc.add(DirectoryObject(key = Callback(CancelAction, title = L(TEXT_TITLE_DELETE_CANCELED), mode = CANCEL_MODE_ASK_ACTION, params = cancelParams),
                           title = L(TEXT_TITLE_CANCEL)))      
    return oc


#@route(PREFIX +'/removefromplaylist')
@indirect
def removeFromPlaylist(playlistkey, key, tracktitle, mode):
    Log.Debug('removing track from  playlist')
    playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False)
    if playlist != None:
        tracks = playlist.xpath('%s[@key="%s"]' % (PL_XPATH_TRACK, key))
        for track in tracks:
            if tracktitle == '':
                tracktitle = track.get(ATTR_TITLE)
            playlist.remove(track)
        SaveSinglePlaylist(playlistkey, playlist)
        UpdateGlobalPlaylists(playlistkey = playlistkey, playlist = playlist)
        
        if mode == PL_MODE_ASK:
            # Directly return to the playlist
            return PlaylistEditMenu(title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_ASK,  playlist.get(ATTR_TITLE)),
                                    key = playlistkey,
                                    mode = PL_MODE_ASK)
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_MSG_TRACK_REMOVED_FROM_PLAYLIST, tracktitle))
            
    pass


@indirect
def moveTrack(query, playlistkey, trackkey, mode):
    if query != None and len(query) > 0:
        #try:
        # the query must be a valid integer !
        new_position = int(query)
        if  new_position > 0:
            # Let's Move the track
            playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False)
            if playlist != None:
                # Find the element with given trackkey
                track = playlist.xpath('%s[@key="%s"]' % (PL_XPATH_TRACK, trackkey))[0]
                if track != None:
                    track_parent = track.getparent()
                    trackindex = track_parent.index(track) + 1
                    Log.Debug('moveTrack: Original position = %d' % trackindex)
                    if new_position == trackindex:                        
                        return showMessage(message_text = L(TEXT_MSG_TRACK_NOT_MOVED))                
                    # Insert the element at
                    if new_position < trackindex:
                        new_position = new_position - 1
                    track_parent.insert(new_position, track)
                    SaveSinglePlaylist(playlistkey, playlist)
                    if mode == PL_MODE_ASK:
                        # Directly return to the playlist
                        return PlaylistEditMenu(title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_ASK, playlist.get(ATTR_TITLE)),
                                                key = playlistkey,
                                                mode = PL_MODE_ASK)
                    return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_MSG_TRACK_MOVED_TO, query))
                    
        #except Exception:
        #    Log.Debug('ERROR: moving Track')
                        
    return showMessage(message_text = L(TEXT_MSG_TRACK_NOT_MOVED))


#
# Create playlist
#

@route(PREFIX +'/createplaylistoptions', settings=dict)
def CreatePlaylistMenu(settings):
    oc = ObjectContainer(title2 = L(TEXT_MENU_ACTION_CREATE_PLAYLIST), view_group='List', no_cache = True, no_history = True)    
    oc.add(InputDirectoryObject(key = Callback(CreatePLSetOption, itype = NEW_PL_TITLE, settings = settings),
                                title = Locale.LocalStringWithFormat(TEXT_MENU_CREATEPL_ENTER_TITLE , settings[NEW_PL_TITLE]),
                                prompt = L(TEXT_MENU_CREATEPL_ENTER_TITLE_PROMPT)))
    oc.add(InputDirectoryObject(key = Callback(CreatePLSetOption, itype = NEW_PL_DESCRIPTION, settings = settings),
                                title = Locale.LocalStringWithFormat(TEXT_MENU_CREATEPL_ENTER_DESCR, settings[NEW_PL_DESCRIPTION]),
                                prompt = L(TEXT_MENU_CREATEPL_ENTER_DESCR_PROMPT)))
    oc.add(PopupDirectoryObject(key = Callback(CreatePLSelectTypeMenu, settings = settings),
                                title = Locale.LocalStringWithFormat(TEXT_MENU_CREATEPL_SELECT_TYPE, settings[NEW_PL_TYPE])))
    oc.add(DirectoryObject(key = Callback(CreatePLCreatePlaylist, settings = settings, returnkeyonly = False),
                           title = L(TEXT_MENU_CREATEPL_CREATE_LIST)))  
    return oc


@route(PREFIX +'/setplaylistoption', settings=dict)
def CreatePLSetOption(query, itype, settings):
    settings[itype] = query
    return CreatePlaylistMenu(settings)


@route(PREFIX +'/selectplaylisttype', settings=dict)
def CreatePLSelectTypeMenu(settings):
    oc = ObjectContainer(title2 = L(TEXT_MENU_CREATEPL_SELECT_TYPE_PROMPT), view_group='List', no_cache = True, no_history = True)
    oc.title1 = L(TEXT_MENU_CREATEPL_SELECT_TYPE_PROMPT)
    for playlist_type in PL_TYPES:
        oc.add(DirectoryObject(key = Callback(CreatePLSetOption, query = playlist_type, itype = NEW_PL_TYPE, settings = settings),
                               title = playlist_type))         
    return oc


@route(PREFIX +'/createplaylist', settings=dict)
def CreatePLCreatePlaylist(settings, returnkeyonly):
    if settings[NEW_PL_TITLE] != None:
        return addPlaylist(settings = settings, returnkeyonly = returnkeyonly)
        
    return showMessage(L(TEXT_ERROR_MISSING_TITLE))


@route(PREFIX +'/addplaylist', settings=dict)
def addPlaylist(settings, returnkeyonly):
    playlistsElem = LoadOrCreateGlobalPlaylist()
    allPlaylists = FillGlobalPlaylists(playlistsElem)
    
    if allPlaylists == None or playlistsElem == None:
        return showMessage('ERROR: Error loading playlist information')

    # Generate a new key!
    playlistKey = getNextPlaylistKey(allPlaylists = allPlaylists)
    if playlistKey == None:
        return showMessage(TEXT_ERROR_NO_FREE_KEYS)
    
    # This should not be possible anymore!
    if playlistKey in allPlaylists.keys():
        return showMessage(Locale.LocalStringWithFormat(TEXT_ERROR_PLAYLIST_EXISTS, playlistKey))
    
    # Add the playinfo    
    elNewPlaylist = etree.SubElement(playlistsElem, PLAYLIST_ROOT)
    # atributes for TrackObject
    elNewPlaylist.set(ATTR_KEY, playlistKey)                                                
    elNewPlaylist.set(ATTR_TITLE, settings[NEW_PL_TITLE])
    elNewPlaylist.set(ATTR_PLTYPE, settings[NEW_PL_TYPE])
    elNewPlaylist.set(ATTR_DESCR, settings[NEW_PL_DESCRIPTION])
    
    # For now, just set the title. Tobe changed to store the settings object in the allPlaylists dict
    allPlaylists[playlistKey] = { ATTR_TITLE : settings[NEW_PL_TITLE], ATTR_DURATION : 0}
    SaveGlobalPlaylist(allPlaylists = allPlaylists, playlistsElem = playlistsElem)
    
    # Also create the playlist.xml file
    CreateSinglePlaylist(playlistkey = playlistKey, settings = settings)
    if returnkeyonly == True:
        return showMessage(playlistKey)
    else:
        return showMessage(Locale.LocalStringWithFormat(TEXT_MSG_PLAYLIST_CREATED,
                                                        playlistTitle(playlist_dict = allPlaylists[playlistKey]),
                                                        playlistKey))
    return oc


#
# Rename playlist
#

#@route(PREFIX +'/renameplaylist')
def RenamePlaylistMenu(title):
    oc = ObjectContainer(title2 = title, no_cache = True, no_history = True)

    allPlaylists = LoadGlobalPlaylists()
    for playlistkey in allPlaylists.keys():
        listtitle = playlistTitle(playlist_dict = allPlaylists[playlistkey])
        oc.add(InputDirectoryObject(key = Callback(RenamePlaylist, playlistkey = playlistkey),
                                    title = listtitle,
                                    prompt = L(TEXT_MENU_RENAMEPL_PROMPT)))      
    return oc


#@route(PREFIX +'/dorenameplaylist')
def RenamePlaylist(query, playlistkey):
    if query != None and len(query) > 0:
        allPlaylists = LoadGlobalPlaylists()
        # change title in main list
        allPlaylists[playlistkey][ATTR_TITLE] = query
        SaveGlobalPlaylist(allPlaylists = allPlaylists)
        
        # Update the playlist.xml file
        playlist = LoadSinglePlaylist(playlistkey = playlistkey, createifmissing = False)
        if playlist != None:
            playlist.set(ATTR_TITLE, query)
            SaveSinglePlaylist(playlistkey, playlist)
                        
    return showMessage(Locale.LocalStringWithFormat(TEXT_MSG_PLAYLIST_RENAMED, query))


#
# Delete playlist 
#

#@route(PREFIX +'/deleteplaylist')
def DeletePlaylistMenu(title):
    oc = ObjectContainer(title2 = title, no_cache = True, no_history = True)

    allPlaylists = LoadGlobalPlaylists()
    confirmDelete = Prefs[PREFS__CONFIRM_DELETE_PL] == True
    for playlistkey in allPlaylists.keys():
        listtitle = playlistTitle(playlist_dict = allPlaylists[playlistkey])
        if confirmDelete:
            oc.add(PopupDirectoryObject(key = Callback(ConfirmDeletePlaylistMenu, playlistkey = playlistkey),
                                        title = listtitle))
        else:
            oc.add(DirectoryObject(key = Callback(DeletePlaylist, playlistkey = playlistkey),
                                   title = listtitle))      
    return oc


#@route(PREFIX +'/confirmdeleteplaylist')
def ConfirmDeletePlaylistMenu(playlistkey):
    oc = ObjectContainer(title1 = L(TEXT_TITLE_CONFIRM_DELETE), no_cache = True, no_history = True)

    oc.add(DirectoryObject(key = Callback(DeletePlaylist, playlistkey = playlistkey), title = L(TEXT_MENU_ACTION_DELETE_PLAYLIST)))      
    oc.add(DirectoryObject(key = Callback(CancelAction, title = L(TEXT_TITLE_DELETE_CANCELED), mode = CANCEL_MODE_DELETE_PL),
                           title = L(TEXT_TITLE_CANCEL)))      
    return oc


#@route(PREFIX +'/dodeleteplaylist')
def DeletePlaylist(playlistkey):
    if playlistkey != None:
        allPlaylists = LoadGlobalPlaylists()
        if playlistkey in allPlaylists.keys():
            # Delete the playlist file
            DeleteSinglePlaylist(playlistkey = playlistkey)
            # Remove the playlist from the list
            del allPlaylists[playlistkey]
            SaveGlobalPlaylist(allPlaylists = allPlaylists)
    return showMessage(L(TEXT_MSG_PLAYLIST_DELETED))


#
# Default User selection
#
def SelectUserMenu():
    oc = ObjectContainer(title2 = L(TEXT_MENU_TITLE_SET_CLIENT_USER), no_cache = True, no_history = True)
    users = getAllUsers()
    for user in users:
        oc.add(DirectoryObject(key = Callback(defaultUserForClient, query = user), title = user))      
    
    oc.add(InputDirectoryObject(key = Callback(defaultUserForClient),
                                title = L(TEXT_MENU_ACTION_SET_CLIENT_USER),
                                prompt = L(TEXT_MENU_SET_CLIENT_USER_PROMPT)))
            
    return oc


def defaultUserForClient(query):    
    if query != getUser():
        SetUserForCurrentClient(query)
        return MainMenu()
    return showMessage('User not changed')

#
# Helper callback for cancel
#

@route(PREFIX +'/cancelaction', params=dict)
def CancelAction(title, mode, params = {}):
    if mode == CANCEL_MODE_DELETE_PL:
        return DeletePlaylistMenu(title = L(TEXT_MENU_ACTION_DELETE_PLAYLIST))
    elif mode == CANCEL_MODE_REMOVE_TR or mode == CANCEL_MODE_ASK_ACTION:
        if params != None and 'playlistkey' in params.keys():
            playlistkey = params['playlistkey']
            allPlaylists = LoadGlobalPlaylists()
            if mode == CANCEL_MODE_REMOVE_TR:
                return PlaylistEditMenu(title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_REMOVE,
                                                                             playlistTitle(playlist_dict = allPlaylists[playlistkey])),
                                        key = playlistkey,
                                        mode = PL_MODE_DELETE)
            else:
                return PlaylistEditMenu(title = Locale.LocalStringWithFormat(TEXT_MENU_TITLE_TRACK_ASK,
                                                                             playlistTitle(playlist_dict = allPlaylists[playlistkey])),
                                        key = playlistkey,
                                        mode = PL_MODE_ASK)
    elif mode == CANCEL_MODE_EDIT_PLAYLIST:
        return MaintainTracksMenu(title = L(TEXT_MENU_ACTION_EDIT_PLAYLIST))
    return showMessage(title)


####################################################################################################
# Browse music sections
####################################################################################################

#@route(PREFIX +'/browsemusic')
def BrowseMusicMenu(title):    
    oc = ObjectContainer(title2 = title, view_group='List')
    pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
    
    sectionUrl = pms_url + LIBRARY_SECTIONS
    el = XML.ElementFromURL(sectionUrl)

    sections = el.xpath('%s[@scanner="Plex Music Scanner"]' % PMS_XPATH_DIRECTORY)	
    for section in sections:	
        title = section.get(ATTR_TITLE)
        key = section.get(ATTR_KEY)
        oc.add(DirectoryObject(key = Callback(BrowseSectionMenu, parentUrl = sectionUrl, title = title, section = key), title = title))
        
    return oc

#@route(PREFIX +'/browsesection')
def BrowseSectionMenu(parentUrl, title, section, append_trailing_slash = True):
    oc = ObjectContainer(title2 = title, view_group='List')
  
    sectionUrl = parentUrl + section 
    if append_trailing_slash:
        sectionUrl = sectionUrl + '/'
    el = XML.ElementFromURL(sectionUrl)
  
    viewgroup = el.get(ATTR_VIEWGROUP)
    if (viewgroup == 'track' or firstElement(el, PMS_XPATH_TRACK) != None):
        tracks = el.xpath(PMS_XPATH_TRACK)
        for track in tracks:
            title = track.get(ATTR_TITLE)
            key = track.get(ATTR_KEY)
            ratingKey = track.get(ATTR_RATINGKEY)
            oc.add(PopupDirectoryObject(key = Callback(BrowseTrackPopupMenu, key = key, tracktitle = title), title = title))
    else:
        sections = el.xpath(PMS_XPATH_DIRECTORY)	
        pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
        for section in sections:	
            title = section.get(ATTR_TITLE)
            key = section.get(ATTR_KEY)
            if attributeAsInt(section.get(ATTR_SEARCH)) != 0:
                oc.add(InputDirectoryObject(key = Callback(SearchMenu, key = section.get(ATTR_KEY), title = section.get(ATTR_PROMPT)),
                                            prompt = section.get(ATTR_PROMPT),
                                            title = section.get(ATTR_TITLE)))
            elif key.startswith('/'):
                oc.add(DirectoryObject(key = Callback(BrowseSectionMenu, parentUrl = pms_url, title = title, section = key), title = title))
            else:
                oc.add(DirectoryObject(key = Callback(BrowseSectionMenu, parentUrl = sectionUrl, title = title, section = key), title = title))
  
    return oc     

@route(PREFIX +'/search')
def SearchMenu(query, key, title):
    if query != None and len(query) > 0:
        pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
        return BrowseSectionMenu(parentUrl = pms_url,
                                 title = "%s '%s'" % (title, query),
                                 section = '/%s&query=%s' % (key, query),
                                 append_trailing_slash = False)
    return showMessage(L(TEXT_ERROR_EMPTY_SEARCH_QUERY))


#@route(PREFIX +'/browsetrack')
def BrowseTrackPopupMenu(key, tracktitle):
    oc = ObjectContainer(title2 = L(TEXT_MENU_TITLE_TRACK_ACTIONS), no_cache = True)
    oc.title1 = L(TEXT_MENU_TITLE_TRACK_ACTIONS)
    
    allPlaylists = LoadGlobalPlaylists()
    for playlistkey in allPlaylists.keys():
        listtitle = playlistTitle(playlist_dict = allPlaylists[playlistkey], include_duration = True)
        oc.add(PopupDirectoryObject(key = Callback(addToPlaylist, playlistkey = playlistkey, key = key, tracktitle = tracktitle , returnkeyonly = False),
                                    title = listtitle))
    return oc


def addToPlaylist(playlistkey, key, tracktitle = '', returnkeyonly = False):   
    # use key to get the track information
    pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
    trackUrl = pms_url + key + '/'
    el = XML.ElementFromURL(trackUrl)
    if el == None:
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_ERROR_NO_METADATA, key))                      
    track = firstElement(el, PMS_XPATH_TRACK)
    if track == None:
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_ERROR_NO_TRACK_FOUND, tracktitle, key))
    if tracktitle == '':
        tracktitle = track.get(ATTR_TITLE)
    media = firstElement(track, PMS_XPATH_MEDIA)
    if media == None:
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_ERROR_NO_MEDIA_FOR_TRACK, tracktitle, key))                
    part = firstElement(media, PMS_XPATH_PART)
    if part == None:
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_ERROR_NO_TRACK_DATA, tracktitle, key))                

    playlist = LoadSinglePlaylist(playlistkey = playlistkey)
    if playlist != None:
        if trackInPlaylist(track.get(ATTR_KEY), playlist) == True:
            return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_MSG_TRACK_ALREADY_IN_PLAYLIST, tracktitle, key))
        
        createTrackElement(playlist = playlist, track = track, media = media, part = part, pms_url = pms_url)
        SaveSinglePlaylist(playlistkey, playlist)
        UpdateGlobalPlaylists(playlistkey = playlistkey, playlist = playlist)
        
        if returnkeyonly == True:
            return showMessage(message_text = track.get(ATTR_KEY))
            
        return showMessage(message_text = Locale.LocalStringWithFormat(TEXT_MSG_TRACK_ADDED_TO_PLAYLIST, tracktitle, playlist.get(ATTR_TITLE)))
            
    return showMessage(message_text = L(TEXT_ERROR_TRACK_NOT_ADDED))


def createTrackElement(playlist, track, media, part, pms_url):
    elNewtrack = etree.SubElement(playlist, 'Track')
    # atributes for TrackObject
    elNewtrack.set(ATTR_KEY, track.get(ATTR_KEY))                                                
    elNewtrack.set(ATTR_TITLE, track.get(ATTR_TITLE))
    elNewtrack.set(ATTR_PMS_URL, pms_url)
    setAttributeIfPresent(elNewtrack, track, ATTR_RATINGKEY)
    setAttributeIfPresent(elNewtrack, part, ATTR_DURATION)
    setAttributeIfPresent(elNewtrack, track, ATTR_ART)
    setAttributeIfPresent(elNewtrack, track, ATTR_THUMB)
    # additional atributes for MediaObject
    setAttributeIfPresent(elNewtrack, media, ATTR_BITRATE)
    setAttributeIfPresent(elNewtrack, media, ATTR_AUDIOCODEC)
    setAttributeIfPresent(elNewtrack, media, ATTR_AUDIOCHANNELS)
    setAttributeIfPresent(elNewtrack, media, ATTR_CONTAINER)
    # additional atributes for PartObject
    elNewtrack.set(ATTR_PARTKEY, part.get(ATTR_KEY))
    pass


####################################################################################################
# Multi user
####################################################################################################


def LoadGlobalUsers():
    if Data.Exists(CLIENT_USER_LIST):
        try:
            client_users = Data.LoadObject(CLIENT_USER_LIST)
            if client_users != None:
                users = getAllUsers()
                for client_id in client_users.keys():
                    if client_users[client_id] in users:
                        pass
                    else:
                        del client_users[client_id]
                Dict[DICT_KEY_CLIENT_LIST] = client_users
                return
        except Exception:
            pass
        
    Dict[DICT_KEY_CLIENT_LIST] = {}    
    pass


def SaveGlobalUsers():
    try:
        client_users = Dict[DICT_KEY_CLIENT_LIST]
        if client_users != None:
            Data.SaveObject(item = CLIENT_USER_LIST, obj = client_users)
    except Exception:
        pass


def SetUserForCurrentClient(user):
    setUserForClient(client_id = getClientIdentifier(), user = user)
    

def setUserForClient(client_id, user):
    if client_id != None and client_id != CLIENT_UNKNOWN and len(user) > 0:
        client_users = Dict[DICT_KEY_CLIENT_LIST]
        if client_users == None:
            client_users = {}
        client_users[client_id] = user
        Dict[DICT_KEY_CLIENT_LIST] = client_users
        SaveGlobalUsers()


def getUser():
    return getUserForClient()


def getUserForClient():
    try:
        client_id = getClientIdentifier()
        if client_id != CLIENT_UNKNOWN:
            client_users = Dict[DICT_KEY_CLIENT_LIST]
            if client_users != None and client_id in client_users.keys():
                if client_users[client_id] != None:
                    return client_users[client_id]
    except Exception:
        pass    
    return Prefs[PREFS__USERNAME]


def getClientIdentifier():
    if REQUEST_HEADER_CLIENTID in Request.Headers.keys():
        return Request.Headers[REQUEST_HEADER_CLIENTID]
    return CLIENT_UNKNOWN


def getAllUsers():
    users_list = []
    def_user = Prefs[PREFS__USERNAME]
    try:
        path = GetSupportPath('Data', 'DataItems')
        user_files = [f for f in os.listdir(path) if f.endswith(FILE_ALLPLAYLIST_SUFFIX)]
        for file in user_files:
            user = file[:-len(FILE_ALLPLAYLIST_SUFFIX)]
            users_list.append(user)
            if def_user != None and user == def_user:
                def_user = None
    except Exception:
        pass
    if def_user != None:
        users_list.append(def_user)
    return users_list

####################################################################################################
# Load / Save playlist
####################################################################################################

def LoadGlobalPlaylists():
    # Load all existing playlists (name only) for the current user from XML file
    # AND fill the global dict with playlists
    playlistsElem = LoadOrCreateGlobalPlaylist()
    return FillGlobalPlaylists(playlistsElem)


def FillGlobalPlaylists(playlistsElem):
    allPlaylists = {}
    if playlistsElem != None:
        for playlist in playlistsElem.xpath(PL_XPATH_PLAYLIST):
            allPlaylists[playlist.get(ATTR_KEY)] = { ATTR_TITLE : playlist.get(ATTR_TITLE),
                                                    ATTR_DURATION : attributeAsInt(playlist.get(ATTR_DURATION), 0)}
    return allPlaylists

		
def LoadOrCreateGlobalPlaylist():
    # Load all existing playlists (name only) for the current user from XML file
    playlistsElem = LoadGlobalPlaylistsFile(playlistsName = getPlaylistName())
    if playlistsElem == None:
        playlistsElem = CreateGlobalPlaylist()
    return playlistsElem

	
def SaveGlobalPlaylist(allPlaylists, playlistsElem = None, playlistsName = ''):
    if playlistsName == '':
        playlistsName = getPlaylistName()
    if playlistsElem == None:
        playlistsElem = LoadGlobalPlaylistsFile(playlistsName = playlistsName)
    if playlistsElem != None and  etree.iselement(playlistsElem):
        try:
            # Update elements according the global allPlaylists
            for playlist in playlistsElem.xpath(PL_XPATH_PLAYLIST):
                playlistKey = playlist.get(ATTR_KEY)
                if playlistKey in allPlaylists.keys():
                    # Update the title
                    playlist.set(ATTR_TITLE, allPlaylists[playlistKey][ATTR_TITLE])
                    playlist.set(ATTR_DURATION, str(allPlaylists[playlistKey][ATTR_DURATION]))
                else:
                    # this playlist no longer in the global list: remove from the xml
                    playlist.getparent().remove(playlist)
            
            # Write to file
            playlistsElem.set(ATTR_VERSION, CURRENT_VERSION_ALL)
            etree.ElementTree(playlistsElem).write(playlistsName, pretty_print = True)
        except Exception:
            Log.Debug('ERROR: in SaveGlobalPlaylist() ')
            pass


def LoadGlobalPlaylistsFile(playlistsName):
    Log.Debug('LoadGlobalPlaylistFile: %s' % playlistsName)
    if os.path.isfile(playlistsName):
        try:
            tree = etree.parse(playlistsName)
            root = tree.getroot()
            return root
        except:            
            Log.Debug('ERROR: in LoadGlobalPlaylistsFile(%s)' % playlistsName)
            return None
    return None


def CreateGlobalPlaylist():    
    allPlaylists = {}
    newplaylists = etree.Element(PLAYLIST_ALL_ROOT)
    if newplaylists != None:
        newplaylists.set(ATTR_VERSION, CURRENT_VERSION_ALL)
        SaveGlobalPlaylist(allPlaylists = allPlaylists, playlistsElem = newplaylists)
    return newplaylists;


def UpdateGlobalPlaylists(playlistkey, playlist):
    if playlist != None:
        duration = attributeAsInt(playlist.get(ATTR_DURATION), 0)
        allPlaylists = LoadGlobalPlaylists()
        if playlistkey in allPlaylists.keys():
            allPlaylists[playlistkey][ATTR_DURATION] = duration
            SaveGlobalPlaylist(allPlaylists)
    pass


def LoadSinglePlaylist(playlistkey, createifmissing = True, suffix = ""):   
    full_filename = GetPlaylistFileName(playlistkey = playlistkey, suffix = suffix)
    Log.Debug('LoadSinglePlaylist: %s' % full_filename)
    if os.path.isfile(full_filename):
        try:
            tree = etree.parse(full_filename)
            root = tree.getroot()
            return root
        except:            
            Log.Debug('ERROR: in LoadSinglePlaylist(%s)' % full_filename)
            return None
    if createifmissing == True and ondeck == False:
        allPlaylists = LoadGlobalPlaylists()
        newsettings = { NEW_PL_TITLE : allPlaylists[playlistkey], NEW_PL_TYPE : PL_TYPE_SIMPLE, NEW_PL_DESCRIPTION : ''}
        return CreateSinglePlaylist(playlistkey = playlistkey, settings = newsettings)
    return None


def SaveSinglePlaylist(playlistkey, playlist, suffix = ""):
    full_filename = GetPlaylistFileName(playlistkey = playlistkey, suffix = suffix)
    Log.Debug('SaveSinglePlaylist: %s' % full_filename)
    if etree.iselement(playlist):
        try:
            duration = 0
            tracks = playlist.xpath('%s' % PL_XPATH_TRACK)
            for track in tracks:
                duration = duration + attributeAsInt(track.get(ATTR_DURATION), 0)
            # Store duration in seconds
            Log.Debug("Total duration = %d" % duration)
            duration = duration // 1000
            playlist.set(ATTR_DURATION, str(duration))
            playlist.set(ATTR_VERSION, CURRENT_VERSION_SINGLE)
            etree.ElementTree(playlist).write(full_filename, pretty_print = True)
        except Exception:
            Log.Debug('ERROR: in SaveSinglePlaylist(%s)' % full_filename)
            pass
    pass    
    

def CreateSinglePlaylist(playlistkey, settings = {}):    
    newplaylist = etree.Element(PLAYLIST_ROOT)
    if newplaylist != None:
        newplaylist.set(ATTR_KEY, playlistkey)
        newplaylist.set(ATTR_VERSION, CURRENT_VERSION_SINGLE)
        newplaylist.set(ATTR_TITLE, settings[NEW_PL_TITLE])
        newplaylist.set(ATTR_PLTYPE, settings[NEW_PL_TYPE])
        newplaylist.set(ATTR_DESCR, settings[NEW_PL_DESCRIPTION])
        SaveSinglePlaylist(playlistkey, newplaylist)        
    return newplaylist;


def DeleteSinglePlaylist(playlistkey, suffix = ""):   
    full_filename = GetPlaylistFileName(playlistkey = playlistkey, suffix = suffix)
    Log.Debug('DeleteSinglePlaylist: %s' % full_filename)
    DeleteSingleFile(filename = full_filename)
    pass


def DeleteSingleFile(filename):
    if os.path.isfile(filename):
        try:
            os.remove(filename)
        except:
            pass
    pass    


def getPlaylistName(full_path = True):
    username = getUser()
    playlistsName = '%s%s' % (username, FILE_ALLPLAYLIST_SUFFIX)
    if full_path == True:
        return Core.storage.join_path(GetSupportPath('Data', 'DataItems'), playlistsName)        
    return playlistsName


def getNextPlaylistKey(allPlaylists):
    if allPlaylists != None:
        nextKey = 1
        while nextKey <= 9999:
            if keyString(key_number = nextKey) in allPlaylists.keys():
                nextKey += 1
            else:
                return keyString(key_number = nextKey)
    return None


##
# Methods to provide easy access through URL. Not called directly by the plugin
#


@route(PREFIX +'/users')
def getUserList():
    oc = ObjectContainer(title1 = 'All users', no_cache = True)
    
    user_list = getAllUsers()
    for user in user_list:
        oc.add(DirectoryObject(key = user, title = user))
    return oc


@route(PREFIX +'/users/current')
def getCurrentUser():
    oc = ObjectContainer(title1 = 'All users', no_cache = True)
    
    user = getUserForClient()
    oc.add(DirectoryObject(key = user, title = getClientIdentifier()))
    return oc


@route(PREFIX +'/users/set')
def setCurrentUser(user):
    SetUserForCurrentClient(user = user)
    if getClientIdentifier() != CLIENT_UNKNOWN:
        LoadOrCreateGlobalPlaylist()
    return getCurrentUser()


@route(PREFIX +'/users/delete')
def deleteUser(user):
    if user != None and len(user) > 0:
        playlistsName = '%s%s' % (user, FILE_ALLPLAYLIST_SUFFIX)
        playlistsName = Core.storage.join_path(GetSupportPath('Data', 'DataItems'), playlistsName)        
        playlistsElem = LoadGlobalPlaylistsFile(playlistsName = playlistsName)
        if playlistsElem != None:
            allPlaylists = FillGlobalPlaylists(playlistsElem = playlistsElem)
            for playlistkey in allPlaylists.keys():
                # Delete the playlist file(s)
                DeleteSingleFile(filename = GetPlaylistFileNameUser(user = user, playlistkey = playlistkey))
                DeleteSingleFile(filename = GetPlaylistFileNameUser(user = user, playlistkey = playlistkey, suffix = FILE_SUFFIX_ONDECK))
                DeleteSingleFile(filename = GetPlaylistFileNameUser(user = user, playlistkey = playlistkey, suffix = FILE_SUFFIX_STARTED))
                # Remove the playlist from the list
        DeleteSingleFile(filename = playlistsName)
        # update the default users for all clients if neccesary
        LoadGlobalUsers()
        SaveGlobalUsers()
    return getCurrentUser()


@route(PREFIX +'/playlists')
def getAllPlaylists():
    oc = ObjectContainer(title1 = 'All playlists', no_cache = True)
    logRequest()
    playlistsElem = LoadGlobalPlaylistsFile(playlistsName = getPlaylistName())
    if playlistsElem != None:
        for playlist in playlistsElem.xpath(PL_XPATH_PLAYLIST):
            key = playlist.get(ATTR_KEY)
            title = playlist.get(ATTR_TITLE)
            duration = attributeAsInt(playlist.get(ATTR_DURATION))
            oc.add(DirectoryObject(key = key, title = title, summary = playlist.get(ATTR_DESCR), duration = duration))
    return oc


@route(PREFIX +'/playlists/list')
def singlePlaylist(key):
    if validatePlaylistKey(key):
        playlist = LoadSinglePlaylist(playlistkey = key, createifmissing = False)
        oc = ObjectContainer(title1 = key, title2 = playlist.get(ATTR_TITLE), no_cache = True, content = ContainerContent.Tracks)
        if playlist != None:
            tracks = playlist.xpath(PL_XPATH_TRACK)
            track_nr = 0
            for track in tracks:
                track_nr += 1
                title = track.get(ATTR_TITLE)
                key = track.get(ATTR_KEY)
                ratingKey = track.get(ATTR_RATINGKEY)            
                trackObject = TrackObject(title = title, key = key,
                                          rating_key = ratingKey,
                                          duration = attributeAsInt(track.get(ATTR_DURATION)))
                oc.add(trackObject)
        return oc
    return showMessage('ERROR: No playlist with key %s found' % key)


@route(PREFIX +'/playlists/create')
def createNewPlaylist(title, pltype, description):    
    if validatePlaylistType(pltype):
        newsettings = { NEW_PL_TITLE : title, NEW_PL_TYPE : pltype, NEW_PL_DESCRIPTION : description}
        return CreatePLCreatePlaylist(settings = newsettings, returnkeyonly = True)
    return showMessage('ERROR: Playlist type %s not supported' % pltype)


@route(PREFIX +'/playlists/delete')
def deleteSinglePlaylist(key):
    if validatePlaylistKey(key):
        return DeletePlaylist(playlistkey = key)
    return showMessage('ERROR: No playlist with key %s found' % key)


@route(PREFIX +'/playlists/rename')
def renameSinglePlaylist(key, newname):
    if validatePlaylistKey(key):
        return RenamePlaylist(query = newname, playlistkey = key)
    return showMessage('ERROR: No playlist with key %s found' % key)


@route(PREFIX +'/tracks/add')
def addTrackToPlaylist(playlistkey, key):
    if validatePlaylistKey(playlistkey):
        if not key.startswith('/'):
            key = '/library/metadata/%s' % key
        return addToPlaylist(playlistkey = playlistkey, key = key, returnkeyonly = True)
    return showMessage('ERROR: No playlist with key %s found' % playlistkey)


@route(PREFIX +'/tracks/remove')
def removeTrackFromPlaylist(playlistkey, key):
    if validatePlaylistKey(playlistkey):
        if not key.startswith('/'):
            key = '/library/metadata/%s' % key
        return removeFromPlaylist(playlistkey = playlistkey, key = key, tracktitle = '', mode = PL_MODE_DELETE)
    return showMessage('ERROR: No playlist with key %s found' % playlistkey)


@route(PREFIX +'/tracks/move')
def moveTrackInPlaylist(playlistkey, key, to):
    if validatePlaylistKey(playlistkey):
        if not key.startswith('/'):
            key = '/library/metadata/%s' % key
        return moveTrack(query = to,
                         playlistkey = playlistkey,
                         trackkey = key,
                         mode = PL_MODE_MOVE)
    return showMessage('ERROR: No playlist with key %s found' % playlistkey)


@route(PREFIX + '/tracks/addall')
def addAllTracksToPlaylist(playlistkey):    
    if validatePlaylistKey(playlistkey):
        playlist = LoadSinglePlaylist(playlistkey, createifmissing = False)
        if playlist != None:
            pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])              
            sectionUrl = pms_url + LIBRARY_SECTIONS
            el = XML.ElementFromURL(sectionUrl)
            tracks_added = 0
            sections = el.xpath('%s[@scanner="Plex Music Scanner"]' % PMS_XPATH_DIRECTORY)	
            for section in sections:	
                title = section.get(ATTR_TITLE)
                key = section.get(ATTR_KEY) + '/all'
                tracks_added += addAllTracksFromSection(playlist = playlist, parentUrl = sectionUrl, section = key)

            if tracks_added > 0:
                SaveSinglePlaylist(playlistkey, playlist)            
        return showMessage('%d Tracks added to playlist with key %s' % (tracks_added, playlistkey))
    return showMessage('ERROR: No playlist with key %s found' % playlistkey)


def addAllTracksFromSection(playlist, parentUrl, section):
    sectionUrl = parentUrl + section 
    el = XML.ElementFromURL(sectionUrl)  
    tracks_added = 0
    viewgroup = el.get(ATTR_VIEWGROUP)
    if (viewgroup == 'track' or firstElement(el, PMS_XPATH_TRACK) != None):
        tracks = el.xpath(PMS_XPATH_TRACK)
        for track in tracks:
            key = track.get(ATTR_KEY)
            tracks_added += addSingleTrackToPlaylist(playlist = playlist, key = key)
    else:
        sections = el.xpath(PMS_XPATH_DIRECTORY)	
        pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
        for section in sections:	
            key = section.get(ATTR_KEY)
            if attributeAsInt(section.get(ATTR_SEARCH)) != 0:
                pass
            else:
                if key.startswith('/'):
                    parentUrl = pms_url
                else:
                    parentUrl = sectionUrl
                tracks_added += addAllTracksFromSection(playlist = playlist, parentUrl = parentUrl, section = key)
  
    return tracks_added     

def addSingleTrackToPlaylist(playlist, key):   
    # use key to get the track information
    if playlist == None:
        return 0
    pms_url = 'http://%s:%s' %(Prefs[PREFS__PLEXIP], Prefs[PREFS__PLEXPORT])
    trackUrl = pms_url + key + '/'
    el = XML.ElementFromURL(trackUrl)
    if el == None:
        return 0
    track = firstElement(el, PMS_XPATH_TRACK)
    if track == None:
        return 0
    media = firstElement(track, PMS_XPATH_MEDIA)
    if media == None:
        return 0
    part = firstElement(media, PMS_XPATH_PART)
    if part == None:
        return 0

    if trackInPlaylist(track.get(ATTR_KEY), playlist) == True:
        return 0

    createTrackElement(playlist = playlist, track = track, media = media, part = part, pms_url = pms_url)
    return 1


####################################################################################################
# Generic helper functions
####################################################################################################

def logRequest():
    for header in Request.Headers.keys():
        Log.Debug('REQUEST.HEADER: %s=%s' % (header, Request.Headers[header]))
    pass
    

def validatePlaylistType(pltype):
    return pltype in PL_TYPES


def validatePlaylistKey(key):
    allPlaylists = LoadGlobalPlaylists()
    return allPlaylists != None and key in allPlaylists.keys()


def trackTitle(title, index):
    return '%02d - %s' % (index, title)


def keyString(key_number):
    return '%04d' % key_number


def setAttributeIfPresent(to_elem, from_elem, attr_name):
    if to_elem != None and from_elem != None and attr_name != None and from_elem.get(attr_name) != None:
        to_elem.set(attr_name, from_elem.get(attr_name))
    pass


def attributeAsInt(attr_value, def_value = 0):
    if attr_value != None:
        try:
            if attr_value.isdigit():
                return int(attr_value)
        except Exception:
            pass
    return def_value


def firstElement(element, query):
    if element != None and query != None:
        try:
            elem = element.xpath(query)
            if elem != None and len(elem) > 0:
                return elem[0]
        except Exception:
            pass
    return None


def trackInPlaylist(trackkey, playlist):
    if playlist != None and trackkey != None:
        track = playlist.xpath('%s[@key="%s"]' % (PL_XPATH_TRACK, trackkey))
        if track != None and len(track) > 0:
            return True
    return False


def playlistTitle(playlist_dict, include_duration = False):
    if include_duration == True:
        duration = playlist_dict[ATTR_DURATION]
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        return '[%02d:%02d:%02d] %s' % (hours, minutes, seconds, playlist_dict[ATTR_TITLE])
    return playlist_dict[ATTR_TITLE]


def showMessage(message_text):
    return ObjectContainer(header = L(TEXT_MAIN_TITLE), message=message_text, no_history = True, no_cache = True)


def GetSupportPath(directory, subdirectory = None):
    return Core.storage.join_path(Core.app_support_path, Core.config.plugin_support_dir_name, directory, PLUGIN_DIR, subdirectory)


def GetPlaylistFileName(playlistkey, suffix = ""):
    return GetPlaylistFileNameUser(user = getUser(), playlistkey = playlistkey, suffix = suffix)


def GetPlaylistFileNameUser(user, playlistkey, suffix = ""):
    playlist_filename = '%s - %s%s.xml' % (user, playlistkey, suffix)
    return Core.storage.join_path(GetSupportPath('Data', 'DataItems'), playlist_filename)
