import discord
import asyncio
import requests

# Debugging
import logging

from riotwatcher import RiotWatcher
from riotwatcher import LoLException, error_429

from jshbot.exceptions import ErrorTypes, BotException

__version__ = '0.1.0'
EXCEPTION = 'Riot API plugin'
uses_configuration = True

def get_commands():
    '''
    Sets up new commands and shortcuts in the proper syntax.
    '''

    commands = {}
    shortcuts = {}
    manual = {}
    
    commands['blitz'] = ([
        'summoner: ?extra',
        'match: ?extra'],[
        ('summoner', 'user', 's', 'i', 'info'),
        ('extra', 'x', 'e', 'verbose', 'detail', 'detailed', 'more')])

    shortcuts['summoner'] = ('blitz -summoner {}', '^')

    manual['blitz'] = {
        'description': 'Get League of Legends information from the API.',
        'usage': [
            ('-info <summoner> (-extra)', 'Gets the information of the given '
            'summoner. Extra information provides a more verbose result.'),
            ('-match <summoner> (-id <match ID>)', 'Gets the current or most '
                'recent match data.')],
        'shortcuts': [
            ('summoner <arguments>', '-summoner <arguments>')]}

    return (commands, shortcuts, manual)

def api_cooldown():
    raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
            "API is being used too often right now. Please try again later.")

def get_summoner_wrapper(watcher, name):
    '''
    Wraps the obtaining of a summoner information with exception handling.
    '''
    try:
        summoner = watcher.get_summoner(name=name)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else:
            try: # Maybe we were given an ID
                summoner = watcher.get_summoner(_id=name)
            except Exception as e:
                raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                        "Summoner \"" + name + "\" not found.", e=e)
    except Exception as e:
        raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                "Failed to retrieve summoner information.", e=e)
    return summoner

def get_league_wrapper(watcher, summoner_id):
    '''
    Wraps the obtaining of a league with exception handling. Returns an empty
    dictionary if the summoner has not played any ranked games.
    '''
    try:
        league = watcher.get_league_entry(summoner_ids=[summoner_id])
        return league[str(summoner_id)][0]
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else: # Summoner has not played ranked
            logging.warn("Summoner has not played ranked.")
            return {}
    except Exception as e:
        raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                "Failed to retrieve summoner league.", e=e)

def get_match_list_wrapper(watcher, summoner_id):
    '''
    Gets the match list of the summoner. Returns an empty list if there are no
    matches.
    '''
    try:
        return watcher.get_match_list(summoner_id)['matches']
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else:
            logging.warn("Summoner hsa no match list.")
            return []

def get_recent_match(match_list, no_team=False):
    '''
    Gets the most recent match from the match list. If no_team is True, then
    it gets the most recent match that isn't RANKED_TEAM_5x5.
    '''
    if not match_list:
        return None
    elif not no_team: # Just get first match
        return match_list[0]['matchId']
    else:
        for match in match_list:
            if match['queue'].startswith('RANKED_TEAM_'):
                continue
            else:
                return match['matchId']
        return None # No suitable match was found

def get_match_wrapper(watcher, match_id):
    '''
    Gets the match given match_id. Includes exception handling.
    '''
    try:
        return watcher.get_match(match_id)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        return None

def get_current_match_wrapper(watcher, summoner_id):
    '''
    Returns the current match if there is one, otherwise it returns None.
    '''
    try:
        return watcher.get_current_game(summoner_id)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        return None

def get_mastery_wrapper(bot, summoner_id, top=True):
    '''
    Returns the current player mastery if it exists, otherwise returns None.
    '''
    region1 = 'na'
    region2 = 'NA1'
    api_key = bot.configurations['discrank.py']['token']
    url = ('https://{region1}.api.pvp.net/championmastery/location/{region2}/'
        'player/{player}/{top}champions?api_key={key}')
    r = requests.get(url.format(region1=region1, region2=region2,
            player=summoner_id, top=('top' if top else ''), key=api_key))
    result = r.json()
    if 'status' in result:
        error_code = result['status']['status_code']
        if error_code == 429:
            api_cooldown()
        else:
            logging.error("This is the requests result: " + str(result))
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION, 
                    "Failed to retrieve mastery data.")
    else:
        return result

