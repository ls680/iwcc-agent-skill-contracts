from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Event:
    operator: str
    subject: str = ""
    target: str = ""

    def key(self) -> str:
        return ":".join((self.operator, self.subject, self.target))


@dataclass(frozen=True, order=True)
class Milestone:
    kind: str
    ordinal: int = 1

    def key(self) -> str:
        return f"{self.kind}#{self.ordinal}"

