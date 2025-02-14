# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument, attribute-defined-outside-init

'''doc'''
####################################################################################
### If new classes are added here, we must add to write_hints._get_white_list_words#
####################################################################################

##################################################################################
# if add another UNSPECIFIED class, update mmo.write_hints.py:make_species_hints #
##################################################################################

import os.path as _path

from xlwings import view as _view

import funclib.stringslib as _stringslib

from funclib.baselib import list_flatten as _flat
import funclib.pandaslib as _pd

import gazetteerdb.gaz as _gaz

from mmodb import species as _species
from mmodb import cb as _cb
from nlp import baselib as _nlpbase
from nlp import typo as _typo
from nlp import relib as _relib
import funclib.iolib as _iolib
import mmo.settings as _settings



all_ = set()
all_single = set()


class Substitutions():
    '''known substitutions used to expand the gazetteer'''
    scars = ['scar', 'scars', 'skier', 'skiers', 'skeer', 'skeers']
    docks = ['dock', 'docks']
    beach = ['beach', 'sand', 'sands']
    prom = ['prom', 'promenade', 'esplanade']
    breakwater = ['breakwater', 'breaky', 'breakey', 'breakie']
    marsh = ['marsh', 'marshes', 'marshs']
    rock = ['rock', 'rocks']
    ledge = ['ledge', 'ledges']
    platform = ['platform', 'platforms']
    jetty = ['jetty', 'quay']
    headland = ['headland', 'promontory', 'ness']




class UnspecifiedKeys():
    '''dictionary keys for unspecified
    dicts. for convieniance'''
    blenny = 'blenny (unspecified)'
    bream = 'bream (unspecified)'
    eel = 'eel (unspecified)'
    flatfish = 'flatfish (unspecified)'
    goby = 'goby (unspecified)'
    gurnard = 'gurnard (unspecified)'
    mullet = 'mullet (unspecified)'
    pipefish = 'pipefish (unspecified)'
    rockling = 'rockling (unspecified)'
    sand_eel = 'sand eel (unspecified)'
    sea_scorpion = 'sea scorpion (unspecified)'
    shad = 'shad (unspecified)'
    skate_ray = 'skate/ray (unspecified)'
    sole = 'sole (unspecified)'
    squid = 'squid (unspecified)'
    sturgeon = 'sturgeon (unspecified)'
    weeverfish = 'weeverfish (unspecified)'
    wrasse = 'wrasse (unspecified)'


#region helper funcs
def _clean(lst):
    '''clean list'''
    return  [_stringslib.filter_alphanumeric1(s, strict=True, remove_double_quote=True, remove_single_quote=True).lower() for s in lst]

def _fixiter(v, type_=list):
    '''fx'''
    if isinstance(v, (float, int, str)):
        return type_(v)
    return v

def _get_season(month_key):
    '''given a month get the season'''
    if month_key in ['december', 'january', 'february']: return 'winter'
    if month_key in ['march', 'april', 'may']: return 'spring'
    if month_key in ['june', 'july', 'august']: return 'summer'
    return 'autumn'
#endregion

TYPOS_MIN_LENGTH = 5
TYPOS_FIX_FIRST_N_CHARS = 2
TYPO_OPTIONS_ALL = set(('nouns_common', 'nouns_proper', 'verbs', 'phrases', 'adjectives')) #these match the allowed word types in NEBLists, they arnt relevant for the dict classes because they are all nouns


#this is used in clean_ugc.py as search replace on ugc content before writing to txt_cleaned and title_cleaned
UGC_PHRASE_SUBSTITUTION_DICT = {
                'rod': ['bass rod', 'seabass rod', 'flatty rod', 'flattie rod', 'flatfish rod', 'shark rod', 'mackerel rod', 'mackeral rod', 'mackie rod', 'boat rod', 'salmon rod', 'trout rod', 'seatrout rod'], 
                'feathers': ['mackerel feathers', 'mackeral feathers', 'mackie feathers', 'herring feathers'],
                'fly': ['mullet fly', 'seatrout fly', 'trout fly', 'salmon fly'],
                'flies': ['mullet flies', 'seatrout flies', 'trout flies', 'salmon flies']
                }


#also see spreadsheet sources_master.xlsx
FORUM_IFCA_AFLOAT = {
                'boat angling / angling afloat': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'boat-fishing-reports': ['north east', 'north west', 'northumberland'],
                'boat talk': ['cornwall', 'devon and severn', 'southern'],
                'general boat fishing talk': ['cornwall', 'devon and severn', 'southern'],
                'boat owners forum': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'south coast': ['southern', 'sussex'], 'whitby, holderness & the humber catch reports': ['north east', 'eastern'],
                'boat fishing nesa': ['north east', 'northumberland'],
                'boat catch reports nesa': ['north east', 'northumberland']
                }

FORUM_IFCA_CHARTER = {
                'latest fishing reports england': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'], #charterboat uk
                'charterboatuk boats': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'], #charterboat uk
                'cbuk boat detail text wales-scotland': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'] #charterboat uk
                }

