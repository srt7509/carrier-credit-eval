"""数字签名模块（HMAC-SHA256）"""
import hashlib
import hmac
import json
from typing import Dict

from settings import SECRET_KEY


def generate_signature(score_record: Dict) -> str:
    """生成评分记录数字签名（HMAC-SHA256）

    Args:
        score_record: 评分记录字典，包含 entity_id, score_value, grade 等字段

    Returns:
        HMAC-SHA256 签名字符串
    """
    payload = {
        "entity_id": score_record["entity_id"],
        "score_value": score_record["score_value"],
        "grade": score_record["grade"],
    }
    payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hmac.new(SECRET_KEY.encode(), payload_bytes, hashlib.sha256).hexdigest()


def verify_signature(score_record: Dict, signature: str) -> bool:
    """校验签名是否有效"""
    expected = generate_signature(score_record)
    # 使用 hmac.compare_digest 防时序攻击
    return hmac.compare_digest(expected, signature)


def generate_score_hash(score_record: Dict) -> str:
    """生成评分记录哈希（用于区块链存证，不含密钥）"""
    payload = {
        "entity_id": score_record["entity_id"],
        "score_value": score_record["score_value"],
        "grade": score_record["grade"],
        "dimension_scores": score_record.get("dimension_scores", {}),
    }
    payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload_bytes).hexdigest()


if __name__ == "__main__":
    # 测试签名功能
    test_score = {
        "entity_id": "C001",
        "score_value": 85.5,
        "grade": "AA",
        "dimension_scores": {"履约能力": 25.0, "合规记录": 18.0},
    }

    sig = generate_signature(test_score)
    print(f"签名: {sig}")

    is_valid = verify_signature(test_score, sig)
    print(f"验证结果: {is_valid}")  # True

    tampered_score = test_score.copy()
    tampered_score["score_value"] = 90.0
    is_tampered = verify_signature(tampered_score, sig)
    print(f"篡改检测结果: {is_tampered}")  # False

    hash_val = generate_score_hash(test_score)
    print(f"哈希: {hash_val}")
