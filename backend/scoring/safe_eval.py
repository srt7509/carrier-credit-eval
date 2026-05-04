"""安全表达式求值器（基于 AST，替代 eval）"""
import ast
import operator
from typing import Any, Dict


class SafeEvalError(ValueError):
    """表达式求值异常"""


class SafeEvaluator:
    """AST 解析式安全求值器，仅允许算术运算和 max/min 函数"""

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }

    _ALLOWED_FUNCS = {"max": max, "min": min}

    def __init__(self, variables: Dict[str, Any]):
        self._vars = variables

    def evaluate(self, expr: str) -> float:
        try:
            tree = ast.parse(expr.strip(), mode="eval")
        except SyntaxError as e:
            raise SafeEvalError(f"表达式语法错误: {expr} - {e}")
        return self._eval_node(tree.body)

    def _eval_node(self, node) -> float:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise SafeEvalError(f"不支持的常量类型: {type(node.value).__name__}")

        if isinstance(node, ast.Name):
            val = self._vars.get(node.id)
            if val is None:
                raise SafeEvalError(f"未知变量: {node.id}")
            return float(val)

        if isinstance(node, ast.BinOp):
            op = self._OPERATORS.get(type(node.op))
            if op is None:
                raise SafeEvalError(f"不支持的运算符: {type(node.op).__name__}")
            return op(self._eval_node(node.left), self._eval_node(node.right))

        if isinstance(node, ast.UnaryOp):
            op = self._OPERATORS.get(type(node.op))
            if op is None:
                raise SafeEvalError(f"不支持的一元运算符: {type(node.op).__name__}")
            return op(self._eval_node(node.operand))

        if isinstance(node, ast.Call):
            func_name = getattr(node.func, "id", None)
            if func_name not in self._ALLOWED_FUNCS:
                raise SafeEvalError(f"不允许调用函数: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return float(self._ALLOWED_FUNCS[func_name](*args))

        raise SafeEvalError(f"不支持的 AST 节点: {type(node).__name__}")
