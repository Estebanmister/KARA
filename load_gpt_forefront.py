import requests
import os
from nltk.corpus import wordnet
from KARA import Core
api_key = os.getenv('FOREFRONT_KEY')
api_url = os.getenv('FOREFRONT_URL')

headers = {"Authorization": api_key}


class FFNEOX(Core):
    def __init__(self):
        pass

    def infer(self, message, gen_len=100, stop=['\n'], top_p=1, temp=0.7):
        body = {
            "text": message,
            "top_p": top_p,
            "top_k": 40,
            "temperature": temp,
            "repetition_penalty": 1.0,
            "length": gen_len,
            "stop_sequences": stop
        }

        res = requests.post(
            api_url,
            json=body,
            headers=headers
        )
        try:
            data = res.json()
            return data['result'][0]['completion']
        except:
            print(res)
            raise ConnectionError

    def instruct(self,mess):
        # very sophisticated
        return self.infer(mess)

    # todo: move this into the KARA class
    def decide(self, context, name):
        max_chars = 2048 * 3
        body = {
            "text": context[len(context)-max_chars:].strip(" "),
            "top_p": 1,
            "top_k": 10,
            "temperature": 0.8,
            "repetition_penalty": 0.5,
            "length": 5,
            "stop_sequences": [" "]
        }

        res = requests.post(
            api_url,
            json=body,
            headers=headers
        )
        data = res.json()
        return name.lower() in data['result'][0]['completion'].lower()

    def emotions_shown(self, mess, flavour, name):
        max_chars = 2048*3
        chars_left = max_chars-(len("Read the following conversation: \n")
                                + len("\n\nWhat emotions (separated by a comma) would "+name+" be feeling right now?\n\nAnswer: "+name+" is")
                                + 20)
        response = self.infer("Read the following conversation: \n"+mess[len(mess)-chars_left:]
                         + "\n\nWhat emotions would "+name+" be feeling right now?\n\nAnswer: "+name+" is", gen_len=20)
        response = response.replace('\n', ' ').replace('-', ' ').lower().split(' ')
        for resp in response:
            if resp.lower() in flavour.flavours or resp.lower() in flavour.similar:
                return resp, response
            for syn in wordnet.synsets(resp):
                for l in syn.lemmas():
                    if l.name().lower() in flavour.flavours or l.name().lower() in flavour.similar:
                        return l.name(), response


