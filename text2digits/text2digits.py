from warnings import warn as _warn

UNITS = [
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
    'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
    'sixteen', 'seventeen', 'eighteen', 'nineteen',
]
TENS = [
    'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'
]
SCALES = ['hundred', 'thousand', 'million', 'billion', 'trillion']
ORDINAL_WORDS = {'zero':0, 'nought':0, 'nowt':0, 'nothing':0, 'nil':0, 'zippo':0, 'zip':0, 'naught':0, 'nada':0, 'zilch':0,
                 'first':1, 'single':1, 'lone':1, 'solitary':1, 'another':1, 'final':1, '1st':1, 'a':1,
                 'second': 2, 'few':2, 'couple':2, 'ii':2, 'pair':2, 'deuce':2, 'brace':2, 'duo':2, '2nd':2, 'dual': 2,
                 'third': 3, 'iii': 3, '3rd':3, 'trio':3, 'triplet':3, 'threesome':3, 'triad':3,
                 'fourth': 4, 'iv': 4, '4th':4, 'tetrad':4, 'quartet':4, 'quadruplet':4,
                 'fifth': 5, 'v': 5, '5th':5, 'quintet':5, 'pentad':5, 'quint':5,
                 'sixth': 6, 'vi': 6, '6th':6, 'half dozen':6, 'half a dozen': 6, 'half-dozen':6, 'halfdozen':6,
                 'seventh': 7, 'vii': 7, '7th':7,
                 'eighth': 8, 'viii': 8, '8th':8,
                 'ninth': 9, 'iv': 9, '9th':9,
                 'tenth': 10, '10th': 10, #'X': 10, other uses
                 'eleventh': 11, 'xi': 11,
                 'twelfth': 12, 'dozen':12, 'xii':12,
                 'thirteenth': 13,'xiii':13,
                 'fourteenth': 14, 'vx': 14,
                 'fifteenth': 15, 'xv': 15,
                 'sixteenth': 16, 'xvi': 16,
                 'seventeenth': 17, 'xvii': 17,
                 'eighteenth': 18, 'xviii': 18,
                 'nineteenth': 19, 'xix': 19,
                 #'quarter':0.25,
                 #'half':0.5,
                 #'three quarters': 0.75,
                 #'two thirds': 0.667, 'two-thirds': 0.667,
                 #'one third': 0.333, 'one-third': 0.333,
                 'tens': 20,
                 'hundreds': 200,
                 'thousands': 2000,
                 'millions': 2000000
                 }

ORDINAL_ENDINGS = [('ieth', 'y'), ('th', '')]

ORDINAL_WORDS_AS_LIST = [d[0] for d in ORDINAL_WORDS.items()]

class TextPreprocessor:
    @staticmethod
    def bigram(word1, word2):
        '''
        Returns the bigram similarity of 2 words
        '''
        word1 = word1.lower()
        word2 = word2.lower()
        word1_length = len(word1)
        word2_length = len(word2)
        pairs1 = []
        pairs2 = []

        for i in range(word1_length):
            if i == word1_length - 1:
                continue
            pairs1.append(word1[i] + word1[i+1])

        for i in range(word2_length):
            if i == word2_length - 1:
                continue
            pairs2.append(word2[i] + word2[i+1])

        similar = [word for word in pairs1 if word in pairs2]

        return float(len(similar)) / float(max(len(pairs1), len(pairs2)))

    @staticmethod
    def get_similarity(item1, item2):
        '''
        Returns a number within the range (0,1) determining how similar
        item1 is to item2. 0 indicates perfect dissimilarity while 1
        indicates equality.
        '''
        return TextPreprocessor.bigram(item1, item2)

    @staticmethod
    def get_match(word, collection, threshold):
        '''
        Returns the most syntactically similar word in the collection
        to the specified word.
        '''
        match = None
        max_similarity = 0

        for item in collection:
            similarity = TextPreprocessor.get_similarity(word, item)
            if similarity > max(max_similarity, threshold):
                match = item
                max_similarity = similarity

        return match


