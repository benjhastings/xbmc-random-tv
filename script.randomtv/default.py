# Random TV Show selecter
# Massive thanks to the developers of the script.randommovie addon by el_Paraguayo, without whom this would not have been possible
#
# Author - benjhastings
# Website - https://github.com/benjhastings/xbmc-random-tv/
# Version - 1.2
# Compatibility - pre-Eden
#

import xbmc
import xbmcgui
import xbmcaddon
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random
import simplejson as json

__settings__ = xbmcaddon.Addon(id="script.randomtv")
#Settings for displaying of the prompts
unwatched_settings = True if __settings__.getSetting('unwatched') == 'true' else False
watched_settings = True if __settings__.getSetting('watched') == 'true' else False

#Settings for the default option to use if the prompts are not displayed
default_unwatched_settings = True if __settings__.getSetting('default_unwatched') == 'true' else False
default_watched_settings = True if __settings__.getSetting('default_watched') == 'true' else False
genre_settings = True if __settings__.getSetting('genre') == 'true' else False
show_settings = True if __settings__.getSetting('show') == 'true' else False


"""
Get the full list of shows from a users library
"""
def get_tv_show_library():
    # get the raw JSON output
    try:
        shows = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "fields": ["genre", "playcount", "file"]}, "id": 1}'), errors='ignore')
        shows = json.loads(shows)
        # older "pre-Eden" versions accepted "fields" parameter but this was changed to "properties" in later versions.
        # the next line will throw an error if we're running newer version
        testError = shows["result"]
    except KeyError:
        shows = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "properties": ["genre", "playcount", "file"]}, "id": 1}'), errors='ignore')
        shows = json.loads(shows)
        # and return it
    return shows

tv_shows_json = get_tv_show_library()

"""
Methods for getting the genre and the show listing
"""

def select_genre(watched, unwatched):
    """
    Select the genre
    """
    success = False
    my_genres = []
    selected_genre = None
    for show in tv_shows_json["result"]["tvshows"]:
        # Let's get the tv show genres
        # Restrict the list of only tv shows that match either watched or unwatched
        if check_watched_unwatched(watched, unwatched, show):
            genres = show["genre"].split(" / ")
            for genre in genres:
                # check if the genre is a duplicate
                if not genre in my_genres:
                    # if not, add it to our list
                    my_genres.append(genre)
                    #sort the list
    my_genres = sorted(my_genres)
    #prompt user to select genre
    select_genre_dialog = xbmcgui.Dialog().select("Select genre:", my_genres)
    #check whether user cancelled selection
    if not select_genre_dialog == -1:
        # get the user's chosen genre
        selected_genre = my_genres[select_genre_dialog]
        success = True
    else:
        success = False
        # return the genre and whether the choice was successfult
    return success, selected_genre

def select_show(watched, unwatched, selected_genre):
    """
    Select the show
    """
    success = False
    my_shows = []
    selected_show = None
    for show in tv_shows_json["result"]["tvshows"]:
        if check_watched_unwatched(watched, unwatched, show):
            #If a genre has been specified then check to see if it matches the show
            #If it does add it to the list.
            #If no genre specified then add the show to the list
            if selected_genre is not None:
                genres = show["genre"].split(" / ")
                for genre in genres:
                    # check if the genre is a duplicate
                    if selected_genre in show['genre'] and show['label'] not in my_shows:
                        # if not, add it to our list
                        my_shows.append(show['label'])
            else:
                my_shows.append(show['label'])
                #Sort the list
    my_shows = sorted(my_shows)
    #prompt user to select show
    select_show_dialog = xbmcgui.Dialog().select("Select show:", my_shows)
    #check whether user cancelled selection
    if not select_show_dialog == -1:
        # get the user's chosen genre
        selected_show = my_shows[select_show_dialog]
        success = True
    else:
        success = False
        #return the genre and whether the choice was successfult
    return success, selected_show

"""
Get a random TV Show using get_random season and get_random_episode
"""

def get_random_show(watched, unwatched, selected_genre, selected_show):
    #Set up an empty list for the tv shows
    shows_list = []
    # loop through all tv shows
    for show in tv_shows_json["result"]["tvshows"]:
        # reset the criteria flag
        meets_criteria = False

        #Check if the entire show is unwatched or not

        if check_watched_unwatched(watched, unwatched, show):

            #Check to see if the show is unwatched (if we are filtering by watched)
            if watched or unwatched:
                meets_criteria = check_watched_unwatched(watched, unwatched, show)

            #Check to see if the show genre matches the specified genre
            if selected_genre:
                meets_criteria = check_genre(selected_genre, show)

            #Check to see if the show matches the specified show
            if selected_show is not None:
                meets_criteria = check_show(selected_show, show)

            #If we haven't been asked to filter by genre, show or watched then the show automatically meets critiera
            if not unwatched and not watched and selected_show is None and selected_genre is None:
                meets_criteria = True

            #If it meets the criteria then add it to the list
            if meets_criteria:
                shows_list.append(show["tvshowid"])

    #Picks a random show from the list
    random_show = random.choice(shows_list)
    #Picks a random season of this show
    random_season = get_random_season(random_show)
    #Picks a random episode of this season
    random_episode = get_random_episode(watched, unwatched, random_show, random_season)
    # return the filepath
    return random_episode


