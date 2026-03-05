from PIL import Image
from renderer.base import Renderer


class BaseScreen:
    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.width = renderer.width
        self.height = renderer.height

    def render(self) -> Image.Image:
        raise NotImplementedError