def get_top_champions(static, mastery):
    '''
    Gets the top 3 champions based on mastery. If for any reason the mastery
    argument is empty, this returns None.
    '''
    if not mastery:
        return None
    champions = ''
    for x in range(3):
        champion_id = str(mastery[x]['championId'])
        champions += static[1][champion_id]['name'] + ', '
    return champions[:-2] if champions else None

def get_mastery_details(static, mastery):
    '''
    Returns a string of details for the given mastery.
    '''
    champion_id = str(mastery['championId'])
    champion_name = static[1][champion_id]['name']
    return ('{0}:\n'
        '\tPoints: {1[championPoints]}\n'
        '\tLevel: {1[championLevel]}\n'
        '\tHighest Grade: {1[highestGrade]}\n').format(champion_name, mastery)

def get_participant(match, summoner_id, finished):
    '''
    Gets the summoner from the given match.
    '''

    if finished: # Add summoner name and match URI to final return
        for participant_entry in match['participantIdentities']:
            if participant_entry['player']['summonerId'] == summoner_id:
                index = participant_entry['participantId'] - 1
                break
        participant = match['participants'][index]
        participant.update(participant_entry['player'])
        return participant

    else: # Just the match given should be sufficient
        for participant in match['participants']:
            if participant['summonerId'] == summoner_id:
                return participant

def get_champion_kda(watcher, summoner_id, champion_id):
    '''
    Returns a string of the given summoner's KDA of the given champion. If the
    stats cannot be retrieved, return 'n/a'.
    '''
    try:
        stats = watcher.get_ranked_stats(summoner_id)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else:
            return 'n/a'
    for champion in stats['champions']:
        if champion['id'] == champion_id:
            break
    sessions = champion['stats']['totalSessionsPlayed']
    if sessions == 0:
        return 'n/a (no games)'
    kills = champion['stats']['totalChampionKills'] / sessions
    deaths = champion['stats']['totalDeathsPerSession'] / sessions
    assists = champion['stats']['totalAssists'] / sessions
    value = (kills + assists) / (1 if deaths == 0 else deaths)
    return "{0:.1f}/{1:.1f}/{2:.1f} ({3:.1f})".format(
            kills, deaths, assists, value)

def get_kill_participation(match, participant_id, side):
    '''
    Returns a string of the kill participation of the summoner in the match.
    '''
    total_kills = 0
    for participant in match['participants']:
        if participant['teamId'] == side:
            if participant['participantId'] == participant_id:
                participant_kills = participant['stats']['kills']
                participant_kills += participant['stats']['assists']
            total_kills += participant['stats']['kills']
    return '{0:.1f}%'.format(100*participant_kills/total_kills)

