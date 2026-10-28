import time
from typing import Dict, Any, List, Optional
import pandas as pd

class TransformationHistory:
    """
    Manages an undo/redo stack of DataFrame checkpoints for reversible data cleaning.
    """
    def __init__(self, initial_df: pd.DataFrame, max_history: int = 15):
        self.history: List[Dict[str, Any]] = [{
            "df": initial_df.copy(),
            "action": "Initial State",
            "timestamp": time.time(),
            "row_count": len(initial_df),
            "column_count": len(initial_df.columns)
        }]
        self.current_idx = 0
        self.max_history = max_history

    def push(self, new_df: pd.DataFrame, action_desc: str):
        # Truncate any redo steps ahead of current index
        self.history = self.history[:self.current_idx + 1]
        
        self.history.append({
            "df": new_df.copy(),
            "action": action_desc,
            "timestamp": time.time(),
            "row_count": len(new_df),
            "column_count": len(new_df.columns)
        })
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.current_idx += 1

    def undo(self) -> Optional[pd.DataFrame]:
        if self.current_idx > 0:
            self.current_idx -= 1
            return self.history[self.current_idx]["df"].copy()
        return None

    def redo(self) -> Optional[pd.DataFrame]:
        if self.current_idx < len(self.history) - 1:
            self.current_idx += 1
            return self.history[self.current_idx]["df"].copy()
        return None

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "index": i,
                "action": h["action"],
                "timestamp": h["timestamp"],
                "row_count": h["row_count"],
                "column_count": h["column_count"],
                "is_current": (i == self.current_idx)
            }
            for i, h in enumerate(self.history)
        ]
