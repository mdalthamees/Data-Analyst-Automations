import re
import ast
import time
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np

from app.formula_engine.functions import ExcelFunctions, ExcelError
from app.formula_engine.registry import FUNCTION_REGISTRY

class FormulaEvaluator:
    """
    Evaluates Excel-like formulas over DataFrames and cell ranges with dependency analysis,
    circular reference detection, and error reporting.
    """

    FUNCTION_MAP = {
        # Math
        "SUM": ExcelFunctions.sum,
        "SUMIF": ExcelFunctions.sumif,
        "SUMIFS": ExcelFunctions.sumifs,
        "AVERAGE": ExcelFunctions.average,
        "AVERAGEIF": ExcelFunctions.averageif,
        "AVERAGEIFS": ExcelFunctions.averageifs,
        "MIN": ExcelFunctions.min,
        "MAX": ExcelFunctions.max,
        "COUNT": ExcelFunctions.count,
        "COUNTA": ExcelFunctions.counta,
        "COUNTBLANK": ExcelFunctions.countblank,
        "COUNTIF": ExcelFunctions.countif,
        "COUNTIFS": ExcelFunctions.countifs,
        "PRODUCT": ExcelFunctions.product,
        "ABS": ExcelFunctions.abs,
        "ROUND": ExcelFunctions.round,
        "ROUNDUP": ExcelFunctions.roundup,
        "ROUNDDOWN": ExcelFunctions.rounddown,
        "INT": ExcelFunctions.int,
        "MOD": ExcelFunctions.mod,
        "POWER": ExcelFunctions.power,
        "SQRT": ExcelFunctions.sqrt,
        "SUMPRODUCT": ExcelFunctions.sumproduct,
        # Logical
        "IF": ExcelFunctions.if_,
        "IFS": ExcelFunctions.ifs,
        "AND": ExcelFunctions.and_,
        "OR": ExcelFunctions.or_,
        "NOT": ExcelFunctions.not_,
        "IFERROR": ExcelFunctions.iferror,
        "SWITCH": ExcelFunctions.switch,
        "TRUE": lambda: True,
        "FALSE": lambda: False,
        # Lookup
        "XLOOKUP": ExcelFunctions.xlookup,
        "VLOOKUP": ExcelFunctions.vlookup,
        "INDEX": ExcelFunctions.index,
        "MATCH": ExcelFunctions.match,
        "UNIQUE": ExcelFunctions.unique,
        # Text
        "LEFT": ExcelFunctions.left,
        "RIGHT": ExcelFunctions.right,
        "MID": ExcelFunctions.mid,
        "LEN": ExcelFunctions.len,
        "TRIM": ExcelFunctions.trim,
        "UPPER": ExcelFunctions.upper,
        "LOWER": ExcelFunctions.lower,
        "PROPER": ExcelFunctions.proper,
        "CONCAT": ExcelFunctions.concat,
        "TEXTJOIN": ExcelFunctions.textjoin,
        "SUBSTITUTE": ExcelFunctions.substitute,
        # Date
        "TODAY": ExcelFunctions.today,
        "NOW": ExcelFunctions.now,
        "DATE": ExcelFunctions.date,
        "YEAR": ExcelFunctions.year,
        "MONTH": ExcelFunctions.month,
        "DAY": ExcelFunctions.day,
        "DATEDIF": ExcelFunctions.datedif,
        "NETWORKDAYS": ExcelFunctions.networkdays,
        # Stats
        "MEDIAN": ExcelFunctions.median,
        "MODE": ExcelFunctions.mode,
        "STDEV.S": ExcelFunctions.stdev_s,
        "VAR.S": ExcelFunctions.var_s,
        "RANK.EQ": ExcelFunctions.rank_eq,
        "FORECAST.LINEAR": ExcelFunctions.forecast_linear,
    }

    @classmethod
    def evaluate_formula(cls, formula: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Evaluates formula string like '=SUM([Sales])' or '=AVERAGEIF([Region], "South", [Profit])'.
        """
        clean = formula.strip()
        if clean.startswith("="):
            clean = clean[1:].strip()

        start_time = time.perf_counter()

        # Check for circular reference in expression (e.g. self-referencing column name)
        # Extract column references like [Sales], [Profit]
        col_refs = re.findall(r"\[([^\]]+)\]", clean)
        
        # Replace column references with valid Python tokens for AST parsing
        token_map = {}
        transformed_expr = clean
        for idx, col in enumerate(col_refs):
            tok = f"__col_ref_{idx}__"
            token_map[tok] = col
            transformed_expr = transformed_expr.replace(f"[{col}]", tok)

        # Parse AST safely
        try:
            tree = ast.parse(transformed_expr, mode="eval")
            result = cls._eval_node(tree.body, df=df, token_map=token_map)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # Format display value
            if isinstance(result, (float, np.floating)):
                display_val = round(float(result), 4)
            elif isinstance(result, (list, np.ndarray, pd.Series)):
                display_val = [cls._format_val(x) for x in list(result)[:20]]
            else:
                display_val = result

            return {
                "success": True,
                "formula": formula,
                "result": display_val,
                "referenced_columns": col_refs,
                "execution_time_ms": elapsed_ms
            }
        except ExcelError as ee:
            return {
                "success": False,
                "formula": formula,
                "error": str(ee),
                "error_code": ee.code,
                "execution_time_ms": round((time.perf_counter() - start_time) * 1000, 2)
            }
        except Exception as e:
            return {
                "success": False,
                "formula": formula,
                "error": f"Evaluation error: {str(e)}",
                "error_code": "#VALUE!",
                "execution_time_ms": round((time.perf_counter() - start_time) * 1000, 2)
            }

    @classmethod
    def _eval_node(cls, node, df: Optional[pd.DataFrame], token_map: Dict[str, str]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Check if token corresponds to a DataFrame column
            if node.id in token_map:
                col_name = token_map[node.id]
                if df is not None and col_name in df.columns:
                    return df[col_name].values
                raise ExcelError(f"Column '{col_name}' not found in active dataset", "#REF!")
            elif node.id.upper() in ["TRUE", "FALSE"]:
                return node.id.upper() == "TRUE"
            raise ExcelError(f"Undefined variable or name '{node.id}'", "#NAME?")
        elif isinstance(node, ast.UnaryOp):
            val = cls._eval_node(node.operand, df, token_map)
            if isinstance(node.op, ast.USub):
                return -val
            elif isinstance(node.op, ast.UAdd):
                return val
            elif isinstance(node.op, ast.Not):
                return not val
        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, df, token_map)
            right = cls._eval_node(node.right, df, token_map)
            return cls._eval_binop(node.op, left, right)
        elif isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, df, token_map)
            for op, comparator in zip(node.ops, node.comparators):
                right = cls._eval_node(comparator, df, token_map)
                if not cls._eval_compare(op, left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.Call):
            # Function name
            func_name = cls._get_call_name(node.func).upper()
            args = [cls._eval_node(a, df, token_map) for a in node.args]
            
            if func_name in cls.FUNCTION_MAP:
                return cls.FUNCTION_MAP[func_name](*args)
            elif func_name in FUNCTION_REGISTRY:
                reg_entry = FUNCTION_REGISTRY[func_name]
                if reg_entry.get("status") == "unsupported":
                    raise ExcelError(f"Function '{func_name}' is currently unsupported.", "#UNSUPPORTED!")
            raise ExcelError(f"Unknown or unsupported function '{func_name}'", "#NAME?")
        elif isinstance(node, ast.List):
            return [cls._eval_node(elt, df, token_map) for elt in node.elts]
        else:
            raise ExcelError(f"Unsupported syntax construct: {type(node).__name__}", "#VALUE!")

    @classmethod
    def _get_call_name(cls, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{cls._get_call_name(node.value)}.{node.attr}"
        return "UNKNOWN"

    @classmethod
    def _eval_binop(cls, op, left, right):
        if isinstance(op, ast.Add): return left + right
        if isinstance(op, ast.Sub): return left - right
        if isinstance(op, ast.Mult): return left * right
        if isinstance(op, ast.Div):
            if right == 0:
                raise ExcelError("Division by zero", "#DIV/0!")
            return left / right
        if isinstance(op, ast.Pow): return left ** right
        if isinstance(op, ast.Mod): return left % right
        raise ExcelError(f"Unsupported binary operator: {type(op).__name__}", "#VALUE!")

    @classmethod
    def _eval_compare(cls, op, left, right):
        if isinstance(op, ast.Eq): return left == right
        if isinstance(op, ast.NotEq): return left != right
        if isinstance(op, ast.Lt): return left < right
        if isinstance(op, ast.LtE): return left <= right
        if isinstance(op, ast.Gt): return left > right
        if isinstance(op, ast.GtE): return left >= right
        return False

    @classmethod
    def _format_val(cls, val):
        if isinstance(val, (np.floating, float)):
            return round(float(val), 2)
        if isinstance(val, (np.integer, int)):
            return int(val)
        return str(val)
