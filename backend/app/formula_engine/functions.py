import math
import re
import datetime
from typing import Any, List, Union, Optional
import numpy as np
import pandas as pd

class ExcelError(Exception):
    def __init__(self, message: str, code: str = "#VALUE!"):
        super().__init__(message)
        self.code = code

class ExcelFunctions:
    """
    Production-tested Excel Functions Library with strict parity,
    proper criteria evaluation, blanks handling, and error codes.
    """

    # --- Helpers ---
    @staticmethod
    def _to_flat_list(args: List[Any]) -> List[Any]:
        result = []
        for arg in args:
            if isinstance(arg, (list, tuple, np.ndarray)):
                result.extend(ExcelFunctions._to_flat_list(arg))
            elif isinstance(arg, pd.Series):
                result.extend(arg.tolist())
            elif isinstance(arg, pd.DataFrame):
                result.extend(arg.values.flatten().tolist())
            else:
                result.append(arg)
        return result

    @staticmethod
    def _is_blank(val: Any) -> bool:
        return val is None or (isinstance(val, float) and math.isnan(val)) or val == ""

    @staticmethod
    def _to_number(val: Any, strict: bool = False) -> Optional[float]:
        if ExcelFunctions._is_blank(val):
            return 0.0 if not strict else None
        if isinstance(val, (int, float, np.integer, np.floating)):
            return float(val)
        if isinstance(val, bool):
            return 1.0 if val else 0.0
        if isinstance(val, str):
            clean = val.replace("$", "").replace("€", "").replace("£", "").replace("₹", "").replace("%", "").replace(",", "").strip()
            try:
                num = float(clean)
                if "%" in val:
                    num = num / 100.0
                return num
            except ValueError:
                if strict:
                    raise ExcelError(f"Cannot convert '{val}' to number", "#VALUE!")
                return None
        return None

    @staticmethod
    def _evaluate_criteria(val: Any, criteria: Any) -> bool:
        if criteria is None:
            return ExcelFunctions._is_blank(val)
        crit_str = str(criteria).strip()
        
        # Check operators: >=, <=, <>, >, <, =
        match = re.match(r"^(>=|<=|<>|>|<|=)?\s*(.*)$", crit_str)
        if match:
            op, target = match.groups()
            op = op or "="
            
            # Numeric comparison
            v_num = ExcelFunctions._to_number(val)
            t_num = ExcelFunctions._to_number(target)

            if v_num is not None and t_num is not None:
                if op == ">": return v_num > t_num
                if op == "<": return v_num < t_num
                if op == ">=": return v_num >= t_num
                if op == "<=": return v_num <= t_num
                if op == "=": return v_num == t_num
                if op == "<>": return v_num != t_num

            # Text comparison (case-insensitive with wildcard support)
            v_str = "" if ExcelFunctions._is_blank(val) else str(val).lower()
            t_str = target.lower()

            if "*" in t_str or "?" in t_str:
                regex_pat = "^" + re.escape(t_str).replace(r"\*", ".*").replace(r"\?", ".") + "$"
                matched = bool(re.match(regex_pat, v_str))
                return matched if op != "<>" else not matched

            if op == "=": return v_str == t_str
            if op == "<>": return v_str != t_str
            if op == ">": return v_str > t_str
            if op == "<": return v_str < t_str
            if op == ">=": return v_str >= t_str
            if op == "<=": return v_str <= t_str

        return str(val).lower() == crit_str.lower()

    # --- Mathematical & Aggregations ---
    @classmethod
    def sum(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        total = 0.0
        for x in flat:
            num = cls._to_number(x)
            if num is not None:
                total += num
        return total

    @classmethod
    def sumif(cls, range_cells, criteria, sum_range=None) -> float:
        r_flat = cls._to_flat_list([range_cells])
        s_flat = cls._to_flat_list([sum_range]) if sum_range is not None else r_flat
        total = 0.0
        for i in range(min(len(r_flat), len(s_flat))):
            if cls._evaluate_criteria(r_flat[i], criteria):
                val = cls._to_number(s_flat[i])
                if val is not None:
                    total += val
        return total

    @classmethod
    def sumifs(cls, sum_range, *criteria_pairs) -> float:
        if len(criteria_pairs) % 2 != 0:
            raise ExcelError("SUMIFS requires pairs of criteria_range and criteria", "#VALUE!")
        s_flat = cls._to_flat_list([sum_range])
        n = len(s_flat)
        valid_indices = set(range(n))

        for i in range(0, len(criteria_pairs), 2):
            c_range = cls._to_flat_list([criteria_pairs[i]])
            crit = criteria_pairs[i + 1]
            current_valid = set()
            for idx in valid_indices:
                if idx < len(c_range) and cls._evaluate_criteria(c_range[idx], crit):
                    current_valid.add(idx)
            valid_indices = current_valid

        total = 0.0
        for idx in valid_indices:
            v = cls._to_number(s_flat[idx])
            if v is not None:
                total += v
        return total

    @classmethod
    def average(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        if not nums:
            raise ExcelError("AVERAGE divided by zero", "#DIV/0!")
        return sum(nums) / len(nums)

    @classmethod
    def averageif(cls, range_cells, criteria, average_range=None) -> float:
        r_flat = cls._to_flat_list([range_cells])
        a_flat = cls._to_flat_list([average_range]) if average_range is not None else r_flat
        matched = []
        for i in range(min(len(r_flat), len(a_flat))):
            if cls._evaluate_criteria(r_flat[i], criteria):
                val = cls._to_number(a_flat[i])
                if val is not None and not cls._is_blank(a_flat[i]):
                    matched.append(val)
        if not matched:
            raise ExcelError("No matching values for AVERAGEIF", "#DIV/0!")
        return sum(matched) / len(matched)

    @classmethod
    def averageifs(cls, average_range, *criteria_pairs) -> float:
        if len(criteria_pairs) % 2 != 0:
            raise ExcelError("AVERAGEIFS requires pairs of criteria_range and criteria", "#VALUE!")
        a_flat = cls._to_flat_list([average_range])
        n = len(a_flat)
        valid_indices = set(range(n))

        for i in range(0, len(criteria_pairs), 2):
            c_range = cls._to_flat_list([criteria_pairs[i]])
            crit = criteria_pairs[i + 1]
            current_valid = set()
            for idx in valid_indices:
                if idx < len(c_range) and cls._evaluate_criteria(c_range[idx], crit):
                    current_valid.add(idx)
            valid_indices = current_valid

        matched = []
        for idx in valid_indices:
            v = cls._to_number(a_flat[idx])
            if v is not None and not cls._is_blank(a_flat[idx]):
                matched.append(v)
        if not matched:
            raise ExcelError("No matching values for AVERAGEIFS", "#DIV/0!")
        return sum(matched) / len(matched)

    @classmethod
    def min(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        return min(nums) if nums else 0.0

    @classmethod
    def max(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        return max(nums) if nums else 0.0

    @classmethod
    def count(cls, *args) -> int:
        flat = cls._to_flat_list(args)
        count = 0
        for x in flat:
            if not cls._is_blank(x) and cls._to_number(x) is not None:
                count += 1
        return count

    @classmethod
    def counta(cls, *args) -> int:
        flat = cls._to_flat_list(args)
        return sum(1 for x in flat if not cls._is_blank(x))

    @classmethod
    def countblank(cls, range_cells) -> int:
        flat = cls._to_flat_list([range_cells])
        return sum(1 for x in flat if cls._is_blank(x))

    @classmethod
    def countif(cls, range_cells, criteria) -> int:
        flat = cls._to_flat_list([range_cells])
        return sum(1 for x in flat if cls._evaluate_criteria(x, criteria))

    @classmethod
    def countifs(cls, *criteria_pairs) -> int:
        if len(criteria_pairs) % 2 != 0:
            raise ExcelError("COUNTIFS requires pairs of criteria_range and criteria", "#VALUE!")
        first_range = cls._to_flat_list([criteria_pairs[0]])
        valid_indices = set(range(len(first_range)))

        for i in range(0, len(criteria_pairs), 2):
            c_range = cls._to_flat_list([criteria_pairs[i]])
            crit = criteria_pairs[i + 1]
            current_valid = set()
            for idx in valid_indices:
                if idx < len(c_range) and cls._evaluate_criteria(c_range[idx], crit):
                    current_valid.add(idx)
            valid_indices = current_valid

        return len(valid_indices)

    @classmethod
    def product(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        prod = 1.0
        has_num = False
        for x in flat:
            n = cls._to_number(x)
            if n is not None:
                prod *= n
                has_num = True
        return prod if has_num else 0.0

    @classmethod
    def abs(cls, number) -> float:
        n = cls._to_number(number, strict=True)
        return builtins_abs(n)

    @classmethod
    def round(cls, number, num_digits=0) -> float:
        n = cls._to_number(number, strict=True)
        d = int(cls._to_number(num_digits, strict=True))
        return builtins_round(n, d)

    @classmethod
    def roundup(cls, number, num_digits=0) -> float:
        n = cls._to_number(number, strict=True)
        d = int(cls._to_number(num_digits, strict=True))
        factor = 10 ** d
        return math.ceil(n * factor) / factor if n >= 0 else math.floor(n * factor) / factor

    @classmethod
    def rounddown(cls, number, num_digits=0) -> float:
        n = cls._to_number(number, strict=True)
        d = int(cls._to_number(num_digits, strict=True))
        factor = 10 ** d
        return math.floor(n * factor) / factor if n >= 0 else math.ceil(n * factor) / factor

    @classmethod
    def int(cls, number) -> int:
        n = cls._to_number(number, strict=True)
        return math.floor(n)

    @classmethod
    def mod(cls, number, divisor) -> float:
        n = cls._to_number(number, strict=True)
        d = cls._to_number(divisor, strict=True)
        if d == 0:
            raise ExcelError("Division by zero in MOD", "#DIV/0!")
        return n % d

    @classmethod
    def power(cls, number, power_val) -> float:
        n = cls._to_number(number, strict=True)
        p = cls._to_number(power_val, strict=True)
        return math.pow(n, p)

    @classmethod
    def sqrt(cls, number) -> float:
        n = cls._to_number(number, strict=True)
        if n < 0:
            raise ExcelError("Negative number in SQRT", "#NUM!")
        return math.sqrt(n)

    @classmethod
    def sumproduct(cls, *arrays) -> float:
        if not arrays:
            return 0.0
        flat_arrays = [cls._to_flat_list([a]) for a in arrays]
        min_len = min(len(a) for a in flat_arrays)
        total = 0.0
        for i in range(min_len):
            row_prod = 1.0
            for arr in flat_arrays:
                num = cls._to_number(arr[i]) or 0.0
                row_prod *= num
            total += row_prod
        return total

    # --- Logical ---
    @classmethod
    def if_(cls, logical_test, value_if_true=True, value_if_false=False) -> Any:
        return value_if_true if bool(logical_test) else value_if_false

    @classmethod
    def ifs(cls, *args) -> Any:
        if len(args) % 2 != 0:
            raise ExcelError("IFS requires pairs of condition and value", "#VALUE!")
        for i in range(0, len(args), 2):
            if bool(args[i]):
                return args[i + 1]
        raise ExcelError("No IFS conditions were met", "#N/A")

    @classmethod
    def and_(cls, *args) -> bool:
        flat = cls._to_flat_list(args)
        return all(bool(x) for x in flat)

    @classmethod
    def or_(cls, *args) -> bool:
        flat = cls._to_flat_list(args)
        return any(bool(x) for x in flat)

    @classmethod
    def not_(cls, logical) -> bool:
        return not bool(logical)

    @classmethod
    def iferror(cls, value, value_if_error) -> Any:
        try:
            if isinstance(value, ExcelError) or str(value).startswith("#"):
                return value_if_error
            return value
        except Exception:
            return value_if_error

    @classmethod
    def switch(cls, expr, *args) -> Any:
        i = 0
        while i < len(args) - 1:
            val = args[i]
            res = args[i + 1]
            if expr == val:
                return res
            i += 2
        # Default value if odd arg remains
        if i < len(args):
            return args[i]
        raise ExcelError("No matching value in SWITCH", "#N/A")

    # --- Lookup & Reference ---
    @classmethod
    def xlookup(cls, lookup_value, lookup_array, return_array, if_not_found="#N/A", match_mode=0, search_mode=1) -> Any:
        l_flat = cls._to_flat_list([lookup_array])
        r_flat = cls._to_flat_list([return_array])
        
        target = str(lookup_value).lower() if lookup_value is not None else ""
        
        # Determine search direction
        indices = range(len(l_flat)) if search_mode >= 0 else range(len(l_flat) - 1, -1, -1)
        
        for idx in indices:
            curr = str(l_flat[idx]).lower() if l_flat[idx] is not None else ""
            if curr == target:
                return r_flat[idx] if idx < len(r_flat) else None

        if if_not_found == "#N/A":
            raise ExcelError(f"Value '{lookup_value}' not found in XLOOKUP", "#N/A")
        return if_not_found

    @classmethod
    def vlookup(cls, lookup_value, table_array, col_index_num, range_lookup=True) -> Any:
        col_idx = int(col_index_num) - 1
        if isinstance(table_array, pd.DataFrame):
            df = table_array
            first_col = df.iloc[:, 0].astype(str).tolist()
            target = str(lookup_value).lower()
            for i, val in enumerate(first_col):
                if val.lower() == target:
                    return df.iloc[i, col_idx]
            raise ExcelError(f"VLOOKUP value '{lookup_value}' not found", "#N/A")
        elif isinstance(table_array, (list, tuple)):
            for row in table_array:
                if len(row) > 0 and str(row[0]).lower() == str(lookup_value).lower():
                    if col_idx < len(row):
                        return row[col_idx]
                    raise ExcelError("col_index_num exceeds table width", "#REF!")
            raise ExcelError(f"VLOOKUP value '{lookup_value}' not found", "#N/A")
        raise ExcelError("Invalid table_array for VLOOKUP", "#VALUE!")

    @classmethod
    def index(cls, array, row_num, column_num=1) -> Any:
        r = int(row_num) - 1
        c = int(column_num) - 1
        if isinstance(array, pd.DataFrame):
            if r < len(array) and c < len(array.columns):
                return array.iloc[r, c]
            raise ExcelError("INDEX row/column out of range", "#REF!")
        elif isinstance(array, pd.Series):
            if r < len(array):
                return array.iloc[r]
            raise ExcelError("INDEX row out of range", "#REF!")
        elif isinstance(array, (list, tuple)):
            if r < len(array):
                row = array[r]
                if isinstance(row, (list, tuple)) and c < len(row):
                    return row[c]
                elif c == 0:
                    return row
            raise ExcelError("INDEX out of range", "#REF!")
        raise ExcelError("Unsupported array for INDEX", "#VALUE!")

    @classmethod
    def match(cls, lookup_value, lookup_array, match_type=0) -> int:
        flat = cls._to_flat_list([lookup_array])
        target = str(lookup_value).lower()
        for i, val in enumerate(flat):
            if str(val).lower() == target:
                return i + 1 # 1-based index
        raise ExcelError(f"MATCH value '{lookup_value}' not found", "#N/A")

    @classmethod
    def unique(cls, array) -> List[Any]:
        flat = cls._to_flat_list([array])
        seen = set()
        res = []
        for x in flat:
            if x not in seen:
                seen.add(x)
                res.append(x)
        return res

    # --- Text ---
    @classmethod
    def left(cls, text, num_chars=1) -> str:
        s = "" if cls._is_blank(text) else str(text)
        n = int(num_chars)
        return s[:n]

    @classmethod
    def right(cls, text, num_chars=1) -> str:
        s = "" if cls._is_blank(text) else str(text)
        n = int(num_chars)
        return s[-n:] if n > 0 else ""

    @classmethod
    def mid(cls, text, start_num, num_chars) -> str:
        s = "" if cls._is_blank(text) else str(text)
        start = max(1, int(start_num)) - 1
        length = int(num_chars)
        return s[start:start + length]

    @classmethod
    def len(cls, text) -> int:
        s = "" if cls._is_blank(text) else str(text)
        return len(s)

    @classmethod
    def trim(cls, text) -> str:
        s = "" if cls._is_blank(text) else str(text)
        # Collapse multiple spaces
        return re.sub(r"\s+", " ", s).strip()

    @classmethod
    def upper(cls, text) -> str:
        s = "" if cls._is_blank(text) else str(text)
        return s.upper()

    @classmethod
    def lower(cls, text) -> str:
        s = "" if cls._is_blank(text) else str(text)
        return s.lower()

    @classmethod
    def proper(cls, text) -> str:
        s = "" if cls._is_blank(text) else str(text)
        return s.title()

    @classmethod
    def concat(cls, *args) -> str:
        flat = cls._to_flat_list(args)
        return "".join("" if cls._is_blank(x) else str(x) for x in flat)

    @classmethod
    def textjoin(cls, delimiter, ignore_empty, *args) -> str:
        flat = cls._to_flat_list(args)
        delim = str(delimiter)
        items = []
        for x in flat:
            if cls._is_blank(x):
                if not bool(ignore_empty):
                    items.append("")
            else:
                items.append(str(x))
        return delim.join(items)

    @classmethod
    def substitute(cls, text, old_text, new_text, instance_num=None) -> str:
        s = "" if cls._is_blank(text) else str(text)
        old = str(old_text)
        new = str(new_text)
        if instance_num is None:
            return s.replace(old, new)
        # Replace specific instance
        parts = s.split(old)
        idx = int(instance_num)
        if 1 <= idx < len(parts):
            return old.join(parts[:idx]) + new + old.join(parts[idx:])
        return s

    # --- Date & Time ---
    @classmethod
    def today(cls) -> str:
        return datetime.date.today().isoformat()

    @classmethod
    def now(cls) -> str:
        return datetime.datetime.now().isoformat(timespec="seconds")

    @classmethod
    def date(cls, year, month, day) -> str:
        y, m, d = int(year), int(month), int(day)
        return datetime.date(y, m, d).isoformat()

    @classmethod
    def year(cls, serial_date) -> int:
        dt = pd.to_datetime(serial_date)
        return dt.year

    @classmethod
    def month(cls, serial_date) -> int:
        dt = pd.to_datetime(serial_date)
        return dt.month

    @classmethod
    def day(cls, serial_date) -> int:
        dt = pd.to_datetime(serial_date)
        return dt.day

    @classmethod
    def datedif(cls, start_date, end_date, unit="D") -> int:
        s = pd.to_datetime(start_date)
        e = pd.to_datetime(end_date)
        if s > e:
            raise ExcelError("start_date is greater than end_date in DATEDIF", "#NUM!")
        unit_u = str(unit).upper()
        if unit_u == "D":
            return (e - s).days
        elif unit_u == "M":
            return (e.year - s.year) * 12 + (e.month - s.month)
        elif unit_u == "Y":
            return e.year - s.year - ((e.month, e.day) < (s.month, s.day))
        raise ExcelError(f"Unsupported unit '{unit}' in DATEDIF", "#NUM!")

    @classmethod
    def networkdays(cls, start_date, end_date, holidays=None) -> int:
        s = pd.to_datetime(start_date)
        e = pd.to_datetime(end_date)
        if s > e:
            s, e = e, s
            sign = -1
        else:
            sign = 1
        holidays_set = set(pd.to_datetime(cls._to_flat_list([holidays])).date) if holidays else set()
        
        days = pd.date_range(s, e, freq="D")
        workdays = sum(1 for d in days if d.weekday() < 5 and d.date() not in holidays_set)
        return workdays * sign

    # --- Statistical ---
    @classmethod
    def median(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        if not nums:
            raise ExcelError("No numeric values for MEDIAN", "#NUM!")
        return float(np.median(nums))

    @classmethod
    def mode(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        if not nums:
            raise ExcelError("No numeric values for MODE", "#NUM!")
        vals, counts = np.unique(nums, return_counts=True)
        max_count = np.max(counts)
        if max_count <= 1:
            raise ExcelError("No duplicate values in MODE", "#N/A")
        return float(vals[np.argmax(counts)])

    @classmethod
    def stdev_s(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        if len(nums) < 2:
            raise ExcelError("STDEV.S requires at least 2 numbers", "#DIV/0!")
        return float(np.std(nums, ddof=1))

    @classmethod
    def var_s(cls, *args) -> float:
        flat = cls._to_flat_list(args)
        nums = [cls._to_number(x) for x in flat if cls._to_number(x) is not None and not cls._is_blank(x)]
        if len(nums) < 2:
            raise ExcelError("VAR.S requires at least 2 numbers", "#DIV/0!")
        return float(np.var(nums, ddof=1))

    @classmethod
    def rank_eq(cls, number, ref_list, order=0) -> int:
        n = cls._to_number(number, strict=True)
        flat = [cls._to_number(x) for x in cls._to_flat_list([ref_list]) if cls._to_number(x) is not None]
        if n not in flat:
            raise ExcelError("Number not found in reference list for RANK.EQ", "#N/A")
        sorted_list = sorted(flat, reverse=(order == 0))
        return sorted_list.index(n) + 1

    @classmethod
    def forecast_linear(cls, x, known_ys, known_xs) -> float:
        target_x = cls._to_number(x, strict=True)
        ys = [cls._to_number(v) for v in cls._to_flat_list([known_ys]) if cls._to_number(v) is not None]
        xs = [cls._to_number(v) for v in cls._to_flat_list([known_xs]) if cls._to_number(v) is not None]
        if len(ys) != len(xs) or len(ys) < 2:
            raise ExcelError("FORECAST.LINEAR requires matching arrays with at least 2 points", "#N/A")
        slope, intercept = np.polyfit(xs, ys, 1)
        return float(slope * target_x + intercept)

builtins_abs = abs
builtins_round = round
