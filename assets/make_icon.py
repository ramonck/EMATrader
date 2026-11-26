"""Render the SVG mark to the desktop PNG used by PyInstaller."""

from pathlib import Path

from PIL import Image, ImageDraw


def main():
    scale = 4
    image = Image.new("RGBA", (256 * scale, 256 * scale))
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle(tuple(n * scale for n in (8, 8, 248, 248)), 55 * scale, fill="#101723")

    def stroke(points, color, width=13):
        scaled = [(x * scale, y * scale) for x, y in points]
        pen.line(scaled, fill=color, width=width * scale, joint="curve")
        radius = width * scale / 2
        for x, y in scaled:
            pen.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)

    stroke([(50, 155), (87, 123), (121, 137), (170, 82), (207, 82)], "#52e3b2")
    stroke([(50, 186), (87, 155), (122, 168), (170, 114), (207, 114)], "#52e3b2")
    stroke([(184, 60), (218, 60), (218, 94)], "#f1f6ff")
    pen.ellipse(tuple(n * scale for n in (42, 147, 58, 163)), fill="#f1f6ff")
    image.resize((256, 256), Image.Resampling.LANCZOS).save(Path(__file__).with_name("icon.png"))


if __name__ == "__main__":
    main()
