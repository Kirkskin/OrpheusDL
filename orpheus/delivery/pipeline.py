from dataclasses import dataclass, field
from typing import Dict

from orpheus.services import brain, EventType, Event
from .queue import delivery_queue


@dataclass
class DeliveryTelemetry(Event):
    job_id: str = ""
    status: str = "pending"
    service: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def __init__(self, **kwargs):
        metadata = kwargs.pop("metadata", {})
        super().__init__(type=EventType.DELIVERY, metadata=metadata)
        self.job_id = kwargs.get("job_id", "")
        self.status = kwargs.get("status", "pending")
        self.service = kwargs.get("service", "")
        self.metadata.update(metadata)


class DeliveryPipeline:
    def __init__(self):
        self._counter = 0

    def begin_job(self, service: str, media_type: str, media_id: str) -> str:
        self._counter += 1
        job_id = f"{service}-{media_type}-{self._counter}"
        event = DeliveryTelemetry(
            job_id=job_id,
            status="started",
            service=service,
            metadata={"media_type": media_type, "media_id": media_id},
        )
        brain.record_event(event)
        return job_id

    def complete_job(self, job_id: str, service: str, success: bool, **metadata):
        event = DeliveryTelemetry(
            job_id=job_id,
            status="success" if success else "failed",
            service=service,
            metadata=metadata,
        )
        brain.record_event(event)

    def submit(self, fn, *args, **kwargs):
        return delivery_queue.submit(fn, *args, **kwargs)


delivery_pipeline = DeliveryPipeline()
