"""CDXML and binary CDX import using the publicly documented tagged format.
Supported drawing objects are mapped to editable ErezDraw objects. Unsupported
objects/properties are reported; this is not a lossless ChemDraw round trip.
"""
from __future__ import annotations
import math,struct,xml.etree.ElementTree as ET
from xml.parsers import expat
from pathlib import Path
from rdkit import Chem
SCALE=4/3
DISPLAY={0:'Solid',1:'Dash',2:'Hash',3:'WedgedHashBegin',4:'WedgedHashEnd',5:'Bold',6:'WedgeBegin',7:'WedgeEnd',8:'Wavy',9:'HollowWedgeBegin',10:'HollowWedgeEnd'}
STYLES={'Solid':'normal','Dash':'dashed','Hash':'hashed','Bold':'boldBond','WedgeBegin':'wedge','WedgeEnd':'wedge','WedgedHashBegin':'hash','WedgedHashEnd':'hash','HollowWedgeBegin':'hollowWedge','HollowWedgeEnd':'hollowWedge','Wavy':'wavy'}
class ImportErrorDetail(ValueError):pass

def integer(value,what):
    """CDXML attributes are file-controlled text; report a bad one as an import error."""
    try:return int(value)
    except (TypeError,ValueError) as e:raise ImportErrorDetail('Invalid ChemDraw '+what+'.') from e

def decimal(value,what):
    try:result=float(value)
    except (TypeError,ValueError) as e:raise ImportErrorDetail('Invalid ChemDraw '+what+'.') from e
    if not math.isfinite(result):raise ImportErrorDetail('Invalid ChemDraw '+what+'.')
    return result

def numbers(value,count=None):
    try:result=[float(v) for v in value.replace(',',' ').split()]
    except (ValueError,AttributeError) as e:raise ImportErrorDetail('Invalid ChemDraw coordinate.') from e
    if count is not None and len(result)!=count or not all(math.isfinite(v) and abs(v)<750000 for v in result):raise ImportErrorDetail('Invalid ChemDraw coordinate count or range.')
    return result

def _check_xml(data):
    """Stream-check untrusted XML before building a tree: no entity declarations
    (in any encoding), bounded nesting depth and element count."""
    parser=expat.ParserCreate();depth=0;count=0
    def start(name,attrs):
        nonlocal depth,count
        depth+=1;count+=1
        if depth>100 or count>30000:raise ImportErrorDetail('ChemDraw document exceeds import limits.')
    def end(name):
        nonlocal depth
        depth-=1
    def entity(*args):raise ImportErrorDetail('XML entities are not allowed in drawing imports.')
    parser.StartElementHandler=start;parser.EndElementHandler=end;parser.EntityDeclHandler=entity
    try:parser.Parse(data,True)
    except expat.ExpatError as e:raise ImportErrorDetail('Invalid ChemDraw XML: '+str(e)) from e

