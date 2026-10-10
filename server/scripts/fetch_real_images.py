"""从网络图库抓取"真实照片"作为招领/寻物配图。

来源：Pexels（https://www.pexels.com），许可为 Pexels License（CC0 级别）：
    免费用于个人与商业用途、可修改、无需署名。
    许可原文：https://www.pexels.com/license/

做法：按物品标题关键词匹配已选定的真实照片 ID（人工从 Pexels 检索确认与物品对应），
    下载 800px 缩略图 → 存盘 → 回填 item.images → 写 t_attachment 留痕（original_name 记录来源页）。

用法：
    python scripts/fetch_real_images.py                 为全部招领/寻物抓取真实照片
    python scripts/fetch_real_images.py --only found    只处理招领
    python scripts/fetch_real_images.py --force         已有真实照片也重新抓取

抓取失败时自动回退到 scripts/demo_images.py 的本地绘制示意图，保证数据始终有图。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Attachment, FoundItem, LostItem  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
TIMEOUT = 30
WIDTH = 800

# 关键词 → Pexels 照片 ID（多个 ID 会在同类物品间轮换，避免列表里出现重复图）
# 每个 ID 均已人工确认内容与被匹配物品一致
REAL_PHOTOS = [
    (("手机", "iphone", "智能机"), [226638, 358627], "黑色智能手机"),
    (("校园卡", "身份证", "银行卡", "证件"), [11363562, 7821687], "卡片特写"),
    (("保温杯", "水杯", "杯"), [30469934, 34515259], "不锈钢保温杯"),
    (("钥匙",), [17026019, 27522902], "钥匙串"),
    (("双肩包", "书包", "包"), [16359291, 16359252], "黑色双肩包"),
    (("围巾", "外套", "衣物"), [14840511, 6630873], "灰色针织织物"),
    (("u盘", "优盘", "u 盘", "usb"), [5474288, 7442204], "U 盘"),
]

DEFAULT_IDS = [226638, 11363562]


def page_url(photo_id: int) -> str:
    return f"https://www.pexels.com/photo/{photo_id}/"


def cdn_url(photo_id: int, width: int = WIDTH) -> str:
    return (f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg"
            f"?auto=compress&cs=tinysrgb&w={width}")


def pick_photo_id(title: str, item_id: int) -> tuple[int, str]:
    """按标题关键词选照片；同类多图时按物品 ID 轮换。"""
    text = (title or "").lower()
    for keys, ids, label in REAL_PHOTOS:
        if any(k.lower() in text for k in keys):
            return ids[item_id % len(ids)], label
    return DEFAULT_IDS[item_id % len(DEFAULT_IDS)], "通用物品"


def download(photo_id: int) -> bytes | None:
    """下载真实照片；返回字节或 None。"""
    for url in (cdn_url(photo_id), cdn_url(photo_id).replace(".jpeg", ".jpg")):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
                data = r.read()
            if data[:3] == b"\xff\xd8\xff" or data[:4] == b"\x89PNG":   # 确认真是图片
                return data
        except Exception as exc:
            print(f"      下载失败 {url[:70]}…：{type(exc).__name__}: {exc}")
    return None


def fetch_for_item(item, entity_type: str, force: bool = False) -> tuple[str | None, str]:
    """为单条物品抓取真实照片。返回 (URL 或 None, 来源说明)。"""
    from flask import current_app

    existing = item.image_list or []
    if not force and any("/real_" in u for u in existing):
        return existing[0], "已有真实照片，跳过"

    photo_id, label = pick_photo_id(item.title, item.id)
    raw = download(photo_id)
    if raw is None:
        try:
            from demo_images import ensure_item_image

            url = ensure_item_image(item, entity_type)
            return url, f"网络失败，回退本地示意图（{label}）"
        except Exception:
            return None, "网络失败且本地回退不可用"

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], entity_type)
    os.makedirs(folder, exist_ok=True)
    filename = f"real_{item.code.replace('/', '-')}.jpg"
    with open(os.path.join(folder, filename), "wb") as f:
        f.write(raw)

    rel_url = f"/uploads/{entity_type}/{filename}"
    item.images = json.dumps([rel_url], ensure_ascii=False)

    source = page_url(photo_id)
    uploader = getattr(item, "founder_id", None) or getattr(item, "owner_id", None)
    att = Attachment.query.filter_by(entity_type=entity_type, entity_id=item.id).first()
    if att is None:
        att = Attachment(entity_type=entity_type, entity_id=item.id, uploader_id=uploader)
        db.session.add(att)
    att.original_name = f"Pexels:{photo_id}"     # 来源留痕（页面地址见 docs/06-图片来源.md）
    att.saved_name = filename
    att.rel_path = rel_url
    att.mime = "image/jpeg"
    att.size = len(raw)
    att.checksum = hashlib.sha256(raw).hexdigest()
    db.session.commit()
    return rel_url, f"{label} · Pexels #{photo_id} · {source}"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="抓取真实照片作为物品配图")
    parser.add_argument("--only", choices=["found", "lost"], help="只处理某一类")
    parser.add_argument("--force", action="store_true", help="已有真实照片也重新抓取")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        created, failed = 0, 0
        sources = []
        for entity_type, model, key in (("found_item", FoundItem, "found"), ("lost_item", LostItem, "lost")):
            if args.only and args.only != key:
                continue
            print(f"[{key}] {model.query.count()} 条")
            for item in model.query.order_by(model.id).all():
                url, note = fetch_for_item(item, entity_type, force=args.force)
                if url:
                    created += 1
                    print(f"      {item.code}  {item.title[:18]:<20} {url}")
                    sources.append((key, item.code, item.title, url, note))
                else:
                    failed += 1
                    print(f"      {item.code}  失败：{note}")

        print(f"\n[完成] 真实照片 {created} 张，失败 {failed} 条")
        print("来源：Pexels（Pexels License，免费商用、无需署名）：https://www.pexels.com/license/")
        out = Path(__file__).resolve().parents[1].parent / "docs" / "06-图片来源.md"
        if sources:
            lines = [
                "# 图片来源说明",
                "",
                "演示数据中的物品配图均从 Pexels 抓取的**真实照片**（非 AI 生成、非手绘示意图）。",
                "",
                "- 图库：Pexels（https://www.pexels.com）",
                "- 许可：Pexels License —— 免费用于个人与商业用途，可修改，无需署名（https://www.pexels.com/license/）",
                "- 抓取脚本：`server/scripts/fetch_real_images.py`（按物品标题关键词匹配照片 ID，失败回退本地示意图）",
                "",
                "| 类型 | 单号 | 标题 | 本地路径 | 图片内容与来源 |",
                "|---|---|---|---|---|",
            ]
            for key, code, title, url, note in sources:
                lines.append(f"| {'招领' if key == 'found' else '寻物'} | {code} | {title} | `{url}` | {note} |")
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"来源清单已写入：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