FORUM_IFCA_KAYAK = {
                'kayak angling forum': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'kayak-fishing-reports': ['north east', 'north west', 'northumberland'],
                'fishing kayaks': ['cornwall', 'devon and severn', 'southern', ''],
                'kayak fishing': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'kayak': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex']}

FORUM_IFCA_SHORE = {'sea fishing and venue questions': ['north west'],
                'north-west-fishing-reports': ['north west'],
                'humber estuary': ['north east', 'eastern'], 
                'north east catch reports': ['north east', 'northumberland'],
                'easy access venues/directions for all areas': ['north west'],
                'thames estuary': ['kent and essex', 'eastern'],
                'tsf sea fishing': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'isle of wight': ['southern'],
                'south west coast': ['devon and severn', 'cornwall', 'isles of scilly'],
                'east-coast-sea-fishing-reports': ['eastern', 'kent and essex'],
                'dorset fishing': ['southern'],
                'east coast catch reports': ['eastern', 'kent and essex'],
                'south-west-sea-fishing-reports': ['devon and severn', 'cornwall', 'isles of scilly'],
                'south-east-sea-fishing-reports': ['sussex', 'eastern'],
                'east coast': ['eastern', 'north east', 'northumberland'],
                'cornwall fishing': ['cornwall'],
                'north west coast': ['north west'],
                'north east coast': ['north east', 'northumberland'],
                'south east coast': ['sussex', 'kent and essex', 'eastern'],
                'beach talk': ['southern', 'cornwall', 'devon and severn'],
                'south east catch reports': ['sussex', 'kent and essex'],
                'south-coast-sea-fishing-reports': ['sussex', 'southern'],
                'south coast & ci catch reports': ['southern', 'sussex'], 
                'south west catch reports': ['southern', 'devon and severn', 'cornwall', 'isles of scilly'],
                'fishing session reports': ['north west'],
                'north west & the isle of man catch reports': ['north west'],
                'somerset fishing': ['devon and severn'],
                'devon fishing': ['devon and severn'],
                'north-east-sea-fishing-reports': ['north east', 'northumberland'],
                'merseyside/fylde coast/cumbrian venues/directions': ['north west'],
                'sea fishing': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'west coast': ['cornwall', 'devon and severn'],
                'where-to-sea-fish': ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'],
                'shore catch reports nesa': ['north east', 'northumberland'],
                'shore fishing nesa': ['north east', 'northumberland'],
                'lure fishing nesa': ['north east', 'northumberland'],
                'lure catch reports nesa': ['north east', 'northumberland'],
                'shore fishing missed nesa': ['north east', 'northumberland']
                }

FORUM_IFCA = {**FORUM_IFCA_SHORE, **FORUM_IFCA_KAYAK, **FORUM_IFCA_AFLOAT, **FORUM_IFCA_CHARTER}

IFCAS = {'cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex'}



class Typos():
    '''This are for the 
    list handler. The dict
    based stuff accepts true or false'''
    phrases = 'phrases'
    verbs = 'verbs'
    nouns_proper = 'nouns_proper'
    nouns_common = 'nouns_common'
    adjectives = 'adjectives'


class GazetteerWords():
    '''gaz words'''
    #from  ifca_area_wgs84
    VALID_IFCAS = ['cornwall', 'devon and severn', 'eastern', 'isles of scilly', 'kent and essex', 'north east', 'north west', 'northumberland', 'southern', 'sussex']
    #from counties_wgs84
    VALID_COUNTIES = ['barking and dagenham', 'bath and north east somerset', 'bedfordshire', 'berkshire', 'bexley', 'blackburn with darwen', 'bournemouth', 'brent', 'brighton and hove', 'bristol', 'bromley', 'buckinghamshire', 'cambridgeshire', 'camden', 'cheshire', 'cornwall', 'croydon', 'cumbria', 'darlington', 'derby', 'derbyshire', 'devon', 'dorset', 'durham', 'ealing', 'east riding of yorkshire', 'east sussex', 'enfield', 'essex', 'gloucestershire', 'greenwich', 'hackney', 'halton', 'hammersmith and fulham', 'hampshire', 'haringey', 'harrow', 'hartlepool', 'havering', 'herefordshire', 'hertfordshire', 'hillingdon', 'hounslow', 'isle of wight', 'islington', 'kensington and chelsea', 'kent', 'kingston upon hull', 'kingston upon thames', 'lambeth', 'lancashire', 'leicester', 'leicestershire', 'lewisham', 'lincolnshire', 'london', 'luton', 'manchester', 'medway', 'merseyside', 'merton', 'middlesbrough', 'milton keynes', 'newham', 'norfolk', 'north east lincolnshire', 'north lincolnshire', 'north somerset', 'north yorkshire', 'northamptonshire', 'northumberland', 'nottingham', 'nottinghamshire', 'oxfordshire', 'peterborough', 'plymouth', 'poole', 'portsmouth', 'redbridge', 'redcar and cleveland', 'richmond upon thames', 'rutland', 'shropshire', 'somerset', 'south gloucestershire', 'south yorkshire', 'southampton', 'southend-on-sea', 'southwark', 'staffordshire', 'stockton-on-tees', 'stoke-on-trent', 'suffolk', 'surrey', 'sutton', 'swindon', 'telford and wrekin', 'thurrock', 'torbay', 'tower hamlets', 'tyne and wear', 'waltham forest', 'wandsworth', 'warrington', 'warwickshire', 'west midlands', 'west sussex', 'west yorkshire', 'westminster', 'wiltshire', 'worcestershire', 'york', 'antrim', 'ards', 'armagh', 'ballymena', 'ballymoney', 'banbridge', 'belfast', 'carrickfergus', 'castlereagh', 'coleraine', 'cookstown', 'craigavon', 'derry', 'down', 'dungannon', 'fermanagh', 'larne', 'limavady', 'lisburn', 'magherafelt', 'moyle', 'newry and mourne', 'newtownabbey', 'north down', 'omagh', 'strabane', 'aberdeen', 'aberdeenshire', 'angus', 'argyll and bute', 'clackmannanshire', 'dumfries and galloway', 'dundee', 'east ayrshire', 'east dunbartonshire', 'east lothian', 'east renfrewshire', 'edinburgh', 'eilean siar', 'falkirk', 'fife', 'glasgow', 'highland', 'inverclyde', 'midlothian', 'moray', 'north ayshire', 'north lanarkshire', 'orkney islands', 'perthshire and kinross', 'renfrewshire', 'scottish borders', 'shetland islands', 'south ayrshire', 'south lanarkshire', 'stirling', 'west dunbartonshire', 'west lothian', 'anglesey', 'blaenau gwent', 'bridgend', 'caerphilly', 'cardiff', 'carmarthenshire', 'ceredigion', 'conwy', 'denbighshire', 'flintshire', 'gwynedd', 'merthyr tydfil', 'monmouthshire', 'neath port talbot', 'newport', 'pembrokeshire', 'powys', 'rhondda, cynon, taff', 'swansea', 'torfaen', 'vale of glamorgan', 'wrexham']
    #from counties_wgs84
    UK_COUNTRIES = ['england', 'northern ireland', 'scotland', 'wales']



class GroupsForUnspecified():
    '''these are used to determine if we have found a specifc species
    in write hints.py, if we have not, we then look for group terms'''
    SOLE_SPECIFIED_KEYS = set(_clean(['Dover Sole', 'Lemon Sole', 'Sand Sole']))
    SKATE_RAY_SPECIFIED_KEYS = set(_clean(['Common Stingray', 'Ray (Blonde)', 'Ray (Cuckoo)', 'Ray (Eagle)', 'Ray (Electric)', 'Ray (Marbled-Electric)', 'Ray (Sandy)', 'Ray (Shagreen)', 'Ray (Small Eyed)', 'Ray (Spotted)', 'Ray (Starry)', 'Ray (Thornback)', 'Ray (Undulate)']))
    BREAM_SPECIFIED_KEYS = set(_clean(["Black Bream", "Couch's Seabream", "Gilthead Sea Bream", "Pandora Sea Bream", "Ray's Bream", "Red Sea Bream", "White Sea Bream"]))
    MULLET_SPECIFIED_KEYS = set(_clean(["Golden-Grey Mullet", "Red Mullet", "Thick Lipped Grey Mullet", "Thin Lipped Grey Mullet"]))
    FLATFISH_SPECIFIED_KEYS = set(_clean(['Brill', 'Dab', 'Dover Sole', 'Flounder', 'Lemon Sole', 'Long Rough Dab', 'Megrim', 'Plaice', 'Sand Sole', 'Topknot', 'Turbot', 'Witch']))


#region LISTS HANDLER
class _NamedEntityBase():
    '''base class for named entities
    This handles the automated extending of word lists
    from the subclassing class according to variable naming
    ie. do variable names contain noun verb etc

    common nouns are pluralised
    verbs are conjugated
    typos are generated for all word types, according to typos argument
    '''

    def __init__(self):
        '''init'''
        self.allwords = set()
        self.all_base_words = set()
        self.all_base_words |= self.nouns_common
        self.all_base_words |= self.nouns_proper
        self.all_base_words |= self.verbs
        self.all_base_words |= self.adjectives
        self.all_base_words |= self.phrases

        self.nouns_common_expanded = set()
        self.verbs_expanded = set()
        self.adjectives_expanded = set()
        self.nouns_proper_expanded = set()
        self.phrases_expanded = set()
        self._get()
        
    

    def _get(self):

        if self._dump_load() and not self.force_load:
            assert self.allwords, 'allwords loaded from file system, but it is empty'
            print('Loaded words for %s from file' % self.dump_name)
            return

        print('Getting typos for %s' % self.dump_name)
        nouns_proper = set(self.nouns_proper); verbs = set(self.verbs); phrases = set(self.phrases); nouns_common = set(self.nouns_common); adjectives = set(self.adjectives)
        if self.typos: #typos can be none
            if isinstance(self.typos, str): self.typos = (self.typos,)
            assert set(self.typos).issubset(TYPO_OPTIONS_ALL), 'Invalid typos options. Typos must be in %s. Check subclass initialisation.' % TYPO_OPTIONS_ALL
        nouns_proper = set(self.nouns_proper)

        if self.add_similiar:
            wds = []
            for w in self.nouns_common:
                wds.append(w)
                wds.extend(_nlpbase.lemma_bag_all(w, force_plural=True))
            nouns_common |= set(wds)

            wds = []
            for w in verbs:
                wds.append(w)
                wds.extend(_nlpbase.lemma_bag_all(w)) #lamma_bag_all obeys verb and nouns plural/conjugation by default
            verbs |= set(wds)
        elif self.simple_expansion:
            wds = []
            for w in self.nouns_common:
                wds.append(w)
                wds.extend(_nlpbase.plural_sing(w))
            nouns_common |= set(wds)
            
            wds = []
            for w in verbs:
                wds.append(w)
                wds.extend(_nlpbase.conjugate(w)) #lamma_bag_all obeys verb and nouns plural/conjugation by default
            verbs |= set(wds)


        if self.typos:
            if 'phrases' in self.typos: phrases |= set(_typo.typos(phrases, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH))
            if 'verbs' in self.typos: verbs |= set(_typo.typos(verbs, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH))
            if 'nouns_proper' in self.typos: nouns_proper |= set(_typo.typos(nouns_proper, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH))
            if 'nouns_common' in self.typos: nouns_common |= set(_typo.typos(nouns_common, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH))
            if 'adjectives' in self.typos: adjectives |= set(_typo.typos(adjectives, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH))
        self.allwords |= nouns_proper 
        self.allwords |= verbs
        self.allwords |= phrases 
        self.allwords |= nouns_common 
        self.allwords |= adjectives
        

        self.nouns_common_expanded = nouns_common
        self.verbs_expanded = verbs
        self.adjectives_expanded = adjectives
        self.nouns_proper_expanded = nouns_proper
        self.phrases_expanded = phrases

        try:
            self._dump_dump()
            print('Dumped allwords for %s' % self.dump_name) 
        except Exception as _:
            print('allwords created, but dump failed for %s' % self.dump_name)


    def _dump_get_name(self, varname):
        fname = '%s_%s.pkl' % (self.dump_name, varname)
        return _path.normpath(_path.join(_settings.PATHS.NAMED_ENTITIES_DUMP_FOLDER, fname))


    def _dump_load(self):
        try:
            self.allwords = _iolib.unpickle(self._dump_get_name('allwords'))
            if not self.allwords:
                self.allwords = set()
                return False
            return True
        except Exception as _:
            return False

    def _dump_dump(self):
        s = self._dump_get_name('allwords')
        _iolib.pickle(self.allwords, s)


    def indices(self, s, use_proper=False):
        '''(str, bool) -> dict
        returns a dictionary with the word frequencies
        found in str for all words in the class

        s: the text to search
        use_proper: use the original word set, not the set with typos etc.

        Example:
        >>>instr('the black black fox is grey')
        {'black':[1]}
        '''
        
        out = {}
        if not s: return out
        if use_proper:
            words = self.all_base_words
        else:
            words = self.allwords

        for word in words:
            word = word.lstrip().rstrip()
            if word:
                inds = _relib.get_indices(s, word)
                if inds:
                    out[word] = inds
        return out


    def lookup(self, s):
        '''simple lookup for word s'''
        m = []
        if s in self.nouns_common: m += ['nouns_common']
        if s in self.nouns_common: m += ['nouns_proper']
        if s in self.nouns_common: m += ['verb']
        if s in self.nouns_common: m += ['adjective']
        if s in self.nouns_common: m += ['phrase']
        if s in self.all_words: m += ['phrase']
        print(' '.join(s))
                



class NEBLists(_NamedEntityBase):
    '''Create an list of words based on kwarg options

    Supported kwargs are:
    add_similiar: use wordnet to find similiar words and pluralise and conjugate
    typos: add typos for words, typos in('nouns', 'verbs', 'phrases', 'others')
    '''
    def __init__(self, dump_name, nouns_proper=None, nouns_common=None, verbs=None, phrases=None, adjectives=None, simple_expansion=False, add_similiar=False, typos=('nouns_common', 'nouns_proper', 'verbs', 'phrases', 'adjectives'), force_load=False):
        ld = lambda v: set(v) if v else set()
        assert not (simple_expansion and add_similiar), 'simple_expansion and add_similiar should not both be true'
        self.nouns_common = ld(nouns_common)
        self.nouns_proper = ld(nouns_proper)
        self.dump_name = dump_name
        self.verbs = ld(verbs)
        self.phrases = ld(phrases)
        self.adjectives = ld(adjectives)
        self.add_similiar = add_similiar
        self.typos = typos
        self.simple_expansion = simple_expansion
        self.force_load = force_load
        super().__init__()
#endregion






#region DICT HANDLER

class _NamedEntityBaseDict():

    def __init__(self):
        self._setdic()

    
    def _setdic(self):
        '''Sets self.noun_dict_all by generating
        typos and plurals using noun_dict, where
        noun_dict is set by the inheriting class
        '''
        assert isinstance(self.nouns_dict, dict), 'nouns_dict was not a dict in %s' % self.dump_name
        assert self.nouns_dict, 'nouns_dict was empty in %s' % self.dump_name
        if self._dump_load():
            assert self.nouns_dict_all, 'noun_dicts_all loaded, but was empty for %s' % self.dump_name
            print('Loaded noun_dicts_all for %s' % self.dump_name)
            return

        self.nouns_dict_all = {} #explicit
        print('Generating words for %s' % self.dump_name)
        for key, key_words in self.nouns_dict.items():  #speciesid is the proper name, it should also be in words as the alias includes the proper name
            assert key_words, 'noun_dict %s was empty' % key
            wds = []            
            for w in key_words:
                if 'unspecified' in w: continue #TODO temporary kludge to exclude unspecified
                wds += _nlpbase.plural_sing(w)

            if self.typos:
                wds += _typo.typos(wds, filter_start_n=TYPOS_FIX_FIRST_N_CHARS, min_length=TYPOS_MIN_LENGTH)
            
            s_wds = set(wds)
            if self.exclude:
                s_exclude = set(self.exclude)
                s_wds = s_wds.difference(s_exclude)

            self.nouns_dict_all[key] = s_wds

        try:
            self._dump_dump()
            print('Dumped nouns_dict_all for %s' % self.dump_name) 
        except Exception as _:
            print('nouns_dict_all created, but dump failed for %s' % self.dump_name)
                    

    def _dump_get_name(self, varname):
        fname = '%s_%s.pkl' % (self.dump_name, varname)
        return _path.normpath(_path.join(_settings.PATHS.NAMED_ENTITIES_DUMP_FOLDER, fname))


    def _dump_load(self):
        '''dump load'''
        try:
            self.nouns_dict_all = _iolib.unpickle(self._dump_get_name('nouns_dict_all'))
            if not self.nouns_dict_all:
                self.nouns_dict_all = set()
                return False
            return True
        except Exception as _:
            return False

    def _dump_dump(self):
        '''dump'''
        s = self._dump_get_name('nouns_dict_all')
        _iolib.pickle(self.nouns_dict_all, s)

    def view(self):
        '''view the dict in excel'''
        _view(_pd.df_from_dict(self.nouns_dict_all))

    def indices(self, s, keyid):
        '''(str, str)

        check if any verson exists in keyid
        returns a dictionary with the word frequencies
        found in str which are in the class

        kwargs are passed to the base get function and are:
        add_similiar:bool
        force_conjugate:bool
        typos=('nouns', 'verbs', 'phrases', 'others')
        force_plural_singular:bool
        as_set:bool

        Example:
        >>>indices('the black black fox is grey')
        {'black':[5,11]}
        '''
        out = {}
        words = self.nouns_dict_all.get(keyid)
        assert words, 'nouns_dict_all had no items for key %s' % keyid
        for word in words:
            inds = _relib.get_indices(s, word)
            if inds:
                out[word] = inds
        return out


    def get_by_key(self, key, use_proper=False):
        '''this gets a list of values for the dict key key,
        where key identifies the groups, eg the key may be
        speciesid

        key: dictionary key text identifying all versions of a word, eg they dictionary key
        'bass', which contains different words for bass. {'bass':['silver', 'bass', 'schoolie' ..]}
        use_proper: use the list without typos and plurals, otherwise uses 
        '''
        assert self.nouns_dict, 'nouns_dict was empty'
        assert self.nouns_dict_all, 'nouns_dict was empty'
        if use_proper:
            words = self.nouns_dict[key]
        else:
            words = self.nouns_dict_all[key]
        return set(words)


    def get_flat_set(self):
        '''() -> set
        Gets a set of all words.
        This is used as a whitelist filter for stopwords
        '''
        assert self.nouns_dict_all, 'self.all was accessed, but self.all was empty.'
        a = _flat([list(x) for x in self.nouns_dict_all.values()])
        return set(a)

    
    def lookup(self, s):
        '''simple lookup for words'''
        m = []

        for k, it in self.nouns_dict_all():
            if s in it: m += [k]
        if m:
            print(' '.join(m))
                




class NEBDicts(_NamedEntityBaseDict):
    '''class to hand dicts of words
    '''

    def __init__(self, nouns_dict, dump_name, typos=True, exclude=None):
        self.nouns_dict = nouns_dict
        assert isinstance(nouns_dict, dict), 'Unexpected type %s' % type(nouns_dict)
        self.typos = typos
        self.dump_name = dump_name
        self.exclude = exclude
        self.nouns_dict_all = set()
        super().__init__()
#endregion


#region NamedEntity Subclasses
Afloat = NEBLists(
    dump_name='Afloat',
    adjectives=['seasick'],
    nouns_proper=['pescador'],  #kayak and a boat
    nouns_common=["boat", "tub", "ship", "inflatable", "sail", "onboard", "anchor", 'slipway', 'tiller', 'starboard', 'aft', 'engine', 'outboard', 'prop', 'propellor'],
    verbs=["launch", "sail", "drift", 'steamed', 'motored', "launched", "sailed", "drifting", "anchored", 'puke', 'boat'],
    phrases=["sea sick", "dropped anchor"],
    typos=(Typos.verbs, Typos.nouns_proper),
    add_similiar=False,
    simple_expansion=True
    )


#indeed dentex and trio lll, is el-el-el not III on CB-UK
exclude_cb = set(['barracuda', 'bite', 'bluefin', 'bounty', 'kingfisher', 'caroline', 'charisma', 'chieftain', 'chocolate', 'discovery',
                  'famous', 'fish on', 'freedom', 'hermit', 'hurricane', 'independent', 'mac', 'mistress', 'obsession', 'optimist', 'plan b', 'porbeagle',
                  'predator', 'queensferry', 'rocket', 'shaking', 'snapper', 'sovereign', 'spot on', 'starfish', 'sunrise', 'typhoon', 'venture', 'warrior',
                  'why worry', 'yellowfin', 'progress', 'great white', 'tiger', 'osprey', 'thresher', 'marlin', 'adelaide'])
l = _clean(['Aces High', 'Adelaide', 'Adventuress', 'Ailish', 'Alba Deep', 'Aldeburgh Angler', 'Alexia', 'Ali-Cat', 'AliCat', 'All Aboard M.F.V. fulmar II',
            'Alliance', 'Als Spirit', 'AlyKat', 'AlyKat', 'Amaretto III', 'Amaretto IV', 'Amarisa', 'Amatheia', 'Amino', 'Angelus', 'Anglo Dawn III',
            'Anne Clare', 'Aquavitesse', 'Aquila', 'Aries 3', 'Aries II', 'Atlanta', 'Atlantic Blue', 'Atlantic Diver', 'Atlantic Explorer', 'Atlantis', 'Atlantis',
            'Bachanalian', 'Barracuda', 'Bay Surveyor', 'Bayside', 'Becca-Marie', 'Beowulf', 'Bessie Vee', 'Better Days', 'Big Buoy', 'Bite', 'Blazer 2', 'Blue Duo',
            'Blue Fin', 'Blue Marlin', 'Blue Mink', 'Blue Thunder', 'Blue Turtle', 'Bluedawn', 'Bluefin', 'Blueye 2', 'Bon Amy', 'Bonaventure II', 'Boney M', 'Bonwey',
            'Bootlegger', 'Bounty', 'Bounty Hunter', 'Boy Carl', 'Boy Richard', 'Bramblewick', 'Branscombe Pearl', 'Brigand', 'Brightlingsea Fishing Charters',
            'Brighton Diver', 'Buccaneer', 'C Cheetah', 'Capriole', 'Caroline', 'Carrick Lee', 'Carrie Jane', 'Castaway', 'Catch 22', 'Celtic Fox', 'Celtic Warrior',
            'Challenger 2', 'Channel Cheiftain 5', 'Channel Diver', 'Channel Warrior', 'Charisma', 'Charlotte Louise', 'Che Sara Sara', 'Chieftain', 'Chinook 11',
            'Chinook 3', 'Chinquita', 'Chocolate', 'Chrisanda', 'Christine Ann', 'Christyann', 'Cleveland Princess', 'Cloud Nine', 'Cobra 3', 'Cobra III', 
            'Crimson Tide', 'Crusader 2', 'Cumbrae', 'Dakala Mist', 'Danda', 'Danny Boy', 'Dannyboy II', 'Danse De Leau', 'Daphne Carole', 'Dawn Breaker',
            'Dawn Mist', 'Dawn Raider', 'Dawn Tide', 'DAWN TIDE II', 'Dawn Venture', 'Deep Blue', 'Defiant', 'Delta Sunrise.', 'Dentex', 'Dentex III', 'Dentex lll',
            'Diablo', 'Discovery', 'Dointhedo', 'Dolly P', 'Dominator', 'Double Six', 'Drakkar', 'Duchess II', 'Duke IV', 'Dulcie T', 'Dusk Diver',
            'Eastern Promise', 'Eastern Promise 2', 'Edwin John', 'Elegance', 'Emma Jayne', 'Emma Kate', 'Endeavour', 'Enterprise', 'Escapade',
            'Evelyn Jane II', 'Evelyn-Jane', 'Excalibur', 'Excel 2', 'Famous', 'Final Answer', 'Fins-up', 'Fire Fox', 'Fish On!', 'Flamer IV', 'Flamer 4',
            'Folkestone Voyager', 'Force 10', 'Foxy Lady', 'Frances Jane', 'Freedom', 'Galloper', 'Gemini 3', 'Gemini II', 'George Griffiths MBE', 'Girl Gray',
            'Girl Mandy', 'Glad Tidings', 'Gloria B11', 'Gold-Rush', 'Great Escape', 'Great White', 'Grey Fox', 'Grey Viking', 'Gypsy 2', 'Hard Labour', 'Heartbeat',
            'Heidi J', 'Hermit', 'Hermit of Hythe', 'High Flyer', 'High Flyer 2', 'Highlander', 'Hurricane', 'Hvita', 'Independent', 'In-T-Net', 'Jay Jay', 'Jean K',
            'Jenifers Pride', 'Jensen', 'Jensen & Suveran', 'Jessica Hettie', 'JFK 2', 'Jo Dan', 'Jo-Dan', 'Joint Venture', 'Jo-Jo', 'JoJo', 'Jolly Fisherman', 'Jolly Roger',
            'Joy Belle', 'Jozilee', 'Jubrae', 'Julie D', 'Just Mary', 'Kaimalino', 'Kaimalino', 'Karyl-Anne', 'Katie Ann', 'Katrina', 'Kayleigh-L', 'Kelleys Hero Charters',
            'Kellys Hero', 'Kelsey Leigh', 'Kimberley', 'Kingfisher', 'Kingfisher', 'Kingfisher & Equaliser', 'Kingfisher II', 'Kittiwake 3', 'Kraken', 'Lady Ann',
            'Lady Anne', 'Lady D', 'Lady Elsie', 'Lady Essex III', 'Lady Grace', 'Lady Helen', 'Lady Lucy II', 'Lady Mary', 'Lady Of The Lake', 'Lady Sarah', 'Lady Tina',
            'Last Laugh', 'Laura III', 'Lead Us', 'Lesley Jane', 'Libby', 'Lillie May', 'Lily Lolo', 'Lizy', 'Lone Shark', 'Lone Shark III', 'Louise Jane', 'Lowestoft Provider',
            'Lynander', 'M.F.V. Fulmar', 'M.F.V. Tamesis', 'M.V. Penetrater', 'Madonna', 'Malaki', 'Manta Ray', 'Margaret Elaine', 'Marie F', 'Marlin', 'Mary Ellen',
            'Maverick', 'Meerkat', 'Mermaid II', 'Mersey Lass', 'Mia Jay', 'Michelle Mary', 'Mirage', 'Miss Patty', 'Missy Moo', 'Mistress',
            'Mistress Linda', 'Misty Blue', 'Misty Lady', 'Moonraker', 'Moonshine', 'Morgan James', 'Morgan M', 'Morning Breeze', 'MV Freedom', 'Mystique', 'Mystique II',
            'Natalie Kristen II', 'Nemesis', 'Neptune', 'Never Can Tell A', 'North Star', 'Nova Stella.', 'Oberon', 'Obsession', 'Ocean Crusader', 'Ocean explorer',
            'Ocean Lass', 'Ocean Runner', 'Ocean Warrior 3', 'Ocean-Pearl II', 'Offshore Rebel IV', 'On A Promise', 'Optimist', 'Optimist', 'Orca', 'Osprey',
            'Osprey & TeddieBoy', 'Osprey II', 'Our Gemma', 'Our Joe-L', 'Our Joy', 'Out Rage', 'Out The Blue', 'Outlaw', 'Pace Arrow', 'Panther', 'Pathfinder',
            'Patrice II', 'Patricia Rose', 'Peace & Plenty', 'Peganina', 'Pegasus', 'Penetrater', 'Pioneer', 'Piscary', 'Piscine', 'PLAN B', 'Portia',
            'Predator', 'Predator', 'Predator', 'Pride and Joy', 'Private Venture', 'Progress', 'Providence', 'Purdy and Flamer 2', 'Queensferry', 'Racheal Jane',
            'Rachel K', 'Random Harvest II', 'Rapid Fisher', 'Razorbill  3', 'Razorbill 3', 'Red 5', 'Reecer', 'Reel Action', 'Reel Deal', 'Restorick III', 'Robert Mark',
            'Rose-Ann', 'Rough Diamond 2', 'Royal Charlotte', 'Royal Eagle', 'RubyD', 'Ruby-D', 'Sally Ann', 'Sally Ann', 'Sally Ann Jo', 'Saltwind', 'Sambe', 'Samuel Irvin 3',
            'San Gina I', 'San Gina II', 'Sapphire', 'Sarah Michelle', 'Saxon Lady', 'Scooby Doo Too', 'Sea  Leopard',
            'Sea Angler II', 'Sea Breeze 3', 'Sea Fever', 'Sea Fire ', 'Sea Fox', 'Sea Leopard', 'Sea Leopard', 'Sea Otter 2', 'Sea Searcher', 'Sea Spray',
            'Sea swift', 'Sea Tradar', 'Sea Urchin II', 'Sea Urchin III', 'Seabreeze 3', 'Seabreeze III', 'Sea-Juicer', 'Sea-Otter 2', 'Seawatch 1', 'Secret Star',
            'Seeker', 'Senija', 'Serenity', 'Serenity', 'Sha-King', 'Shalimar', 'Shande 3', 'Shande III', 'She Likes It 2', 'She Likes It II', 'She Likes It Rough 2',
            'Shogun (Marna Marine)', 'Shokwave', 'Shy-Torque III', 'Silver Halo', 'Silver Sea', 'Silver Spray', 'Size Matters', 'Skerry Belle', 'Skylark', 'Snapper', 'Snowstar',
            'Sophie Lea', 'Southern Angler', 'Southern Star', 'Spirit Of Arun', 'Sportsmans Night', 'Spot On!', 'Stoney Broke', 'Striker', 'Supanova', 'Supanova II', 'Susie B',
            'Suveran', 'Swallow IV', 'Swin Ranger', 'Swordfish', 'T.J. Gannet', 'T.J.Gannet', 'Tamesis', 'Tango', 'Taxi Boat Charters Poseidon', 'Telmar', 'Telmar II',
            'Tempus Fugit', 'The African Queen', 'Thistle B', 'Three Sisters', 'Three Sisters', 'Threesisters', 'Thresher', 'Tiger', 'Tiger Lily', 'Tina Dawn', 'Top Cat',
            'Top Cat III', 'TopCat', 'Toplines', 'Torbay Belle', 'Tracy Jane', 'Trio 3', 'Trio III', 'TRIO lll', 'Trojan Warrior Whitby', 'Trot On', 'TROT-ON',
            'True Blue', 'Trueblue', 'Trya II', 'Tuonela', 'Tuskar', 'Two Dogs', 'Unity', 'Upholder', 'Valkyrie', 'Venture', 'Venus', 'Viking', 'Voyager', 'Waderbay',
            'Wandering Star', 'Warlord', 'Warrior', 'Wave Cheiftain', 'Wave Dancer', 'Wetwheels', 'White Maiden', 'White Maiden II', 'White Marlin', 'Why Worry',
            'Wight Huntress', 'Wight Rebel', 'Wight Sapphire', 'Wight Spirit', 'Wild Frontier', 'Wild Frontier 2', 'Yellowfin', 'Yorkshire Lass', 'Yorkshire Lass II', 
            'Yorkshire Rose', 'Yorkshireman'])
l = [n.lower() for n in l]
l = _nlpbase.expansions(l, {'1':['i'], '2': ['ii'], '3': ['iii'], '4': ['iv'], '5':['v'], 'M.F.V.':['MFV', 'MV', 'M.V.']})
l = list(set(l).difference(exclude_cb)) #exclude these
AfloatCharterBoat = NEBLists(
    dump_name='AfloatCharterBoat',
    nouns_proper=l,
    verbs=["charter", "skipper", "hire"],
    nouns_common=['charter'],
    phrases=['charter boat'],
    typos=(Typos.nouns_common, Typos.verbs),
    add_similiar=False,
    simple_expansion=True
    )


#this stricter list is used so we can link on names with the cb table for ugc forum extracted data
d =_cb.get_cb()
assert d, '_cb.get_cb() failed'
d = list(set(d).difference(exclude_cb)) #exclude these
AfloatCharterBoatProperOnly = NEBLists(
    dump_name='AfloatCharterBoatProperOnly',
    nouns_proper=d,
    typos=None,
    add_similiar=False,
    simple_expansion=False
    )


AfloatKayak = NEBLists(
    dump_name='AfloatKayak',
    nouns_common=["kayak", "yak"],
    nouns_proper=["tarpon", "trident", "scupper", "paddle", "fatyak", "dorado", "teksport", "emotion", 'cuda', 'mirage', 'profish', 'outback', 'sturgeon', 'wilderness', 'aquago', 'juntos', 'malibu', 'huntsman', 'profisha', 'revo 16', 'gosea', 'tetra', 'feelfree', 'hobbie', 'dorado', 'wilderness systems', 'wido', 'riber', 'perception', 'systemx', 'tootega', "kaskazi", 'galaxy', 'viking', 'werner', 'railblaza', "prowler"],
    phrases=['mirage outback', 'pelican catch', 'lifetime muskie', "fat yak", 'system x', 'jackson cuda', 'cuda 14'],
    verbs=['kayaking', 'paddled'],
    typos=None,
    add_similiar=False)


AfloatPrivate = NEBLists(
    dump_name='AfloatPrivate',
    nouns_common=['rib', 'oar', "dinghy", 'dory', 'outboard'],
    nouns_proper=['arvor', 'fibramar', 'treeve', 'quicksilver', 'fastliner', 'strikeline', 'leisurecat', 'mallon', 'beneteau', 'antares', 'reiver', 'saltram', 'colvic', 'navistar'],
    phrases=['wilson flyer', 'nord star', 'cougar cat', 'mitchell 22', 'sea line', 'orkney 520'],
    typos=None,
    add_similiar=False,
    simple_expansion=True)


GearAngling = NEBLists(
    dump_name='GearAngling',
    nouns_common=["rod", "beachcaster", "beachcasters", "rod", "bait", "plug", 'lure', 'spinner'],
    nouns_proper=['redgill'],
    phrases=['beach caster', 'beach casters', 'livebait', 'live bait', 'lrf', 'light rock fishing', 'feathering', 'red gill', 'red gills', 'savage gear'],
    verbs=["spinning", 'cast', 'plugging'],
    typos=None,
    add_similiar=False,
    simple_expansion=True)



GearNoneAngling = NEBLists(
    dump_name='GearNoneAngling',
    nouns_common=['seine'],
    verbs=['netting'],
    phrases=['spear gun', 'long lines', 'long line', 'purse net', 'seine net'],
    typos=None,
    add_similiar=False,
    simple_expansion=True
    )


MetrologicalAll = NEBLists(
    dump_name='MetrologicalAll',
    adjectives=['heavy', 'big', 'small', 'huge', 'giant', 'tiny', 'little', 'loads', 'plenty', 'lots'],
    nouns_common=["pound", "pounds", "kilos", "kilo", "kilogram", "kilograms", "grams", "gram", "ounce", "ounces", "lb",
                  "lbs", "ozs", "kg", "kgs", "meter", "meters", "metre", "metres", "cm", "cms", "centimeters",
                  "centimeter", "centimetres", "centimetre", "inch", "inches", "foot", "feet"],
    add_similiar=False,
    typos=None,
    simple_expansion=True
    )



Session = NEBLists(
    dump_name='Session',
    adjectives=['early', 'late'],
    nouns_common=['session', 'trip', "hour", "minute", "hour", 'morning', 'afternoon', 'noon', 'midday', 'flood', 'ebb'],
    phrases=["before low", "after low", "to low", "after high", "to high", "before high", "either side", 'upto low', 'upto high', 'the flood', 'the ebb', 'incoming tide',
             "around high", "around low", "tide out", "tide down", "tide in", "tide up", "packed up", "went home", "p.m.", "a.m.", 'pm', 'a.m', 'p.m', "hrs", "mins", "pound mark", "way back"],
    verbs=['angling', 'arrived', 'casting', 'catch', 'ended', 'fishing', 'hook', 'land', 'leave', 'leave', 'release', 'start', 'stop', 'trolling', 'unhook', 'blanked', 'ebb', 'flood'],
    typos=None,
    simple_expansion=True
    )


MackerelAsBait = NEBLists(
    dump_name='MackerelAsBait',
    adjectives=['frozen'],
    verbs=['baited', 'livebaited', 'deadbaited', 'tipped', 'using'], 
    nouns_common=['fillet', 'side', 'head', 'belly', 'chunk', 'sliver', 'bait', 'flapper', 'strip', 'cocktail', 'head'],
    phrases=['on mackerel', 'on mack', 'on mackeral', 'on mackie', 'on mackey', 'on macky', 'whole mackerel', 'whole mackie', 'whole macky', 'whole mackey', '0.5 mackerel', '0.5 mackey',
                '0.5 macky', '0.5 mackie', 'loaded with mackerel', 'loaded with mackie', 'loaded with mack', 'loaded with macky'],
    typos=None,
    add_similiar=False,
    simple_expansion=True
    )


HerringAsBait = NEBLists(
    dump_name='HerringAsBait',
    adjectives=['frozen'],
    verbs=['baited', 'livebaited', 'deadbaited', 'tipped', 'using'], 
    nouns_common=['fillet', 'side', 'head', 'belly', 'chunk', 'sliver', 'bait', 'flapper', 'strip', 'cocktail', 'head'],
    phrases=['on herring', 'whole herring', '0.5 herring',
                'loaded with herring'],
    typos=None,
    add_similiar=False,
    simple_expansion=True
    )


HaddockAsException = NEBLists(
    adjectives='battered',
    dump_name='HaddockAsException',
    verbs=['fried'], 
    nouns_common=['chips', 'capn', 'captain', 'cap', 'quota'],
    phrases=['haddock and chips'],
    typos=None,
    add_similiar=False,
    simple_expansion=True
    )


BaitSpecies = NEBLists(
    dump_name='BaitSpecies',
    nouns_common=['worm', 'black', 'squid', 'lug', 'sewie', 'prawn', 'crab', 'peeler', 'softie', 'softy', 'bluey',
                'sandeel', 'rag', 'ragworm', 'clam', 'mussel', 'mussle', 'muscle', 'razorclam', 'runnydown'],
    phrases=['maddies'],
    typos=None,
    add_similiar=False,
    simple_expansion=True
    )
#endregion






#region _NamedEntityBaseDict subclasses

##################################################################################
# if add another unspecified class, update mmo.write_hints.py:make_species_hints #
##################################################################################


#These are all entities which require a lookup under a key
#for examples, we need to know that codling and coddo
#are both cod
#Grounds
AfloatAnglingMethod = NEBDicts(
    nouns_dict={'wreck':['wreck', 'wrecking'],
                'ground':['anchor', 'ground', 'general', 'anchored', 'inshore', 'clean ground', 'clear ground'],
                'banks':['banks', 'sand bank', 'sandbank', 'bank'],
                'rough':['reef', 'pinnacle', 'patchy ground', 'rough ground', 'broken ground', 'hard ground'],
                'shark':['shark'],
                'estuary':['estuary', 'mudflat', 'mud flats', 'mud flats', 'esturine', 'estuarine', 'river']},  #river e.g. mersey
    dump_name='AfloatAnglingMethod',
    typos=False)


DateTimeDayOfWeek = NEBDicts(
    nouns_dict={'monday':['monday', 'mon', 'mond', 'monda', 'mdy'], 'tuesday':['tuesday', 'tue', 'tues', 'tuesd', 'tu'],
     'wednesday':['wednesday', 'wed', 'wedn', 'wedne', 'wds'], 'thursday':['thursday', 'thu', 'thur', 'thurs'],
     'friday':['friday', 'fri', 'frid', 'frida', 'fr'], 'saturday':['saturday', 'sat', 'satu', 'satur'],
     'sunday':['sunday', 'sun', 'sund', 'sunda']},
    typos=None,
    dump_name='DateTimeDayOfWeek')



DateTimeMonth = NEBDicts(
    nouns_dict={'january':['january', 'jan'], 'february':['february', 'feb'], 'march':['march', 'mar'], 'april':['april', 'apr'], 'may':['may'],
     'june':['june', 'jun'], 'july':['july', 'jul'], 'august':['august', 'aug'],
     'september':['september', 'sep', 'sept'], 'october':['october', 'oct'], 'november':['november', 'nov'], 'december':['december', 'dec']},
    typos=True,
    dump_name='DateTimeMonth')
DateTimeMonth.get_season = _get_season #append the getseason function for convieniance



DateTimeSeason = NEBDicts(
    nouns_dict={'spring':['spring'], 'winter':['winter', 'wntr'], 'autumn':['autumn', 'aut', 'atmn'], 'summer':['summer']},
    typos=None,
    dump_name='DateTimeSeason'
    )
DateTimeSeason.get_season = _get_season


#common words which are in as species alias to exclude
exclude = ['turbo', 'turbos', 'dog', 'dogs', 'coner', 'cobers', 'cober', 'ba', 'bases', 'black bras', 'sea eagle', 'sea eagles', 'makes', 'solent', 'solents', 'smelt', 'skipper', 'skippers']

d = _species.get_species_as_dict_all()
assert d, '_species.get_species_as_dict_all() failed'
SpeciesAll = NEBDicts(nouns_dict=d,
                            typos=True,
                            dump_name='SpeciesAll',
                            exclude=exclude)



d = _species.get_species_as_dict_sans_unspecified()
assert d, '_species.get_species_as_dict_sans_unspecified() failed'
SpeciesSpecified = NEBDicts(nouns_dict=d,
                            typos=True,
                            dump_name='SpeciesSpecified',
                            exclude=exclude)


d = _species.get_species_as_dict_unspecified()
assert d, '_species.get_species_as_dict_unspecified() failed'
SpeciesUnspecified = NEBDicts(nouns_dict=d,
                              typos=True,
                              dump_name='SpeciesUnspecified',
                              exclude=exclude)



assert d, '_species.get_species_sole() failed'
SpeciesUnspecifiedSole = NEBDicts(nouns_dict=d,
                                  typos=None,
                                  dump_name='SpeciesUnspecifiedSole',
                                  exclude=exclude)


d = _species.get_species_flatfish_unspecified()
assert d, '_species.get_species_flatfish() failed'
SpeciesUnspecifiedFlatfish = NEBDicts(nouns_dict=d,
                                      typos=True,
                                      dump_name='SpeciesUnspecifiedFlatfish',
                                      exclude=exclude)


d = _species.get_species_mullet_unspecified()
assert d, '_species.get_species_mullet() failed'
SpeciesUnspecifiedMullet = NEBDicts(nouns_dict=d,
                                    typos=None,
                                    dump_name='SpeciesUnspecifiedMullet',
                                    exclude=exclude)


d = _species.get_species_bream_unspecified()
assert d, '_species.get_species_bream() failed'
SpeciesUnspecifiedBream = NEBDicts(nouns_dict=d,
                                   typos=True,
                                   dump_name='SpeciesUnspecifiedBream',
                                   exclude=exclude)


d = _species.get_species_skates_rays_unspecified()
assert d, '_species.get_species_skates_rays() failed'
SpeciesUnspecifiedSkatesRays = NEBDicts(nouns_dict=d,
                                        typos=True,
                                        dump_name='SpeciesUnspecifiedSkatesRays',
                                        exclude=exclude)
#endregion
 



def _bld_global_sets(force_dump):
    '''build/load/save global sets
    all_single is primarily for use as a whitelist nlp.stopwords
    '''
    global all_; global all_single
    
    def _bld(word_set):
        '''build whitelist of words for nlp.stopwords'''
        global all_; global all_single       
        ss = {w for w in _flat([v.split() for v in word_set])}
        all_single |= ss  #every single word as a single word, eg 'to high' will be split to 'to', 'high'
        all_ |= word_set #all words and phrases as they appear, e.g. 'to high' will still be 'to high'

    if _iolib.file_exists(_settings.PATHS.NAMED_ENTITIES_ALL) and not force_dump:
        all_ = _iolib.unpickle(_settings.PATHS.NAMED_ENTITIES_ALL)
        print('Loaded named_entities.all from file system')

    if _iolib.file_exists(_settings.PATHS.NAMED_ENTITIES_ALL_SINGLE) and not force_dump:
        all_single = _iolib.unpickle(_settings.PATHS.NAMED_ENTITIES_ALL_SINGLE)
        print('Loaded named_entities.all_single from file system')

    if all_ and all_single: return
    all_single = set(); all_ = set() #just make sure
    print('**loading and dumping named entities ....**')
    _bld(Afloat.allwords)
    _bld(AfloatCharterBoat.allwords)
    _bld(AfloatKayak.allwords)
    _bld(AfloatPrivate.allwords)
    _bld(GearAngling.allwords)
    _bld(GearNoneAngling.allwords)
    _bld(MetrologicalAll.allwords)
    _bld(MetrologicalAll.allwords)
    _bld(DateTimeDayOfWeek.get_flat_set())
    _bld(DateTimeMonth.get_flat_set())
    _bld(DateTimeSeason.get_flat_set())
    _bld(SpeciesAll.get_flat_set())
    _bld(MackerelAsBait.allwords)
    _bld(BaitSpecies.allwords)

    #now try the gazetteer
    try:
        _bld(_gaz.get_all_as_set())
    except AttributeError as _:
        print('Failed to load the gazetter. This will happen if name_cleaned is empty or blank for all gazetter records.\n\nRun mmo.clean_gaz.py.')

    if force_dump or not _iolib.file_exists(_settings.PATHS.NAMED_ENTITIES_ALL):
        _iolib.pickle(all_, _settings.PATHS.NAMED_ENTITIES_ALL)

    if force_dump or not _iolib.file_exists(_settings.PATHS.NAMED_ENTITIES_ALL_SINGLE):
        _iolib.pickle(all_single, _settings.PATHS.NAMED_ENTITIES_ALL_SINGLE)


_bld_global_sets(False)


if __name__ == '__main__':
    print('s')
    quit()
