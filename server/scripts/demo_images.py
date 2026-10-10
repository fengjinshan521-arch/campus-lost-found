"""演示配图生成：为招领/寻物信息自动绘制"相关图片"。

设计目标：
    演示库里的招领信息如果全是空白占位，检索与认领的体验说服力不足。
    本模块按「标题关键词 → 物品形状」绘制示意图（纯代码生成，不依赖网络与素材版权），
    存进 uploads 目录并回填 item.images，同时写入 t_attachment 留痕，与真实上传链路一致。

用法：
    python scripts/demo_images.py                为所有缺图的招领/寻物补图
    python scripts/demo_images.py --force        已有图片也重新生成
    python scripts/demo_images.py --only found   只处理招领

依赖：Pillow（requirements.txt 已声明；缺失时 ensure_item_image 返回 None，不影响主流程）
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:          # 未安装 Pillow 时静默降级，seed 流程照常跑完
    HAS_PIL = False

W, H = 800, 600
BG_TOP = (243, 246, 251)
BG_BOTTOM = (222, 232, 245)
INK = (59, 111, 212)          # 主体蓝
INK_DARK = (45, 88, 176)
ACCENT = (255, 193, 87)       # 点缀橙
GREY = (201, 212, 232)
WHITE = (255, 255, 255)
TEXT_DARK = (33, 43, 60)
TEXT_MUTE = (110, 124, 145)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size: int, bold: bool = False):
    if not HAS_PIL:
        return None
    for path in FONT_CANDIDATES:
        if bold and "msyhbd" not in path and "DejaVu" not in path and "simhei" not in path:
            continue
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _gradient(size=(W, H)):
    img = Image.new("RGB", size, BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(size[1] - 1, 1)
        d.line([(0, y), (size[0], y)], fill=(
            int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t),
            int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t),
            int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t),
        ))
    return img


def _fit(text: str, font, max_width: int) -> str:
    """按像素宽度截断文本并加省略号。"""
    if font is None:
        return text
    if font.getlength(text) <= max_width:
        return text
    out = text
    while out and font.getlength(out + "…") > max_width:
        out = out[:-1]
    return out + "…"


# ---------------------------------------------------------------- 物品形状


def _rr(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_phone(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    bw, bh = int(w * 0.52), int(h * 0.86)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    _rr(d, [cx - bw // 2 + 6, cy - bh // 2 + 8, cx + bw // 2 + 6, cy + bh // 2 + 8], 22, (198, 210, 232))
    _rr(d, [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], 22, INK_DARK)
    _rr(d, [cx - bw // 2 + 10, cy - bh // 2 + 34, cx + bw // 2 - 10, cy + bh // 2 - 34], 8, WHITE)
    d.ellipse([cx - 7, cy - bh // 2 + 14, cx + 7, cy - bh // 2 + 28], fill=(140, 170, 235))
    _rr(d, [cx - 24, cy + bh // 2 - 24, cx + 24, cy + bh // 2 - 12], 6, GREY)


def draw_card(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    cw, ch = int(w * 0.82), int(h * 0.5)
    _rr(d, [cx - cw // 2 + 5, cy - ch // 2 + 7, cx + cw // 2 + 5, cy + ch // 2 + 7], 16, (198, 210, 232))
    _rr(d, [cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2], 16, WHITE, INK, 2)
    _rr(d, [cx - cw // 2, cy - ch // 2, cx + cw // 2, cy - ch // 2 + 26], 16, INK)
    d.rectangle([cx - cw // 2, cy - ch // 2 + 16, cx + cw // 2, cy - ch // 2 + 26], fill=INK)
    d.ellipse([cx - cw // 2 + 18, cy - ch // 2 + 44, cx - cw // 2 + 78, cy - ch // 2 + 104], fill=GREY)
    _rr(d, [cx - cw // 2 + 96, cy - ch // 2 + 56, cx + cw // 2 - 24, cy - ch // 2 + 72], 6, GREY)
    _rr(d, [cx - cw // 2 + 96, cy - ch // 2 + 84, cx + cw // 2 - 60, cy - ch // 2 + 100], 6, (222, 230, 244))
    _rr(d, [cx - cw // 2 + 18, cy + ch // 2 - 30, cx + cw // 2 - 18, cy + ch // 2 - 14], 6, ACCENT)


def draw_book(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    w, h = int((x1 - x0) * 0.8), int((y1 - y0) * 0.56)
    left = [(cx - w // 2, cy - h // 2), (cx - 8, cy - h // 2 - 12),
            (cx - 8, cy + h // 2 - 12), (cx - w // 2, cy + h // 2)]
    right = [(cx + w // 2, cy - h // 2), (cx + 8, cy - h // 2 - 12),
             (cx + 8, cy + h // 2 - 12), (cx + w // 2, cy + h // 2)]
    d.polygon(left, fill=INK)
    d.polygon(right, fill=INK_DARK)
    for i in range(4):
        yy = cy - h // 2 + 26 + i * 22
        d.line([(cx - w // 2 + 22, yy), (cx - 26, yy - 4)], fill=(180, 204, 245), width=3)
        d.line([(cx + 26, yy - 4), (cx + w // 2 - 22, yy)], fill=(150, 180, 228), width=3)


def draw_bag(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    bw, bh = int((x1 - x0) * 0.56), int((y1 - y0) * 0.5)
    _rr(d, [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], 18, INK)
    d.arc([cx - 46, cy - bh // 2 - 62, cx + 46, cy - bh // 2 + 18], 180, 360, fill=INK, width=12)
    _rr(d, [cx - bw // 2 + 18, cy - 6, cx + bw // 2 - 18, cy + 34], 8, INK_DARK)
    _rr(d, [cx - 14, cy + 4, cx + 14, cy + 26], 4, ACCENT)
    d.ellipse([cx - bw // 2 - 2, cy + bh // 2 - 6, cx - bw // 2 + 22, cy + bh // 2 + 18], fill=INK_DARK)
    d.ellipse([cx + bw // 2 - 22, cy + bh // 2 - 6, cx + bw // 2 + 2, cy + bh // 2 + 18], fill=INK_DARK)


def draw_key(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    r = int((y1 - y0) * 0.16)
    d.ellipse([cx - 90 - r, cy - 60 - r, cx - 90 + r, cy - 60 + r], fill=ACCENT, outline=INK_DARK, width=6)
    d.line([(cx - 90, cy - 60 + r), (cx + 96, cy + 52)], fill=ACCENT, width=16)
    d.line([(cx + 96, cy + 52), (cx + 40, cy + 52)], fill=ACCENT, width=14)
    d.line([(cx + 78, cy + 52), (cx + 78, cy + 4)], fill=ACCENT, width=14)
    d.ellipse([cx - 90 - r // 3, cy - 60 - r // 3, cx - 90 + r // 3, cy - 60 + r // 3], fill=BG_TOP)


def draw_cup(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    bw, bh = int((x1 - x0) * 0.4), int((y1 - y0) * 0.56)
    top, bot = cy - bh // 2, cy + bh // 2
    d.polygon([(cx - bw // 2, top), (cx + bw // 2, top), (cx + bw // 2 - 14, bot), (cx - bw // 2 + 14, bot)],
              fill=INK)
    _rr(d, [cx - bw // 2 - 10, top - 26, cx + bw // 2 + 10, top], 10, INK_DARK)
    d.line([(cx + bw // 2 + 22, top + 40), (cx + bw // 2 + 22, bot + 6)], fill=INK_DARK, width=10)
    d.arc([cx - bw // 2 - 14, top + 40, cx + bw // 2 + 14, bot + 6], 270, 90, fill=INK_DARK, width=10)
    d.rectangle([cx - bw // 2 + 12, top + 46, cx + bw // 2 - 12, top + 58], fill=(170, 200, 245))


def draw_umbrella(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    w = int((x1 - x0) * 0.72)
    d.pieslice([cx - w // 2, cy - 150, cx + w // 2, cy + 60], 180, 360, fill=INK)
    d.line([(cx - w // 2 + 10, cy - 45), (cx, cy - 60), (cx + w // 2 - 10, cy - 45)], fill=BG_TOP, width=4)
    d.line([(cx, cy - 60), (cx, cy + 120)], fill=INK_DARK, width=8)
    d.arc([cx, cy + 60, cx + 60, cy + 120], 0, 180, fill=INK_DARK, width=8)


def draw_glasses(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    r = int((y1 - y0) * 0.17)
    d.ellipse([cx - 108 - r, cy - r, cx - 108 + r, cy + r], outline=INK_DARK, width=10)
    d.ellipse([cx + 108 - r, cy - r, cx + 108 + r, cy + r], outline=INK_DARK, width=10)
    d.line([(cx - 108 + r, cy - 8), (cx + 108 - r, cy - 8)], fill=INK_DARK, width=10)
    d.line([(cx - 108 - r, cy - 8), (cx - 108 - r - 54, cy - 34)], fill=INK_DARK, width=10)
    d.line([(cx + 108 + r, cy - 8), (cx + 108 + r + 54, cy - 34)], fill=INK_DARK, width=10)


def draw_headphone(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.arc([cx - 110, cy - 130, cx + 110, cy + 40], 180, 360, fill=INK_DARK, width=18)
    _rr(d, [cx - 150, cy - 10, cx - 82, cy + 78], 22, INK)
    _rr(d, [cx + 82, cy - 10, cx + 150, cy + 78], 22, INK)
    d.ellipse([cx - 140, cy + 8, cx - 92, cy + 56], fill=(170, 200, 245))


def draw_powerbank(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    bw, bh = int((x1 - x0) * 0.36), int((y1 - y0) * 0.66)
    _rr(d, [cx - bw // 2 + 6, cy - bh // 2 + 8, cx + bw // 2 + 6, cy + bh // 2 + 8], 16, (198, 210, 232))
    _rr(d, [cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], 16, INK)
    d.polygon([(cx + 12, cy - 46), (cx - 16, cy + 8), (cx + 2, cy + 8), (cx - 8, cy + 52),
               (cx + 22, cy - 6), (cx + 4, cy - 6)], fill=ACCENT)
    for i in range(4):
        d.rectangle([cx - bw // 2 + 14, cy + bh // 2 - 46 + i * 12, cx - bw // 2 + 40, cy + bh // 2 - 42 + i * 12],
                    fill=(170, 200, 245))


def draw_laptop(d, b):
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    sw, sh = int((x1 - x0) * 0.66), int((y1 - y0) * 0.42)
    _rr(d, [cx - sw // 2, cy - sh // 2 - 30, cx + sw // 2, cy + sh // 2 - 30], 10, INK_DARK)
    _rr(d, [cx - sw // 2 + 14, cy - sh // 2 - 16, cx + sw // 2 - 14, cy + sh // 2 - 44], 6, (214, 228, 248))
    d.polygon([(cx - sw // 2 - 26, cy + sh // 2 - 30), (cx + sw // 2 + 26, cy + sh // 2 - 30),
               (cx + sw // 2 + 44, cy + sh // 2 - 4), (cx - sw // 2 - 44, cy + sh // 2 - 4)], fill=GREY)
    _rr(d, [cx - 40, cy + sh // 2 - 14, cx + 40, cy + sh // 2 - 6], 4, INK)


def draw_box(d, b):
    """兜底图形：礼盒/问号方块。"""
    x0, y0, x1, y1 = b
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    s = int(min(x1 - x0, y1 - y0) * 0.5)
    _rr(d, [cx - s // 2 + 6, cy - s // 2 + 10, cx + s // 2 + 6, cy + s // 2 + 10], 18, (198, 210, 232))
    _rr(d, [cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2], 18, INK)
    _rr(d, [cx - s // 2, cy - 22, cx + s // 2, cy + 22], 6, ACCENT)
    d.rectangle([cx - 14, cy - s // 2, cx + 14, cy + s // 2], fill=ACCENT)


# 关键词 → 绘制器（越靠前优先级越高）
KEYWORD_SHAPES = [
    (("手机", "iphone", "华为", "小米", "智能机"), draw_phone),
    (("充电宝", "电源", "移动电源"), draw_powerbank),
    (("耳机", "airpods"), draw_headphone),
    (("笔记本", "电脑", "macbook"), draw_laptop),
    (("平板", "ipad"), draw_laptop),
    (("保温杯", "水杯", "杯子", "水壶"), draw_cup),
    (("伞",), draw_umbrella),
    (("眼镜", "墨镜"), draw_glasses),
    (("钥匙",), draw_key),
    (("身份证", "学生证", "校园卡", "银行卡", "证件", "卡包"), draw_card),
    (("教材", "笔记", "书", "文具", "笔"), draw_book),
    (("书包", "行李箱", "背包", "箱"), draw_bag),
    (("外套", "围巾", "衣服", "帽"), draw_bag),
]

CATEGORY_SHAPES = {
    "证件卡包": draw_card,
    "电子设备": draw_phone,
    "书籍文具": draw_book,
    "衣物箱包": draw_bag,
    "钥匙": draw_key,
    "生活用品": draw_cup,
    "其他": draw_box,
}


def pick_shape(title: str, category_name: str):
    text = (title or "") + " " + (category_name or "")
    low = text.lower()
    for keys, fn in KEYWORD_SHAPES:
        if any(k in low for k in keys):
            return fn
    return CATEGORY_SHAPES.get(category_name or "", draw_box)


def draw_item_image(title: str, category_name: str, code: str, kind_label: str) -> "Image.Image":
    """绘制一张 800x600 的物品示意图。"""
    img = _gradient()
    d = ImageDraw.Draw(img)

    # 主体图形
    pick_shape(title, category_name)(d, (150, 60, 650, 470))

    # 左上角类型标签
    tag_font = _font(20, bold=True)
    tw = int(tag_font.getlength(kind_label)) if tag_font else 120
    _rr(d, [32, 28, 44 + tw + 24, 68], 20, WHITE)
    d.text((56, 38), kind_label, font=tag_font, fill=INK)

    # 底部信息条
    _rr(d, [40, 470, 760, 566], 18, WHITE)
    title_font = _font(30, bold=True)
    meta_font = _font(20)
    d.text((64, 486), _fit(title or "未命名物品", title_font, 620), font=title_font, fill=TEXT_DARK)
    meta = f"{category_name or '未分类'}  ·  单号 {code or '-'}"
    d.text((64, 528), _fit(meta, meta_font, 620), font=meta_font, fill=TEXT_MUTE)
    return img


def ensure_item_image(item, entity_type: str, force: bool = False) -> str | None:
    """为单条物品生成配图并回填（缺 Pillow 或已有图片时返回 None）。"""
    if not HAS_PIL:
        return None
    if not force and (item.image_list or []):
        return (item.image_list or [None])[0]

    from flask import current_app

    from app.extensions import db
    from app.models import Attachment

    title = item.title
    category_name = getattr(item.category, "name", None) if item.category_id else None
    kind_label = "拾获登记示意图" if entity_type == "found_item" else "寻物启事示意图"
    img = draw_item_image(title, category_name, item.code, kind_label)

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], entity_type)
    os.makedirs(folder, exist_ok=True)
    filename = f"demo_{item.code.replace('/', '-')}.png"
    path = os.path.join(folder, filename)
    img.save(path, format="PNG")

    with open(path, "rb") as f:
        raw = f.read()
    rel_url = f"/uploads/{entity_type}/{filename}"
    item.images = json.dumps([rel_url], ensure_ascii=False)

    uploader = getattr(item, "founder_id", None) or getattr(item, "owner_id", None)
    if not Attachment.query.filter_by(saved_name=filename).first():
        db.session.add(Attachment(
            entity_type=entity_type, entity_id=item.id, uploader_id=uploader,
            original_name=filename, saved_name=filename, rel_path=rel_url,
            mime="image/png", size=len(raw), checksum=hashlib.sha256(raw).hexdigest(),
        ))
    db.session.commit()
    return rel_url


def generate_for_all(force: bool = False, only: str | None = None) -> dict:
    """批量补图，返回统计。"""
    from app.models import FoundItem, LostItem

    stats = {"found": 0, "lost": 0, "skipped": 0}
    for entity_type, model, key in (("found_item", FoundItem, "found"), ("lost_item", LostItem, "lost")):
        if only and only != key:
            continue
        for item in model.query.all():
            url = ensure_item_image(item, entity_type, force=force)
            if url:
                stats[key] += 1
            else:
                stats["skipped"] += 1
    return stats


def main() -> int:
    import argparse

    import app as app_pkg

    parser = argparse.ArgumentParser(description="为招领/寻物信息生成演示配图")
    parser.add_argument("--force", action="store_true", help="已有图片也重新生成")
    parser.add_argument("--only", choices=["found", "lost"], help="只处理某一类")
    args = parser.parse_args()

    if not HAS_PIL:
        print("[跳过] 未安装 Pillow，无法生成配图：pip install Pillow")
        return 1

    application = app_pkg.create_app()
    with application.app_context():
        stats = generate_for_all(force=args.force, only=args.only)
        print(f"[完成] 招领配图 {stats['found']} 张，寻物配图 {stats['lost']} 张，跳过 {stats['skipped']} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
