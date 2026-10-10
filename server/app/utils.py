"""通用工具：脱敏、上传校验、分词与相似度、密码强度、IP、分页。"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import unicodedata
from datetime import datetime

from flask import current_app, has_request_context, request
from werkzeug.utils import secure_filename

# ============================ 1. 敏感信息脱敏 ============================


def desensitize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    p = str(phone).strip()
    return f"{p[:3]}****{p[-4:]}" if len(p) >= 7 else p[:1] + "*" * (len(p) - 1)


def desensitize_email(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    if len(name) <= 1:
        shown = name
    elif len(name) == 2:
        shown = name[0] + "*"
    else:
        shown = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{shown}@{domain}"


def desensitize_name(name: str | None) -> str:
    if not name:
        return ""
    n = str(name).strip()
    if len(n) <= 1:
        return n
    if len(n) == 2:
        return n[0] + "*"
    return n[0] + "*" * (len(n) - 2) + n[-1]


def desensitize_student_no(no: str | None) -> str:
    if not no:
        return ""
    s = str(no).strip()
    return "*" * len(s) if len(s) <= 4 else f"{s[:2]}{'*' * (len(s) - 4)}{s[-2:]}"


def mask_long_digits(text: str | None) -> str:
    """遮蔽正文中的长数字串（身份证号、银行卡号等）。"""
    if not text:
        return ""
    return re.sub(
        r"\d{12,19}",
        lambda m: m.group(0)[:4] + "*" * (len(m.group(0)) - 8) + m.group(0)[-4:],
        text,
    )


# ============================ 2. 上传文件校验 ============================


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_IMAGE_EXT"]


def sniff_image_magic(stream) -> bool:
    """按文件头魔数校验真实类型，防止仅改扩展名绕过。"""
    magic = current_app.config["IMAGE_MAGIC"]
    head = stream.read(16)
    stream.seek(0)
    if not head:
        return False
    if head.startswith(magic["png"]) or head.startswith(magic["gif"]) or head.startswith(magic["jpg"]):
        return True
    return head.startswith(b"RIFF") and head[8:12] == b"WEBP"


def save_upload(file_storage, subdir: str = "") -> tuple[str, str, int, str]:
    """保存上传文件，返回 (对外URL, 原始文件名, 字节大小, sha256)。

    安全策略：扩展名白名单 + 魔数校验 + secure_filename + 随机重命名 + 大小限制。
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("未选择文件")
    filename = file_storage.filename
    if not allowed_file(filename):
        raise ValueError("文件类型不被允许（仅支持 png/jpg/jpeg/gif/webp）")
    if not sniff_image_magic(file_storage.stream):
        raise ValueError("文件内容与图片格式不符，已拒绝")

    ext = filename.rsplit(".", 1)[1].lower()
    safe_base = secure_filename(unicodedata.normalize("NFKD", filename).rsplit(".", 1)[0])[:40] or "img"
    new_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}_{safe_base}.{ext}"

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(folder, exist_ok=True)
    data = file_storage.stream.read()
    if len(data) > current_app.config["MAX_CONTENT_LENGTH"]:
        raise ValueError("文件体积超过限制")
    with open(os.path.join(folder, new_name), "wb") as f:
        f.write(data)

    rel_url = f"/uploads/{subdir}/{new_name}".replace("//", "/").replace("\\", "/")
    return rel_url, filename, len(data), hashlib.sha256(data).hexdigest()


# ============================ 3. 分词与相似度 ============================

STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很",
    "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "个", "吗", "吧",
    "a", "an", "the", "is", "are", "was", "were", "and", "or", "of", "to", "in", "on", "for",
}

TOKEN_RE = re.compile(r"[\u4e00-\u9fa5a-zA-Z0-9]+")


def tokenize(text: str | None) -> list[str]:
    """中文按 2-gram 切分、英文数字按词切分，不依赖 jieba，离线可跑。"""
    if not text:
        return []
    tokens: list[str] = []
    for seg in TOKEN_RE.findall(text.lower()):
        if re.match(r"^[a-z0-9]+$", seg):
            tokens.append(seg)
        elif len(seg) == 1:
            tokens.append(seg)
        else:
            tokens.extend(seg[i:i + 2] for i in range(len(seg) - 1))
    return [t for t in tokens if t and t not in STOPWORDS]


def build_keywords(*parts: str | None, limit: int = 30) -> str:
    seen, ordered = set(), []
    for p in parts:
        for t in tokenize(p):
            if t not in seen:
                seen.add(t)
                ordered.append(t)
    return " ".join(ordered[:limit])


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _freq_vector(text: str | None) -> dict[str, float]:
    vec: dict[str, float] = {}
    for t in tokenize(text):
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec


def cosine_text(a: str | None, b: str | None) -> float:
    va, vb = _freq_vector(a), _freq_vector(b)
    if not va or not vb:
        return 0.0
    dot = sum(va[k] * vb[k] for k in set(va) & set(vb))
    na = sum(v * v for v in va.values()) ** 0.5
    nb = sum(v * v for v in vb.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# ============================ 4. 校园分区归一化 ============================


def normalize_zone(place: str | None) -> str | None:
    if not place:
        return None
    for zone, keywords in current_app.config["CAMPUS_ZONES"].items():
        for kw in keywords:
            if kw in place:
                return zone
    return "其他"


# ============================ 5. 其它 ============================


def check_password_strength(pwd: str) -> tuple[bool, str]:
    if len(pwd) < current_app.config["PASSWORD_MIN_LEN"]:
        return False, f"密码长度至少 {current_app.config['PASSWORD_MIN_LEN']} 位"
    score = sum([
        bool(re.search(r"[a-z]", pwd)),
        bool(re.search(r"[A-Z]", pwd)),
        bool(re.search(r"\d", pwd)),
        bool(re.search(r"[^A-Za-z0-9]", pwd)),
    ])
    if score < 2:
        return False, "密码需至少包含字母、数字、符号中的两类"
    if re.search(r"(.)\1{3,}", pwd):
        return False, "密码不得包含 4 位以上连续重复字符"
    return True, ""


def client_ip() -> str:
    """校园网常有反向代理，优先取 X-Forwarded-For 首段。"""
    if not has_request_context():
        return "unknown"
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else (request.remote_addr or "unknown")


def generate_code(prefix: str, seq: int, year: int | None = None) -> str:
    """生成业务单号：LF-2026-0001 / XS-2026-0003 / RQ-2026-0012。"""
    return f"{prefix}-{year or datetime.now().year}-{seq:04d}"


def paginate(query, page: int = 1, per_page: int | None = None):
    """统一分页：页码非法回退首页，error_out=False 避免越界 404。"""
    per = per_page or current_app.config["ITEMS_PER_PAGE"]
    try:
        page = max(int(page), 1)
    except (TypeError, ValueError):
        page = 1
    return query.paginate(page=page, per_page=per, error_out=False)