def _cdx_tree(data):
    if len(data)<30 or data[:8]!=b'VjCD0100':raise ImportErrorDetail('Not a ChemDraw CDX file.')
    pos=28;root=ET.Element('CDXML');stack=[root];warnings=set();objects=0
    tags={0x8000:'document',0x8001:'page',0x8002:'group',0x8003:'fragment',0x8004:'n',0x8005:'b',0x8006:'t',0x8007:'graphic'}
    def take(size):
        nonlocal pos
        if pos+size>len(data):raise ImportErrorDetail('Truncated ChemDraw CDX file.')
        part=data[pos:pos+size];pos+=size;return part
    def uint(buf,signed=False):return int.from_bytes(buf,'little',signed=signed)
    def coord(buf):
        if len(buf)!=4:raise ImportErrorDetail('Invalid CDX coordinate property.')
        return struct.unpack('<i',buf)[0]/65536
    def text(buf):
        if len(buf)<2:raise ImportErrorDetail('Invalid CDX text.')
        count=uint(buf[:2]);offset=2+count*10
        if offset>len(buf):raise ImportErrorDetail('Invalid CDX text style runs.')
        return buf[offset:].decode('cp1252',errors='replace').replace('\x00',''),buf[2:offset]
    while pos<len(data):
        tag=uint(take(2))
        if tag==0:
            if len(stack)>1:stack.pop()
            elif any(data[pos:]):raise ImportErrorDetail('Unexpected data after CDX document end.')
            else:break
            continue
        if tag&0x8000:
            objects+=1
            if objects>30000 or len(stack)>100:raise ImportErrorDetail('ChemDraw file exceeds import limits.')
            oid=uint(take(4));node=ET.SubElement(stack[-1],tags.get(tag,'unsupported'),{'id':str(oid)})
            if node.tag=='unsupported':warnings.add(f'Unsupported CDX object type 0x{tag:04x}.')
            stack.append(node);continue
        length=uint(take(2));length=uint(take(4)) if length==65535 else length;buf=take(length);node=stack[-1]
        if tag==0x0200:
            if length!=8:raise ImportErrorDetail('Invalid CDX position.')
            node.set('p',f'{coord(buf[4:])} {coord(buf[:4])}')
        elif tag==0x0204:
            if length!=16:raise ImportErrorDetail('Invalid CDX bounding box.')
            v=[coord(buf[i:i+4]) for i in range(0,16,4)];node.set('BoundingBox',f'{v[1]} {v[0]} {v[3]} {v[2]}')
        elif tag in {0x0400,0x0402,0x0421,0x0422,0x0600,0x0601,0x0603,0x0604,0x0605,0x0a00,0x0a02}:
            value=uint(buf,tag==0x0421)
            if tag==0x0601:node.set('Display',DISPLAY.get(value,'Unsupported'))
            elif tag==0x0600:node.set('Order',{1:'1',2:'2',4:'3',0x80:'1.5',0x1000:'dative'}.get(value,'Unsupported'))
            elif tag==0x0603:node.set('DoublePosition',{0:'Center',1:'Right',2:'Left',256:'Center',257:'Right',258:'Left'}.get(value,'Unknown'))
            else:node.set({0x0400:'NodeType',0x0402:'Element',0x0421:'Charge',0x0422:'Radical',0x0604:'B',0x0605:'E',0x0a00:'GraphicType',0x0a02:'ArrowType'}[tag],str(value))
        elif tag==0x0700:
            value,runs=text(buf)
            if not runs:ET.SubElement(node,'s').text=value
            else:
                entries=[struct.unpack('<HHHHH',runs[i:i+10]) for i in range(0,len(runs),10)]
                for i,(start,font,face,size,color) in enumerate(entries):
                    end=entries[i+1][0] if i+1<len(entries) else len(value)
                    ET.SubElement(node,'s',{'font':str(font),'face':str(face),'size':str(size/20),'color':str(color)}).text=value[start:end]
        elif tag==0x0100:
            if length<4:raise ImportErrorDetail('Invalid CDX font table.')
            count=uint(buf[2:4]);offset=4;table=ET.SubElement(root,'fonttable')
            for _ in range(count):
                if offset+6>length:raise ImportErrorDetail('Truncated CDX font table.')
                fid,charset,n=struct.unpack('<HHH',buf[offset:offset+6]);offset+=6
                if offset+n>length:raise ImportErrorDetail('Truncated CDX font name.')
                ET.SubElement(table,'font',{'id':str(fid),'name':buf[offset:offset+n].decode('cp1252',errors='replace')});offset+=n
        elif tag==0x0300:
            if length<2:raise ImportErrorDetail('Invalid CDX color table.')
            count=uint(buf[:2]);table=ET.SubElement(root,'colortable')
            if 2+count*6>length:raise ImportErrorDetail('Truncated CDX color table.')
            for i in range(count):
                r,g,b=struct.unpack('<HHH',buf[2+i*6:8+i*6]);ET.SubElement(table,'color',{'r':str(r/65535),'g':str(g/65535),'b':str(b/65535)})
        elif tag in {0x0805,0x0806,0x0807,0x0808,0x0809}:
            root.set({0x0805:'BondLength',0x0806:'BoldWidth',0x0807:'LineWidth',0x0808:'MarginWidth',0x0809:'HashSpacing'}[tag],str(coord(buf)))
        elif tag==0x0804:root.set('BondSpacing',str(uint(buf)/10))
        elif tag in (0x080a,0x080b) and length==8:
            font,face,size,color=struct.unpack('<HHHH',buf);prefix='Label' if tag==0x080a else 'Caption'
            for key,val in [('Font',font),('Face',face),('Size',size/20),('Color',color)]:root.set(prefix+key,str(val))
        elif tag==0x0008:node.set('Name',text(buf)[0])
    if len(stack)>1:raise ImportErrorDetail('Unclosed CDX object.')
    for child in list(root):
        if child.tag=='document':
            root.attrib.update(child.attrib)
            for sub in list(child):root.append(sub)
            root.remove(child)
    return root,warnings

