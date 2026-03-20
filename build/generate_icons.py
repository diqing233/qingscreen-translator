"""
生成 ScreenTranslator 图标文件（icon.ico / icon.icns）
依赖：Pillow
用法：python build/generate_icons.py
"""
import os
import sys
import struct
import zlib

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))


def draw_icon_pixels(size):
    """生成简单的 ST 字母图标，返回 RGBA bytes"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 圆角背景
        margin = size // 8
        r = size // 5
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=r,
            fill=(30, 120, 220, 255),
        )
        # 文字 "ST"
        font_size = size // 3
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        text = "ST"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) // 2 - bbox[0], (size - th) // 2 - bbox[1]),
            text,
            font=font,
            fill=(255, 255, 255, 255),
        )
        return img
    except ImportError:
        return None


def make_png_bytes(size):
    """用纯 Python 生成最小 PNG（蓝色圆角方块），不依赖 Pillow"""
    # 简单纯色 PNG
    width = height = size
    raw_rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            # 圆角判断
            cx, cy = width / 2, height / 2
            r = width * 0.42
            corner_r = width * 0.18
            dx, dy = abs(x - cx), abs(y - cy)
            in_rect = dx <= r and dy <= r
            in_corner = (dx > r - corner_r and dy > r - corner_r and
                         (dx - (r - corner_r)) ** 2 + (dy - (r - corner_r)) ** 2 > corner_r ** 2)
            if in_rect and not in_corner:
                row += bytes([30, 120, 220, 255])  # RGBA blue
            else:
                row += bytes([0, 0, 0, 0])  # transparent
        raw_rows.append(b'\x00' + bytes(row))

    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data, 9)

    def chunk(name, data):
        c = name + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')
    return png


def generate_ico(output_path):
    """生成 .ico 文件（包含 16/32/48/256 四种尺寸）"""
    sizes = [16, 32, 48, 256]
    images_png = []

    for size in sizes:
        img = draw_icon_pixels(size)
        if img is not None:
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            images_png.append((size, buf.getvalue()))
        else:
            images_png.append((size, make_png_bytes(size)))

    # ICO 格式：header + directory + data
    num = len(images_png)
    header = struct.pack('<HHH', 0, 1, num)  # reserved, type=1(ICO), count
    offset = 6 + num * 16
    directory = b''
    data = b''
    for size, png_bytes in images_png:
        sz = size if size < 256 else 0
        directory += struct.pack('<BBBBHHII',
                                 sz, sz,   # width, height
                                 0, 0,     # color count, reserved
                                 1, 32,    # planes, bit count
                                 len(png_bytes), offset)
        offset += len(png_bytes)
        data += png_bytes

    with open(output_path, 'wb') as f:
        f.write(header + directory + data)
    print(f"Generated: {output_path}")


def generate_icns(output_path):
    """生成 .icns 文件（包含 ic07/ic08/ic09 三种尺寸）"""
    # icns type codes -> sizes
    entries = [
        (b'ic07', 128),
        (b'ic08', 256),
        (b'ic09', 512),
    ]
    chunks = b''
    for type_code, size in entries:
        img = draw_icon_pixels(size)
        if img is not None:
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()
        else:
            png_bytes = make_png_bytes(size)
        chunk_len = 8 + len(png_bytes)
        chunks += type_code + struct.pack('>I', chunk_len) + png_bytes

    total_len = 8 + len(chunks)
    with open(output_path, 'wb') as f:
        f.write(b'icns' + struct.pack('>I', total_len) + chunks)
    print(f"Generated: {output_path}")


if __name__ == '__main__':
    ico_path = os.path.join(BUILD_DIR, 'icon.ico')
    icns_path = os.path.join(BUILD_DIR, 'icon.icns')

    generate_ico(ico_path)
    generate_icns(icns_path)
    print("Done.")
