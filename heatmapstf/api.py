"""
heatmapstf is an API wrapper over the heatmaps.tf site which seeks to provide and easy interface to the data
as well as additional tools to minimize the amount of work needed to get the data in a very usable form. The
API reports kill data from many non-Valve TF2 servers.

Example Usage:
    from heatmapstf import HeatmapsAPI
    api = HeatmapsAPI()
    print api.get_all_map_statistics()
    print api.get_kill_data('ctf_2fort', limit=50)
"""
__author__ = 'Robert P. Cope'

import requests
import logging

from utils import rate_limit

heatmaps_logger = logging.getLogger(__name__)
if not heatmaps_logger.handlers:
    ch = logging.StreamHandler()
    heatmaps_logger.addHandler(ch)
    heatmaps_logger.setLevel(logging.INFO)


class TFMap(object):
    def __init__(self, json_dict):
        self.__dict__.update(json_dict)


class TFKillData(object):
    def __init__(self, data_dict):
        self.__dict__.update(data_dict)


#TODO: Find a way to import all item definitions correctly.
class HeatmapsTFAPI(object):
    API_BASE_URI = 'http://heatmaps.tf'

    DEFAULT_DELAY_TIME = 500  # Delay time in ms (let's play nice)

    FIELDS_LIST = {'id', 'timestamp', 'killer_class', 'killer_weapon', 'killer_x', 'killer_y', 'killer_z',
                   'victim_class', 'victim_x', 'victim_y', 'victim_z', 'customkill', 'damagebits', 'death_flags',
                   'team'}

    TEAMS = {'red', 'blue', 'spectator', 'teamless'}

    CLASSES = {'scout', 'sniper', 'demoman', 'medic', 'pyro', 'heavy', 'spy', 'engineer', 'soldier', 'unknown'}

    CUSTOM_KILLS = {1: 'Headshot',
                    2: 'Backstab',
                    3:	'Burning',
                    4:	'Wrench Fix',
                    5:	'Minigun',
                    6:	'Suicide',
                    7:	'Hadouken Taunt (Pyro)',
                    8:	'Burning Flare',
                    9:	'High Noon Taunt (Heavy)',
                    10:	'Grand Slam Taunt (Scout)',
                    11:	'Penetrate My Team',
                    12:	'Penetrate All Players',
                    13:	'Fencing Taunt (Spy)',
                    14:	'Penetrate Headshot',
                    15:	'Arrow Stab Taunt (Sniper)',
                    16:	'Telefrag',
                    17:	'Burning Arrow',
                    18:	'Flyingburn',
                    19:	'Pumpkin Bomb',
                    20:	'Decapitation',
                    21:	'Grenade Taunt (Soldier)',
                    22:	'Baseball',
                    23:	'Charge Impact',
                    24:	'Barbarian Swing Taunt (Demoman',
                    25:	'Air Sticky Burst',
                    26:	'Defensive Sticky (Scottish Resistance?)',
                    27:	'Pickaxe',
                    28:	'Direct Hit Rocket',
                    29:	'Decapitation Boss',
                    30:	'Stickbomb Explosion',
                    31:	'Aegis Round',
                    32:	'Flare Explosion',
                    33:	'Boots Stomp',
                    34:	'Plasma',
                    35:	'Plasma Charged',
                    36:	'Plasma Gib',
                    37:	'Practice Sticky',
                    38:	'Eyeball Rocket',
                    39:	'Headshot Decapitation',
                    40:	'Armageddon Taunt (Pyro)',
                    41:	'Flare Pellet',
                    42:	'Cleaver',
                    43:	'Cleaver Crit',
                    44:	'Sapper Recorder Death',
                    45:	'Merasmus Player Bomb',
                    46:	'Merasmus Grenade',
                    47:	'Merasmus Zap',
                    48:	'Merasmus Decapitation',
                    49:	'Cannonball Push',
                    50:	'Guitar Riff Taunt (UNUSED)'}

    DEATH_FLAGS = {1:   'Killer Domination',
                   2:	'Assister Domination',
                   4:	'Killer Revenge',
                   8:	'Assister Revenge',
                   16:	'First Blood',
                   32:	'Dead Ringer',
                   64:	'Interrupted',
                   128:	'Gibbed',
                   256:	'Purgatory'}

    KILLER_INDEX = {0: 'Unknown',
                    1: 'Scout',
                    2: 'Sniper',
                    3: 'Soldier',
                    4: 'Demoman',
                    5: 'Medic',
                    6: 'Heavy',
                    7: 'Pyro',
                    8: 'Spy',
                    9: 'Engineer'}

    ITEM_INDEX = {-1: 'Sentry',
                  -2: 'Mini-Sentry'}

    def __init__(self):
        heatmaps_logger.info('HeatmapsTFAPI intialized.')
        self.session = requests.Session()


    @rate_limit(wait_time=DEFAULT_DELAY_TIME)
    def _get_data(self, sub_uri, params=None, headers=None):
        #Convert them to empty dicts if nothing was passed in.
        headers = headers or {}
        params = params or {}
        url = "{base_uri}/{sub_uri}".format(base_uri=self.API_BASE_URI, sub_uri=sub_uri)
        response = self.session.get(url, headers=headers, params=params)
        print response.url
        response.raise_for_status()
        return response.json()

    def get_all_map_statistics(self, raw=False):
        """
        Grab a list of all the maps available and their associated names and kill counts.
        :param raw: (OPTIONAL) If raw is True, return the raw JSON from the API, otherwise return a list of
                    TFMap objects, each of which have attributes 'name' and 'kill_count'
        :return: A list of dicts in raw mode or TFMap objects is not in raw mode with the map name and kill count.
        """
        try:
            map_statistics_list = self._get_data('data/maps.json')
            return map_statistics_list if raw else map(TFMap, map_statistics_list)
        except requests.HTTPError as e:
            heatmaps_logger.exception('Faulted on bad HTTP status trying to get all map statistics from'
                                      ' data/maps.json!')
            raise e

    @staticmethod
    def _check_data(data, expected_set, message, exception_mesage):
        try:
            assert set(data) <= expected_set
        except AssertionError:
            heatmaps_logger.exception(message)
            heatmaps_logger.error('Bad values: {}'.format(set(data) - expected_set))
            raise ValueError(exception_mesage)

    #TODO: Make sure none of this code is too ridiculously dangerous.
    def _clean_kill_data(self, raw_response):
        map_data = raw_response.get('map_data')
        field_names = raw_response.get('fields')
        cleaned_kills = []
        for kill in raw_response.get('kills'):
            data_dict = dict([(field_names[i], value) for i, value in enumerate(kill)])
            data_dict['map_data'] = map_data
            if 'killer_class' in field_names:
                data_dict['killer_class_name'] = self.KILLER_INDEX.get(data_dict.get('killer_class'))
            if 'victim_class' in field_names:
                data_dict['victim_class_name'] = self.KILLER_INDEX.get(data_dict.get('victim_class'))
            if 'killer_weapon' in field_names:
                data_dict['killer_weapon_name'] = self.ITEM_INDEX.get(data_dict.get('killer_weapon'))
            if 'customkill' in field_names:
                data_dict['customkill_name'] = self.CUSTOM_KILLS.get(data_dict.get('customkill'))
            if 'death_flags' in field_names:
                flag_names = map(self.DEATH_FLAGS.get,
                                 [2 ** i for i in xrange(9) if 2 ** i in data_dict['death_flags']])
                data_dict['death_flag_names'] = flag_names

            cleaned_kills.append(TFKillData(data_dict))
        return cleaned_kills

    def get_kill_data(self, map_name, fields=None, limit=50, killer_classes=None, killer_teams=None,
                      victim_classes=None, raw=False):
        """

        :param map_name: The name of the map to retrieve data for.
        :param fields: (OPTIONAL) A list of fields to return in the query.

            Possible Fields:
            ------------------------------------------
            id - The internal identifier for this kill
            timestamp - The UNIX timestamp at which this kill occured
            killer_class - The class of the killer
            killer_weapon - The weapon of the killer
            killer_x
            killer_y
            killer_z
            victim_class - The class of the killer
            victim_x
            victim_y
            victim_z
            customkill - The custom kill bits for this kill
            damagebits - The damage bits for this kill
            death_flags - The death flags for this kill
            team - The team of the killer

            NOTE: For some fields, _if raw mode is off_, additional fields will be returned with interpreted results.
            killer_class and victim_class will also yield killer_class_name and victim_class_name, which are the names
            corresponding to the class index returned by the API. killer_weapon will yield killer_weapon_name which
            gives the name of the weapon used. customkill will yield customkill_name, which is the name that the
            customkill details, and death_flags will yeild a new list called death_flag_names, which gives the
            string names of all the death flags that apply to the kill.

        :param limit: (OPTIONAL) The maximum number of query results to return. Default is 50
        :param killer_classes: (OPTIONAL) A list of classes that executed the kill to search over. Default is all.

            Possible Killer Classes
            ------------------------------------------
            unknown
            scout
            sniper
            soldier
            demoman
            medic
            heavy
            pyro
            spy
            engineer

        :param killer_teams: (OPTIONAL) A list of teams the killer was on to search over. Default is all.

            Possible Killer Teams
            ------------------------------------------
            teamless
            spectator
            red
            blu


        :param victim_classes: (OPTIONAL) A list of classes that were killed to search over. Default is all.

            Possible Victim Classes
            ------------------------------------------
            unknown
            scout
            sniper
            soldier
            demoman
            medic
            heavy
            pyro
            spy
            engineer

        :param raw: If true, return the raw JSON, if false, convert everything into TFKill objects, and return
                    extra data about some fields.
        :return: Raw JSON data from the call or a list of TFKill objects detailing each kill.
        """
        params = {}
        params.update(limit=limit)
        if fields:
            self._check_data(fields, self.FIELDS_LIST,
                             'Threw assert because of bad fields argument: {}'.format(fields),
                             'An invalid field type was specified!')
            params.update(fields=",".join(fields))
        if killer_classes:
            self._check_data(killer_classes, self.CLASSES,
                             'Threw assert because of bad killer_classes argument: {}'.format(killer_classes),
                             'An invalid value was give in killer_classes!')
            params.update(killer_class=",".join(killer_classes))
        if killer_teams:
            self._check_data(killer_teams, self.TEAMS,
                             'Threw assert because of bad killer_teams argument: {}'.format(killer_teams),
                             'An invalid value was given in killer_teams!')
            params.update(killer_team=",".join(killer_teams))
        if victim_classes:
            self._check_data(victim_classes, self.CLASSES,
                             'Threw assert because of bad victim_classes argument: {}'.format(victim_classes),
                             'An invalid value was give in victim_classes!')
            params.update(victim_class=",".join(victim_classes))
        try:
            print params
            sub_uri = 'data/kills/{map_name}.json'.format(map_name=map_name)
            response = self._get_data(sub_uri, params=params)
            return response if raw else self._clean_kill_data(response)
        except requests.HTTPError as e:
            heatmaps_logger.exception('Send bad data or server not responding!')
            raise e