def get_match_table(static, match, mastery, summoner_id, finished=True, 
        verbose=False):
    '''
    Returns a scoreboard view of the given match. Values differ depending on
    whether or not the match is finished.
    '''

    participant = get_participant(match, summoner_id, finished)
    response = ''

    # Get game type
    if finished:
        queue_id = static[3][match['queueType']]
    else:
        queue_id = str(match['gameQueueConfigId'])
    game = static[3][queue_id]

    # Get KDA
    champion_id = participant['championId']
    if finished: # Pull from participant data
        stats = participant['stats']
        value = ((stats['kills'] + stats['assists']) / 
                (1 if stats['deaths'] == 0 else stats['deaths']))
        kda = "{0[kills]}/{0[deaths]}/{0[assists]} ({1})".format(stats, value)
    else: # Pull from league data
        kda = get_champion_kda(static[0], summoner_id, champion_id)

    # Very detailed table
    if verbose:
        response = '```diff\n' # Use + and - to highlight
        return "blargh"

    # Simple 3 line game info
    else:
        spell1 = static[2][str(participant['spell1Id'])]['name']
        spell2 = static[2][str(participant['spell2Id'])]['name']
        champion = static[1][str(champion_id)]['name']
        for champion_mastery in mastery:
            if champion_mastery['championId'] == champion_id:
                break
        mastery_data = "({0[championPoints]}|{0[championLevel]})".format(
                champion_mastery)
        if finished:
            status = 'Won' if participant['stats']['winner'] else 'Lost'
            kill_participation = get_kill_participation(
                    match, participant['participantId'], participant['teamId'])
            response += ("Game Type: {0}\n"
                    "{1} - {2} {3} - Kill Participation {4} - {5} - {6}\n"
                    "Status: {7}").format(game, champion, kda, mastery_data,
                            kill_participation, spell1, spell2, status)
        else:
            side = 'Blue' if participant['teamId'] == 100 else 'Red'
            minutes = int(match['gameLength']/60)
            seconds = match['gameLength'] % 60
            response += ("Game Type: {0}\n"
                    "{1} - {2} {3} - {4} - {5}\n"
                    "Side: {6}\n"
                    "Time: {7}:{8}").format(game, champion, kda, mastery_data,
                            spell1, spell2, side, minutes, seconds)
    return response

def get_summoner_information(bot, watcher, name, verbose=False):
    '''
    Returns a nicely formatted string of information about the given summoner.
    '''
    static = bot.data['discrank.py'] # Static data
    summoner = get_summoner_wrapper(watcher, name)
    mastery = get_mastery_wrapper(
            bot, summoner['id'], top=False)
    response = ("***`{0[name]}`***\n"
        "**Summoner ID:** {0[id]}\n"
        "**Level:** {0[summonerLevel]}\n"
        "**Top Champions:** {1}\n\n").format(
                summoner, get_top_champions(static, mastery))

    # Get league information
    league = get_league_wrapper(watcher, summoner['id'])
    if league:

        # Extra champion mastery data if we want extra information
        if verbose:
            mastery_details = []
            for it in range(3):
                mastery_details.append(get_mastery_details(static, mastery[it]))
            response += ("***`Champion Mastery`***\n"
                "**First:** {0}"
                "**Second:** {1}"
                "**Third:** {2}\n").format(*mastery_details)

        # Ranked statistics
        entries = league['entries'][0]
        division = league['tier'].capitalize() + ' ' + entries['division']
        wlr = 100 * entries['wins'] / (entries['wins'] + entries['losses'])
        response += ("***`Ranked Statistics`***\n"
            "**Rank:** {0}\n"
            "**League Points:** {1[leaguePoints]}\n"
            "**Wins/Losses:** {1[wins]}/{1[losses]}\n"
            "**W/L Percent:** {2:.2f}%\n\n").format(division, entries, wlr)

        # Get last match or current match information
        match = get_current_match_wrapper(watcher, summoner['id'])
        currently_playing = bool(match)
        if not currently_playing: # Get most recent match
            match_list = get_match_list_wrapper(watcher, summoner['id'])
            recent_match = get_recent_match(match_list, no_team=True)
            match = get_match_wrapper(watcher, recent_match)

        # If a suitable match was found, get the information
        if match:
            response += "***`{} Match`***\n".format(
                    'Current' if currently_playing else 'Last')
            response += get_match_table(static, match, mastery, summoner['id'],
                    finished=(not currently_playing), verbose=verbose)
        else:
            response += "A most recent match was not found..."
    else:
        response += "This summoner has not played ranked yet this season..."

    return response

async def get_response(bot, message, parsed_command, direct):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    if base == 'blitz':

        watcher = bot.data['discrank.py'][0]
        if plan_index == 0: # Get basic summoner information
            response = get_summoner_information(bot, watcher,
                    options['summoner'], verbose=('extra' in options))
        elif plan_index == 1: # Get match information
            response = "What"

    return (response, tts, message_type, extra)

