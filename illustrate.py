from PIL import Image, ImageDraw, ImageFont
from typing import Any
import logging


class BoardIllustrator:
    height: int
    width: int
    _draw: Any
    _outline_width: int
    MARGIN = 200

    def __init__(self, height: int, width: int):
        self.image_width = 1600
        self.image_height = 1200
        if height/width > self.image_height/self.image_width:
            scaling = self.image_height/height
            self.image_width = int(width * scaling)
        else:
            scaling = self.image_width/width
            self.image_height = int(height * scaling)
        self.scaling = scaling

        self._outline_width = 2
        self.image = Image.new('RGBA', (self.image_width+BoardIllustrator.MARGIN,
                                        self.image_height+BoardIllustrator.MARGIN), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.height = height
        self.width = width
        self.font = ImageFont.truetype('Arial.ttf', size=25)
        self.container_offset = (
            BoardIllustrator.MARGIN//2, BoardIllustrator.MARGIN // 2)
        self._container(height, width)

    def add_rectangle(self, lx: int, ly: int, height: int, width: int, color: str, annotate=False, text_color='black'):
        '''pillow's rectangle makes the border width grow to the inside'''
        tl = (int(lx*self.scaling+self.container_offset[0]),
              int(ly*self.scaling+self.container_offset[1]))
        br = ((lx+width)*self.scaling+self.container_offset[0],
              (ly+height)*self.scaling+self.container_offset[1])
        self.draw.rectangle([tl, br], outline='black',
                            width=self._outline_width, fill=color)
        if annotate:
            self.annotate_box((lx, ly), height, width, text_color)

    def show(self):
        self.image.show()

    def annotate_box(self, tl: tuple[int, int], height: int, width: int, color):
        '''tl and height width is in terms of mm not pixels'''
        height_caption = f"{height} mm"
        width_caption = f"{width} mm"
        location_x = int(self.container_offset[0]+tl[0]*self.scaling)
        location_y = int(self.container_offset[1]+tl[1]*self.scaling)
        height_pixels, width_pixels = int(
            height*self.scaling), int(width*self.scaling)
        logging.debug(f"rendering annotation at positions in pixels {
            location_x, location_y} scaling factor is {self.scaling}")
        self._vertical_text(self.image, height_caption,
                            (location_x+5, location_y), height_pixels, text_color=color)
        self._horizontal_text(self.image, width_caption,
                              (location_x, location_y), width_pixels, text_color=color)

    def _vertical_text(self, background, caption: str, tl: tuple[int, int], element_height: int, text_color='black'):
        '''creates vertical text starting at coordinates `tl`
        then is y centered around tl.y + element_height'''
        bbox = self.font.getbbox(caption)
        length, height = int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])
        offset = (element_height - length)//2
        txt = Image.new('RGBA', (length+10, height+10),
                        color=(255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        d.text((5, 5), caption, fill=text_color, font=self.font)
        txt90 = txt.rotate(-90, expand=1)
        background.alpha_composite(txt90, (tl[0], tl[1]+offset))
        return background

    def _horizontal_text(self, background, caption: str, tl: tuple[int, int], element_width: int, text_color='black'):
        '''creates vertical text starting at coordinates `tl`
        then is y centered around tl.y + element_height'''
        bbox = self.font.getbbox(caption)
        length, height = int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])
        offset = (element_width - length)//2
        txt = Image.new('RGBA', (length+10, height+10),
                        color=(255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        d.text((5, 5), caption, fill=text_color, font=self.font)
        background.alpha_composite(txt, (tl[0]+offset, tl[1]))
        return background

    def _container(self, height, width):
        offset_x, offset_y = self.container_offset
        container_dimensions_x, container_dimensions_y = (
            int(width*self.scaling), int(height*self.scaling))
        self.draw.rectangle([(offset_x-self._outline_width, offset_y-self._outline_width),
                             (offset_x+container_dimensions_x+self._outline_width, offset_y+container_dimensions_y+self._outline_width)],
                            outline='black', width=self._outline_width)

        self._horizontal_text(
            self.image, f"{width} mm", (self.container_offset[0], self.container_offset[1] * 2 // 3 - 10), container_dimensions_x)
        self._vertical_text(
            self.image, f"{height} mm", (self.container_offset[0] * 2 // 3 - 10, 0), container_dimensions_y)


if __name__ == '__main__':
    illustrator = BoardIllustrator(60, 50)
    illustrator.add_rectangle(10, 10, 30, 30, 'gray')
    illustrator.show()
