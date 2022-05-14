"""
THIS IS MOSTLY NOT MY CODE.

This code has been taken from the mesh-transformer-jax repo of user kingoflolz, it has been modified to fit the Core class
I have NOT tested this lately, as you need a TPU to run this (a v3 i believe)
"""

import argparse
import json
import time

import jax
import numpy as np
import optax

from mesh_transformer import util
from mesh_transformer.checkpoint import read_ckpt
from mesh_transformer.sampling import nucleaus_sample
from mesh_transformer.transformer_shard import CausalTransformer
import transformers
from smart_open import open

from mesh_transformer.util import clip_by_global_norm
from Kara import Core


def parse_args():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/6B_roto_256.json", help="Config file location")

    args = parser.parse_args()
    return args


class GPTJ(Core):
    def __init__(self):
        args = parse_args()
        params = json.load(open(args.config))

        gradient_accumulation_steps = params.get("gradient_accumulation_steps", 1)
        per_replica_batch = params["per_replica_batch"]
        cores_per_replica = params["cores_per_replica"]

        assert cores_per_replica <= 8

        self.bucket = params["bucket"]
        self.model_dir = params["model_dir"]
        self.layers = params["layers"]
        self.d_model = params["d_model"]
        self.n_heads = params["n_heads"]
        self.n_vocab = params["n_vocab"]
        self.seq = params["seq"]
        self.norm = params["norm"]

        params["sampler"] = nucleaus_sample
        opt = optax.chain(
            optax.scale(1 / gradient_accumulation_steps),
            clip_by_global_norm(1),
            optax.scale_by_adam(),
            optax.additive_weight_decay(0),
            optax.scale(-1),
            optax.scale_by_schedule(util.gpt3_schedule(0, 1, 0, 0))
        )

        params["optimizer"] = opt

        start = time.time()
        print(f"jax devices: {jax.device_count()}")
        print(f"jax runtime initialized in {time.time() - start:.06}s")

        self.mesh_shape = (jax.device_count() // cores_per_replica, cores_per_replica)
        self.devices = np.array(jax.devices()).reshape(self.mesh_shape)

        with open(f"gs://{self.bucket}/{self.model_dir}/meta.json", "r") as f:
            meta = json.load(f)

        ckpt_step = meta["checkpoints"][-1]
        print(f"using checkpoint {ckpt_step}")

        self.total_batch = per_replica_batch * jax.device_count() // cores_per_replica
        with jax.experimental.maps.mesh(self.devices, ('dp', 'mp')):
            self.network = CausalTransformer(params)

            start = time.time()
            self.network.state = read_ckpt(self.network.state, f"gs://{self.bucket}/{self.model_dir}/step_{self.ckpt_step}/", self.devices.shape[1])
            print(f"network loaded in {time.time() - start:.06}s")

            local_shards = max(jax.local_device_count() // self.mesh_shape[1], 1)
            del self.network.state["opt_state"]
            self.network.state = self.network.move_xmap(self.network.state, np.zeros(local_shards))

            self.tokenizer = transformers.GPT2TokenizerFast.from_pretrained('gpt2')

    def infer(self, text, gen_len=50, stop=(), top_p=0.9, temp=0.75):
        if len(text) > (self.seq*3):
            context = text[len(text)-(self.seq*3):]
        else:
            context = text
        with jax.experimental.maps.mesh(self.devices, ('dp', 'mp')):
            tokens = self.tokenizer.encode(context)
            start = time.time()
            provided_ctx = len(tokens)
            pad_amount = self.seq - provided_ctx
            if pad_amount < 0:
                padded_tokens = tokens
                print('got here')
            else:
                padded_tokens = np.pad(tokens, ((pad_amount, 0),)).astype(np.uint32)
            batched_tokens = np.array([padded_tokens] * self.total_batch)
            length = np.ones(self.total_batch, dtype=np.uint32) * len(tokens)
            output = self.network.generate(batched_tokens, length, gen_len, {"top_p": np.ones(self.total_batch) * top_p,
                                                                        "temp": np.ones(self.total_batch) * temp})
            ready_outputs = []
            for idx, o in enumerate(output[1][0][:, :, 0]):
                ready_outputs.append(self.tokenizer.decode(o))
            print(f"completion done in {time.time() - start:06}s")
            return ready_outputs[0]

    def instruct(self, text):
        return self.infer(text)

    def decide(self, text, name):
        return name.lower() in self.infer(text, gen_len=10).lower()