"""图片上传与展示模块用例：multipart 上传、伪图片拦截、绑定与回显。"""
from __future__ import annotations

import io

import pytest

from conftest import found_payload, login, ADMIN_PWD, STAFF_PWD, STUDENT_PWD


def _png_bytes(color=(59, 111, 212), size=(4, 4)) -> bytes:
    """生成真实 PNG（魔数合法），不依赖 Pillow 也可用手工字节。"""
    try:
        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", size, color).save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # 1x1 白色最小 PNG（手工字节）
        import base64
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQAB"
            "h6FO1AAAAABJRU5ErkJggg=="
        )


def _login_staff(client, staff):
    login(client, staff.username, STAFF_PWD)


def test_upload_then_create_found_with_image(client, app, category, staff):
    """先传图拿 URL，再登记招领并绑定，列表/详情回显 image_list。"""
    _login_staff(client, staff)

    resp = client.post("/api/v1/upload", data={
        "file": (io.BytesIO(_png_bytes()), "phone.png"),
        "entity_type": "found_item",
    }, content_type="multipart/form-data")
    assert resp.status_code == 200
    url = resp.get_json()["data"]["url"]
    assert url.startswith("/uploads/found_item/")   # entity_type 会被用作存储子目录

    payload = found_payload(category)
    payload["happen_time"] = payload["happen_time"].strftime("%Y-%m-%dT%H:%M")  # 与前端 datepicker 一致
    payload["images"] = [url]
    resp = client.post("/api/v1/items/found", json=payload)
    assert resp.status_code == 200
    item_id = resp.get_json()["data"]["item"]["id"]

    resp = client.get(f"/api/v1/items/found/{item_id}")
    assert resp.get_json()["data"]["item"]["image_list"] == [url]


def test_create_found_with_direct_multipart_file(client, app, category, staff):
    """登记表单直接携带 images 文件：一次请求完成建档 + 存图 + 绑定。"""
    _login_staff(client, staff)
    raw = found_payload(category)
    raw["happen_time"] = raw["happen_time"].strftime("%Y-%m-%dT%H:%M")
    data = {k: str(v) for k, v in raw.items()}
    data["features"] = ",".join(found_payload(category)["features"])
    resp = client.post("/api/v1/items/found", data={
        **data,
        "images": (io.BytesIO(_png_bytes()), "backpack.jpg"),
    }, content_type="multipart/form-data")
    assert resp.status_code == 200
    image_list = resp.get_json()["data"]["item"]["image_list"]
    assert len(image_list) == 1 and "/uploads/found_item/" in image_list[0]

    # 文件真实落盘且可通过 /uploads 访问
    resp = client.get(image_list[0])
    assert resp.status_code == 200
    assert resp.data[:4] == b"\x89PNG" or resp.data[:3] == b"\xff\xd8\xff"


def test_fake_image_rejected(client, app, staff):
    """扩展名伪装成 png 的非图片内容被魔数校验拦截。"""
    _login_staff(client, staff)
    resp = client.post("/api/v1/upload", data={
        "file": (io.BytesIO(b"this is not an image at all"), "evil.png"),
        "entity_type": "found_item",
    }, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "不符" in resp.get_json()["msg"] or "不被允许" in resp.get_json()["msg"]


def test_upload_requires_login(client, app):
    """未登录不能上传文件。"""
    resp = client.post("/api/v1/upload", data={
        "file": (io.BytesIO(_png_bytes()), "x.png"),
    }, content_type="multipart/form-data")
    assert resp.status_code == 401


def test_demo_image_generator(app, category, staff):
    """演示配图生成器：回填 image_list 并写 t_attachment 留痕。"""
    from scripts.demo_images import HAS_PIL, ensure_item_image

    if not HAS_PIL:
        pytest.skip("未安装 Pillow")
    from app.extensions import db
    from app.models import Attachment
    from app.services import item_service

    item = item_service.create_found_item(found_payload(category), staff)
    assert item.image_list == []

    url = ensure_item_image(item, "found_item")
    assert url and url.startswith("/uploads/found_item/demo_")
    assert item.image_list == [url]

    att = Attachment.query.filter_by(entity_type="found_item", entity_id=item.id).first()
    assert att is not None and att.mime == "image/png" and att.size > 0

    # 已有图片时不重复生成
    assert ensure_item_image(item, "found_item") == url
