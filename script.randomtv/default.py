# Random movie selecter
# Massive thanks to the developers of the script.randommitems addon, without whom this would not have been possible
#
# Author - el_Paraguayo
# Website - https://github.com/benjhastings/xbmc-random-tv/
# Version - 0.1
# Compatibility - pre-Eden
#

import xbmc
import xbmcgui
from urllib import quote_plus, unquote_plus
import re
import sys
import os
import random
import simplejson as json

#Set preferences
filter_genres = False
filter_shows = False
prompt_user = True



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

def get_random_episode(filter_watched, random_show, random_season):
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
        if episode not in episode_list and check_unwatched(filter_watched, episode):
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

def check_unwatched(filter_watched, object):
    #Checks to see if the show is valid by checking to see if the show (or episode) has been watched
    return True if ( filter_watched and object["playcount"] == 0 ) or not filter_watched else False

def get_random_show(filter_watched, selected_genre, selected_show):
    #Set up an empty list for the tv shows
    shows_list = []
    # loop through all tv shows
    for show in tv_shows_json["result"]["tvshows"]:
        # reset the criteria flag
        meetsCriteria = False

        #Check if the entire show is unwatched or not
        if check_unwatched(filter_watched, show):
            #Check to see if the show matches the criteria
            if check_show(selected_show, show):
                meetsCriteria = True
            #Check to see if the genre matches the criteria (if it does also check to make sure the show matches the selected genre)
            if check_genre(selected_genre, show):
                meetsCriteria = True
                if check_show(selected_show, show):
                    meetsCriteria = True
                else:
                    meetsCriteria = False
            #If we haven't been asked to filter by watched, genre or show then add it to the list
            if ( not filter_watched and selected_genre is None and selected_show is None ):
                meetsCriteria = True

            #If it meets the criteria then add it to the list
            if meetsCriteria:
                shows_list.append(show["tvshowid"])

    #Picks a random show from the list
    random_show = random.choice(shows_list)
    #Picks a random season of this show
    random_season = get_random_season(random_show)
    #Picks a random episode of this season
    random_episode = get_random_episode(filter_watched, random_show, random_season)
    # return the filepath
    return random_episode

def select_genre(filter_watched):
    """
    Select the genre
    """
    success = False
    my_genres = []
    selected_genre = None
    for show in tv_shows_json["result"]["tvshows"]:
        # Let's get the tv show genres
        # If we're only looking at unwatched movies then restrict list to those movies
        if check_unwatched(filter_watched, show):
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

def select_show(filter_watched, selected_genre):
    """
    Select the show
    """
    success = False
    my_shows = []
    selected_show = None
    for show in tv_shows_json["result"]["tvshows"]:
        if check_unwatched(filter_watched, show):
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

def ask_question(type=False, unwatched=False):
    #Asks user a question
    select_answer = False

    if type == False and unwatched == True:
        a = xbmcgui.Dialog().yesno("Watched Episodes" % {'type':type}, "Restrict selection to unwatched episodes only?")
    else:
        a = xbmcgui.Dialog().yesno("Select %(type)s" % {'type':type}, "Do you want to select a %(type)s to watch?" % {'type':type})
    # deal with the output
    if a == 1:
    # set filter
        select_answer = True
    return select_answer


#Get the full list of shows from a users library
tv_shows_json = get_tv_show_library()

#Ask user if they want to restrict the episodes to unwatched only
unwatched = ask_question(unwatched=True)

#We want to prompt the user
if prompt_user:
    #We haven't prompted them for a genre yet
    if not filter_genres:
        filter_genres = ask_question('genre')
        selected_genre = None
        genre_success = True
        if filter_genres:
            genre_success, selected_genre = select_genre(unwatched)

    #We haven't prompted them for a show yet
    if not filter_shows:
        filter_shows = ask_question('show')
        selected_show = None
        show_success = True
        if filter_shows:
            show_success, selected_show = select_show(unwatched, selected_genre)

#If both genre and show returned successfully (i.e. the user didn't exit out from the choice screen)
#then get a random episode that matches the criteria
if genre_success and show_success:
    random_episode = get_random_show(unwatched, selected_genre, selected_show)
    if random_episode:
        xbmc.executebuiltin('PlayMedia(' + random_episode + ',0,noresume)')