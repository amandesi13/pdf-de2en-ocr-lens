from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def main() -> None:
    out = Path(__file__).with_name("sample_german_technical.pdf")
    c = canvas.Canvas(str(out), pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Technischer Bericht")
    c.setFont("Helvetica", 11)
    c.drawString(72, height - 100, "Die Messung zeigt Spannung, Strom und Leistung im Netzwerk.")

    c.rect(90, height - 240, 160, 80)
    c.rect(340, height - 240, 160, 80)
    c.line(250, height - 200, 340, height - 200)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(170, height - 195, "Eingang")
    c.drawCentredString(420, height - 195, "Ausgang")
    c.setFont("Helvetica", 10)
    c.drawString(72, height - 290, "Diagrammbeschriftungen sollen per OCR erkannt werden.")

    image = Image.new("RGB", (520, 120), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=24)
    draw.rectangle((20, 25, 220, 95), outline="black", width=3)
    draw.rectangle((300, 25, 500, 95), outline="black", width=3)
    draw.line((220, 60, 300, 60), fill="black", width=3)
    draw.text((55, 48), "Nur im Bild", fill="black", font=font)
    draw.text((335, 48), "Steuerung", fill="black", font=font)
    image_path = out.with_suffix(".png")
    image.save(image_path)
    c.drawImage(ImageReader(str(image_path)), 72, height - 440, width=420, height=96)
    c.drawString(72, height - 465, "Die obere Grafik ist ein eingebettetes Rasterbild.")

    c.save()
    print(out)


if __name__ == "__main__":
    main()
