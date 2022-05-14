import random


class Flavour:
    def __init__(self, name, personality, initial_mood, cons):
        """
        Create a FLAVOUR personality and mood handler object
        parameters:
            name: name of the chatbot
            personality: tuple of strings, keywords describing the personality of the chatbot
            inital_mood: tuple of strings, keywords describing the mood at the start of the first conversation
            cons: Core type object, transformer model to use for QA
        """
        # Emotions corresponding to the available animated characters
        self.flavours = ["shy", "playful", "helpful", "angry"]
        # how many synonyms we hard coded for each flavour
        self.similar_count = 3
        # Potential synonyms to those emotions todo: make this dynamic
        self.similar = ["sad", "sadness", 'worried', "cheeky", 'happy', 'glad', "kind", 'thankful',
                        "frustrated", 'mad', 'dubious', '']
        self.choice = "helpful"
        self.mood = initial_mood
        self.personality = personality
        self.cons = cons
        self.name = name

    def select(self, flavour):
        self.choice = flavour

    def generate(self):
        # Generate a prompt that will describe the chatbot
        # The placement of this prompt highly affects its efficiency, and thus it is still experimental
        return self.name+" is"+self.cons.instruct(random.choice(["Generate", "Write"])+" a sentence that describes a person named " +
                                  self.name + " who is: " + ', '.join(self.personality)+" and is currently feeling: " +
                                  ', '.join(self.mood) + "\n\nAnswer: "+self.name+" is a")

    def convertvidi(self, prompt):
        # UNUSED todo: next update
        if self.choice not in self.flavours:
            if self.choice not in self.similar:
                return None
            for i, word in enumerate(self.similar):
                if self.choice == word:
                    # round UP
                    self.choice = self.flavours[round(i / self.similar_count)]
        if self.choice == "shy":
            return prompt.replace("talking to", "reluctantly talking to")
        elif self.choice == "playful":
            return prompt.replace(".\n\n", " as kindly as possible.\n\n")
        elif self.choice == "angry":
            return prompt.replace(".\n\n", " though you don't really want to\n\n")
        elif self.choice == "helpful":
            return prompt.replace(".\n\n", ". You want to be helpful to them.\n\n")