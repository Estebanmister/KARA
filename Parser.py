import nltk
from nltk.stem.wordnet import WordNetLemmatizer


class character:
    def __init__(self, name):
        self.name = name
        self.IGNORE_ACTIONS = ['say']
    def get_actions(self, text):
        text_sep = text.split(" ")
        open_t = False
        open_a = False
        say = ""
        actions = []
        action = ""
        who = text.split(":")[0]
        
        for word in text_sep:
            if '//' in word or '(' in word:
                break
            if word.count('"') > 0:
                if word.count('"') > 1:
                    say = say+word.replace('"',"")+" "
                else:
                    open_t = not open_t
                    say = say+word.replace('"',"")+" "
            elif open_t:
                say = say+word.replace('"',"")+""
            if word.count('*') > 0:
                if word.count('*') > 1:
                    action = action+word.replace('*',"")+" "
                    actions.append(action)
                else:
                    open_a = not open_a
                    action = action+word.replace('*',"")+" "
                    if not open_a:
                        actions.append(action)
                        action = ""
            elif open_a:
                action = action+word.replace('*',"")+" "
        say = text.split(":")[1].split("*")[0].strip(" ").replace(" says", "")
        filtered = self.trusted_filter(actions)
        return say, who, filtered

    def trusted_filter(self, actions):
        for action in actions:
            words = action.split(" ")
            what = []
            verbs = ['VBZ',
                'VBP', 
                'VBD',
                'VBG']
            for word in words:
                if word == '':
                    continue
                nt = nltk.pos_tag([word])[0]
                if nt[1] in verbs:
                    what.append(nt[0])
                    continue
                ntt = nltk.word_tokenize("He " + word)
                nt = nltk.pos_tag(ntt)[1]
                if nt[1] in verbs:
                    what.append(nt[0])
            return what
                
                
            

    def filter_actions(self, actions):
        verbs = ['VBZ',
                'VBP', 
                'VBD',
                'VBG']
        to_do = []
        current_name = self.name
        tmp_bool = False
        for actionl in actions:
            ntt = nltk.word_tokenize(actionl)
            nt = nltk.pos_tag(ntt)
            for word in nt:
                print(word[0], word[1], current_name)
                if word[1] == "PRP" or word[0].lower() == current_name.lower():
                    tmp_bool = True
                if word[1] in verbs and tmp_bool:
                    v = WordNetLemmatizer().lemmatize(word[0], 'v')
                    if not v in self.IGNORE_ACTIONS:
                        to_do.append(v)
            if not any(to_do):
                for word in reversed(nt):
                    if word[0] == current_name:
                        tmp_bool = True
                    if word[1] in verbs and tmp_bool:
                        v = WordNetLemmatizer().lemmatize(word[0], 'v')
                        if not v in self.IGNORE_ACTIONS:
                            to_do.append(v)
            
        return to_do
