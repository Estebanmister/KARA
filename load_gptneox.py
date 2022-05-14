"""
I HAVE NOT TESTED THIS YET.
"""
import nltk
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import openai
import os
from KARA import Core
api_key = os.getenv('GOOSE_KEY')
api_url = os.getenv('GOOSE_URL')


class GooseNEOX(Core):
    def __init__(self):
        self.openai = openai
        self.openai.api_base = api_url
        self.openai.api_key = api_key

    def infer(self, mess, gen_len=60, top_p=1, all=False, stop="\n"):
        if len(mess) > 4000:
            mess = mess[len(mess)-3300:]
        completion = self.openai.Completion.create(
            engine="gpt-neo-20b",
            prompt=mess,
            max_tokens=gen_len,
            top_p=top_p)
        txt = completion.choices[0].text
        if all:
            return txt
        else:
            text = txt.split("\n")
            output = text[0]
            for i in text:
                if i == "" or i.startswith("..."):
                    continue
                elif not " says :" in i:
                    return i
                elif "Kara says : " in i:
                    return i.replace("Kara says : ", "")
            return output

    def emotions_shown(self, mess, flavour, top_p=1):
        for i in range(3):
            if len(mess) > 9400:
                mess = mess[len(mess)-6600:]
            seed = "Name the emotions that the following conversation display:\n"+mess+"\nEmotions shown:\n-"
            response = self.infer(seed, 6, all=True, top_p=top_p)
            response = response.replace('-', '').replace(' ', '').lower().split('\n')
            for resp in response:
                if resp.lower() in flavour.flavours:
                    return resp, response
                if any(list(map(lambda a: resp.lower() in a, flavour.similar))):
                    woop = list(map(lambda a: resp.lower() in a, flavour.similar))
                    return flavour.flavours[list(map(lambda a: resp.lower() in a, flavour.similar)).index(True)], response
                for syn in wordnet.synsets(resp):
                    for l in syn.lemmas():
                        if any(list(map(lambda a: l.name().lower() in a, flavour.similar))):
                            return flavour.flavours[list(map(lambda a: l.name().lower() in a, flavour.similar)).index(True)], response
                        if l.name().lower() in flavour.flavours:
                            return l.name(), response
        return None

    def decide(self, log, name):
        if len(log) > 9400:
            log = log[len(log)-6600:]
        response = self.infer(log, all=True, gen_len=4, top_p=1)
        return name.lower() in response.lower()

    def instruct(self, mess):
        return self.infer(mess, all=True).split("\n")[0]