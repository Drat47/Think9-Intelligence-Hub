import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Draw background and header/footer
        self.saveState()
        
        # We don't draw slide decorations on slide 1 (Title slide)
        if self._pageNumber > 1:
            # Draw header bar
            self.setFillColor(colors.HexColor("#0B0F19"))
            self.rect(0, 540, 792, 72, fill=True, stroke=False)
            
            # Header text/brand
            self.setFillColor(colors.white)
            self.setFont("Helvetica-Bold", 12)
            self.drawString(36, 573, "THINK9 INTELLIGENCE HUB")
            
            self.setFillColor(colors.HexColor("#38BDF8"))
            self.setFont("Helvetica", 10)
            self.drawString(36, 553, "Centralized Decision Support & Quality Memory Log")
            
            # Draw footer bar line
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(36, 36, 756, 36)
            
            # Footer text & page numbering
            self.setFillColor(colors.HexColor("#64748B"))
            self.setFont("Helvetica", 8)
            self.drawString(36, 22, "Think9 Portfolio Decision Platform")
            
            page_text = f"Slide {self._pageNumber} of {page_count}"
            self.drawRightString(756, 22, page_text)
        else:
            # Title slide background gradient representation
            self.setFillColor(colors.HexColor("#0B0F19"))
            self.rect(0, 0, 792, 612, fill=True, stroke=False)
            
            # Accent bar
            self.setFillColor(colors.HexColor("#38BDF8"))
            self.rect(0, 0, 792, 10, fill=True, stroke=False)
            
        self.restoreState()

def create_pitch_deck():
    pdf_path = os.path.join(os.path.dirname(__file__), "think9_pitch_deck.pdf")
    
    # Setup document in Landscape mode
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=90,  # Below header bar
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_main_style = ParagraphStyle(
        'TitleMain',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=38,
        leading=44,
        textColor=colors.HexColor("#38BDF8"),
        alignment=1, # Center
        spaceAfter=15
    )
    
    title_sub_style = ParagraphStyle(
        'TitleSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#94A3B8"),
        alignment=1, # Center
        spaceAfter=30
    )
    
    title_presenter_style = ParagraphStyle(
        'TitlePresenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.white,
        alignment=1,
        spaceAfter=5
    )
    
    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0B0F19"),
        spaceAfter=20
    )
    
    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=19,
        textColor=colors.HexColor("#334155"),
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=8
    )
    
    visual_style = ParagraphStyle(
        'SlideVisual',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0D9488"),
        backColor=colors.HexColor("#F0FDF4"),
        borderColor=colors.HexColor("#BBF7D0"),
        borderWidth=0.5,
        borderPadding=10,
        spaceAfter=15,
        leftIndent=10,
        rightIndent=10
    )

    story = []
    
    # ------------------ Slide 1: Title Slide ------------------
    # Adjust top margin temporarily by spacers
    story.append(Spacer(1, 100))
    story.append(Paragraph("Think9 Intelligence Hub", title_main_style))
    story.append(Paragraph('"Every decision makes Think9 smarter."', title_sub_style))
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Presenter</b>: AI Architect & Lead Engineer", title_presenter_style))
    story.append(Paragraph("Centralized Decision Support & Institutional Quality Memory Log", ParagraphStyle('TitleFooter', parent=title_presenter_style, fontSize=10, textColor=colors.HexColor("#64748B"))))
    story.append(PageBreak())
    
    # Load and parse pitch_deck.md
    pitch_deck_path = os.path.join(os.path.dirname(__file__), "pitch_deck.md")
    with open(pitch_deck_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_slide = None
    slide_title = ""
    visual_text = ""
    bullets = []
    
    def process_last_slide():
        if not slide_title:
            return
        story.append(Paragraph(slide_title, slide_title_style))
        if visual_text:
            story.append(Paragraph(f"<b>Suggested Slide Visual</b>: {visual_text}", visual_style))
            story.append(Spacer(1, 10))
        for bullet in bullets:
            story.append(Paragraph(f"&bull; {bullet}", bullet_style))
            story.append(Spacer(1, 3))
        story.append(PageBreak())
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("## Slide 1:"):
            # Already handled title manually
            continue
        if line.startswith("## Slide"):
            process_last_slide()
            current_slide = line
            slide_title = ""
            visual_text = ""
            bullets = []
        elif line.startswith("* **Title**:"):
            slide_title = line.replace("* **Title**:", "").strip()
        elif line.startswith("* **Subtitle**:") or line.startswith("* **Presenter**:") or line.startswith("* **Visual**:"):
            visual_text = line.replace("* **Visual**:", "").replace("* **Subtitle**:", "").strip()
        elif line.startswith("- ") or line.startswith("* "):
            clean_bullet = line.replace("- ", "").replace("* ", "").strip()
            # Remove any ** bold tags or format cleanly
            bullets.append(clean_bullet)
            
    # Process the final slide
    process_last_slide()
    
    # Remove last page break to avoid blank page
    if story and isinstance(story[-1], PageBreak):
        story.pop()
        
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF generated successfully at:", pdf_path)

if __name__ == "__main__":
    create_pitch_deck()
