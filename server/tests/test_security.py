"""安全措施用例：脱敏、上传校验、敏感信息保护、日志落点（4 条）。"""
from __future__ import annotations

import io

from app.services import item_service
from app.utils import (
    desensitize_email,
    desensitize_name,
    desensitize_phone,
    desensitize_student_no,
    mask_long_digits,
)
from conftest import found_payload


def test_desensitize_functions():
    assert desensitize_phone("13812345678") == "138****5678"
    assert desensitize_email("zhangsan@campus.edu.cn").endswith("@campus.edu.cn")
    assert "*" in desensitize_email("zhangsan@campus.edu.cn").split("@")[0]
    assert desensitize_name("张三丰") == "张*丰"
    assert "*" in desensitize_student_no("2022010101")
    assert "****" in mask_long_digits("身份证 110101199001011234")


def test_upload_rejects_fake_image(client, login_as, student):
    """扩展名伪装成 png 但内容是文本，应被魔数校验拒绝。"""
    login_as(student)
    resp = client.post(
        "/api/v1/upload",
        data={"file": (io.BytesIO(b"this is definitely not an image"), "evil.png")},
        content_type="multipart/form-data",
    )
    assert resp.get_json()["code"] != 0


def test_sensitive_item_masked_for_others(client, login_as, app, category, staff, student2):
    sensitive = item_service.create_found_item(
        found_payload(category, title="捡到校园卡一张", is_sensitive=True,
                      description="身份证号 110101199001011234，姓名张三"), staff)
    login_as(student2)
    resp = client.get(f"/api/v1/items/found/{sensitive.id}")
    item = resp.get_json()["data"]["item"]
    assert "110101199001011234" not in item["description"]
    assert "敏感" in item["description"]


def test_operation_log_written(app, category, staff):
    from app.repositories import LogRepository

    item = item_service.create_found_item(found_payload(category), staff)
    logs = LogRepository.trace("found_item", item.id)
    assert any(log.action == "found_item_create" for log in logs)
