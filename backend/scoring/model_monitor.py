"""模型监控模块 — KS/AUC/PSI/Spearman 计算"""
import math
from typing import List, Dict


def calculate_ks(scores: List[float], labels: List[int]) -> float:
    """计算 KS 值"""
    if not scores or not labels:
        return 0.0
    paired = sorted(zip(scores, labels), key=lambda x: x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0
    ks = 0.0
    cum_pos, cum_neg = 0, 0
    for _, label in paired:
        if label == 1:
            cum_pos += 1
        else:
            cum_neg += 1
        tpr = cum_pos / n_pos
        fpr = cum_neg / n_neg
        ks = max(ks, abs(tpr - fpr))
    return round(ks, 4)


def calculate_auc(scores: List[float], labels: List[int]) -> float:
    """计算 AUC（梯形法近似）"""
    if not scores or not labels:
        return 0.0
    paired = sorted(zip(scores, labels), key=lambda x: x[0], reverse=True)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0
    auc = 0.0
    tp = 0
    fp = 0
    prev_tp = 0
    prev_fp = 0
    prev_score = None
    for score, label in paired:
        if prev_score is not None and score != prev_score:
            auc += abs(fp - prev_fp) * (tp + prev_tp) / 2
            prev_tp = tp
            prev_fp = fp
        if label == 1:
            tp += 1
        else:
            fp += 1
        prev_score = score
    auc += abs(fp - prev_fp) * (tp + prev_tp) / 2
    auc /= (n_pos * n_neg)
    return round(auc, 4)


def calculate_psi(scores_old: List[float], scores_new: List[float], buckets: int = 10) -> float:
    """计算 Population Stability Index"""
    if not scores_old or not scores_new:
        return 0.0
    n_old = len(scores_old)
    n_new = len(scores_new)
    all_scores = scores_old + scores_new
    min_s, max_s = min(all_scores), max(all_scores)
    if max_s == min_s:
        return 0.0
    psi = 0.0
    for i in range(buckets):
        low = min_s + (max_s - min_s) * i / buckets
        high = min_s + (max_s - min_s) * (i + 1) / buckets
        if i == buckets - 1:
            high = max_s + 0.001
        old_pct = sum(1 for s in scores_old if low <= s < high) / n_old
        new_pct = sum(1 for s in scores_new if low <= s < high) / n_new
        old_pct = max(old_pct, 0.0001)
        new_pct = max(new_pct, 0.0001)
        psi += (new_pct - old_pct) * math.log(new_pct / old_pct)
    return round(psi, 4)


def calculate_spearman(scores1: List[float], scores2: List[float]) -> float:
    """计算 Spearman 秩相关系数"""
    if len(scores1) != len(scores2) or len(scores1) < 3:
        return 0.0

    def rank(data):
        sorted_idx = sorted(range(len(data)), key=lambda i: data[i])
        ranks = [0] * len(data)
        i = 0
        while i < len(data):
            j = i
            while j < len(data) and data[sorted_idx[j]] == data[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j + 1) / 2
            for k in range(i, j):
                ranks[sorted_idx[k]] = avg_rank
            i = j
        return ranks

    rank1 = rank(scores1)
    rank2 = rank(scores2)
    n = len(scores1)
    d_sq = sum((r1 - r2) ** 2 for r1, r2 in zip(rank1, rank2))
    rho = 1 - 6 * d_sq / (n * (n * n - 1))
    return round(rho, 4)


def generate_model_performance_snapshot(
    champion_scores: List[float],
    challenger_scores: List[float],
    labels: List[int],
    period: str,
) -> Dict:
    """生成双模型性能快照"""
    return {
        "period": period,
        "champion": {
            "ks": calculate_ks(champion_scores, labels),
            "auc": calculate_auc(champion_scores, labels),
            "psi": 0.0,  # PSI 需要与上一期对比
            "mean_score": round(sum(champion_scores) / len(champion_scores), 2) if champion_scores else 0,
        },
        "challenger": {
            "ks": calculate_ks(challenger_scores, labels),
            "auc": calculate_auc(challenger_scores, labels),
            "psi": 0.0,
            "mean_score": round(sum(challenger_scores) / len(challenger_scores), 2) if challenger_scores else 0,
        },
        "spearman": calculate_spearman(champion_scores, challenger_scores),
    }
