"""Original schematic glassware for air-sensitive organometallic apparatus drawings.

All parts are grouped pen annotations, never atoms or chemical bonds. The same
catalog supplies the Qt palette and the browser/native-macOS template picker.
"""
import copy
import html
import json
import math
from pathlib import Path


class Part:
    def __init__(self, name, category):
        self.name, self.category, self.paths = name, category, []

    def line(self, *points, closed=False, fill='none'):
        self.paths.append({'points': [{'x': round(x, 3), 'y': round(y, 3)} for x, y in points],
                           'closed': closed, 'fill': fill})
        return self

    def arc(self, x, y, rx, ry, start=0, end=360, count=40):
        return self.line(*[(x+rx*math.cos(math.radians(start+(end-start)*i/count)),
                            y+ry*math.sin(math.radians(start+(end-start)*i/count))) for i in range(count+1)])

    def neck(self, x=0, top=-75, bottom=-28, width=18):
        self.line((x-width/2, bottom), (x-width/2, top), (x+width/2, top), (x+width/2, bottom))
        self.line((x-width/2-2, top+5), (x+width/2+2, top+5))
        return self

    def valve(self, x, y):
        self.line((x-9,y-5),(x+9,y-5),(x+9,y+5),(x-9,y+5),closed=True)
        self.line((x,y-5),(x,y-13),(x+13,y-13))
        return self

    def frit(self, left, right, y):
        self.line((left,y-3),(right,y-3),(right,y+3),(left,y+3),closed=True)
        for x in range(int(left)+3,int(right),6): self.line((x-2,y+2),(x+2,y-2))
        return self

    def fragment(self):
        annotations = [dict(id=f'glass-{i}', type='pen', x=0, y=0, angle=0,
                            heads='none', lineWidth=1.4, dashed=False, **copy.deepcopy(path))
                       for i,path in enumerate(self.paths)]
        return {'atoms': [], 'bonds': [], 'annotations': annotations, 'ligands': [],
                'groups': [{'id':'glass-group','atoms':[], 'annotations':[a['id'] for a in annotations], 'integral':True}]}

    def svg(self):
        points=[p for path in self.paths for p in path['points']]
        x,y=min(p['x'] for p in points)-6,min(p['y'] for p in points)-6
        w,h=max(p['x'] for p in points)-x+6,max(p['y'] for p in points)-y+6
        paths=[]
        for path in self.paths:
            d='M'+' L'.join(f"{p['x']} {p['y']}" for p in path['points'])+(' Z' if path['closed'] else '')
            paths.append(f'<path d="{d}" fill="{path["fill"]}"/>')
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="150" height="100" role="img" aria-label="{html.escape(self.name)}"><g stroke="#151b20" stroke-width="1.4" stroke-linejoin="round" fill="none">'+''.join(paths)+'</g></svg>'


