"""匹配推荐：六因子加权相似度算法。

    score = Σ(w_i × f_i) / Σ(w_i)     权重可在 .env 或后台系统参数中调整

| 因子 | 权重 | 计算方式 |
|------|------|----------|
| category 类别 | 0.25 | 同分类 1.0；同父级二级分类 0.6；不同 0 |
| keyword 关键词 | 0.20 | 标题+关键词分词集合 Jaccard |
| location 地点 | 0.15 | 同分区 1.0；邻接分区 0.5；不同 0.1；地点原文互含 +0.1 |
| time 时间 | 0.15 | exp(-Δdays/7) 指数衰减；拾获早于遗失超 1 天判 0.1 |
| feature 特征 | 0.15 | 特征标签集合 Jaccard |
| text 文本 | 0.10 | 描述词频余弦相似度 |

设计要点：因子可解释（明细写入 detail）；阈值过滤；幂等（唯一约束，重复跑只更新分数）。
"""
from __future__ import annotations

import json
import math

from flask import current_app

from app.models import FoundItem, LostItem, MatchRecord, SystemSetting
from app.repositories import FoundItemRepository, LostItemRepository, MatchRepository
from app.utils import cosine_text, jaccard, tokenize


# ---------------------------------------------------------------- 单因子


def factor_category(found: FoundItem, lost: LostItem) -> float:
    if found.category_id and found.category_id == lost.category_id:
        return 1.0
    fc, lc = found.category, lost.category
    if not fc or not lc:
        return 0.0
    if fc.parent_id and fc.parent_id == lc.parent_id:
        return 0.6
    if (fc.parent_id or fc.id) == (lc.parent_id or lc.id):
        return 0.6
    return 0.0


def factor_keyword(found: FoundItem, lost: LostItem) -> float:
    a = set(tokenize(f"{found.title} {found.keywords or ''}"))
    b = set(tokenize(f"{lost.title} {lost.keywords or ''}"))
    return jaccard(a, b)


def factor_location(found: FoundItem, lost: LostItem) -> float:
    adjacency = current_app.config["ZONE_ADJACENCY"]
    za, zb = found.found_zone, lost.lost_zone
    base = 0.1
    if za and za == zb:
        base = 1.0
    elif za and zb and zb in adjacency.get(za, []):
        base = 0.5
    pa, pb = (found.found_place or ""), (lost.lost_place or "")
    if pa and pb and (pa in pb or pb in pa):
        base = min(1.0, base + 0.1)
    return base


def factor_time(found: FoundItem, lost: LostItem) -> float:
    if not found.found_time or not lost.lost_time:
        return 0.0
    delta_days = (found.found_time - lost.lost_time).total_seconds() / 86400.0
    if delta_days < -1:      # 拾获早于遗失：不合理
        return 0.1
    decay = current_app.config["MATCH_TIME_DECAY_DAYS"]
    return round(math.exp(-abs(delta_days) / decay), 4)


def factor_feature(found: FoundItem, lost: LostItem) -> float:
    a = {str(x).strip() for x in found.feature_list}
    b = {str(x).strip() for x in lost.feature_list}
    return jaccard(a, b)


def factor_text(found: FoundItem, lost: LostItem) -> float:
    return round(cosine_text(found.description, lost.description), 4)


FACTORS = {
    "category": factor_category,
    "keyword": factor_keyword,
    "location": factor_location,
    "time": factor_time,
    "feature": factor_feature,
    "text": factor_text,
}


# ---------------------------------------------------------------- 综合评分


def load_weights() -> dict:
    """权重优先级：后台 SystemSetting > 配置文件。"""
    weights = dict(current_app.config["MATCH_WEIGHTS"])
    try:
        row = SystemSetting.query.filter_by(key="match_weights").first()
        if row and row.value:
            weights.update(json.loads(row.value))
    except Exception:
        pass
    return weights


def compute_score(found: FoundItem, lost: LostItem, weights: dict | None = None) -> tuple[float, dict]:
    weights = weights or load_weights()
    parts = {name: round(fn(found, lost), 4) for name, fn in FACTORS.items()}
    total_w = sum(weights.get(k, 0.0) for k in parts) or 1.0
    score = sum(weights.get(k, 0.0) * v for k, v in parts.items()) / total_w
    detail = {
        "factors": parts,
        "weights": {k: weights.get(k, 0.0) for k in parts},
        "total": round(score, 4),
    }
    return round(score, 4), detail


def level_of(score: float) -> str:
    if score >= 0.75:
        return "high"
    return "medium" if score >= current_app.config["MATCH_THRESHOLD"] else "low"


def score_pair(found: FoundItem, lost: LostItem, persist: bool = True):
    score, detail = compute_score(found, lost)
    rec = MatchRepository.upsert(found.id, lost.id, score, detail, level_of(score)) if persist else None
    return score, detail, rec


# ---------------------------------------------------------------- 推荐入口


def recommend_for_lost(lost_id: int, limit: int = 10, min_score: float | None = None) -> list[dict]:
    """为一条寻物启事推荐候选拾获物品。"""
    lost = LostItem.query.get_or_404(lost_id)
    threshold = current_app.config["MATCH_THRESHOLD"] if min_score is None else min_score
    results = []
    for found in FoundItemRepository.candidates_for_matching():
        score, detail, rec = score_pair(found, lost)
        if score >= threshold:
            results.append({"found_item": found, "score": score, "detail": detail, "record": rec})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def recommend_for_found(found_id: int, limit: int = 10, min_score: float | None = None) -> list[dict]:
    """为一条拾获登记推荐可能的失主。"""
    found = FoundItem.query.get_or_404(found_id)
    threshold = current_app.config["MATCH_THRESHOLD"] if min_score is None else min_score
    results = []
    for lost in LostItemRepository.candidates_for_matching():
        score, detail, rec = score_pair(found, lost)
        if score >= threshold:
            results.append({"lost_item": lost, "score": score, "detail": detail, "record": rec})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def run_full_matching(push_notify: bool = True) -> dict:
    """全量重算（可挂定时任务或后台按钮）。"""
    from app.services import notify_service

    founds = FoundItemRepository.candidates_for_matching()
    losts = LostItemRepository.candidates_for_matching()
    threshold = current_app.config["MATCH_THRESHOLD"]
    weights = load_weights()

    created = updated = notified = 0
    for lost in losts:
        for found in founds:
            score, detail = compute_score(found, lost, weights)
            if score < threshold:
                continue
            existed = MatchRepository.pair(found.id, lost.id)
            MatchRepository.upsert(found.id, lost.id, score, detail, level_of(score))
            if existed:
                updated += 1
            else:
                created += 1
                if push_notify:
                    notify_service.notify_match(found, lost, score)
                    notified += 1
    current_app.logger.info("全量匹配完成：新增 %s，更新 %s，通知 %s", created, updated, notified)
    return {"created": created, "updated": updated, "notified": notified,
            "pairs": len(founds) * len(losts)}


def explain(match_record: MatchRecord) -> list[dict]:
    """把明细翻译成人话，供前端展示"推荐理由"。"""
    labels = {
        "category": "类别一致", "keyword": "关键词重合", "location": "地点邻近",
        "time": "时间接近", "feature": "特征相符", "text": "描述相似",
    }
    d = match_record.detail_dict()
    factors, weights = d.get("factors", {}), d.get("weights", {})
    return [
        {
            "name": labels.get(k, k),
            "factor": factors.get(k, 0),
            "weight": weights.get(k, 0),
            "contribution": round(factors.get(k, 0) * weights.get(k, 0), 4),
        }
        for k in FACTORS
    ]
