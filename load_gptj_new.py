"""
I actually recommend using this one for GPTJ, it might actually run better.
Still requires a TPU though
"""
import jax
jax.devices()
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from KARA import Core

# trick to make it load faster
def no_init(loading_code):
    def dummy(self):
        return
    
    modules = [torch.nn.Linear, torch.nn.Embedding, torch.nn.LayerNorm]
    original = {}
    for mod in modules:
        original[mod] = mod.reset_parameters
        mod.reset_parameters = dummy
    
    result = loading_code()
    for mod in modules:
        mod.reset_parameters = original[mod]
    
    return result


class HFGPTJ(Core):
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
        self.model = no_init(lambda: AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B", revision='float16', low_cpu_mem_usage=True))
        self.seq = 2048

    def infer(self, text, gen_len=50, stop=(), top_p=0.9, temp=75):
        if len(text)>(self.seq*3):
            context = text[len(text)-(self.seq*3):]
        else:
            context = text
        tokens = self.tokenizer.encode(context, return_tensors="pt")
        print(len(tokens[0]))
        out = self.model.generate(tokens, min_length=len(tokens[0])+gen_len, max_length=len(tokens[0])+gen_len, top_p=top_p)
        return self.tokenizer.decode(out[0]).replace(context, "")

    def instruct(self, text):
        return self.infer(text)

    def decide(self, text, name):
        return name.lower() in self.infer(text, gen_len=4).lower()

