#from load_vidi import *
from FLAVOUR import *
from Syl import *
import stanza
# uncomment this at the first run
#stanza.download('en')
nlp = stanza.Pipeline('en', processors='tokenize,ner')

# Context fraction used for emotion detection and internal decisions
c = 2
# Number of cycles to prevent Kara from quickly switching decisions
THRESHOLD = 2

# sample emotions every x ticks
EMOTION_SAMPLING = 4

# Token max
MAX_TOKENS = 2048
LETTERS_PER_TOKEN = 3


class Core:
    def decide(self, context, name):
        pass

    def instruct(self, action):
        pass

    def infer(self, message, gen_len, stop, top_p, temp):
        pass


class Kara:
    def __init__(self, chat_log, ai_name, core, vidi, flavour_core=None, personality=('kind', 'loving'),
                 initial_mood=('helpful',), memories = False, SALIERI = False):
        """
        Create a Chatbot
        parameters:
            chat_log: string, previous conversations
            ai_name: the name of the chatbot
            core: a Core object, defines what type of transformer the bot will use
            vidi: a Vidi object, defines what algorithm the bot will use to see images
            flavour_core: optional, a Core object, defines what transformer will be used to determine emotions and personalities
            personality: Tuple, defaults to ('kind', 'loving'), the keywords used by FLAVOUR to generate a personality
            initial_mood: Tuple, defaults to ('helpful',), keywords used by FLAVOUR to determine what avatar to use for SALIERI
            memories: BOOL, defines if the memory function should be enabled (can cause problems with the chat log is too small
            SALIERI: BOOL, generate a gif of the character speaking whatever output it generates
        """
        self.name = ai_name

        # todo: find a permanent solution to clean the chat log, ACTIVELY
        chat_log = chat_log.replace("’", "'").replace("â€™", "'").replace("´", "'")

        if flavour_core is None:
            self.flavour = Flavour(ai_name, personality=personality, initial_mood=initial_mood, cons=core)
        else:
            self.flavour = Flavour(ai_name, personality=personality, initial_mood=initial_mood, cons=flavour_core)

        self.vidi = vidi
        self.core = core
        self.salieri = SALIERI
        if SALIERI:
            # create the animated characters for each emotion (todo: make this dynamic)
            self.sylshy = SylCharacter(ai_name.lower()+"_shy")
            self.sylhelpful = SylCharacter(ai_name.lower() + "_helpful")
            self.sylangry = SylCharacter(ai_name.lower() + "_angry")
            self.sylplayful = SylCharacter(ai_name.lower() + "_playful")

        self.chat_log = chat_log
        self.flavour_prompt = self.flavour.generate()
        self.memories = memories
        self.decision_counter = 0
        self.clock = 0

    def show(self, who, image, img_type):
        self.chat_log += who + " shows you an image of " + self.vidi.describe(image, img_type) + "\n"

    def perceive(self, image, img_type):
        self.chat_log += "You see a " + self.vidi.describe(image, img_type) + "\n"

    def update_flavour(self):
        self.flavour_prompt = self.flavour.generate()

    def update_log(self, message, who):
        self.chat_log += who + " says : " + message + '\n'

    def memory_lookup(self, context_list, to_search):
        """
        Use Stanza to find entities within to_search, and search those entities on the context
        parameters:
            context_list: list of strings
            to_search: string
        """
        doc = nlp(to_search)
        memories = []
        entities = doc.entities
        # For every entity, check if it has been mentioned before, and attach the context related to that entity
        for entity in entities:
            for b, line in enumerate(context_list):
                if entity.text.lower() in line.lower().split(":"):
                    memories.append([context_list[b-1], context_list[b], context_list[b+1]])
        return memories

    def query(self):
        """
        Create a prompt and ask the core to generate a response for the AI
        The prompt consists of = FLAVOUR prompt (personality and mood) + memories related to the previous message +
         Previous conversations and images in chronological order +
        """
        # Split the chat log into lines
        splut = self.chat_log.split("\n")
        # take out the last last to check memories
        previous = splut.pop()
        joined_memories = []
        if self.memories:
            # perform the memory look up, according to the entities found by Stanza
            memories = self.memory_lookup(splut, ':'.join(previous.split(':')[1:]))
            # only take the last 3 memories, the chronological order of the conversation is more important.
            memories = memories[len(memories)-3:]
            joined_memories = []
            for memory in memories:
                joined_memories.append("\n".join(memory))

        # Cut the chat log to fit the 2048 * 3 character limit
        char_max = MAX_TOKENS * LETTERS_PER_TOKEN
        memories_length = len('\n'.join(joined_memories))
        chars_left = char_max-(memories_length+len(self.flavour_prompt)+len(previous)+len(self.name+" says :") +
                               10 + (100*LETTERS_PER_TOKEN))
        from_log = len('\n'.join(splut))-chars_left
        # Combine all the strings into a singular prompt
        chat_log = self.flavour_prompt + '\n\n' + '\n'.join(joined_memories)\
                   + "\n\n" + '\n'.join(splut)[from_log:] + '\n' + previous + "\n" + self.name + " says :"
        # print(len(chat_log))
        # print(char_max)

        # Generate the bot's message
        output = self.core.infer(chat_log)
        print("Said " + output)
        self.chat_log += self.name + " says : " + output + '\n'

        # According to the previous cycle's emotions, determined by FLAVOUR
        # Generate a simple moving avatar through SALIERI, and save it on a gif
        if self.salieri:
            if self.flavour.choice == "shy":
                self.sylshy.save(self.sylshy.use_parser(self.name + " says : "+output))
            elif self.flavour.choice == "helpful":
                self.sylhelpful.save(self.sylhelpful.use_parser(self.name + " says : " + output))
            elif self.flavour.choice == "angry":
                self.sylangry.save(self.sylangry.use_parser(self.name + " says : " + output))
            elif self.flavour.choice == "playful":
                self.sylplayful.save(self.sylplayful.use_parser(self.name + " says : " + output))
        # yes this does happen
        if output == "":
            return None
        return output

    def tick(self, force=False):
        # Kara's internal clock.
        if self.clock % 10 == 0:
            # Only determine emotions every 10 cycles, to save on resources
            result = self.flavour.cons.emotions_shown(
                self.chat_log[len(self.chat_log) // c:], self.flavour, self.name)

            if result is not None:
                self.flavour.choice, self.flavour.mood = result
            # Update the verbose prompt describing their behaviour
            self.update_flavour()
        self.clock += 1
        if self.decision_counter == 0 or force:
            # test this first so Kara doesnt have to use the transformer to decide
            if force:
                return self.query()
            # If we have reached 0, it means kara must make a decision again
            elif self.core.decide(self.chat_log[len(self.chat_log) // c:], self.name) or force:
                # Make Kara talk
                return self.query()
            else:
                # If kara has decided to stop talking, prevent her from talking for a threshold set of cycles
                self.decision_counter = THRESHOLD
                return None
        else:
            # Decrement decision counter
            self.decision_counter -= 1
            return None


# Example application
if __name__ == "__main__":
    ff = open("chat_log.txt")
    cht = ff.read()
    ff.close()
    kara = Kara(cht, "Kara", core='forefront')
    name = input("Your name?")
    while True:
        kara.update_log(input("Say something: "), name)
        output = kara.tick()
        if output is None:
            print("Kara has nothing to say yet")
        else:
            print("Kara says : " + output)