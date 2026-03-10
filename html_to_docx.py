#!/usr/bin/env python3
"""
Convierte la presentación HTML (index.html) a un documento Word (.docx)
con tamaño de página Carta (Letter) y saltos de página en secciones lógicas.
Solo usa biblioteca estándar de Python (sin python-docx ni beautifulsoup).
"""

import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

# Tamaño Carta en twips (1 pulgada = 1440 twips): 8.5" x 11"
LETTER_WIDTH_TWIPS = 12240   # 8.5 * 1440
LETTER_HEIGHT_TWIPS = 15840  # 11 * 1440

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Colores de la presentación HTML (hex sin #, para OOXML)
COLOR_PRIMARY_DARK = "002171"   # --primary-dark títulos
COLOR_TEXT = "212121"          # --text cuerpo
COLOR_HEADER_BG = "002171"     # fondo encabezados tabla
COLOR_HEADER_FG = "FFFFFF"
COLOR_ROW_ALT = "FAFAFA"       # filas alternas tabla


def esc_xml(text):
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def run_text(elem, text, bold=False, color=None):
    """Añade un run de texto a un elemento w:p. color = hex sin # (ej. 002171)."""
    if not text and color is None:
        return
    r = ET.SubElement(elem, f"{{{W_NS}}}r")
    if bold or color:
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        if bold:
            ET.SubElement(rPr, f"{{{W_NS}}}b")
        if color:
            c = ET.SubElement(rPr, f"{{{W_NS}}}color")
            c.set(f"{{{W_NS}}}val", color)
    ET.SubElement(r, f"{{{W_NS}}}t", attrib={"xml:space": "preserve"}).text = esc_xml(text)
    return r


def _pPr_with_spacing(p, style=None, space_before=None, space_after=None, indent_left=None):
    """Añade pPr con estilo y/o espaciado (en twips, 20 twips ≈ 1pt)."""
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    if style:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", style)
    if space_before is not None or space_after is not None:
        sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        if space_before is not None:
            sp.set(f"{{{W_NS}}}before", str(space_before))
        if space_after is not None:
            sp.set(f"{{{W_NS}}}after", str(space_after))
    if indent_left is not None:
        ind = ET.SubElement(pPr, f"{{{W_NS}}}ind")
        ind.set(f"{{{W_NS}}}left", str(indent_left))
    return pPr


def paragraph(parent, text, bold=False, style=None):
    """Crea un párrafo (w:p) con un solo run de texto."""
    p = ET.SubElement(parent, f"{{{W_NS}}}p")
    if style:
        _pPr_with_spacing(p, style=style, space_after=120)
    elif not style and (text or bold):
        _pPr_with_spacing(p, space_after=100)
    if text or bold:
        run_text(p, text or "", bold=bold, color=COLOR_TEXT if not style else None)
    return p


def paragraph_break(parent):
    """Añade un salto de página."""
    p = ET.SubElement(parent, f"{{{W_NS}}}p")
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    ET.SubElement(r, f"{{{W_NS}}}br", attrib={f"{{{W_NS}}}type": "page"})
    return p


def paragraph_from_inline_elements(parent, parts):
    """parts: list of (text, bold) tuples. Párrafo normal con color texto."""
    p = ET.SubElement(parent, f"{{{W_NS}}}p")
    _pPr_with_spacing(p, space_after=100)
    for text, bold in parts:
        if text:
            run_text(p, text, bold=bold, color=COLOR_TEXT)
    return p


def table_row(parent, cells_text):
    """Añade una fila de tabla con celdas de texto."""
    tr = ET.SubElement(parent, f"{{{W_NS}}}tr")
    for cell_text in cells_text:
        tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
        tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
        ET.SubElement(tcPr, f"{{{W_NS}}}tcW", attrib={f"{{{W_NS}}}w": "3000", f"{{{W_NS}}}type": "dxa"})
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        run_text(p, cell_text, bold=False)
    return tr


class DocxBodyBuilder(HTMLParser):
    """Extrae contenido del body del HTML y construye el árbol OOXML del body del documento."""

    def __init__(self):
        super().__init__()
        self.body_blocks = []  # list of ("h1"|"h2"|"h4"|"p"|"li"|"table"|"page_break", content)
        self._in_script = False
        self._in_style = False
        self._in_body = False
        self._stack = []
        self._current_tag = None
        self._current_text = []
        self._current_parts = []  # for inline (text, bold)
        self._table_rows = []
        self._in_td = False
        self._td_text = []
        self._in_th = False
        self._th_text = []
        self._row_cells = []
        self._card_count = 0
        self._in_thead = False

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        if tag == "script":
            self._in_script = True
        if tag == "style":
            self._in_style = True
        if tag == "body":
            self._in_body = True
        if not self._in_body or self._in_script or self._in_style:
            return
        if tag in ("h1", "h2", "h3", "h4"):
            self._current_tag = tag
            self._current_text = []
        elif tag == "p":
            self._current_tag = "p"
            self._current_parts = []
        elif tag == "strong":
            self._stack.append("strong")
        elif tag in ("ul", "ol"):
            pass
        elif tag == "li":
            self._current_tag = "li"
            self._current_parts = []
        elif tag == "table":
            self._table_rows = []
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tbody":
            self._in_thead = False
        elif tag == "tr":
            self._row_cells = []
        elif tag == "th":
            self._in_th = True
            self._th_text = []
        elif tag == "td":
            self._in_td = True
            self._td_text = []
        elif tag == "div":
            cls = attrs_d.get("class", "")
            if "card-header" in cls:
                self._current_tag = "card_header"
                self._current_text = []
            if "card-body" in cls:
                self._card_count += 1
                if self._card_count == 2:
                    self.body_blocks.append(("page_break", None))
        elif tag == "span" and "numero" in attrs_d.get("class", ""):
            self._current_tag = "numero"
            self._current_text = []

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "style":
            self._in_style = False
        if tag == "body":
            self._in_body = False
        if not self._in_body or self._in_script or self._in_style:
            return
        if tag in ("h1", "h2", "h3", "h4") and self._current_tag == tag:
            text = "".join(self._current_text).strip()
            if text:
                self.body_blocks.append((tag, text))
            self._current_tag = None
        elif tag == "p" and self._current_tag == "p":
            if self._current_parts:
                self.body_blocks.append(("p", list(self._current_parts)))
            self._current_tag = None
        elif tag == "strong":
            if self._stack and self._stack[-1] == "strong":
                self._stack.pop()
        elif tag == "li" and self._current_tag == "li":
            if self._current_parts:
                self.body_blocks.append(("li", list(self._current_parts)))
            self._current_tag = None
        elif tag == "th":
            if self._in_th:
                cell_text = "".join(self._th_text).strip()
                self._row_cells.append(cell_text)
            self._in_th = False
        elif tag == "td":
            if self._in_td:
                cell_text = "".join(self._td_text).strip()
                self._row_cells.append(cell_text)
            self._in_td = False
        elif tag == "tr":
            if self._row_cells:
                self._table_rows.append(list(self._row_cells))
        elif tag == "table":
            if self._table_rows:
                self.body_blocks.append(("table", list(self._table_rows)))
        elif tag == "div" and self._current_tag == "card_header":
            text = "".join(self._current_text).strip()
            if text:
                self.body_blocks.append(("h2", text))
            self._current_tag = None

    def handle_data(self, data):
        if self._in_script or self._in_style:
            return
        # No strip here so we preserve spaces; only skip completely empty
        if self._current_tag in ("h1", "h2", "h3", "h4", "numero", "card_header"):
            self._current_text.append(data)
        elif self._current_tag == "p" or self._current_tag == "li":
            text = data  # keep spaces for inline
            bold = "strong" in self._stack
            self._current_parts.append((text, bold))
        elif self._in_td:
            self._td_text.append(data)
        elif self._in_th:
            self._th_text.append(data)


def build_document_xml(blocks):
    """Construye el XML del cuerpo del documento Word con tamaño Carta y saltos de página."""
    try:
        ET.register_namespace("w", W_NS)
    except AttributeError:
        pass
    root = ET.Element(f"{{{W_NS}}}document")
    root.set("xmlns:w", W_NS)
    body = ET.SubElement(root, f"{{{W_NS}}}body")

    for kind, content in blocks:
        if kind == "page_break":
            paragraph_break(body)
            continue
        if kind in ("h1", "h2", "h3", "h4"):
            style = "Heading1" if kind == "h1" else "Heading2" if kind == "h2" else "Heading3"
            space_after = 200 if kind == "h1" else 180 if kind == "h2" else 120
            p = ET.SubElement(body, f"{{{W_NS}}}p")
            _pPr_with_spacing(p, style=style, space_after=space_after)
            run_text(p, content, bold=True, color=COLOR_PRIMARY_DARK)
            continue
        if kind == "p":
            if isinstance(content, list):
                paragraph_from_inline_elements(body, content)
            else:
                paragraph(body, content)
            continue
        if kind == "li":
            p = ET.SubElement(body, f"{{{W_NS}}}p")
            _pPr_with_spacing(p, space_after=80, indent_left=720)
            run_text(p, "• ", bold=False, color=COLOR_TEXT)
            for t, b in content:
                if t:
                    run_text(p, t, bold=b, color=COLOR_TEXT)
            continue
        if kind == "table":
            tbl = ET.SubElement(body, f"{{{W_NS}}}tbl")
            tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
            ET.SubElement(tblPr, f"{{{W_NS}}}tblW", attrib={f"{{{W_NS}}}w": "0", f"{{{W_NS}}}type": "auto"})
            tblBorders = ET.SubElement(tblPr, f"{{{W_NS}}}tblBorders")
            for border_tag in ("top", "left", "bottom", "right", "insideH", "insideV"):
                b = ET.SubElement(tblBorders, f"{{{W_NS}}}{border_tag}")
                b.set(f"{{{W_NS}}}val", "single")
                b.set(f"{{{W_NS}}}sz", "4")
                b.set(f"{{{W_NS}}}color", "E0E0E0")
            for i, row in enumerate(content):
                tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
                is_header = i == 0
                for cell_text in row:
                    tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
                    tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
                    ET.SubElement(tcPr, f"{{{W_NS}}}tcW", attrib={f"{{{W_NS}}}w": "3000", f"{{{W_NS}}}type": "dxa"})
                    if is_header:
                        shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
                        shd.set(f"{{{W_NS}}}val", "clear")
                        shd.set(f"{{{W_NS}}}fill", COLOR_HEADER_BG)
                    elif i % 2 == 1:
                        shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
                        shd.set(f"{{{W_NS}}}val", "clear")
                        shd.set(f"{{{W_NS}}}fill", COLOR_ROW_ALT)
                    p = ET.SubElement(tc, f"{{{W_NS}}}p")
                    run_text(p, cell_text or "", bold=is_header, color=COLOR_HEADER_FG if is_header else COLOR_TEXT)
            continue

    # Propiedades de sección: tamaño Carta
    sectPr = ET.SubElement(body, f"{{{W_NS}}}sectPr")
    pgSz = ET.SubElement(sectPr, f"{{{W_NS}}}pgSz", attrib={
        f"{{{W_NS}}}w": str(LETTER_WIDTH_TWIPS),
        f"{{{W_NS}}}h": str(LETTER_HEIGHT_TWIPS),
    })
    pgMar = ET.SubElement(sectPr, f"{{{W_NS}}}pgMar", attrib={
        f"{{{W_NS}}}top": "1440",
        f"{{{W_NS}}}right": "1440",
        f"{{{W_NS}}}bottom": "1440",
        f"{{{W_NS}}}left": "1440",
        f"{{{W_NS}}}header": "720",
        f"{{{W_NS}}}footer": "720",
    })

    return root


def create_docx(html_path: Path, output_path: Path):
    """Lee index.html, extrae contenido y escribe presentacion.docx."""
    html_content = html_path.read_text(encoding="utf-8")
    # Quitar scripts y estilos para que el parser no se confunda con tags dentro de strings
    html_content = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html_content, flags=re.IGNORECASE)
    html_content = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html_content, flags=re.IGNORECASE)

    parser = DocxBodyBuilder()
    parser.feed(html_content)
    blocks = parser.body_blocks

    doc_root = build_document_xml(blocks)

    # Serializar document.xml: Word espera prefijo w: y xmlns:w
    doc_str = ET.tostring(doc_root, encoding="unicode", method="xml")
    # ET puede generar ns0:; normalizar a w: para Word
    for prefix in ("ns0", "ns1", "ns2"):
        doc_str = doc_str.replace(f"xmlns:{prefix}=", "xmlns:w=").replace(f"{prefix}:", "w:")
    if "xmlns:w=" not in doc_str:
        doc_str = doc_str.replace("<w:document>", f'<w:document xmlns:w="{W_NS}">', 1)
    # Quitar xmlns duplicado si existe
    doc_str = re.sub(r'\s*xmlns:w="[^"]+"(?=.*xmlns:w=)', " ", doc_str, count=1)
    if not doc_str.strip().startswith("<?xml"):
        doc_str = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + doc_str

    # Contenidos mínimos para un DOCX válido
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

    rels_root = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    word_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/><w:szCs w:val="22"/>
        <w:color w:val="212121"/>
        <w:lang w:val="es-ES"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="100"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="100" w:line="360" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="212121"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1" w:default="0">
    <w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="120" w:after="200"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/><w:color w:val="002171"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2" w:default="0">
    <w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="160" w:after="180"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/><w:color w:val="002171"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3" w:default="0">
    <w:name w:val="Heading 3"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="100" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="002171"/></w:rPr>
  </w:style>
</w:styles>"""

    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties">
  <dc:title>Presentación - Módulo de Formas Configurables</dc:title>
  <dc:creator>ibQuoter</dc:creator>
  <cp:lastModifiedBy>html_to_docx</cp:lastModifiedBy>
</cp:coreProperties>"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>Python html_to_docx</Application>
</Properties>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels_root)
        zf.writestr("word/_rels/document.xml.rels", word_rels)
        zf.writestr("word/document.xml", doc_str)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("docProps/core.xml", core_xml)
        zf.writestr("docProps/app.xml", app_xml)

    print(f"Generado: {output_path}")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    html_path = base / "index.html"
    output_path = base / "presentacion_formas_configurables.docx"
    if not html_path.exists():
        print(f"No se encuentra {html_path}")
        exit(1)
    create_docx(html_path, output_path)
