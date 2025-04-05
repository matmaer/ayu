from dataclasses import dataclass
import json

from pytest_ahriman.utils import EventType


@dataclass
class Event:
    event_type: EventType
    event_payload: dict

    def serialize(self) -> str:
        return json.dumps(
            {"type": self.event_type, "payload": self.event_payload}, indent=4
        )