def get_random_season(random_show):
    #Gets a random season from the show that is passed in
    try:
        seasons = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": { "tvshowid": %(tvshowid)i, "fields": ["season"]}, "id": 1}' % {'tvshowid':random_show}), errors='ignore')
        seasons = json.loads(seasons)
        testError = seasons["result"]
    except KeyError:
        seasons = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": { "tvshowid": %(tvshowid)i, "properties": ["season"]}, "id": 1}' % {'tvshowid':random_show}), errors='ignore')
        seasons = json.loads(seasons)
    season_list = []
    for season in seasons['result']['seasons']:
        if season not in season_list:
            season_list.append(season['season'])
    random_season = random.choice(season_list)
    return random_season

def get_random_episode(watched, unwatched, random_show, random_season):
    #gets a random episode from the show and the season that are passed in
    try:
        episodes = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %(tvshowid)i, "season" :%(season_id)i, "fields": ["season", "file", "playcount"]}, "id": 1}' % {'tvshowid':random_show, 'season_id':random_season}), errors='ignore')
        episodes = json.loads(episodes)
        testError = episodes['result']
    except KeyError:
        episodes = unicode(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %(tvshowid)i, "season" :%(season_id)i, "properties": ["season", "file", "playcount"]}, "id": 1}' % {'tvshowid':random_show, 'season_id':random_season}), errors='ignore')
        episodes = json.loads(episodes)
    episode_list = []
    for episode in episodes['result']['episodes']:
        #Checks to make sure the individual episode is unwatched or not (depending on whether we are filtering for unwatched)
        if episode not in episode_list and check_watched_unwatched(watched, unwatched, episode):
            episode_list.append(episode['file'])
    random_episode = random.choice(episode_list)
    return random_episode

def check_show(selected_show, show):
    #Checks to see if the show is valid for selection by seeing if the show matches the selected show
    return True if selected_show is not None and selected_show == show['label'] else False

def check_genre(selected_genre, show):
    #Checks to see if the show is valid for selection by seeing if the shows genre matches the selected genre
    if selected_genre is not None:
        showsgenre = []
        showsgenre = show["genre"].split(" / ")
    return True if selected_genre is not None and selected_genre in showsgenre else False

def check_watched_unwatched(watched, unwatched, object):
    #Checks to see if either check_watched() or check_unwatched() returns True
    if watched:
        return check_watched(object)
    if unwatched:
        return check_unwatched(object)
    #if watched and unwatched are both False then just return True as we want all shows included
    return True

def check_unwatched(object):
    #Checks to see if the show is valid by checking to see if the show (or episode) has been watched
    return True if object["playcount"] == 0 else False

def check_watched(object):
    #Checks to see if the show is valid by checking to see if the show (or episode) has been watched
    return True if object["playcount"] >= 1 else False

"""
End Random Episode Selector
"""

"""
Method for prompts
"""
def ask_question(type=False, watched=False, unwatched=False):
    #Asks user a question
    select_answer = False

    if type == False and (unwatched == True or watched == True):
        a = xbmcgui.Dialog().yesno("%satched Episodes" % ('Un' if unwatched == True else 'W'), "Restrict selection to %swatched episodes only?" % ('un' if unwatched == True else ''))
    else:
        a = xbmcgui.Dialog().yesno("Select %(type)s" % {'type':type}, "Do you want to select a %(type)s to watch?" % {'type':type})
        # deal with the output
    if a == 1:
    # set filter
        select_answer = True
    return select_answer

"""
If either unwatched or watched are False in the settings then don't ask the question about unwatched/watched
and set the appropriate defaults
"""
unwatched = False
if unwatched_settings:
    unwatched = ask_question(unwatched=True)

watched = False
if watched_settings:
    watched = ask_question(watched=True)

#Set defaults if necessary
if not unwatched_settings and not watched_settings and not default_watched_settings:
    unwatched = default_unwatched_settings

if not watched_settings and not unwatched_settings and not default_unwatched_settings:
    watched = default_watched_settings

"""
Prompt the User for genre/show selection
"""

genre_success = True
selected_genre = None
filter_genres = False
filter_shows = False
if not filter_genres and genre_settings:
    filter_genres = ask_question('genre')
    if filter_genres:
        genre_success, selected_genre = select_genre(watched, unwatched)

selected_show = None
show_success = True
#We haven't prompted them for a show yet
if not filter_shows and show_settings:
    filter_shows = ask_question('show')
    if filter_shows:
        show_success, selected_show = select_show(watched, unwatched, selected_genre)

#If both genre and show returned successfully (i.e. the user didn't exit out from the choice screen)
#then get a random episode that matches the criteria
if genre_success and show_success:
    random_episode = get_random_show(watched, unwatched, selected_genre, selected_show)
    if random_episode:
        xbmc.executebuiltin('PlayMedia(' + random_episode + ',0,noresume)')



