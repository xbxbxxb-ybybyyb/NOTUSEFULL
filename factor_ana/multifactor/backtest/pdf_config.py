__author__ = "Software Authors: Xu Deyuan"
__copyright__ = "Copyright (C) 2019 HTSC"
__license__ = "Private"
__version__ = "1.0"
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Spacer,Paragraph
from reportlab.lib.styles import getSampleStyleSheet
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
def generate_first_page(canvas,doc,title='Factor Backtest Report'):
    canvas.saveState()
    canvas.setTitle(title=title)
    canvas.drawCentredString(PAGE_WIDTH/2.0+10,PAGE_HEIGHT-108,title)
    canvas.setFont(psfontname=font_name,size=CANVAS_FONT_SIZE)
    canvas.restoreState()
def generate_later_pages(canvas,doc):
    canvas.saveState()
    canvas.setFont(psfontname=font_name,size=CANVAS_FONT_SIZE)
    canvas.restoreState()
plt.style.use('ggplot')
plt.ioff()
font_name='STSong-Light'
legend_loc='upper left'
font_title_weight='normal'
if platform.system()=='Windows':
    pdfmetrics.registerFont(TTFont(font_name,r'C:/Windows/Fonts/'+font_name+'.ttf'))
else:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]
CANVAS_FONT_SIZE=8
pdf_styles=getSampleStyleSheet()
heading_size=pdf_styles['Heading4']
img_width=7.5
img_height=2.5
fig_width=img_width*3
fig_height=img_height*3
max_fig_width=18
max_fig_height=27
font_size_title=20
font_size_axis=17
font_size_legend=16
img_format='png'
img_dpi=100
class NumberedCanvas(canvas.Canvas):
    def __init__(self,*args,**kwargs):
        canvas.Canvas.__init__(self,*args,**kwargs)
        self._saved_page_states=[]
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        num_pages=len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    def draw_page_number(self,page_count):
        self.setFont(font_name,int(CANVAS_FONT_SIZE*0.8))
        self.drawCentredString(PAGE_WIDTH/2+10,0.8*inch,'Page %d of %d'%(self._pageNumber,page_count))
