import fitz
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Create an image containing text
image = Image.new("RGB", (1200, 500), "white")
draw = ImageDraw.Draw(image)

draw.text(
    (50, 100),
    "TRIAD AI DOCUMENT MANAGEMENT SYSTEM",
    fill="black"
)

draw.text(
    (50, 200),
    "Scanned PDF OCR Testing Successful",
    fill="black"
)

draw.text(
    (50, 300),
    "Tesseract extracts text from scanned documents.",
    fill="black"
)

# Save image temporarily
image_path = Path("tests/scanned_page.png")
image.save(image_path)

# Insert image into a PDF
pdf = fitz.open()
page = pdf.new_page(width=600, height=250)

page.insert_image(
    page.rect,
    filename=str(image_path)
)

pdf.save("tests/scanned_test.pdf")
pdf.close()

image_path.unlink()

print("Scanned test PDF created successfully!")