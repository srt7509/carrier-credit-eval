"""数据表模型定义"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Shipper:
    """货主数据模型"""
    shipper_id: str
    name: str
    shipper_type: str  # 企业/个人
    total_orders: int
    completed_orders: int
    on_time_payment_rate: float
    overdue_count: int
    overdue_amount: float
    avg_order_value: float
    complaint_count: int
    cooperation_months: int
    credit_trend_score: float = 80.0


@dataclass
class Carrier:
    """承运商企业数据模型（不再作为评价对象）"""
    carrier_id: str
    name: str
    unified_credit_code: str = ""
    cooperation_start_date: str = ""
    cooperation_mode: str = "长期协议"  # 长期协议 / 临时竞价
    fleet_size: int = 0  # 实际车辆数
    qualification: str = "全资质"  # 全资质 / 单一-普货 / 单一-危化品


@dataclass
class Vehicle:
    """车辆数据模型（评价对象）"""
    vehicle_id: str
    carrier_id: str  # FK -> Carrier
    license_plate: str  # 牌照号
    driver_name: str  # 司机姓名
    transport_category: str = "普货"  # 普货 / 危化品-易燃液体 / 危化品-气体 / 危化品-剧毒品
    total_orders: int = 0
    completed_orders: int = 0
    on_time_orders: int = 0
    complaint_count: int = 0
    accident_count: int = 0
    violation_count: int = 0
    license_valid: bool = True
    on_time_payment_rate: float = 0.0
    overdue_amount: float = 0.0
    avg_customer_rating: float = 0.0
    damage_rate: float = 0.0
    cooperation_months: int = 0
    credit_trend_score: float = 80.0
    recent_3m_orders: int = 0
    risk_label: str = "正常"


@dataclass
class CreditScore:
    """信用评分结果模型"""
    entity_id: str
    entity_type: str  # vehicle/shipper
    score_value: float
    grade: str
    dimension_scores: dict = field(default_factory=dict)
    risk_flags: list = field(default_factory=list)
    signature: Optional[str] = None
    tx_hash: Optional[str] = None
    eval_period: str = ""
    eval_time: datetime = field(default_factory=datetime.now)
    is_current: bool = True
    model_version: str = ""  # 评分模型版本
    eval_mode: str = "普运"  # 评价模式: 普运 / 危化品

    def to_dict(self):
        import json
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "score_value": self.score_value,
            "grade": self.grade,
            "dimension_scores": json.dumps(self.dimension_scores),
            "risk_flags": json.dumps(self.risk_flags),
            "signature": self.signature,
            "tx_hash": self.tx_hash,
            "eval_period": self.eval_period,
            "eval_time": self.eval_time.isoformat(),
            "is_current": self.is_current,
            "model_version": self.model_version,
            "eval_mode": self.eval_mode,
        }


@dataclass
class BlockchainRecord:
    """区块链存证记录模型"""
    entity_id: str
    score_hash: str
    tx_hash: str
    block_number: int
    on_chain_time: datetime = field(default_factory=datetime.now)
    verified: bool = False


@dataclass
class ScoreEvent:
    """评分事件模型（扣分/加分）"""
    entity_id: str
    event_type: str  # deduction / addition / one_vote_veto
    event_desc: str
    score_change: float
    event_time: datetime = field(default_factory=datetime.now)
    category: str = ""  # 事件分类


@dataclass
class AlertRecord:
    """预警记录模型"""
    entity_id: str
    entity_name: str
    alert_type: str  # 评分快速下滑 / 一票否决触发 / 许可证即将过期 / 连续多单投诉
    severity: str  # 高 / 中 / 低
    trigger_time: datetime = field(default_factory=datetime.now)
    current_score: float = 0.0
    status: str = "未处理"  # 未处理 / 处理中 / 已处理
    handler_note: str = ""


@dataclass
class ModelPerformance:
    """模型性能指标"""
    period: str  # 评估周期 YYYY-MM
    model_version: str  # champion / challenger
    ks: float
    auc: float
    psi: float
    spearman: Optional[float] = None  # 仅双模型对比时有值
    epv_satisfied: Optional[bool] = None
    record_time: datetime = field(default_factory=datetime.now)


@dataclass
class ModelRegistry:
    """模型注册信息"""
    model_version: str  # v1.0 / v2.0 等
    model_role: str  # champion / challenger / archived
    online_date: str
    update_cycle: str = "月度"  # 月度
    dimension_count: int = 5
    status: str = "运行中"  # 运行中 / 影子运行中 / 达标待切换 / 已切换 / 已归档
    consecutive_pass_months: int = 0  # 连续达标月数


@dataclass
class BusinessRule:
    """业务联动规则"""
    rule_type: str  # access_threshold / dispatch_priority / margin_ratio / financial_service / one_vote_veto / alert_threshold
    rule_key: str  # 规则键
    rule_value: str  # JSON 格式的值
    description: str = ""
    is_active: bool = True
    updated_at: datetime = field(default_factory=datetime.now)
