"""
Strategy 19.5: Economic Announcements Trading
Trading only on specific announcement dates (e.g., FOMC, NFP, CPI).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import date
import numpy as np

router = APIRouter(prefix="/macro", tags=["macro"])


class AnnouncementEvent(BaseModel):
    event_type: str = Field(..., description="Event type (FOMC, NFP, CPI, GDP, etc.)")
    event_date: date
    expected_value: float = Field(..., description="Consensus expectation")
    actual_value: float | None = Field(None, description="Actual value if released")
    previous_value: float = Field(..., description="Previous release value")


class EconomicAnnouncementsRequest(BaseModel):
    events: list[AnnouncementEvent] = Field(..., description="Upcoming/recent events")
    asset: str = Field(..., description="Asset to trade (SPY, TLT, USD, etc.)")
    historical_reactions: dict[str, float] = Field(..., description="Avg move per event type (bps)")
    position_size: float = Field(1.0, description="Base position size")
    surprise_threshold: float = Field(0.5, description="Std dev threshold for surprise")


class EconomicAnnouncementsResponse(BaseModel):
    strategy: str = "economic_announcements"
    signal: int = Field(..., description="1=long, -1=short, 0=no trade")
    event_type: str = Field(..., description="Event driving the signal")
    surprise_magnitude: float = Field(..., description="Surprise in std devs")
    expected_move: float = Field(..., description="Expected move (bps)")
    position_multiplier: float = Field(..., description="Suggested position scaling")
    trade_window: str = Field(..., description="Recommended trade window")


class EventCalendarRequest(BaseModel):
    events: list[AnnouncementEvent]
    days_ahead: int = Field(7, description="Days to look ahead")


class EventCalendarResponse(BaseModel):
    upcoming_events: list[dict]
    high_impact_count: int
    recommended_days: list[str]


@router.post("/economic-announcements", response_model=EconomicAnnouncementsResponse)
def economic_announcements(req: EconomicAnnouncementsRequest):
    tradeable_events = [e for e in req.events if e.actual_value is not None]

    if not tradeable_events:
        pending = [e for e in req.events if e.actual_value is None]
        if pending:
            next_event = pending[0]
            return EconomicAnnouncementsResponse(
                signal=0,
                event_type=next_event.event_type,
                surprise_magnitude=0.0,
                expected_move=req.historical_reactions.get(next_event.event_type, 0),
                position_multiplier=0.0,
                trade_window=f"Pending: {next_event.event_date}",
            )

    latest_event = tradeable_events[-1]
    surprise = latest_event.actual_value - latest_event.expected_value

    historical_std = abs(req.historical_reactions.get(latest_event.event_type, 10)) / 2
    surprise_magnitude = surprise / historical_std if historical_std > 0 else 0

    base_reaction = req.historical_reactions.get(latest_event.event_type, 0)

    if latest_event.event_type == "FOMC":
        signal = -1 if surprise > 0 else (1 if surprise < 0 else 0)
    elif latest_event.event_type in ["NFP", "GDP"]:
        signal = 1 if surprise > 0 else (-1 if surprise < 0 else 0)
    elif latest_event.event_type == "CPI":
        signal = -1 if surprise > 0 else (1 if surprise < 0 else 0)
    else:
        signal = 1 if surprise > 0 else (-1 if surprise < 0 else 0)

    if abs(surprise_magnitude) < req.surprise_threshold:
        signal = 0

    position_multiplier = min(2.0, abs(surprise_magnitude)) * req.position_size
    expected_move = base_reaction * surprise_magnitude

    return EconomicAnnouncementsResponse(
        signal=signal,
        event_type=latest_event.event_type,
        surprise_magnitude=float(surprise_magnitude),
        expected_move=float(expected_move),
        position_multiplier=float(position_multiplier),
        trade_window="0-30 minutes post-release",
    )


@router.post("/event-calendar", response_model=EventCalendarResponse)
def event_calendar(req: EventCalendarRequest):
    today = date.today()
    upcoming = [
        {
            "event": e.event_type,
            "date": str(e.event_date),
            "expected": e.expected_value,
            "previous": e.previous_value,
        }
        for e in req.events
        if e.event_date >= today and (e.event_date - today).days <= req.days_ahead
    ]

    high_impact_types = {"FOMC", "NFP", "CPI", "GDP"}
    high_impact_count = sum(1 for e in upcoming if e["event"] in high_impact_types)

    recommended_days = list(set(e["date"] for e in upcoming if e["event"] in high_impact_types))

    return EventCalendarResponse(
        upcoming_events=upcoming,
        high_impact_count=high_impact_count,
        recommended_days=sorted(recommended_days),
    )
