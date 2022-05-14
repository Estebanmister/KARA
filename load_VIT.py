import jax
import requests
from PIL import Image
from VIDI import VisualCore

# must be run on a local TPU
class VITCore(VisualCore):
    # works with Pillow images.
    def __init__(self):
        loc = "ydshieh/vit-gpt2-coco-en"

        self.feature_extractor = ViTFeatureExtractor.from_pretrained(loc)
        self.tokenizer = AutoTokenizer.from_pretrained(loc)
        self.model = VisionEncoderDecoderModel.from_pretrained(loc)

        self.gen_kwargs = {"max_length": 16, "num_beams": 4}

    @jax.jit
    def generate(self, pixel_values):
        output_ids = self.model.generate(pixel_values, **self.gen_kwargs).sequences
        return output_ids

    def predict(self, image):
        pixel_values = self.feature_extractor(images=image, return_tensors="np").pixel_values
        output_ids = self.generate(pixel_values)
        preds = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]
        return preds

    def perceive(self, image):
        return "You are in "+predict(image)[0]

    def caption(self, image):
        return "You are in " + predict(image)[0]