def parts():
    result=[]
    def new(name, category='Schlenk / air-sensitive'):
        p=Part(name,category);result.append(p);return p
    def bulb(p):
        p.arc(0,12,36,38,-75,255).neck(bottom=-25)
        return p
    bulb(new('Round-bottom flask','Flasks'))
    p=bulb(new('Three-neck round-bottom flask','Flasks'))
    # Side necks terminate at the flask shoulder.
    for sign in [-1,1]:
        p.line((sign*23,-17),(sign*39,-49),(sign*53,-42),(sign*34,-7))
        p.line((sign*37,-45),(sign*52,-38))
    p=bulb(new('Schlenk flask with sidearm'))
    p.line((9,-44),(39,-44));p.line((9,-34),(39,-34));p.valve(44,-39)
    p.line((53,-44),(68,-44),(68,-62));p.line((53,-34),(78,-34),(78,-62));p.line((66,-62),(80,-62))
    p=new('Schlenk tube with sidearm').neck(top=-75,bottom=42,width=32)
    p.arc(0,42,16,16,0,180,20);p.line((16,-42),(40,-42));p.line((16,-32),(40,-32));p.valve(45,-37)
    p.line((54,-42),(72,-42));p.line((54,-32),(72,-32))
    p=new('J. Young NMR tube')
    p.line((-5,-30),(-5,72));p.arc(0,72,5,5,0,180,16);p.line((5,72),(5,-30))
    p.line((-8,-30),(-8,-48),(8,-48),(8,-30),closed=True);p.line((-12,-48),(-12,-62),(12,-62),(12,-48),closed=True)
    p.line((-8,-54),(8,-54));p.line((-8,-58),(8,-58))
    p=bulb(new('Valved storage ampoule'))
    p.valve(0,-57);p.line((-6,-75),(-6,-89),(6,-89),(6,-75))
    p=new('Septum cap','Connections')
    p.line((-15,-8),(15,-8),(15,6),(10,6),(10,17),(-10,17),(-10,6),(-15,6),closed=True)
    for x in range(-11,14,5):p.line((x,-5),(x,3))
    p=new('Cannula transfer needle','Connections')
    p.line((-65,42),(-65,-27),(-60,-35),(-50,-39),(50,-39),(60,-35),(65,-27),(65,42))
    p.line((-62,42),(-62,-26),(-58,-32),(-49,-36),(49,-36),(58,-32),(62,-26),(62,42))
    p=new('Syringe and needle','Connections')
    p.line((-12,-32),(-12,24),(12,24),(12,-32),closed=True);p.line((-20,-32),(20,-32))
    p.line((-3,-32),(-3,-65),(3,-65),(3,-32));p.line((-14,-65),(14,-65))
    p.line((-6,24),(-3,35),(3,35),(6,24));p.line((-1,35),(-1,70),(1,73),(1,35))
    for y in range(-20,21,10):p.line((-12,y),(-4,y))
    p=new('Glass stopcock','Connections');p.line((-45,-5),(45,-5));p.line((-45,5),(45,5));p.valve(0,0)
    p=new('Bent vacuum adapter','Connections')
    p.line((-12,48),(-12,-15),(5,-32),(48,-32));p.line((0,48),(0,-10),(10,-20),(48,-20));p.line((-15,43),(3,43))
    p=new('Ground-glass stopper','Connections')
    p.line((-11,30),(-14,-10),(14,-10),(11,30),closed=True);p.line((-5,-10),(-5,-25),(5,-25),(5,-10));p.arc(0,-32,16,7)
    p=new('Fritted Schlenk filter','Filtration').neck(top=-80,bottom=-30,width=26)
    p.line((-13,-30),(-27,-18),(-27,24),(-8,45),(-8,72));p.line((13,-30),(27,-18),(27,24),(8,45),(8,72));p.frit(-27,27,20)
    p.line((27,-12),(49,-12));p.line((27,-2),(49,-2));p.valve(54,-7);p.line((63,-12),(78,-12));p.line((63,-2),(78,-2))
    p=new('Filter stick / fritted dip tube','Filtration')
    p.line((-6,-70),(-6,40),(-14,40),(-14,57),(14,57),(14,40),(6,40),(6,-70));p.frit(-14,14,52)
    p=new('Hirsch / Büchner funnel','Filtration')
    p.line((-33,-45),(-33,-8),(-7,20),(-7,65));p.line((33,-45),(33,-8),(7,20),(7,65));p.frit(-33,33,-8)
    p=new('Pressure-equalizing addition funnel','Addition')
    p.neck(top=-92,bottom=-65,width=16);p.line((-8,-65),(-23,-52),(-23,12),(-7,29),(-7,40));p.line((8,-65),(23,-52),(23,12),(7,29),(7,40))
    p.valve(0,45);p.line((-6,50),(-6,90));p.line((6,50),(6,90))
    p.line((23,-45),(42,-45),(42,73),(6,73));p.line((23,-37),(34,-37),(34,65),(6,65))
    p=new('Dropping funnel','Addition')
    p.neck(top=-80,bottom=-58,width=16);p.arc(0,-22,25,38,-72,252);p.line((-8,14),(-8,35));p.line((8,14),(8,35));p.valve(0,40)
    p.line((-6,45),(-6,80));p.line((6,45),(6,80))
    p=new('Liebig condenser','Vacuum / reflux')
    p.line((-6,-90),(-6,90));p.line((6,-90),(6,90));p.line((-6,-65),(-18,-57),(-18,57),(-6,65));p.line((6,-65),(18,-57),(18,57),(6,65))
    for y in [-42,42]:p.line((18,y-4),(42,y-4));p.line((18,y+4),(42,y+4))
    p=new('Cold-finger condenser','Vacuum / reflux')
    p.line((-25,70),(-25,-55),(25,-55),(25,70));p.line((-12,-80),(-12,43));p.arc(0,43,12,12,0,180,20);p.line((12,43),(12,-80))
    p.line((-3,-80),(-3,40));p.line((3,-80),(3,40));p.line((25,30),(48,30));p.line((25,40),(48,40))
    p=new('Vacuum cold trap','Vacuum / reflux')
    p.line((-25,-55),(-25,45));p.arc(0,45,25,20,0,180,24);p.line((25,45),(25,-55),(-25,-55))
    p.line((-12,-55),(-12,-83),(-48,-83));p.line((-4,-55),(-4,-91),(-48,-91));p.line((8,-55),(8,33));p.line((16,33),(16,-83),(48,-83));p.line((8,-55),(8,-91),(48,-91))
    p=new('Oil / gas bubbler','Vacuum / reflux')
    p.line((-22,-52),(-22,45));p.arc(0,45,22,15,0,180,24);p.line((22,45),(22,-52),(-22,-52))
    p.line((-7,-52),(-7,32));p.line((1,-52),(1,32));p.line((-7,-52),(-7,-80),(-37,-80));p.line((1,-52),(1,-88),(-37,-88))
    p.line((9,-52),(9,-76),(36,-76));p.line((17,-52),(17,-68),(36,-68));p.line((-20,20),(20,20))
    p=new('Dual vacuum / inert-gas manifold','Manifolds')
    for y in [-38,-10]:p.line((-110,y-4),(110,y-4));p.line((-110,y+4),(110,y+4))
    for x in [-72,-24,24,72]:
        p.line((x-4,-34),(x-4,-14));p.line((x+4,-34),(x+4,-14));p.valve(x,8)
        p.line((x-4,-6),(x-4,3));p.line((x+4,-6),(x+4,3));p.line((x-4,13),(x-4,47));p.line((x+4,13),(x+4,47));p.line((x-7,40),(x+7,40))
    p=new('Vacuum-transfer receiver','Vacuum / reflux')
    bulb(p);p.line((9,-49),(34,-49),(34,-69));p.line((9,-39),(44,-39),(44,-69));p.line((32,-69),(46,-69))
    # Pilot-scale schematic symbols; dimensions are drawing units, not specifications.
    def vessel(p, width=48, top=-45, bottom=65):
        p.line((-width,top),(-width,bottom));p.arc(0,bottom,width,18,0,180,32)
        p.line((width,bottom),(width,top));p.arc(0,top,width,13,180,360,32)
        p.line((-width-5,top), (width+5,top));return p
    def agitator(p, bottom=40):
        p.line((-17,-115),(17,-115),(17,-84),(-17,-84),closed=True)
        p.line((-4,-84),(-4,bottom),(4,bottom),(4,-84))
        p.line((-30,bottom-8),(30,bottom+8));p.line((-30,bottom+8),(30,bottom-8))
    def jacket(p):
        p.line((-60,-34),(-60,64));p.arc(0,64,60,29,0,180,32);p.line((60,64),(60,-34))
        for sign,y in [(-1,40),(1,-15)]:
            p.line((sign*60,y-5),(sign*84,y-5));p.line((sign*60,y+5),(sign*84,y+5))
    p=vessel(new('Jacketed stirred reactor','Pilot-scale reactors'));jacket(p);agitator(p)
    p.line((-32,-55),(-45,-80),(-32,-86),(-21,-58));p.line((25,-56),(25,-82),(39,-82),(39,-48))
    p.line((-6,83),(-6,105));p.line((6,83),(6,105));p.valve(0,110)
    for x in [-43,43]:p.line((x,85),(x,120),(x+14,120))
    p=vessel(new('Jacketed glass filter reactor','Pilot-scale reactors'));jacket(p);agitator(p,35);p.frit(-48,48,55)
    p.line((-6,83),(-6,115));p.line((6,83),(6,115));p.valve(0,120)
    p.line((24,-58),(24,-82),(38,-82),(38,-50))
    p=vessel(new('Pilot reactor with overhead condenser','Pilot-scale reactors'));jacket(p);agitator(p)
    p.line((28,-56),(28,-140),(38,-140),(38,-51));p.line((22,-75),(22,-125),(44,-125),(44,-75),closed=True)
    p.line((44,-116),(64,-116));p.line((44,-108),(64,-108));p.line((44,-90),(64,-90));p.line((44,-82),(64,-82))
    p=vessel(new('Pressure Nutsche filter','Pilot-scale filtration'),width=60,top=-36,bottom=48);p.frit(-60,60,38)
    p.line((-8,-48),(-8,-78),(8,-78),(8,-48));p.line((60,-16),(85,-16));p.line((60,-6),(85,-6))
    p.line((-7,66),(-7,95));p.line((7,66),(7,95));p.valve(0,100)
    for x in [-50,50]:p.line((x,65),(x,110),(x+15,110))
    p=vessel(new('Agitated Nutsche filter dryer','Pilot-scale filtration'),width=60,top=-36,bottom=48)
    agitator(p,25);p.frit(-60,60,38)
    p.line((-72,-25),(-72,49));p.arc(0,49,72,28,0,180,32);p.line((72,49),(72,-25))
    for y in [-15,35]:p.line((72,y-4),(95,y-4));p.line((72,y+4),(95,y+4))
    p.line((-7,66),(-7,103));p.line((7,66),(7,103));p.line((-60,7),(-86,7),(-86,25),(-60,25))
    p=vessel(new('Large glass fritted filter funnel','Pilot-scale filtration'),width=48,top=-60,bottom=25);p.frit(-48,48,17)
    p.line((-8,43),(-8,92));p.line((8,43),(8,92));p.valve(0,97)
    for x in [-62,62]:p.line((x,-50),(x,95),(x+12,95));p.line((x,-20),(x*.75,-20))
    p=vessel(new('Cartridge / bag pressure filter','Pilot-scale filtration'),width=35,top=-56,bottom=58)
    p.line((-40,-56),(40,-56));p.line((-40,-49),(40,-49))
    for x in [-17,0,17]:p.line((x-5,-35),(x-5,42),(x+5,42),(x+5,-35),closed=True)
    for sign,y in [(-1,-25),(1,30)]:p.line((sign*35,y-5),(sign*65,y-5));p.line((sign*35,y+5),(sign*65,y+5))
    p=vessel(new('Jacketed receiver / hold vessel','Pilot-scale reactors'));jacket(p)
    for x in [-23,23]:p.line((x-6,-57),(x-6,-84),(x+6,-84),(x+6,-57))
    p.line((-6,83),(-6,110));p.line((6,83),(6,110));p.valve(0,115)
    return result


def glassware_catalog():
    return [{'name':p.name,'category':p.category,'svg':p.svg(),'template':p.fragment()} for p in parts()]


if __name__ == '__main__':
    path=Path(__file__).resolve().parent/'assets/glassware.json'
    path.write_text(json.dumps(glassware_catalog(),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Wrote {len(parts())} glassware templates to {path}')
