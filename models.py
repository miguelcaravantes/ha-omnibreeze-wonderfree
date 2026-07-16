"""Models for OmniBreeze Wonderfree."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DiscoveredDevice:
    """A Wonderfree device found on the LAN."""

    host: str
    port: int
    product_key: str
    device_key: str
    name: str


@dataclass(slots=True, frozen=True)
class FanStatus:
    """Current DC2313R state."""

    power: bool
    mode: int
    speed: int
    oscillating: bool
    sound: bool
    display: bool
    temperature: int
    countdown: int
