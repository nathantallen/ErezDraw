"""Clipboard SVG plus native bitmap/PNG for Microsoft Word and other applications."""
import math
from PySide6.QtCore import QByteArray,QBuffer,QIODevice,QMimeData
from PySide6.QtGui import QImage,QPainter
from PySide6.QtSvg import QSvgRenderer

def graphics_mime(svg,fragment=None):
    renderer=QSvgRenderer(QByteArray(svg.encode('utf-8')))
    if not renderer.isValid():raise ValueError('The drawing could not be rendered for the clipboard.')
    size=renderer.defaultSize();w=max(1,size.width());h=max(1,size.height());scale=min(3,8192/w,8192/h,math.sqrt(32_000_000/(w*h)))
    image=QImage(max(1,math.ceil(w*scale)),max(1,math.ceil(h*scale)),QImage.Format.Format_ARGB32);image.fill(0xffffffff);image.setDotsPerMeterX(round(96*scale/0.0254));image.setDotsPerMeterY(round(96*scale/0.0254))
    painter=QPainter(image);renderer.render(painter);painter.end()
    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');buffer.close()
    mime=QMimeData();mime.setData('image/svg+xml',QByteArray(svg.encode('utf-8')));mime.setImageData(image);mime.setData('image/png',data)
    if fragment is not None:
        import json
        mime.setData('application/x-chemsketch-fragment',QByteArray(json.dumps(fragment).encode('utf-8')))
    # Do not offer JSON as text/plain: Word can choose it instead of the image.
    return mime


def widget_graphics_mime(widget):
    from PySide6.QtCore import QPoint,QRect
    from PySide6.QtSvg import QSvgGenerator
    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly);generator=QSvgGenerator();generator.setOutputDevice(buffer);generator.setSize(widget.size());generator.setViewBox(QRect(0,0,widget.width(),widget.height()));painter=QPainter(generator)
    try:widget.render(painter,QPoint())
    finally:painter.end();buffer.close()
    return graphics_mime(bytes(data).decode('utf-8'))
