from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class Detection:
    bbox: Tuple[float, float, float, float]
    centroid: Tuple[float, float]
    confidence: Optional[float]
    class_name: str = "basket"