def import_chemdraw(data:bytes,name='Imported ChemDraw'):
    if len(data)>5_000_000:raise ImportErrorDetail('Maximum ChemDraw file size is 5 MB.')
    warnings=set()
    if data.startswith(b'VjCD0100'):root,warnings=_cdx_tree(data)
    else:
        if b'<!ENTITY' in data.upper():raise ImportErrorDetail('XML entities are not allowed in drawing imports.')
        _check_xml(data)
        try:root=ET.fromstring(data)
        except ET.ParseError as e:raise ImportErrorDetail('Invalid ChemDraw XML: '+str(e)) from e
        if root.tag!='CDXML':raise ImportErrorDetail('Not a ChemDraw CDXML document.')
    nodes=list(root.iter())
    if len(nodes)>30000:raise ImportErrorDetail('ChemDraw document exceeds import limits.')
    # Elements inside an atom node (labels, nested fragments), found in one pre-order pass.
    inside_atom=set()
    for parent in nodes:
        if parent.tag=='n' or parent in inside_atom:inside_atom.update(parent)
    fonts={f.get('id'):f.get('name','Arial') for f in root.iter('font')}
    colors=['#ffffff','#000000']
    for c in root.iter('color'):
        values=[round(max(0,min(1,decimal(c.get(k,'0'),'color table')))*255) for k in ('r','g','b')];colors.append('#%02x%02x%02x'%tuple(values))
    def style(text_node,label=False):
        runs=list(text_node.iter('s'));first=runs[0] if runs else text_node;prefix='Label' if label else 'Caption'
        face=integer(first.get('face',root.get(prefix+'Face','0')),'text style');size=decimal(first.get('size',root.get(prefix+'Size','10' if label else '12')),'text size')*SCALE
        color=integer(first.get('color',root.get(prefix+'Color','1')),'text color')
        if len(runs)>1:warnings.add('Rich text runs are flattened to the first run style.')
        return {'font':fonts.get(first.get('font',root.get(prefix+'Font')),'Arial'),'size':max(6,min(144,size)),'color':colors[color] if 0<=color<len(colors) else '#000000','bold':bool(face&1),'italic':bool(face&2),'underline':bool(face&4)}
    drawing={'format':'chemsketch-classic','version':1,'name':name,'atoms':[],'bonds':[],'annotations':[]}
    ids={};counter=0
    def unique(prefix):
        nonlocal counter
        counter+=1;return prefix+str(counter)
    def point(node):
        value=node.get('p')
        if value:return [v*SCALE for v in numbers(value,2)]
        box=node.get('BoundingBox')
        if box:return [v*SCALE for v in numbers(box,4)[:2]]
        raise ImportErrorDetail('A drawing object has no 2D position.')
    for n in root.iter('n'):
        if n in inside_atom:
            warnings.add('Nested label fragments are retained as labels, not expanded chemical fragments.');continue
        x,y=point(n);nid=n.get('id')
        if not nid or nid in ids:raise ImportErrorDetail('Missing or duplicate ChemDraw atom ID.')
        aid=unique('a');ids[nid]=aid
        label_node=n.find('t');label=''.join(label_node.itertext()).strip() if label_node is not None else ''
        atomic=integer(n.get('Element','6'),'element number')
        if not label:
            if 1<=atomic<=118:label=Chem.GetPeriodicTable().GetElementSymbol(atomic)
            else:label='*';warnings.add('Unknown element was imported as a placeholder.')
        atom={'id':aid,'x':x,'y':y,'label':label[:40],'charge':integer(n.get('Charge','0'),'atom charge')}
        if abs(atom['charge'])>20:raise ImportErrorDetail('Atom charge exceeds editor limits.')
        if label_node is not None:atom['textStyle']=style(label_node,True)
        else:atom['textStyle']=style(ET.Element('s'),True)
        radical=n.get('Radical','0');value={'Doublet':1,'Singlet':2,'Triplet':2,'2':1,'1':2,'3':2}.get(radical,0)
        if value:atom['radical']=value
        if n.get('Isotope'):warnings.add('Isotope properties are not yet imported.')
        drawing['atoms'].append(atom)
    pairs=set()
    for b in root.iter('b'):
        if b.get('B') not in ids or b.get('E') not in ids:
            warnings.add('A bond to an unsupported/nested node was skipped.');continue
        if b.get('B')==b.get('E'):
            warnings.add('A bond with identical endpoints was skipped.');continue
        begin,end=ids[b.get('B')],ids[b.get('E')];order={'1':1,'2':2,'3':3,'1.5':4,'dative':1}.get(b.get('Order','1'))
        if order is None:raise ImportErrorDetail('Unsupported ChemDraw bond order '+str(b.get('Order'))+'.')
        display=b.get('Display','Solid')
        if display not in STYLES:raise ImportErrorDetail('Unsupported ChemDraw bond display '+display+'.')
        bond={'id':unique('b'),'a':begin,'b':end,'order':order,'style':'coord' if b.get('Order')=='dative' else STYLES[display]}
        if display.endswith('End'):bond['a'],bond['b']=bond['b'],bond['a']
        if order==2 and display=='Wavy':bond['style']='crossBond'
        if b.get('DoublePosition') in ('Left','Right','Center'):bond['doublePosition']=b.get('DoublePosition').lower()
        pair=tuple(sorted([begin,end]))
        if pair in pairs:raise ImportErrorDetail('Duplicate ChemDraw bond endpoints.')
        pairs.add(pair);drawing['bonds'].append(bond)
    for t in root.iter('t'):
        if t in inside_atom:continue
        text=''.join(t.itertext()).strip()
        if not text:continue
        x,y=point(t);drawing['annotations'].append({'id':unique('t'),'type':'text','x':x,'y':y,'text':text[:500],'textStyle':style(t)})
    for g in list(root.iter('graphic'))+list(root.iter('arrow')):
        box=g.get('BoundingBox');graphic=g.get('GraphicType','Line');variant=None
        if g.tag=='arrow' and g.get('Head3D') and g.get('Tail3D'):
            head=numbers(g.get('Head3D'));tail=numbers(g.get('Tail3D'));x,y=tail[:2];xx,yy=head[:2]
        elif box:
            # ChemDraw line bounds are head-x/head-y/tail-x/tail-y, not min/max.
            xx,yy,x,y=numbers(box,4)
        else:warnings.add('A graphic without usable endpoints was skipped.');continue
        if graphic in ('Rectangle','3'):variant='elements'
        elif graphic in ('Oval','4'):variant='ellipse'
        elif graphic in ('Bracket','6'):variant='bracket'
        elif graphic not in ('Line','1'):
            warnings.add('Unsupported graphic type '+graphic+' was skipped.');continue
        arrow=g.get('ArrowType','2')
        if not variant and arrow in ('Equilibrium','8'):variant='equilibrium'
        if not variant and arrow in ('HalfHead','1'):variant='fishhook'
        item={'id':unique('r'),'type':'arrow','x':x*SCALE,'y':y*SCALE,'x2':xx*SCALE,'y2':yy*SCALE}
        if variant:item['variant']=variant
        drawing['annotations'].append(item)
    for group in root.iter('group'):
        atom_keys=[ids[n.get('id')] for n in group.iter('n') if n.get('id') in ids]
        if atom_keys:drawing.setdefault('groups',[]).append({'id':unique('g'),'atoms':atom_keys,'annotations':[],'integral':False})
    for tag in ['curve','embeddedobject','table','tlcplate','spectrum','alternativegroup']:
        if any(True for _ in root.iter(tag)):warnings.add('Unsupported '+tag+' objects are not imported.')
    if len(list(root.iter('page')))>1:warnings.add('Multiple pages are combined in one drawing; page layout is not preserved.')
    if not drawing['atoms'] and not drawing['annotations']:raise ImportErrorDetail('No supported drawing objects were found.')
    if len(drawing['atoms'])>5000 or len(drawing['bonds'])>10000 or len(drawing['annotations'])>1000 or len(drawing.get('groups',[]))>1000:raise ImportErrorDetail('Drawing exceeds editor limits.')
    settings={}
    for source,target,factor in [('LineWidth','lineWidth',SCALE),('BoldWidth','boldWidth',SCALE),('BondLength','bondLength',SCALE),('MarginWidth','marginWidth',SCALE),('HashSpacing','hashSpacing',SCALE),('BondSpacing','bondSpacing',.01)]:
        if root.get(source):
            # A cosmetic setting never fails the import; an unusable one is dropped.
            try:value=decimal(root.get(source),'document setting')*factor
            except ImportErrorDetail:value=None
            # Same range the editor accepts for drawing settings; NaN/inf would also be invalid JSON.
            if value is not None and 0<value<=1000:settings[target]=value
            else:warnings.add('Document setting '+source+' is out of range and was ignored.')
    if settings:drawing['drawingSettings']=settings
    return {'drawing':drawing,'warnings':sorted(warnings)}

def read_chemdraw(path):return import_chemdraw(Path(path).read_bytes(),Path(path).stem)
