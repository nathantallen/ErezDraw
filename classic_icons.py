"""Original vector artwork for classic chemical-editor toolbars.
Every pictogram is SVG geometry; no emoji, font fallback or OS stock icons.
"""
import math
from PySide6.QtCore import QByteArray,Qt
from PySide6.QtGui import QIcon,QPixmap,QPainter
from PySide6.QtSvg import QSvgRenderer

PATHS={
 'new':'<path d="M5 3H17L23 9V27H5Z" fill="white"/><path d="M17 3V9H23"/>',
 'open':'<path d="M3 9H12L15 12H28L24 26H3Z" fill="#eee3aa"/><path d="M3 9V6H12L15 9H27V12 M3 26L7 15H28"/>',
 'save':'<path d="M4 3H24L28 7V28H4Z" fill="#b9c3cf"/><path d="M8 3V12H22V3 M9 28V17H23V28" fill="white"/><path d="M18 5V10" stroke-width="3"/>',
 'print':'<path d="M9 3H23V11H9Z M8 21H24V29H8Z" fill="white"/><path d="M4 10H28V23H24V18H8V23H4Z" fill="#d6d6d6"/><path d="M23 13H25 M11 23H21 M11 26H21"/>',
 'undo':'<path d="M7 11C19 3 29 13 23 22C21 25 16 26 12 24 M7 5V12H14"/>',
 'redo':'<path d="M25 11C13 3 3 13 9 22C11 25 16 26 20 24 M25 5V12H18"/>',
 'cut':'<circle cx="8" cy="24" r="4"/><circle cx="20" cy="24" r="4"/><path d="M10 21L24 3 M18 21L7 3"/>',
 'copy':'<path d="M4 3H18V22H4Z M12 10H27V29H12Z" fill="white"/><path d="M15 15H24 M15 19H24 M15 23H24"/>',
 'paste':'<path d="M7 6H24V29H7Z" fill="#ddd1b8"/><path d="M12 3H20V9H12Z" fill="#ddd"/><path d="M12 13H28V29H12Z" fill="white"/><path d="M15 18H25 M15 22H25 M15 26H23"/>',
 'validate':'<path d="M3 16L10 24L27 5" stroke-width="3"/>',
 'cleanup':'<path d="M3 23L10 9L20 15L28 5 M5 27L11 16L21 22L28 10"/><path d="M22 3L28 3L28 9"/>',
 'fit':'<rect x="6" y="6" width="20" height="20"/><path d="M3 11V3H11 M21 3H29V11 M29 21V29H21 M11 29H3V21"/>',
 'rotate':'<path d="M6 20A11 11 0 1 0 8 7 M3 7H9V1"/><path d="M12 12H20V20H12Z" stroke-dasharray="2 2"/>',
 'flip':'<path d="M15 3V29" stroke-dasharray="2 2"/><path d="M3 7L11 16L3 25Z M27 7L19 16L27 25Z"/><path d="M3 3H11 M19 3H27"/>',
 'flipVertical':'<path d="M3 16H29" stroke-dasharray="2 2"/><path d="M7 3L16 11L25 3Z M7 29L16 21L25 29Z"/>',
 'scaleObjects':'<rect x="4" y="16" width="12" height="12"/><path d="M4 12V4H28V28H20" stroke-dasharray="2 2"/><path d="M17 15L28 4 M21 4H28V11"/>',
 'align_left':'<path d="M4 3V29"/><path d="M7 5H24V10H7Z M7 14H18V19H7Z M7 23H28V28H7Z" fill="#555"/>',
 'align_right':'<path d="M28 3V29"/><path d="M8 5H25V10H8Z M14 14H25V19H14Z M4 23H25V28H4Z" fill="#555"/>',
 'align_horizontal':'<path d="M16 2V30"/><path d="M6 5H26V10H6Z M11 14H21V19H11Z M3 23H29V28H3Z" fill="#555"/>',
 'align_top':'<path d="M2 4H30"/><path d="M4 7H9V24H4Z M13 7H18V18H13Z M23 7H28V28H23Z" fill="#555"/>',
 'align_bottom':'<path d="M2 28H30"/><path d="M4 8H9V25H4Z M13 14H18V25H13Z M23 4H28V25H23Z" fill="#555"/>',
 'align_vertical':'<path d="M2 16H30"/><path d="M4 6H9V26H4Z M13 11H18V21H13Z M23 3H28V29H23Z" fill="#555"/>',
 'distribute_x':'<path d="M3 4H8V28H3Z M14 8H19V24H14Z M25 4H30V28H25Z" fill="#555"/><path d="M9 2H13 M20 2H24 M10 0V4 M23 0V4"/>',
 'distribute_y':'<path d="M4 3H28V8H4Z M8 14H24V19H8Z M4 25H28V30H4Z" fill="#555"/><path d="M2 9V13 M2 20V24 M0 10H4 M0 23H4"/>',
 'centerPage':'<rect x="5" y="2" width="22" height="28"/><path d="M10 11H22V21H10Z M16 4V28 M7 16H25"/>',
 'lasso':'<path d="M8 7C-1 11 3 24 16 25C31 27 33 10 23 6C18 4 12 4 8 7Z M10 24L7 29"/>',
 'select':'<rect x="4" y="4" width="24" height="24" stroke-dasharray="1 2"/>',
 'erase':'<path d="M4 20L17 6L27 15L15 28H11Z" fill="#eee"/><path d="M9 15L20 24 M14 28H29"/>',
 'single':'<path d="M5 26L26 5"/>',
 'double':'<path d="M4 23L23 4 M9 28L28 9"/>',
 'triple':'<path d="M2 21L21 2 M6 25L25 6 M10 29L29 10"/>',
 'wedge':'<path d="M5 27L20 4L28 12Z" fill="#111"/>',
 'hash':'<path d="M5 26L6 27 M8 21L12 25 M11 16L17 22 M14 11L22 19 M17 6L27 16"/>',
 'coord':'<path d="M5 27L27 5 M18 5H27V14"/>',
 'text':'<path d="M8 26L16 5L24 26 M11 19H21 M6 26H12 M21 26H27"/>',
 'atom':'<path d="M8 26L16 5L24 26 M11 19H21 M6 26H12 M21 26H27"/>',
 'arrow':'<path d="M2 16H29 M21 10L29 16L21 22"/>',
 'chain':'<path d="M2 22L8 11L14 22L20 11L26 22L30 15"/>',
 'orbital':'<path d="M16 16C-3-5-3 36 16 16C35-5 35 36 16 16Z"/>',
 'symbol':'<circle cx="16" cy="16" r="9"/><path d="M10 16H22 M16 10V22"/>',
 'elements':'<rect x="3" y="4" width="13" height="13"/><ellipse cx="22" cy="22" rx="8" ry="6"/>',
 'bracket':'<path d="M10 3H5V29H10 M22 3H27V29H22"/>',
 'pen':'<path d="M5 27L10 15L24 3L29 8L15 22Z M10 15L15 22 M5 27L10 25"/>',
 'templates':'<rect x="3" y="3" width="26" height="26"/><path d="M3 12H29 M12 3V29 M21 3V29 M3 21H29"/>',
 'query':'<path d="M10 10C10 0 24 2 24 10C24 15 16 14 16 22 M16 27V29" stroke-width="2.5"/>',
 'fragment':'<path d="M3 12L10 5L18 12L25 5 M3 26L10 19L18 26L25 19 M17 2L12 29" stroke-dasharray="2 2"/>',
 'trackball':'<circle cx="16" cy="16" r="12"/><ellipse cx="16" cy="16" rx="5" ry="12"/><ellipse cx="16" cy="16" rx="12" ry="5"/>',
 'chair':'<path d="M2 7L8 23L19 18L30 25L24 9L13 14Z"/>',
 'tlc':'<rect x="5" y="2" width="22" height="28"/><path d="M6 6H26 M6 26H26" stroke-dasharray="2 2"/><circle cx="11" cy="16" r="2" fill="#111"/><circle cx="21" cy="11" r="2" fill="#111"/>',
 'table':'<rect x="3" y="4" width="26" height="24"/><path d="M3 12H29 M3 20H29 M12 4V28 M21 4V28"/>',
 'dashed':'<path d="M4 4L28 28" stroke-dasharray="4 3"/>',
 'hashed':'<path d="M3 5L7 1 M7 9L11 5 M11 13L15 9 M15 17L19 13 M19 21L23 17 M23 25L27 21 M27 29L31 25"/>',
 'boldBond':'<path d="M5 5L27 27" stroke-width="4"/>',
 'crossBond':'<path d="M3 5L27 29 M8 3L24 28 M6 10L26 20"/>',
 'hollowWedge':'<path d="M5 4L29 22L20 29Z"/>',
 'wavy':'<path d="M3 5C12 1 4 14 13 10C22 6 14 20 23 16C32 12 22 27 29 27"/>',
 'chair2':'<path d="M2 25L8 9L19 14L30 7L24 23L13 18Z"/>',
 'cyclopentadiene':'<polygon points="16,3 29,13 24,28 8,28 3,13"/><path d="M8 14L12 24 M24 14L20 24"/>',
 'group':'<rect x="3" y="3" width="26" height="26" stroke-dasharray="2 2"/><rect x="6" y="7" width="11" height="11"/><rect x="15" y="15" width="11" height="11"/>',
 'ungroup':'<rect x="2" y="3" width="14" height="14" stroke-dasharray="2 2"/><rect x="16" y="16" width="14" height="14" stroke-dasharray="2 2"/>',
 'front':'<rect x="3" y="3" width="17" height="17" fill="#eee"/><rect x="12" y="12" width="17" height="17" fill="#e6d985"/>',
 'back':'<rect x="12" y="12" width="17" height="17" fill="#e6d985"/><rect x="3" y="3" width="17" height="17" fill="#eee"/>',
 'zoomIn':'<circle cx="12" cy="12" r="8"/><path d="M18 18L29 29 M7 12H17 M12 7V17"/>',
 'zoomOut':'<circle cx="12" cy="12" r="8"/><path d="M18 18L29 29 M7 12H17"/>',
 'textLeft':'<path d="M4 5H28 M4 11H20 M4 17H28 M4 23H20 M4 29H28"/>',
 'textCenter':'<path d="M4 5H28 M8 11H24 M4 17H28 M8 23H24 M4 29H28"/>',
 'textRight':'<path d="M4 5H28 M12 11H28 M4 17H28 M12 23H28 M4 29H28"/>',
 'textJustify':'<path d="M4 5H28 M4 11H28 M4 17H28 M4 23H28 M4 29H28"/>',
 'subscript':'<path d="M5 4L16 22 M16 4L5 22 M21 20C21 15 28 15 28 20L21 29H29"/>',
 'superscript':'<path d="M5 10L16 28 M16 10L5 28 M21 5C21 0 28 0 28 5L21 14H29"/>',
 'chargeUp':'<circle cx="16" cy="16" r="8"/><path d="M10 16H22 M16 10V22"/>',
 'chargeDown':'<circle cx="16" cy="16" r="8"/><path d="M10 16H22"/>',
 'radical':'<circle cx="16" cy="16" r="3" fill="#111"/>',
 'lonePair':'<circle cx="10" cy="16" r="2" fill="#111"/><circle cx="22" cy="16" r="2" fill="#111"/>',
 'solidArrow':'<path d="M3 16H22"/><polygon points="29,16 21,11 21,21" fill="currentColor"/>',
 'hollowArrow':'<path d="M3 16H22"/><polygon points="29,16 21,11 21,21"/>',
 'boldArrow':'<path d="M3 16H29 M22 10L29 16L22 22" stroke-width="3"/>',
 'dashedArrow':'<path d="M3 16H29 M22 10L29 16L22 22" stroke-dasharray="3 2"/>',
 'resonance':'<path d="M3 16H29 M22 10L29 16L22 22 M10 10L3 16L10 22"/>',
 'equilibriumRight':'<path d="M3 11H29 M22 5L29 11 M23 21H9 M16 27L9 21"/>',
 'equilibriumLeft':'<path d="M9 11H23 M16 5L23 11 M29 21H3 M10 27L3 21"/>',
 'twoWay':'<path d="M3 11H29 M22 5L29 11 M29 21H3 M10 27L3 21 M22 17L29 11 M10 15L3 21"/>',
 'retrosynthetic':'<path d="M3 13H22 M3 19H22 M20 8L29 16L20 24"/>',
 'noGo':'<path d="M3 16H29 M22 10L29 16L22 22 M12 11L20 21 M12 21L20 11"/>',
 'straightFishhook':'<path d="M3 16H29 M22 10L29 16"/>',
 'arcArrow90':'<polyline points="8.22,8.22 8.53,7.92 8.86,7.64 9.19,7.36 9.53,7.10 9.89,6.85 10.25,6.62 10.63,6.40 11.01,6.20 11.39,6.01 11.79,5.84 12.19,5.68 12.60,5.54 13.01,5.41 13.43,5.30 13.85,5.21 14.28,5.14 14.71,5.08 15.14,5.03 15.57,5.01 16.00,5.00 16.43,5.01 16.86,5.03 17.29,5.08 17.72,5.14 18.15,5.21 18.57,5.30 18.99,5.41 19.40,5.54 19.81,5.68 20.21,5.84 20.61,6.01 20.99,6.20 21.37,6.40 21.75,6.62 22.11,6.85 22.47,7.10 22.81,7.36 23.14,7.64 23.47,7.92 23.78,8.22"/><path d="M23.78 8.22L19.06 6.58 M23.78 8.22L22.13 3.50"/>',
 'arcArrow120':'<polyline points="6.47,10.50 6.77,10.01 7.10,9.53 7.45,9.08 7.83,8.64 8.22,8.22 8.64,7.83 9.08,7.45 9.53,7.10 10.01,6.77 10.50,6.47 11.01,6.20 11.53,5.95 12.06,5.73 12.60,5.54 13.15,5.37 13.71,5.24 14.28,5.14 14.85,5.06 15.42,5.02 16.00,5.00 16.58,5.02 17.15,5.06 17.72,5.14 18.29,5.24 18.85,5.37 19.40,5.54 19.94,5.73 20.47,5.95 20.99,6.20 21.50,6.47 21.99,6.77 22.47,7.10 22.92,7.45 23.36,7.83 23.78,8.22 24.17,8.64 24.55,9.08 24.90,9.53 25.23,10.01 25.53,10.50"/><path d="M25.53 10.50L21.39 7.69 M25.53 10.50L25.16 5.51"/>',
 'arcArrow180':'<polyline points="5.00,16.00 5.03,15.14 5.14,14.28 5.30,13.43 5.54,12.60 5.84,11.79 6.20,11.01 6.62,10.25 7.10,9.53 7.64,8.86 8.22,8.22 8.86,7.64 9.53,7.10 10.25,6.62 11.01,6.20 11.79,5.84 12.60,5.54 13.43,5.30 14.28,5.14 15.14,5.03 16.00,5.00 16.86,5.03 17.72,5.14 18.57,5.30 19.40,5.54 20.21,5.84 20.99,6.20 21.75,6.62 22.47,7.10 23.14,7.64 23.78,8.22 24.36,8.86 24.90,9.53 25.38,10.25 25.80,11.01 26.16,11.79 26.46,12.60 26.70,13.43 26.86,14.28 26.97,15.14 27.00,16.00"/><path d="M27.00 16.00L24.83 11.50 M27.00 16.00L29.17 11.50"/>',
 'arcArrow270':'<polyline points="8.22,23.78 7.36,22.81 6.62,21.75 6.01,20.61 5.54,19.40 5.21,18.15 5.03,16.86 5.01,15.57 5.14,14.28 5.41,13.01 5.84,11.79 6.40,10.63 7.10,9.53 7.92,8.53 8.86,7.64 9.89,6.85 11.01,6.20 12.19,5.68 13.43,5.30 14.71,5.08 16.00,5.00 17.29,5.08 18.57,5.30 19.81,5.68 20.99,6.20 22.11,6.85 23.14,7.64 24.08,8.53 24.90,9.53 25.60,10.63 26.16,11.79 26.59,13.01 26.86,14.28 26.99,15.57 26.97,16.86 26.79,18.15 26.46,19.40 25.99,20.61 25.38,21.75 24.64,22.81 23.78,23.78"/><path d="M23.78 23.78L25.42 19.06 M23.78 23.78L28.50 22.13"/>',
 'arcFishhook90':'<polyline points="8.22,8.22 8.53,7.92 8.86,7.64 9.19,7.36 9.53,7.10 9.89,6.85 10.25,6.62 10.63,6.40 11.01,6.20 11.39,6.01 11.79,5.84 12.19,5.68 12.60,5.54 13.01,5.41 13.43,5.30 13.85,5.21 14.28,5.14 14.71,5.08 15.14,5.03 15.57,5.01 16.00,5.00 16.43,5.01 16.86,5.03 17.29,5.08 17.72,5.14 18.15,5.21 18.57,5.30 18.99,5.41 19.40,5.54 19.81,5.68 20.21,5.84 20.61,6.01 20.99,6.20 21.37,6.40 21.75,6.62 22.11,6.85 22.47,7.10 22.81,7.36 23.14,7.64 23.47,7.92 23.78,8.22"/><path d="M23.78 8.22L22.13 3.50"/>',
 'arcFishhook120':'<polyline points="6.47,10.50 6.77,10.01 7.10,9.53 7.45,9.08 7.83,8.64 8.22,8.22 8.64,7.83 9.08,7.45 9.53,7.10 10.01,6.77 10.50,6.47 11.01,6.20 11.53,5.95 12.06,5.73 12.60,5.54 13.15,5.37 13.71,5.24 14.28,5.14 14.85,5.06 15.42,5.02 16.00,5.00 16.58,5.02 17.15,5.06 17.72,5.14 18.29,5.24 18.85,5.37 19.40,5.54 19.94,5.73 20.47,5.95 20.99,6.20 21.50,6.47 21.99,6.77 22.47,7.10 22.92,7.45 23.36,7.83 23.78,8.22 24.17,8.64 24.55,9.08 24.90,9.53 25.23,10.01 25.53,10.50"/><path d="M25.53 10.50L25.16 5.51"/>',
 'arcFishhook180':'<polyline points="5.00,16.00 5.03,15.14 5.14,14.28 5.30,13.43 5.54,12.60 5.84,11.79 6.20,11.01 6.62,10.25 7.10,9.53 7.64,8.86 8.22,8.22 8.86,7.64 9.53,7.10 10.25,6.62 11.01,6.20 11.79,5.84 12.60,5.54 13.43,5.30 14.28,5.14 15.14,5.03 16.00,5.00 16.86,5.03 17.72,5.14 18.57,5.30 19.40,5.54 20.21,5.84 20.99,6.20 21.75,6.62 22.47,7.10 23.14,7.64 23.78,8.22 24.36,8.86 24.90,9.53 25.38,10.25 25.80,11.01 26.16,11.79 26.46,12.60 26.70,13.43 26.86,14.28 26.97,15.14 27.00,16.00"/><path d="M27.00 16.00L29.17 11.50"/>',
 'arcFishhook270':'<polyline points="8.22,23.78 7.36,22.81 6.62,21.75 6.01,20.61 5.54,19.40 5.21,18.15 5.03,16.86 5.01,15.57 5.14,14.28 5.41,13.01 5.84,11.79 6.40,10.63 7.10,9.53 7.92,8.53 8.86,7.64 9.89,6.85 11.01,6.20 12.19,5.68 13.43,5.30 14.71,5.08 16.00,5.00 17.29,5.08 18.57,5.30 19.81,5.68 20.99,6.20 22.11,6.85 23.14,7.64 24.08,8.53 24.90,9.53 25.60,10.63 26.16,11.79 26.59,13.01 26.86,14.28 26.99,15.57 26.97,16.86 26.79,18.15 26.46,19.40 25.99,20.61 25.38,21.75 24.64,22.81 23.78,23.78"/><path d="M23.78 23.78L28.50 22.13"/>',
 'equilibrium':'<path d="M2 11H29 M22 5L29 11 M30 21H3 M10 27L3 21"/>',
 'curvedArrow':'<path d="M4 25C5 4 19 2 28 12 M20 10L28 12L26 4"/>',
 'fishhook':'<path d="M4 25C5 4 19 2 28 12 M20 10L28 12"/>',
 'cpTilt30':'<polygon points="16,7 28,13 23,24 9,24 4,13"/><ellipse cx="16" cy="16" rx="6" ry="4"/>',
 'cpTilt60':'<polygon points="16,10 28,14 23,21 9,21 4,14"/><ellipse cx="16" cy="16" rx="6" ry="2.5"/>',
 'cpTilt75':'<polygon points="16,12 28,15 23,19 9,19 4,15"/><ellipse cx="16" cy="16" rx="6" ry="1.5"/>',
 'ligands':'<polygon points="6,3 15,8 12,17 2,17 0,8"/><path d="M8 10L20 24L29 16 M20 24L29 29"/><circle cx="20" cy="24" r="3"/>',
 'cpAnion':'<polygon points="16,4 28,13 23,27 9,27 4,13"/><circle cx="16" cy="16" r="5"/><path d="M13 16H19 M16 13V19"/>',
 'color':'<path d="M8 23L16 3L24 23 M11 16H21"/><path d="M5 28H27" stroke="#c00000" stroke-width="4"/>',
 'bold':'<path d="M10 4V28 M10 4H18C28 4 28 15 18 15H10 M10 15H19C29 15 29 28 19 28H10" stroke-width="3"/>',
 'italic':'<path d="M13 4H26 M6 28H19 M20 4L12 28"/>',
 'underline':'<path d="M8 4V18C8 28 24 28 24 18V4 M5 29H27"/>',
 'plain':'<path d="M8 28V4H20C30 4 30 17 20 17H8"/>',
}

