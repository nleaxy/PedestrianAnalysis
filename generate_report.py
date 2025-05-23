import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import shutil
import numpy as np

def generate_report(json_path='results/results.json', output_path='results/report.png'):
    if not os.path.exists(json_path):
        print("JSON не найден.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = data.get("total_unique_people", "?")
    peak = data.get("peak_moment", {})
    zone = data.get("peak_density_zone", {})
    movement = data.get("movement_statistics", {})
    filename = data.get("source_file", "unknown_file")

    width, height = 1200, 1500
    background = create_gradient_background(width, height)
    img = Image.fromarray(background)
    draw = ImageDraw.Draw(img)

    font_path = "fonts/Oswald-VariableFont_wght.ttf"
    title_font = ImageFont.truetype(font_path, 80)
    header_font = ImageFont.truetype(font_path, 58)
    font = ImageFont.truetype(font_path, 48)
    font_small = ImageFont.truetype(font_path, 40)

    add_grid_pattern(img, width, height)

    title_text = "ОТЧЁТ ОБРАБОТКИ ВИДЕО"

    draw.rectangle([(0, 0), (width, 160)], fill="#090909")

    text_width = draw.textlength(title_text, font=title_font)
    draw_text_with_glow(img, draw, (width - text_width) // 2, 30, title_text, "#00e6e6", title_font)

    filename_text = f"Файл: {filename}"
    filename_width = draw.textlength(filename_text, font=font_small)
    draw_text_with_glow(img, draw, (width - filename_width) // 2, 120, filename_text, "#888888", font_small)

    draw.line([(40, 190), (width - 40, 190)], fill="#222222", width=2)

    y = 220
    pad = 22
    block_height = 90
    block_width = width - 300

    def block(text, y, color="#ffffff"):
        draw_rounded_rectangle(img, draw, 150, y, 150 + block_width, y + block_height, 25, "#111111", "#141414")
        draw.rectangle([(150, y), (165, y + block_height)], fill=color)
        text_width = draw.textlength(text, font=font)
        draw.text(((width - text_width) // 2, y + pad - 15), text, font=font, fill=color)
        return y + block_height + 30

    y = block(f"Общее число людей: {total}", y, "#f0a500")
    y = block(f"Максимум: {peak.get('count', '?')} чел. в {peak.get('time', '?')} сек.", y, "#00e6e6")
    y = block(f"Пиковый отрезок: {zone.get('start_time', '?')}–{zone.get('end_time', '?')} сек.", y, "#ff4d4d")
    y = block(f"Среднее в пике: {int(zone.get('average_count', 0))} чел.", y, "#66ff66")

    y += 40
    draw.line([(40, y - 10), (width - 40, y - 10)], fill="#222222", width=2)

    chart_title = "Статистика по направлениям:"
    title_width = draw.textlength(chart_title, font=header_font)
    draw_text_with_glow(img, draw, (width - title_width) // 2, y, chart_title, "#00e6e6", header_font)

    y += 150
    directions = ['вверх', 'вниз', 'налево', 'направо']
    counts = [movement.get(dir, 0) for dir in directions]
    max_count = max(counts + [1])
    bar_width = 140
    spacing = 120
    chart_width = (bar_width + spacing) * len(directions) - spacing
    start_x = (width - chart_width) // 2
    baseline = y + 400

    for i in range(1, 5):
        level = baseline - (i * 100)
        draw.line([(start_x - 20, level), (start_x + chart_width + 20, level)], fill="#222222", width=1)

    for i, count in enumerate(counts):
        bar_height = int(380 * count / max_count)
        if bar_height < 60 and count > 0:
            bar_height = 60

        x0 = start_x + i * (bar_width + spacing)
        y0 = baseline - bar_height
        x1 = x0 + bar_width
        y1 = baseline

        radius = 5

        draw_gradient_bar(img, draw, x0, y0 + radius, x1, y1, "#00e6e6", "#008080")
        draw.pieslice([x0, y0, x0 + 2 * radius - 1, y0 + 2 * radius - 1], 180, 360, fill="#00e6e6")
        draw.pieslice([x1 - 2 * radius + 1, y0, x1, y0 + 2 * radius - 1], 180, 360, fill="#00e6e6")
        draw.rectangle([x0 + radius, y0, x1 - radius, y0 + radius], fill="#00e6e6")
            
        text_width = draw.textlength(str(count), font=font)
        draw_text_with_glow(img, draw, x0 + (bar_width - text_width) // 2, y0 - 70, str(count), "#00e6e6", font)
        label_width = draw.textlength(directions[i], font=font_small)
        draw.text((x0 + (bar_width - label_width) // 2, y1 + 20), directions[i], font=font_small, fill="white")

    draw.line([(40, height - 80), (width - 40, height - 80)], fill="#222222", width=2)
    img.save(output_path, quality=95, dpi=(300, 300))
    print(f"✅ Отчёт сохранён в {output_path}")

    os.makedirs("static/results", exist_ok=True)
    shutil.copy(output_path, "static/results/report.png")


def create_gradient_background(width, height):
    background = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        intensity = int(10 + (y / height) * 5)
        background[y, :] = [intensity, intensity, intensity]
    return background

def add_grid_pattern(img, width, height):
    draw = ImageDraw.Draw(img)
    grid_size = 80
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill="#111111", width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill="#111111", width=1)

def draw_text_with_glow(img, draw, x, y, text, color, font):
    text_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text((x, y), text, font=font, fill=color)
    glow = text_layer.filter(ImageFilter.GaussianBlur(2))
    img.paste(glow, (0, 0), glow)
    draw.text((x, y), text, font=font, fill=color)

def draw_rounded_rectangle(img, draw, x0, y0, x1, y1, radius, fill_start, fill_end):
    height = y1 - y0
    width = x1 - x0

    start_color = tuple(int(fill_start[i:i+2], 16) for i in (1, 3, 5))
    end_color = tuple(int(fill_end[i:i+2], 16) for i in (1, 3, 5))

    # gradient as an numpy
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        gradient[y, :] = [r, g, b]

    # creating picture
    gradient_img = Image.fromarray(gradient, mode='RGB')
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)

    mask_draw.rectangle([radius, 0, width - radius, height], fill=255)
    mask_draw.rectangle([0, radius, width, height], fill=255)
    mask_draw.pieslice([0, 0, 2*radius, 2*radius], 180, 270, fill=255)
    mask_draw.pieslice([width - 2*radius, 0, width, 2*radius], 270, 360, fill=255)

    # gradient by mask
    img.paste(gradient_img, (x0, y0), mask)


def draw_gradient_bar(img, draw, x0, y0, x1, y1, color_top, color_bottom):
    height = y1 - y0
    width = x1 - x0
    if height <= 0 or width <= 0:
        return
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    top_color = tuple(int(color_top[i:i+2], 16) for i in (1, 3, 5))
    bottom_color = tuple(int(color_bottom[i:i+2], 16) for i in (1, 3, 5))
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        gradient[y, :] = [r, g, b]
    gradient_img = Image.fromarray(gradient)
    img.paste(gradient_img, (x0, y0))
    draw.line([(x0, y0), (x1, y0)], fill=color_top, width=2)
    draw.line([(x1 - 1, y0), (x1 - 1, y1)], fill=color_bottom, width=1)

if __name__ == "main":
    generate_report()
