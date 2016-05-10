import discord
import asyncio
import requests
import time
import random
import math

# Debugging
import logging

from riotwatcher import RiotWatcher
from riotwatcher import LoLException, error_429

from jshbot.exceptions import ErrorTypes, BotException

__version__ = '0.1.3'
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
        'match: ?basic',
        'mastery: ?champion:',
        'challenge ::::',
        'chests:'],[
        ('summoner', 'user', 's', 'i', 'info'),
        ('extra', 'x', 'e', 'verbose', 'detail', 'detailed', 'more'),
        ('basic', 'b', 'simple', 'concise'),
        ('champion', 'c'),
        ('chests', 'chest', 'box', 'boxes')])

    shortcuts['summoner'] = ('blitz -summoner {}', '^')
    shortcuts['mastery'] = ('blitz -mastery {}', '^')
    shortcuts['challenge'] = ('blitz -challenge {} {} {} {}', '::::')

    manual['blitz'] = {
        'description': 'Get League of Legends information from the API.',
        'usage': [
            ('-summoner <summoner> (-extra)', 'Gets the information of the '
                'given summoner. Extra information provides a more verbose '
                'result.'),
            ('-match <summoner> (-basic)', 'Gets the current or most '
                'recent ranked match data.'),
            ('-mastery <summoner> (-champion <champion>)', 'Gets the mastery '
                'data of the given summoner.'),
            ('-challenge <summoner 1> <summoner 2> <champion 1> <champion 2>',
                'This command compares two summoner\'s mastery points, '
                'mastery levels, and # of games played (ranked) data against '
                'each other.'),
            ('-chests <summoner>', 'Gets the available chests for the given '
                'summoner.')],
        'shortcuts': [
            ('summoner <arguments>', '-summoner <arguments>'),
            ('challenge <summoner 1> <summoner 2> <champion 1> <champion 2>',
                '-challenge <summoner 1> <summoner 2> <champion 1> '
                '<champion 2>'),
            ('mastery <arguments>', '-mastery <arguments>')]}

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

