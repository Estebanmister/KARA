import os
import openai
import nltk
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from FLAVOUR import Flavour
from KARA import Core

api_key = os.getenv('OPENAI_KEY')
api_url = os.getenv('OPENAI_URL')


class GPT3(Core):

    def __init__(self):
        self.openai = openai
        self.openai.api_base = api_url
        self.openai.api_key = api_key

    def infer(self, mess, gen_len=60, stop=("\n", "\r\n"), top_p=1, temp=1):
        if len(mess) > 9400:
            mess = mess[len(mess)-6600:]
        response = self.openai.Completion.create(engine="text-davinci-001", prompt=mess, max_tokens=gen_len, top_p=top_p, stop=stop)['choices'][0]['text']
        if response == '' or '????' in response:
            response = self.openai.Completion.create(engine="text-davinci-001", prompt=mess, max_tokens=gen_len, top_p=top_p)['choices'][0]['text'].split('\n')
            for resp in response:
                if resp != '' and '????' not in resp:
                    return resp.replace('\xa0', '').encode('utf-8').decode()
        return response.replace('\xa0', '').encode('utf-8').decode()

    def decide(self, log, name):
        if len(log) > 9400:
            log = log[len(log)-6600:]
        response = self.openai.Completion.create(engine="text-babbage-001", prompt=log, max_tokens=2, top_p=1)
        return name.lower() in response['choices'][0]['text'].lower()

    def instruct(self, mess):
        if len(mess) > 9400:
            mess = mess[len(mess)-6600:]
        response = self.openai.Completion.create(engine="text-curie-001", prompt=mess, max_tokens=10, top_p=1)
        return response['choices'][0]['text']

    def emotions_shown(self, mess, flavour, top_p=1):
        for i in range(3):
            if len(mess) > 9400:
                mess = mess[len(mess)-6600:]
            seed = "Name the emotions that the following conversation display:\n"+mess+"\nEmotions shown:\n-"
            response = self.openai.Completion.create(engine="text-curie-001", prompt=seed, max_tokens=6, top_p=top_p)
            response = response['choices'][0]['text'].replace('-', '').replace(' ', '').lower().split('\n')
            # dont use this.
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
