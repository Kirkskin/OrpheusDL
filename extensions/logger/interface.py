import json
from datetime import datetime, timezone

from utils.models import ExtensionInformation
from orpheus.services import brain, Event, EventType


extension_settings = ExtensionInformation(
    extension_type='logging',
    settings={'path': 'orpheus.log'}
)


class OrpheusExtension:
    def __init__(self, settings: dict):
        self.path = settings.get('path', 'orpheus.log')
        for event_type in EventType:
            brain.subscribe(event_type, self._handle_event)

    def _handle_event(self, event: Event):
        payload = {
            'type': event.type.name,
            'timestamp': event.timestamp.astimezone(timezone.utc).isoformat(),
            'metadata': event.metadata,
        }
        with open(self.path, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(payload) + '\n')
