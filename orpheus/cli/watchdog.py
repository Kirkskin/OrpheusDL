from typing import List, Tuple

from orpheus.services import brain, CLIEvent, EventType

COLOR_RESET = "\033[0m"
COLOR_WARNING = "\033[33m"
COLOR_ERROR = "\033[31m"
COLOR_INFO = "\033[36m"


def _colorize_hint(hint: str) -> Tuple[str, str]:
    lower = hint.lower()
    if any(keyword in lower for keyword in ["error", "failed", "critical", "fatal"]):
        return "❌ " + COLOR_ERROR + hint + COLOR_RESET, "error"
    if any(keyword in lower for keyword in ["warn", "vpn", "dns", "unstable", "retry"]):
        return "⚠️  " + COLOR_WARNING + hint + COLOR_RESET, "warning"
    if any(keyword in lower for keyword in ["error", "failed", "critical"]):
        return "❌ " + COLOR_ERROR + hint + COLOR_RESET, "error"
    if any(keyword in lower for keyword in ["warn", "vpn", "dns"]):
        return "⚠️  " + COLOR_WARNING + hint + COLOR_RESET, "warning"
    return "ℹ️  " + COLOR_INFO + hint + COLOR_RESET, "info"


class CLIWatchdog:
    def __init__(self):
        brain.subscribe(EventType.CLI, self._on_cli_event)
        self._latest_messages: List[str] = []

    def record_command(self, command: str, context: str = ""):
        event = CLIEvent(command=command, context=context)
        brain.record_event(event)

    def display_hints(self):
        hints = brain.get_last_hints()
        colored = []
        for hint in hints:
            rendered, _ = _colorize_hint(hint)
            if rendered not in self._latest_messages:
                self._latest_messages.append(rendered)
        colored.extend(self._latest_messages)
        return colored

    def _on_cli_event(self, event: CLIEvent):
        self._latest_messages = []


watchdog = CLIWatchdog()