def get_league_wrapper(watcher, summoner_ids):
    '''
    Wraps the obtaining of a league with exception handling. Returns an empty
    dictionary if the summoner has not played any ranked games.
    '''
    try:
        if type(summoner_ids) is list:
            return watcher.get_league_entry(summoner_ids=summoner_ids)
        else:
            league = watcher.get_league_entry(summoner_ids=[summoner_ids])
            return league[str(summoner_ids)][0]
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else:
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
    try: # TODO: Convert to recent game instead, but the API is so different
        return watcher.get_match_list(summoner_id)['matches']
    except Exception as e:
        if e == error_429:
            api_cooldown()
        else:
            logging.warn("Summoner has no match list.")
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
    Returns the current match if there is one, otherwise returns None.
    '''
    try:
        return watcher.get_current_game(summoner_id)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        return None

def get_mastery_wrapper(bot, summoner_id, top=True, champion_id=None):
    '''
    Returns the current player mastery if it exists, otherwise returns None.
    If champion_id is specified, this gets mastery data about that specific
    champion.
    '''
    region1 = 'na'
    region2 = 'NA1'
    api_key = bot.configurations['discrank.py']['token']
    if champion_id:
        champion = '/{}'.format(champion_id)
        top=False
    else:
        champion = 's'
    url = ('https://{region1}.api.pvp.net/championmastery/location/{region2}/'
        'player/{player}/{top}champion{champion}?api_key={key}').format(
            region1=region1, region2=region2, player=summoner_id, 
            top=('top' if top else ''), champion=champion, key=api_key)
    r = requests.get(url)
    try:
        result = r.json()
    except:
        return None
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
        for index, participant in enumerate(match['participants']):
            if participant['summonerId'] == summoner_id:
                participant['participantId'] = index + 1
                return participant

def get_champion_kda(watcher, summoner_id, champion_id):
    '''
    Returns a string of the given summoner's KDA of the given champion. If the
    stats cannot be retrieved, return '0/0/0 (0)', or 'API Limit' if the API is
    being rate limited.
    '''
    try:
        stats = watcher.get_ranked_stats(summoner_id)
    except LoLException as e:
        if e == error_429:
            return 'API Limit'
        else: # Champion data not found
            return '0/0/0 (0)'
    for champion in stats['champions']:
        if champion['id'] == champion_id:
            break
    sessions = champion['stats']['totalSessionsPlayed']
    if sessions == 0:
        return '0/0/0 (0)'
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

def get_bans(static, match, team, finished=True):
    '''
    Returns the 3 bans for the given team in the given match.
    '''
    bans = []
    if finished:
        ban_list = match['teams'][int((team/100) - 1)]['bans']
        for it in range(3):
            bans.append(static[1][str(ban_list[it]['championId'])]['name'])
    else:
        for ban in match['bannedChampions']:
            if ban['teamId'] == team:
                bans.append(static[1][str(ban['championId'])]['name'])
    return bans


def get_match_table(static, match, mastery, summoner_id, finished=True, 
        verbose=False):
    '''
    Returns a scoreboard view of the given match. Values differ depending on
    whether or not the match is finished.
    '''

    # For rank stuff later
    divisions = {
        "V": "5",
        "IV": "4",
        "III": "3",
        "II": "2",
        "I": "1"
    }

    participant = get_participant(match, summoner_id, finished)
    response = ''

    # Get game type and also time if the game is not finished
    if finished:
        queue_id = static[3][match['queueType']]
        game_length_key = 'matchDuration'
    else:
        try:
            queue_id = str(match['gameQueueConfigId'])
        except KeyError:
            queue_id = '0'
        game_length_key = 'gameLength'
    total_length = int(match[game_length_key]) + 180
    minutes = str(int(total_length/60))
    seconds = "{0:02d}".format(total_length % 60)
    game = static[3][queue_id]

    # Get ranking for each player
    summoners = []
    for index, member in enumerate(match['participants']):
        if finished:
            summoner = match['participantIdentities'][index]
            summoners.append(summoner['player']['summonerId'])
        else:
            summoners.append(member['summonerId'])
    league_data = get_league_wrapper(static[0], summoners)

    # Very detailed table
    if verbose:
        response = '```diff\n' # Use + and - to highlight

        # Get winning team number
        if finished and participant['stats']['winner']:
            winning_team = participant['teamId']
        elif finished:
            winning_team = 100 if participant['teamId'] == 200 else 100

        # Add current game time
        response += "{2}Game Time: {0}:{1}\n\n".format(minutes, seconds,
                '' if finished else 'Current ')

        # Loop through each team
        for team in (100, 200):
            
            # Game type
            response += 'Game Type: {}\n'.format(game)
            response += '{} Team'.format(
                    'Blue' if team == 100 else 'Red')

            # Get bans
            try:
                bans = "{0}, {1}, {2}".format(
                        *get_bans(static, match, team, finished))
                response += ' -- Bans [{}]'.format(bans)
            except:
                logging.warn("No bans.")

            # Add game won or lost
            if finished:
                status = 'WON' if team == winning_team else 'LOST'
                response += ' [{}]\n'.format(status)
            else:
                response += '\n'

            # Loop through each participant on the team
            response += ('  Summoner         Rank | Champion     | '
                    'KDA                   | Spell 1  | Spell 2  |\n'
                    '------------------------|--------------|-'
                    '----------------------|----------|----------|\n')
            for index, member in enumerate(match['participants']):
                if member['teamId'] != team: # Continue
                    continue
                
                # Get summoner name
                if finished:
                    summoner = match['participantIdentities'][index]
                    summoner_name = summoner['player']['summonerName']
                    summoner_id = str(summoner['player']['summonerId'])
                else:
                    summoner_name = member['summonerName']
                    summoner_id = str(member['summonerId'])

                # Get summoner rank
                if summoner_id in league_data:
                    league = league_data[summoner_id][0]
                    rank = '({0}{1})'.format(league['tier'][0],
                            divisions[league['entries'][0]['division']])
                else:
                    rank = ''

                # Get champion name and spell names
                champion = static[1][str(member['championId'])]['name']
                spell1 = static[2][str(member['spell1Id'])]['name']
                spell2 = static[2][str(member['spell2Id'])]['name']
                
                # Get KDA
                if finished: # Pull from participant data
                    stats = member['stats']
                    kills, deaths = stats['kills'], stats['deaths']
                    assists = stats['assists']
                    value = "({0:.1f})".format(((kills + assists) / 
                            (1 if deaths == 0 else deaths)))
                    kda = "{0[kills]}/{0[deaths]}/{0[assists]} {1}".format(
                            stats, value)
                else:
                    kda = get_champion_kda(static[0], member['summonerId'],
                            member['championId'])

                # Highlight summoner if this is the one we're looking for
                if index == participant['participantId'] - 1:
                    response += '+ '
                else:
                    response += '  '

                # Add champion name, kda, and spells
                response += ('{}'.format(summoner_name)).ljust(17)
                response += ('{}'.format(rank)).rjust(4) + ' | '
                response += ('{}'.format(champion)).ljust(13) + '| '
                response += ('{}'.format(kda)).ljust(22) + '| '
                response += ('{}'.format(spell1)).ljust(9) + '| '
                response += ('{}'.format(spell2)).ljust(9) + '|'
                response += '\n'

            response += '\n'

        response += '\n```\n'

    # Simple 3-4 line game info
    else:

        # Get KDA
        champion_id = participant['championId']
        if finished: # Pull from participant data
            stats = participant['stats']
            value = "({0:.1f})".format(((stats['kills'] + stats['assists']) / 
                    (1 if stats['deaths'] == 0 else stats['deaths'])))
            kda = "{0[kills]}/{0[deaths]}/{0[assists]} {1}".format(stats, value)
        else: # Pull from league data
            kda = get_champion_kda(static[0], summoner_id, champion_id)

        # Get spell names
        spell1 = static[2][str(participant['spell1Id'])]['name']
        spell2 = static[2][str(participant['spell2Id'])]['name']
        champion = static[1][str(champion_id)]['name']

        # Get mastery data
        for champion_mastery in mastery:
            if champion_mastery['championId'] == champion_id:
                break
        mastery_data = "({0[championPoints]}|{0[championLevel]})".format(
                champion_mastery)

        # Format response
        if finished:
            status = 'Won' if participant['stats']['winner'] else 'Lost'
            kill_participation = get_kill_participation(
                    match, participant['participantId'], participant['teamId'])
            response += ("**Game Type:** {0}\n"
                    "{1} - {2} {3} - Kill Participation {4} - {5} - {6}\n"
                    "Status: {7}").format(game, champion, kda, mastery_data,
                            kill_participation, spell1, spell2, status)
        else:
            side = 'Blue' if participant['teamId'] == 100 else 'Red'
            response += ("**Game Type:** {0}\n"
                    "{1} - {2} {3} - {4} - {5}\n"
                    "Side: {6}\n"
                    "Time: {7}:{8}").format(game, champion, kda, mastery_data, 
                            spell1, spell2, side, minutes, seconds)

    return response

def get_match_table_wrapper(bot, static, watcher, name, verbose=False):
    '''
    Gets the match table. Makes the calling method easier to look at.
    '''

    summoner = get_summoner_wrapper(watcher, name)
    mastery = get_mastery_wrapper(bot, summoner['id'], top=False)

    # Get last match or current match information
    match = get_current_match_wrapper(watcher, summoner['id'])
    currently_playing = bool(match)
    if not currently_playing: # Get most recent match
        match_list = get_match_list_wrapper(watcher, summoner['id'])
        recent_match = get_recent_match(match_list, no_team=True)
        match = get_match_wrapper(watcher, recent_match)

    # If a suitable match was found, get the information
    if match:
        return get_match_table(static, match, mastery, summoner['id'],
                finished=(not currently_playing), verbose=verbose)
    else:
        return "A most recent match was not found..."

def get_summoner_information(bot, static, watcher, name, verbose=False):
    '''
    Returns a nicely formatted string of information about the given summoner.
    '''
    summoner = get_summoner_wrapper(watcher, name)
    mastery = get_mastery_wrapper(bot, summoner['id'], top=False)
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
    else:
        response += "This summoner has not played ranked yet this season...\n"

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
                finished=(not currently_playing), verbose=False)
    else:
        response += "A most recent match was not found...\n"

    return response

def get_formatted_mastery_data(static, champion_data):
    '''
    Returns a formatted string of the given champion mastery data.
    '''
    champion_name = static[1][str(champion_data['championId'])]['name']
    chest = 'Yes' if champion_data['chestGranted'] else 'No'
    if 'lastPlayTime' in champion_data:
        last_played = time.time() - champion_data['lastPlayTime']/1000
        last_played = '{0:.1f} d'.format(last_played/86400)
    else: # No data
        last_played = 'Unknown'
    if 'highestGrade' in champion_data:
        highest_grade = champion_data['highestGrade']
    else:
        highest_grade = 'n/a'
    response = '{}'.format(champion_name).ljust(14) + '| '
    response += '{0[championPoints]}'.format(champion_data).ljust(10) + '| '
    response += '{0[championLevel]}'.format(champion_data).ljust(4) + '| '
    response += '{}'.format(chest).ljust(4) + '| '
    response += '{}'.format(highest_grade).ljust(6) + '| '
    response += '{}'.format(last_played)
    return response + '\n'

def get_mastery_table(bot, static, watcher, name, champion=None):
    '''
    Gets mastery information for the given summoner. If the champion argument
    is specified, it will find the details of that champion only.
    The table generated will be the top 10 champions of the summoner.
    '''
    summoner = get_summoner_wrapper(watcher, name)
    if champion:
        try:
            champion_id = static[1][champion.replace(' ', '').lower()]['id']
            champion_data = get_mastery_wrapper(bot, summoner['id'], 
                    champion_id=champion_id)
        except KeyError:
            raise BotException(ErrorTypes.RECOVERABLE, EXCEPTION,
                    "Champion not found.")
    else:
        champion_data = get_mastery_wrapper(bot, summoner['id'], top=False)
    
    labels = '#  | Champion      | Points    | Lvl | Box | Grade | Last Played '
    line = '---|---------------|-----------|-----|-----|-------|-------------'

    if champion:
        labels = labels[5:]
        line = line[5:]

    response = '```\n{}\n{}\n'.format(labels, line)

    if champion:
        response += get_formatted_mastery_data(static, champion_data)
    else:
        for it in range(10):
            response += '{}'.format(it + 1).ljust(3) + '| '
            response += get_formatted_mastery_data(static, champion_data[it])
    return response + '```'

def get_ranked_stats_wrapper(watcher, summoner_id):
    '''
    Returns the ranked stats with error checking. Returns None if the stats
    do not exist.
    '''
    try:
        return watcher.get_ranked_stats(summoner_id)
    except LoLException as e:
        if e == error_429:
            api_cooldown()
        else:
            return None

def get_challenge_result(bot, static, watcher, arguments):
    '''
    This returns a result of the challenge minigame. The minigame consists of
    pitting two summoners' champions' mastery values against each other. 
    '''

    summoners = [arguments[0], arguments[1]]
    champions = [arguments[2], arguments[3]]
    games = [0, 0]
    names = ['', '']
    ids = [0, 0]

    for it in range(2):

        # Get summoner data and champion ID
        summoners[it] = get_summoner_wrapper(watcher, summoners[it])
        names[it] = summoners[it]['name']
        try: # In case the champion isn't valid
            champions[it] = static[1][champions[it].replace(' ', '').lower()]
            champions[it] = champions[it]['id']
        except KeyError:
            return "Could not find the champion {}.".format(champions[it])

        # Get ranked stats for total games played on each champion
        ids[it] = summoners[it]['id']
        summoners[it] = get_ranked_stats_wrapper(watcher, ids[it])

        if summoners[it]:
            for champion in summoners[it]['champions']:
                if champion['id'] == champions[it]:
                    games[it] = champion['stats']['totalSessionsPlayed']
        if not games[it] or games[it] == 1:
            games[it] = math.e

        # Get champion mastery data for each champion
        data = get_mastery_wrapper(bot, ids[it], champion_id=champions[it])
        if data:
            champions[it] = (data['championPoints'], data['championLevel'])
        else: # No mastery data on this champion
            champions[it] = (math.e, 1)

    # Do the calculation
    if champions[0][1] and champions[1][1] and games[0] and games[1]:

        # Give approximate chance score
        scores = [0, 0]

        # Do calculation stuff
        for it in range(2):
            scores[it] = (champions[it][1] * math.log1p(games[it]) *
                math.log1p(champions[it][0]))

        # Calculate chance
        total = scores[0] + scores[1]
        response = ("Chance of {0} winning: {1:.2f}%\n"
            "Chance of {2} winning: {3:.2f}%\n").format(
                    names[0], 100 * scores[0] / total,
                    names[1], 100 * scores[1] / total)

        # Calculate winner
        random_value = random.random() * total
        response += 'The RNG gods rolled: {0:.1f}\n'.format(random_value)
        response += 'The winner is **{}**!'.format(
                names[0] if random_value < scores[0] else names[1])

        return response

    else:
        return "Something bad happened. Please report!"

def get_chests(bot, static, watcher, name):
    '''
    Returns a formatted string with the list of chests that a summoner has not
    obtained yet through mastery.
    '''

    # Get mastery data
    summoner = get_summoner_wrapper(watcher, name)
    mastery = get_mastery_wrapper(bot, summoner['id'], top=False)
    response = ("Here is a list of champions that {} has not received a chest "
            "for:\n").format(summoner['name'])
    champions = []
    for data in mastery: # Look for chests that can be obtained
        if not data['chestGranted']:
            champion_name = static[1][str(data['championId'])]['name']
            champions.append(champion_name)
    champions.sort()

    if not champions:
        return "This summoner has no mastery data."

    # Format the result
    for it in range(len(champions) % 6):
        champions.append('') # Fill out the rest with empty strings
    total_length = len(champions)

    response += '```\n'
    for it in range(int(total_length/6)):
        for it2 in range(6):
            response += '{}'.format(champions[6*it + it2]).ljust(14)
        response += '\n'
    response += '```'

    return response

async def get_response(bot, message, parsed_command, direct):

    response = ''
    tts = False
    message_type = 0
    extra = None
    base, plan_index, options, arguments = parsed_command

    if base == 'blitz':

        static = bot.data['discrank.py'] # Static data and the watcher
        if plan_index == 0: # Get basic summoner information
            response = get_summoner_information(bot, static, static[0],
                    options['summoner'], verbose=('extra' in options))
        elif plan_index == 1: # Get match information
            response = get_match_table_wrapper(bot, static, static[0],
                    options['match'], verbose=(not 'basic' in options))
        elif plan_index == 2: # Get mastery table
            champion = options['champion'] if 'champion' in options else None
            response = get_mastery_table(bot, static, static[0],
                    options['mastery'], champion=champion)
        elif plan_index == 3: # Challenge
            response = get_challenge_result(bot, static, static[0], arguments)
        elif plan_index == 4: # Chests
            response = get_chests(bot, static, static[0], options['chests']) 

    return (response, tts, message_type, extra)

async def on_ready(bot):

    # Obtain all static data required
    watcher = RiotWatcher(bot.configurations['discrank.py']['token'])
    if not watcher.can_make_request():
        raise BotException(ErrorTypes.STARTUP, EXCEPTION,
            "The given Riot API token cannot get requests.")

    # Add champions by ID and name, and skills by ID
    champions = watcher.static_get_champion_list(data_by_id=True)['data']
    champions_named = watcher.static_get_champion_list()['data']
    champions_named = dict(
            (key.lower(), value) for key, value in champions_named.items())
    champions.update(champions_named)
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

