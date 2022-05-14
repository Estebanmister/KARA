
class VisualCore():

    def caption(self, image, extension):
        return ""

    def perceive(self, image, extension):
        return ""


# VIDI will soon handle the position of the visual
# prompt as well as other details, for now it just redirects requests to the core
class Vidi():
    def __init__(self, core):
        self.core = core

    def perceive(self, image, extension):
        return self.core.perceive(image, extension)

    def caption(self, image, extension):
        return self.core.caption(image, extension)