async def on_ready(bot):

    # Obtain all static data required
    watcher = RiotWatcher(bot.configurations['discrank.py']['token'])
    if not watcher.can_make_request():
        raise BotException(ErrorTypes.STARTUP, EXCEPTION,
            "The given Riot API token cannot get requests.")

    # Add champions and skills by ID
    champions = watcher.static_get_champion_list(data_by_id=True)['data']
    spells = watcher.static_get_summoner_spell_list(data_by_id=True)['data']

    # Add game modes by queue type and name
    modes = {
        "0": "Custom",
        "8": "Normal 3v3",
        "2": "Normal",
        "14": "Normal Draft",
        "4": "Dynamic Queue",
        "6": "Dynamic Queue",
        "9": "Ranked 3v3",
        "41": "Ranked 3v3",
        "42": "Ranked 5v5",
        "16": "This Gamemode doesn't even exist anymore",
        "17": "Same with this one",
        "7": "Co-op vs AI",
        "25": "Co-op vs AI",
        "31": "Co-op vs AI",
        "32": "Co-op vs AI",
        "33": "Co-op vs AI",
        "52": "Co-op vs AI (3v3)",
        "61": "Team Builder",
        "65": "ARAM",
        "70": "One For All",
        "72": "Magma Chamber 1v1",
        "73": "Magma Chamber 2v2",
        "75": "Hexakill",
        "76": "URF",
        "83": "Co-op vs AI (URF)",
        "91": "Doom Bots Lv 1",
        "92": "Doom Bots Lv 2",
        "93": "Doom Bots Lv 3",
        "96": "Ascension",
        "98": "Hexakill",
        "100": "Bilgewater",
        "300": "Legend of the Poro King",
        "313": "Bilgewater ARAM",
        "400": "Team Builder",
        "410": "Dynamic Queue",
        "CUSTOM": "0",
        "NORMAL_3x3": "8",
        "NORMAL_5x5_BLIND": "2",
        "NORMAL_5x5_DRAFT": "14",
        "RANKED_SOLO_5x5": "4",
        "RANKED_PREMADE_5x5*": "6",
        "RANKED_PREMADE_3x3*": "9",
        "RANKED_TEAM_3x3": "41",
        "RANKED_TEAM_5x5": "42",
        "ODIN_5x5_BLIND": "16",
        "ODIN_5x5_DRAFT": "17",
        "BOT_5x5*": "7",
        "BOT_ODIN_5x5": "25",
        "BOT_5x5_INTRO": "31",
        "BOT_5x5_BEGINNER": "32",
        "BOT_5x5_INTERMEDIATE": "33",
        "BOT_TT_3x3": "52",
        "GROUP_FINDER_5x5": "61",
        "ARAM_5x5": "65",
        "ONEFORALL_5x5": "70",
        "FIRSTBLOOD_1x1": "72",
        "FIRSTBLOOD_2x2": "73",
        "SR_6x6": "75",
        "URF_5x5": "76",
        "BOT_URF_5x5": "83",
        "NIGHTMARE_BOT_5x5_RANK1": "91",
        "NIGHTMARE_BOT_5x5_RANK2": "92",
        "NIGHTMARE_BOT_5x5_RANK5": "93",
        "ASCENSION_5x5": "96",
        "HEXAKILL": "98",
        "BILGEWATER_ARAM_5x5": "100",
        "KING_PORO_5x5": "300",
        "COUNTER_PICK": "310",
        "BILGEWATER_5x5": "313",
        "TEAM_BUILDER_DRAFT_UNRANKED_5x5": "400",
        "TEAM_BUILDER_DRAFT_RANKED_5x5": "410"
    }

    bot.data['discrank.py'] = [watcher, champions, spells, modes]

