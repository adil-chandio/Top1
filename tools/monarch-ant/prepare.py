"""Prepare procedural graphics and reference-free CGI texture inputs for offline rendering."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import argparse
import os

CACHE = Path(os.environ.get('MONARCH_ANT_CACHE', '.cache/monarch-cam-ant-film'))
FONT = Path(os.environ.get('MONARCH_FONT_DIR', '/usr/share/fonts/truetype/dejavu'))
WHITE = '#fff5e4'
DIM = '#d2c3ad'
GOLD = '#f7c978'
TEAL = '#a9dcd4'


def assets():
    for source, out, size in [('sand-albedo.png', 'sand.rgba', (768, 768)),
                              ('beyond-the-rim.png', 'matte.rgba', (768, 432))]:
        with Image.open(CACHE/'assets'/source) as im:
            im = ImageOps.fit(im.convert('RGBA'), size, Image.Resampling.LANCZOS)
            (CACHE/'assets'/out).write_bytes(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())


class Screen:
    def __init__(self, w, h, badge=None, color=GOLD):
        self.w, self.h = w, h
        self.k = h/720
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.s = 43
        if badge:
            f = self.font(13, 'mono')
            a = self.p(self.s, 43)
            b = (a[0]+round(self.d.textlength(badge, font=f)+37*self.k), a[1]+round(29*self.k))
            self.d.rounded_rectangle((a, b), radius=round(6*self.k), fill=(17,24,22,232))
            cx, cy = self.p(self.s+13, 57)
            self.d.ellipse((cx-2.7*self.k, cy-2.7*self.k, cx+2.7*self.k, cy+2.7*self.k), fill=color)
            self.d.text(self.p(self.s+24,57), badge, font=f, fill=color, anchor='lm')

    def p(self, x, y):
        return round(x*self.k), round(y*self.k)

    def font(self, n, face='sans'):
        t = {'serif':'DejaVuSerif', 'sans':'DejaVuSans', 'bold':'DejaVuSans-Bold', 'mono':'DejaVuSansMono'}[face]
        return ImageFont.truetype(str(FONT/(t+'.ttf')), max(1, round(n*self.k)))

    def text(self, x,y,text,n=22,face='sans', c=WHITE, a='la', stroke=0):
        self.d.text(self.p(x,y),text,font=self.font(n,face),fill=c,anchor=a,stroke_width=round(stroke*self.k),stroke_fill=(20,26,21,214))

    def line(self, x,y,x1,y1,c=GOLD,w=1):
        self.d.line((self.p(x,y), self.p(x1,y1)), fill=c, width=max(1,round(w*self.k)))

    def card(self, x,y,w,h, fill=(17,25,22,232), outline=(222,195,146,94)):
        self.d.rounded_rectangle((self.p(x,y),self.p(x+w,y+h)),radius=max(3,round(12*self.k)),fill=fill,outline=outline,width=max(1,round(self.k)))

    def lower(self, headline, sub, index=None, accent=GOLD):
        w = max(386, self.d.textlength(sub,font=self.font(18))/self.k+46,
                self.d.textlength(headline,font=self.font(32,'serif'))/self.k+46)
        self.card(self.s,566,w,110)
        self.line(self.s+20,586,self.s+48,586,accent,2)
        if index:
            self.text(self.s+59,586,index,13,'mono',accent,'lm')
        self.text(self.s+20,599,headline,32,'serif')
        self.text(self.s+20,644,sub,18,'sans',DIM)

    def save(self,key):
        path=CACHE/'work'/'overlays';path.mkdir(parents=True,exist_ok=True)
        (path/(key+'.rgba')).write_bytes(self.im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes())


def make(w,h,which):
    for key in which:
        badge, color = 'CGI RECONSTRUCTION', GOLD
        if key in {'proof','replay','free-air','failure','reprise'}:
            badge='TIME-EXPANDED CGI'
        if key in {'inside','elastic','fast','groups','paired','results','ran','jumped','caught','restrained','handling','confound'}:
            badge,color='STUDY ILLUSTRATION',TEAL
        if key in {'title','end','sources','wordmark'}:
            badge=None
        s=Screen(w,h,badge,color)
        if key=='proof':
            s.text(43,686,'MONARCH CAM  /  CONTACT STUDY',14,'mono',WHITE,'ls',1)
        elif key=='title':
            s.line(49,337,95,337,GOLD,2)
            s.text(108,337,'MONARCH CAM     /     FIELD NOTE 01A',16,'mono',GOLD,'lm',1)
            s.text(47,363,'This Ant Bites the',65,'serif',WHITE,stroke=1)
            s.text(46,432,'Ground to Escape',65,'serif',WHITE,stroke=1)
            s.text(51,532,'TRAP-JAW ANT  /  ODONTOMACHUS BRUNNEUS',17,'mono',DIM,stroke=1)
        elif key=='larva':
            s.lower('Antlion larva','Myrmeleon carolinus  •  mostly buried','THE TRAP')
        elif key=='ant':
            s.lower('Trap-jaw ant','Odontomachus brunneus  •  worker','THE ESCAPE')
        elif key=='head':
            s.lower('Mandibles','Two jaws pivot at the front of the head','THE SPRING')
        elif key=='inside':
            s.lower('Elastic head capsule','Stores energy as the closing muscles pull','SCHEMATIC',TEAL)
        elif key=='elastic':
            s.card(43,509,492,164)
            s.text(63,526,'TWO ELASTIC ELEMENTS',14,'mono',GOLD)
            s.d.ellipse((s.p(64,572),s.p(76,584)),fill=TEAL)
            s.text(88,579,'Head capsule pushes',24,'sans',WHITE,'lm')
            s.d.ellipse((s.p(64,618),s.p(76,630)),fill='#e5ac71')
            s.text(88,625,'Muscle–attachment unit pulls',24,'sans',WHITE,'lm')
        elif key=='fast':
            s.card(43,450,448,223)
            s.text(65,469,'SAME-SPECIES LAB STUDY',14,'mono',TEAL)
            s.text(65,502,'77 μs',66,'serif')
            s.text(66,593,'Mean jaw closure',23,'bold',WHITE)
            s.text(66,633,'Not time in the air',18,'sans',DIM)
        elif key=='free-air':
            s.lower('No surface','Jaw closure alone cannot push the ant off a wall.','QUALITATIVE COMPARISON')
        elif key=='replay':
            s.text(43,686,'CONTACT REPLAY  /  NOT TO SCALE IN TIME',14,'mono',WHITE,'ls',1)
        elif key=='failure':
            s.text(43,686,'RECONSTRUCTED FAILED JUMP',14,'mono',WHITE,'ls',1)
        elif key in {'ran','jumped','caught'}:
            s.card(48,322,592,338,fill=(18,27,24,244))
            s.text(75,349,'117 LAB ENCOUNTERS',18,'mono',GOLD)
            rows=[('About half','Ran out'),('15%','Jumped clear'),('Roughly a third','Caught')]
            n={'ran':1,'jumped':2,'caught':3}[key]
            for i,(rate,outcome) in enumerate(rows[:n]):
                y=405+i*63
                s.line(75,y-11,606,y-11,(231,222,189,64))
                s.text(75,y,rate,30,'serif',GOLD if i==1 else WHITE)
                s.text(391,y+6,outcome,22,'sans',WHITE)
            s.text(75,623,'Larabee & Suarez · 2015 · lab observation',15,'sans',DIM)
        elif key in {'groups','paired','results'}:
            if key=='groups':
                cards=[('01','Untouched','Jaws free'),('02','Mock-handled','Jaws free'),('03','Handled','Jaws restrained')]
            else:
                cards=[('02','Mock-handled','Jaws free'),('03','Handled','Jaws restrained')]
            s.text(43,120,'Take away the snap',56,'serif',WHITE,stroke=1)
            s.text(46,194,'CONTROLLED EXPERIMENT   /   76 ANTS PER GROUP',16,'mono',TEAL,stroke=1)
            for i,(no,name,info) in enumerate(cards):
                x=43+396*i
                s.card(x,440,371,204,fill=(16,27,24,242),outline=(174,225,214,124))
                s.text(x+21,465,no,17,'mono',TEAL)
                s.text(x+21,514,name,32,'serif')
                s.text(x+21,569,info,22,'sans',DIM)
                if key=='results' and i==0:
                    s.text(x+21,604,'More escapes by jumping',15,'bold',GOLD)
        elif key=='restrained':
            s.lower('Jaws restrained','The ant can still use her legs.','CONTROLLED EXPERIMENT',TEAL)
        elif key=='handling':
            s.lower('Handling changed running','Even ants with free jaws ran out less often.','THE CONTROL',TEAL)
        elif key=='confound':
            s.lower('Two effects, not one','Handling and loss of the snap must be separated.','THE CONTROL',TEAL)
        elif key=='reprise':
            s.text(43,684,'THE FIRST ESCAPE  /  REPRISE',14,'mono',WHITE,'ls',1)
        elif key=='end':
            s.line(51,457,92,457,GOLD,2)
            s.text(51,478,'For one bite.',62,'serif',WHITE,stroke=1)
            s.text(53,595,'MONARCH CAM   /   END OF FIELD NOTE 01A',16,'mono',GOLD,stroke=1)
        elif key=='sources':
            s.card(43,136,890,436,fill=(15,24,22,247))
            s.text(72,167,'MONARCH CAM  /  FIELD NOTE 01A',16,'mono',TEAL)
            s.text(70,209,'This Ant Bites the Ground to Escape',39,'serif')
            s.line(73,278,891,278,(231,222,189,100))
            s.text(73,302,'Larabee & Suarez · PLOS ONE · 2015',23,'sans')
            s.text(73,337,'doi:10.1371/journal.pone.0124871',19,'mono',DIM)
            s.text(73,397,'Sutton et al. · Journal of Experimental Biology · 2022',23,'sans')
            s.text(73,432,'doi:10.1242/jeb.244077',19,'mono',DIM)
            s.text(73,511,'Original CGI and designed Foley. No lab footage in this film.',18,'sans',DIM)
        s.save(key)


if __name__ == '__main__':
    a=argparse.ArgumentParser();a.add_argument('width',type=int);a.add_argument('height',type=int)
    a.add_argument('overlays',nargs='+');o=a.parse_args();assets();make(o.width,o.height,o.overlays)