class Text2Digits():
    def __init__(self, excluded_chars="", similarity_threshold=0.5):
        self.excluded = excluded_chars
        self.accepted = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        self.numwords = dict()
        self.threshold = similarity_threshold

        self.numwords['and'] = (1, 0)
        for idx, word in enumerate(UNITS): self.numwords[word] = (1, idx)
        for idx, word in enumerate(TENS): self.numwords[word] = (1, (idx+1) * 10)
        for idx, word in enumerate(SCALES): self.numwords[word] = (10 ** (idx * 3 or 2), 0)

    def convert(self, phrase, spell_check=False):
        substr_arr, punctuation_arr = self.get_substr_punctuation(phrase)
        digits_arr = []

        for substr in substr_arr:
            digits_arr.append(self.convert_to_digits(substr, spell_check))

        # Recreate the phrase by zipping the converted phrases with the punctuations
        digits_phrase = "".join([sstr + punct + " " for sstr, punct in zip(digits_arr, punctuation_arr)])

        return digits_phrase.strip()


    def get_substr_punctuation(self, phrase):
        """
        This function takes in a phrase and outputs an array of substring split by punctuation and an array of
        all the punctuations that were stripped out
        """
        substr_arr = []
        punctuation_arr = []
        substr = ""
        strlen = len(phrase)
        count = 0

        for char in phrase:
            count += 1
            if char in (self.accepted + self.excluded):
                substr += char
            else:
                substr_arr.append(substr)
                punctuation_arr.append(char)
                substr = ""

            # when there is no punctuation in a sentence
            if count == strlen and substr:
                substr_arr.append(substr)
                punctuation_arr.append("")

        return substr_arr, punctuation_arr


    #https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
    def convert_to_digits(self, textnum, spell_check=False):
        textnum = textnum.replace('-', ' ')
        current = result = word_count = 0
        curstring = ''
        onnumber = lastunit = lastscale = is_tens = False
        total_words = len(textnum.split())

        for word in textnum.split():
            try:
                word_count += 1
                word = word.lower()
                if word in ORDINAL_WORDS:
                    scale, increment = (1, ORDINAL_WORDS[word])
                    current = current * scale + increment
                    if scale > 100:
                        result += current
                        current = 0
                    onnumber = True
                    lastunit = lastscale = is_tens = False

                else:
                    # Handle endings
                    for ending, replacement in ORDINAL_ENDINGS:
                        if word.endswith(ending) and (word[:-len(ending)] in UNITS or word[:-len(ending)] in TENS):
                            word = "%s%s" % (word[:-len(ending)], replacement)

                    # Handle misspelt words
                    if spell_check:
                        matched_num = TextPreprocessor.get_match(word, self.numwords.keys(), self.threshold)
                        if matched_num is not None:
                            word = matched_num

                    # Is not a number word
                    if (not self.is_numword(word)) or (word == 'and' and not lastscale):
                        if onnumber:
                            # Flush the current number we are building
                            curstring += repr(result + current) + " "
                        curstring += word

                        if word_count != total_words:
                            curstring += " "

                        result = current = 0
                        onnumber = False
                        lastunit = False
                        lastscale = False
                        is_tens = False

                    # Is a number word
                    else:
                        scale, increment = self.from_numword(word)
                        onnumber = True

                        # For cases such as twenty ten -> 2010, twenty nineteen -> 2019
                        if is_tens and (word not in UNITS or word == "ten") and (word not in SCALES):
                            curstring += repr(result + current)
                            result = current = 0

                        if lastunit and (word not in SCALES):
                            # Assume this is part of a string of individual numbers to
                            # be flushed, such as a zipcode "one two three four five"
                            curstring += repr(result + current)
                            result = current = 0

                        if scale > 1:
                            current = max(1, current)

                        current = current * scale + increment
                        if scale > 100:
                            result += current
                            current = 0

                        lastscale = False
                        lastunit = False
                        if word in SCALES:
                            lastscale = True
                        elif word in UNITS:
                            lastunit = True
                        elif word in TENS:
                            is_tens = True
            except Exception as e:
                _warn('Exception:\t%s' % e)
                return word


        if onnumber:
            curstring += repr(result + current)

        return curstring



    def is_numword(self, x):
        if self.is_number(x):
            return True
        if x in self.numwords:
            return True
        return False

    def from_numword(self, x):
        if self.is_number(x):
            scale = 0
            increment = int(x.replace(',', ''))
            return scale, increment
        return self.numwords[x]


    def is_number(self, x):
        if type(x) == str:
            x = x.replace(',', '')
        try:
            float(x)
        except:
            return False
        return True

if __name__ == '__main__':
    t2n = Text2Digits(similarity_threshold=0.7)
    tests = [
        "A random string",
        "I am thirty six years old with a child that is four. I would like to get him four cars!",
        "I was born in twenty ten",
        "I was born in nineteen sixty four",
        "I am the fourth cousin",
        "I am twenty nine",
        "it was twenty ten and was negative thirty seven degrees",
        "thirty twenty one",
        "one thousand six hundred sixty six",
        "one thousand and six hundred and sixty six",
        "sixteen sixty six",
        "eleven hundred twelve",
        "Sixteen and seven",
        "twenty ten and twenty one",
        "I was born in nineteen ninety two and am twenty six years old!",
        "three forty five",
        "nineteen",
        "ninteen",
        "nintteen",
        "ninten",
        "ninetin",
        "ninteen nineti niine"
    ]

    for test in tests:
        print(test + ":", t2n.convert(test, spell_check=True) + "\n")
