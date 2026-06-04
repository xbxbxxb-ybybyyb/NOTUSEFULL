# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import fonts

from reportlab.platypus import PageBreak
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib.dates as plt_dates
import seaborn as sns
from io import BytesIO
from reportlab.platypus import Image
import platform

plt.style.use('ggplot')
plt.ioff()
legend_loc = 'upper left'
font_title_weight = 'normal'
pdf_styles = getSampleStyleSheet()
heading_size = pdf_styles['Heading4']

if platform.system() == 'Windows':
    font_name = 'STSONG'
    pdfmetrics.registerFont(TTFont(font_name, r'C:/Windows/Fonts/' + font_name + '.ttf'))
else:
    try:
        font_name = 'STSONG'
        pdfmetrics.registerFont(TTFont(font_name, font_name + '.TTF'))
        pdf_styles.add(ParagraphStyle(fontName=font_name, name=font_name, leading=20, fontSize=12))
    except:
        font_name = "STSong-Light"
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))

PAGE_HEIGHT = defaultPageSize[1]
PAGE_WIDTH = defaultPageSize[0]
CANVAS_FONT_SIZE = 8
img_width = 7.5
img_height = 2.5
fig_width = img_width * 3
fig_height = img_height * 3
max_fig_width = 18
max_fig_height = 27
font_size_title = 20
font_size_axis = 17
font_size_legend = 16
img_format = 'png'
img_dpi = 100


def generate_first_page(canvas, doc, title='因子回测报告'):
    canvas.saveState()
    canvas.setFont(psfontname='STSONG', size=12)
    canvas.setTitle(title=title)
    canvas.drawCentredString(PAGE_WIDTH / 2.0 + 10, PAGE_HEIGHT - 108, title)
    canvas.restoreState()


def generate_later_pages(canvas, doc):
    canvas.saveState()
    canvas.setFont(psfontname='STSONG', size=CANVAS_FONT_SIZE)
    canvas.restoreState()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont(font_name, int(CANVAS_FONT_SIZE * 0.8))
        self.drawCentredString(PAGE_WIDTH / 2 + 10, 0.8 * inch, '第 %d/%d 页' % (self._pageNumber, page_count))
