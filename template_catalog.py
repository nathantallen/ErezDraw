"""Shared categorized template picker; choosing never edits the document."""
import math


def ring_svg(n, benzene=False):
    pts=[(50+30*math.cos(-math.pi/2+i*2*math.pi/n),40+30*math.sin(-math.pi/2+i*2*math.pi/n)) for i in range(n)]
    lines=['<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+'"/>']
    if benzene:
        for i in (0,2,4):
            a,b=pts[i],pts[(i+1)%n];a=(50+(a[0]-50)*.75,40+(a[1]-40)*.75);b=(50+(b[0]-50)*.75,40+(b[1]-40)*.75)
            lines.append(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}"/>')
    return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="80" viewBox="0 0 100 80"><g fill="none" stroke="#151b20" stroke-width="1.5">'+''.join(lines)+'</g></svg>'


def template_categories(ligands, glassware):
    rings=[{'name':f'{n}-Membered Ring','kind':'tool','tool':f'ring{n}','svg':ring_svg(n)} for n in range(3,9)]
    rings.append({'name':'Benzene','kind':'tool','tool':'benzene','svg':ring_svg(6,True)})
    categories=[{'name':'Rings','items':rings}]
    for prefix,items,kind in [('Ligands',ligands,'ligand'),('Labware',glassware,'glassware')]:
        for category in dict.fromkeys(x['category'] for x in items):
            categories.append({'name':prefix+' — '+category,'items':[dict(name=x['name'],svg=x['svg'],kind=kind,template=x['template']) for x in items if x['category']==category]})
    return categories
