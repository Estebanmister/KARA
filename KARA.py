#from load_vidi import *
from FLAVOUR import *
from Syl import *
import memory_gen

# Number of cycles to prevent Kara from quickly switching decisions
THRESHOLD = 0

# sample emotions every x ticks
EMOTION_SAMPLING = 50

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
    def __init__(self, chat_log, ai_name, core, vidi, flavour_core=None, personality=('kind', 'loving', 'a robot'),
                 initial_mood=('helpful',), SALIERI = False):
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
        temp = chat_log
        if len(chat_log) > (MAX_TOKENS * LETTERS_PER_TOKEN) + 1000:
            temp = chat_log[len(chat_log)-(MAX_TOKENS * LETTERS_PER_TOKEN):]
        self.memories = memory_gen.memory_gen(temp)
        print(self.memories)
        self.chat_log = chat_log
        self.flavour_prompt = self.flavour.generate()
        print(self.flavour_prompt)
        #self.memories = memories
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

    def memory_generation(self, context):
        temp = context
        if len(context) > (MAX_TOKENS * LETTERS_PER_TOKEN) + 1000:
            temp = context[len(context) - (MAX_TOKENS * LETTERS_PER_TOKEN):]
        self.memories = memory_gen.memory_gen(temp)

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

        # Cut the chat log to fit the 2048 * 3 character limit
        char_max = MAX_TOKENS * LETTERS_PER_TOKEN
        chars_left = char_max-(len(self.flavour_prompt)+len(self.memories)+len(previous)+len(self.name+" says :") +
                               10 + (100*LETTERS_PER_TOKEN))
        from_log = len('\n'.join(splut))-chars_left
        # Combine all the strings into a singular prompt
        chat_log = self.flavour_prompt + '\n\n' + self.memories\
                   + "\n\n" + '\n'.join(splut)[from_log:] + '\n' + previous + "\n" + self.name + " says :"
        # print(len(chat_log))
        # print(char_max)

        # Generate the bot's message
        # Sometimes the core may forget to remove some of the prompt, just in case we separate the output by newlines
        # and pick the last one (Or if ending in a trailing newline, the previous one to that)
        output = self.core.infer(chat_log).split('\n')
        if output[-1] == "":
            output = output[-2]
        else:
            output = output[-1]
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
        # yes this does happen, these sort of errors are invitable when working with non zero temps and top-p
        if output == "":
            return None
        return output

    def tick(self, force=False):
        thing = self.chat_log[len(self.chat_log) - MAX_TOKENS * LETTERS_PER_TOKEN:]
        # Kara's internal clock.
        if self.clock % EMOTION_SAMPLING == 0:
            # Only determine emotions every few cycles, to save on resources
            result = self.flavour.cons.emotions_shown(thing, self.flavour, self.name)

            if result is not None:
                self.flavour.choice, self.flavour.mood = result
            # update the memories as well
            self.memory_generation(self.chat_log)
        self.clock += 1
        if self.decision_counter == 0 or force:
            # test this first so Kara doesnt have to use the transformer to decide
            if force:
                return self.query()
            # If we have reached 0, it means kara must make a decision again
            elif self.core.decide(thing, self.name) or force:
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
    from load_gpt_forefront import *
    from load_OFA import *
    # You need a forefront account for this, DM me if you have some other API that you want included
    # (or better yet, make a push request)
    gpt = FFNEOX()
    ofa = OFACore()
    kara = Kara(cht, "Kara", gpt, ofa)
    name = input("Your name?")
    while True:
        kara.update_log(input("Say something: "), name)
        output = kara.tick(force=True)
        if output is None:
            print("Kara has nothing to say yet")
        else:
            print("Kara says : " + output)