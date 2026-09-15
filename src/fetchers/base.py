from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.core.models import Source

class BaseFetcher(ABC):
    def __init__(self, source: Source):
        self.source = source

    @abstractmethod
    def fetch_raw_candidates(self) -> List[Dict[str, Any]]:
        """从对应数据源抓取原始候选活动数据字典列表"""
        pass
