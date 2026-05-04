"""区块链存证模块（eth-tester 全 Python 实现）"""
import logging
from typing import Dict, Optional

from database.db_manager import default_db

logger = logging.getLogger(__name__)

# 惰性初始化区块链客户端
_w3 = None
_accounts = None


def _init_blockchain():
    """惰性初始化区块链连接"""
    global _w3, _accounts

    if _w3 is not None:
        return _w3, _accounts

    try:
        from web3 import Web3
        from eth_tester import EthereumTester, PyEVMBackend

        tester = EthereumTester(backend=PyEVMBackend())
        _w3 = Web3(Web3.EthereumTesterProvider(tester))
        _accounts = _w3.eth.accounts
    except ImportError as e:
        logger.error("区块链模块导入失败: %s", e)
        raise

    return _w3, _accounts


def get_chain_status() -> Dict:
    """获取区块链状态信息"""
    w3, accounts = _init_blockchain()

    return {
        "connected": w3.is_connected(),
        "block_number": w3.eth.block_number,
        "accounts_count": len(accounts),
        "chain_id": w3.eth.chain_id,
        "first_account": accounts[0] if accounts else None,
    }


def record_score_on_chain(score_hash: str, entity_id: str) -> str:
    """将评分哈希上链存证"""
    w3, accounts = _init_blockchain()

    if not accounts:
        raise ValueError("没有可用的测试账户")

    data = f"{entity_id}:{score_hash}"
    tx_hash = w3.eth.send_transaction({
        "from": accounts[0],
        "to": accounts[0],
        "data": w3.to_hex(text=data),
        "gas": 100000,
    })

    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def verify_on_chain(tx_hash: str, score_hash: str, entity_id: str) -> Dict:
    """从链上验证存证"""
    w3, accounts = _init_blockchain()

    try:
        tx = w3.eth.get_transaction(tx_hash)
        chain_data = w3.to_text(tx["input"])
        expected = f"{entity_id}:{score_hash}"

        return {
            "is_valid": chain_data == expected,
            "chain_data": chain_data,
            "expected_data": expected,
            "block_number": tx["blockNumber"],
            "from_address": tx["from"],
            "matched": chain_data == expected,
        }
    except Exception as e:
        return {"is_valid": False, "error": str(e)}


def get_transaction_details(tx_hash: str) -> Dict:
    """获取交易详细信息"""
    w3, accounts = _init_blockchain()

    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    return {
        "tx_hash": tx_hash,
        "block_number": tx["blockNumber"],
        "from": tx["from"],
        "to": tx["to"],
        "gas_used": receipt["gasUsed"],
        "status": receipt["status"],
        "data": w3.to_text(tx["input"]),
    }


def save_blockchain_record(entity_id: str, score_hash: str, tx_hash: str, block_number: int):
    """保存区块链存证记录到数据库"""
    default_db.execute(
        """INSERT INTO blockchain_records (
            entity_id, score_hash, tx_hash, block_number, on_chain_time, verified
        ) VALUES (?, ?, ?, ?, datetime('now'), 0)""",
        (entity_id, score_hash, tx_hash, block_number),
    )


def get_blockchain_records() -> list:
    """获取所有区块链存证记录"""
    rows = default_db.fetchall(
        """SELECT entity_id, score_hash, tx_hash, block_number, on_chain_time, verified
           FROM blockchain_records"""
    )
    return [
        {
            "entity_id": r[0],
            "score_hash": r[1],
            "tx_hash": r[2],
            "block_number": r[3],
            "on_chain_time": r[4],
            "verified": bool(r[5]),
        }
        for r in rows
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== 区块链存证测试 ===")

    status = get_chain_status()
    print(f"链状态: {status}")

    test_hash = "abc123def456"
    test_entity = "C001"
    tx_hash = record_score_on_chain(test_hash, test_entity)
    print(f"交易哈希: {tx_hash}")

    result = verify_on_chain(tx_hash, test_hash, test_entity)
    print(f"验证结果: {result}")

    details = get_transaction_details(tx_hash)
    print(f"交易详情: {details}")

    fake = verify_on_chain(tx_hash, "fake_hash_000", test_entity)
    print(f"篡改检测: {fake}")