def tool_icon(key):
    key=key.removeprefix('missing:')
    if key.startswith('orbital_'):
        _,kind,fill=key.split('_');shade='#111' if fill=='phase' else '#aaa' if fill=='gray' else 'white'
        if kind=='s':shape=f'<circle cx="16" cy="16" r="11" fill="{shade}"/>'
        else:
            def lobe(angle,phase=True,scale=1):return f'<path transform="translate(16 16) rotate({angle}) scale({scale})" d="M0 0C5 -8 13 -8 13 0C13 8 5 8 0 0Z" fill="{shade if phase or fill!="phase" else "white"}"/>'
            if kind=='p':shape=lobe(0)+lobe(180,False)
            elif kind=='hybrid':shape=lobe(0)+lobe(180,False,.4)
            elif kind=='dxy':shape=''.join(lobe(45+i*90,i%2==0,.85) for i in range(4))
            else:shape=lobe(90)+lobe(270)+f'<ellipse cx="16" cy="16" rx="11" ry="3" fill="white"/>'
    elif key.startswith('ring') or key=='benzene':
        n=6 if key=='benzene' else int(key[4:]);pts=' '.join(f'{16+12*math.cos(-math.pi/2+i*2*math.pi/n):.2f},{16+12*math.sin(-math.pi/2+i*2*math.pi/n):.2f}' for i in range(n));shape=f'<polygon points="{pts}"/>'
        if key=='benzene':shape+='<path d="M16 7L23 11 M23 22L16 26 M9 22V11"/>'
    else:shape=PATHS['elements'] if key=='ellipse' else PATHS[key]
    mirror=' transform="translate(32 0) scale(-1 1)"' if key in ['single','double','triple','wedge','hash'] else ''
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><g{mirror} fill="none" stroke="#111" stroke-width="1.4" stroke-linecap="square" stroke-linejoin="miter">{shape}</g></svg>'
    icon=QIcon()
    for size in [24,32,48,64]:
        pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.white);p=QPainter(pix);QSvgRenderer(QByteArray(svg.encode())).render(p);p.end();icon.addPixmap(pix)
    return icon
