"""Make an "Arial" family from Liberation Sans (same metrics).

The reports of the PVA (JasperReports) ask for Arial; without it the report
of the ECD stops with a critical error.
"""

from fontTools.ttLib import TTFont

STYLES = [
    ("Regular", "arial.ttf", "Regular"),
    ("Bold", "arialbd.ttf", "Bold"),
    ("Italic", "ariali.ttf", "Italic"),
    ("BoldItalic", "arialbi.ttf", "Bold Italic"),
]

for source, target, style in STYLES:
    font = TTFont(f"/usr/share/fonts/truetype/liberation/LiberationSans-{source}.ttf")
    for record in font["name"].names:
        if record.nameID in (1, 16):
            record.string = "Arial"
        elif record.nameID in (2, 17):
            record.string = style
        elif record.nameID == 4:
            record.string = "Arial" if style == "Regular" else f"Arial {style}"
        elif record.nameID == 6:
            record.string = "Arial-" + style.replace(" ", "")
    font.save(f"/usr/share/fonts/truetype/arial/{target}")
