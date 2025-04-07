from __future__ import annotations
from dataclasses import dataclass
import json

from ayu.utils import EventType


@dataclass
class Event:
    event_type: EventType
    event_payload: dict

    def serialize(self) -> str:
        return json.dumps(
            {"type": self.event_type, "payload": self.event_payload}, indent=4
        )

    @classmethod
    def deserialize(cls, json_str: str) -> Event:
        event_dict = json.loads(json_str)
        return cls(event_type=event_dict["type"], event_payload=event_dict["payload"])
