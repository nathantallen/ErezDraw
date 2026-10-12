"""Shift-only NMR envelope and hover assignments; no invented J couplings."""
import math
from PySide6.QtCore import Qt,Signal,QPointF
from PySide6.QtGui import QPainter,QColor,QPen,QPainterPath
from PySide6.QtWidgets import QWidget
from nmr_spectrum import multiplet_lines

class SpectrumWidget(QWidget):
    hovered=Signal(object)
    def __init__(self,rows,nucleus,parent=None,molecule=None):
        super().__init__(parent);self.rows=rows;self.nucleus=nucleus;self.molecule=molecule;self.quantum=None;self.quantum_cache={};self.active=[];self.mhz=400.0;self.linewidth=1.0;self.coupled=True;self.setMouseTracking(True);self.setMinimumSize(320,180)
        values=[r['delta'] for r in rows if r['delta'] is not None]
        low,high=((-1,12) if nucleus=='1H' else (-10,220));self.low=min([low]+[x-1 for x in values]);self.high=max([high]+[x+1 for x in values]);self.setToolTip('Estimated first-order spectrum; peak areas reflect equivalent nuclei. Wheel to zoom; double-click to reset. Solvent and strong-coupling effects are not modeled.')
    def xpos(self,delta):return 48+(self.high-delta)/(self.high-self.low)*max(1,self.width()-70)
    def lines(self,row):
        if self.quantum is not None:return self.quantum[next(i for i,r in enumerate(self.rows) if r is row)]
        return multiplet_lines(row,self.mhz,self.nucleus,self.coupled)
    def peaks_near(self,x):return [i for i,r in enumerate(self.rows) if any(abs(self.xpos(delta)-x)<=7 for delta,area in self.lines(r))]
    def wheelEvent(self,event):
        fraction=max(0,min(1,(event.position().x()-48)/max(1,self.width()-70)));focus=self.high-fraction*(self.high-self.low);factor=.75 if event.angleDelta().y()>0 else 1.333333;span=(self.high-self.low)*factor
        if .03<span<400:self.high=focus+fraction*span;self.low=self.high-span;self.update()
        event.accept()
    def mouseDoubleClickEvent(self,event):
        values=[r['delta'] for r in self.rows if r['delta'] is not None];low,high=((-1,12) if self.nucleus=='1H' else (-10,220));self.low=min([low]+[x-1 for x in values]);self.high=max([high]+[x+1 for x in values]);self.update()
    def configure(self,mhz,linewidth,coupled=True):
        self.mhz=mhz;self.linewidth=linewidth;self.coupled=coupled;self.quantum=None
        if self.molecule is not None and self.nucleus=='1H' and coupled:
            from nmr_models import quantum_lines
            if mhz not in self.quantum_cache:self.quantum_cache[mhz]=quantum_lines(self.molecule,self.rows,mhz)
            self.quantum=self.quantum_cache[mhz]
        self.update()
    def mouseMoveEvent(self,event):
        active=self.peaks_near(event.position().x())
        if active!=self.active:self.active=active;self.hovered.emit(active);self.update()
        if active:self.setToolTip('\n'.join(f"{self.rows[i]['delta']:.2f} ppm — {self.rows[i]['count']} nuclei" for i in active))
    def leaveEvent(self,event):self.active=[];self.hovered.emit([]);self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.fillRect(self.rect(),Qt.GlobalColor.white);base=self.height()-38;left=48;right=self.width()-22;top=25
        p.setPen(QColor('#333'));p.drawLine(left,base,right,base);p.drawText(10,18,self.nucleus+f' — {self.mhz:g} MHz');p.drawText(right-45,self.height()-5,'δ / ppm')
        ticks=10
        for j in range(ticks+1):
            value=self.high-(self.high-self.low)*j/ticks;x=self.xpos(value);p.drawLine(QPointF(x,base),QPointF(x,base+5));p.drawText(int(x)-15,base+22,f'{value:.1f}')
        peaks=[(i,delta,area) for i,r in enumerate(self.rows) for delta,area in self.lines(r)];width=self.linewidth/(2*self.mhz);pixel=(self.high-self.low)/max(1,right-left);samples=[]
        # Integrate over each pixel bin, avoiding missed narrow peaks and aliasing.
        for x in range(left,right+1):
            delta=self.high-(x-left)/(right-left)*(self.high-self.low)
            value=sum(area*width*(math.atan((delta+pixel/2-shift)/width)-math.atan((delta-pixel/2-shift)/width))/pixel for i,shift,area in peaks);samples.append(value)
        maximum=max(samples or [1]) or 1;path=QPainterPath()
        for j,value in enumerate(samples):
            point=QPointF(left+j,base-value/maximum*(base-top))
            if j==0:path.moveTo(point)
            else:path.lineTo(point)
        p.setPen(QPen(QColor('#204a76'),1.3));p.drawPath(path)
        # Hover markers follow the integrated envelope instead of drawing every
        # transition as a separate stick with an unrelated height.
        for i,delta,area in peaks:
            if i not in self.active:continue
            x=self.xpos(delta);j=min(len(samples)-1,max(0,round(x-left)));y=base-samples[j]/maximum*(base-top);p.setPen(QPen(QColor('#d32f2f'),1));p.drawLine(QPointF(x,base),QPointF(x,y))
        if self.active:p.drawText(left+8,top+14,', '.join(f"{self.rows[i]['delta']:.2f} ppm" for i in self.active))
