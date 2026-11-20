"""Order job stops to shorten total travel: nearest neighbour, then 2-opt improvement."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass

EARTH_KM = 6371.0088


@dataclass(frozen=True)
class Stop:
    """One job location."""
    id: str
    building: str
    lat: float
    lon: float
    minutes: int = 30


def haversine_km(a: Stop, b: Stop) -> float:
    """Great-circle distance between two stops in kilometres."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dphi, dlam = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(h))


def route_length(route: list[Stop]) -> float:
    """Total km driving the stops in the given order (open path, no return)."""
    return sum(haversine_km(a, b) for a, b in zip(route, route[1:]))


def nearest_neighbour(stops: list[Stop], start: Stop) -> list[Stop]:
    """Greedy route: always drive to the closest unvisited stop. The start stop comes first."""
    left = [s for s in stops if s is not start]
    route = [start]
    while left:
        nxt = min(left, key=lambda s: haversine_km(route[-1], s))
        left.remove(nxt)
        route.append(nxt)
    return route


def two_opt(route: list[Stop]) -> list[Stop]:
    """Reverse segments while that shortens the path. The first stop stays fixed."""
    best = list(route)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                if route_length(candidate) < route_length(best) - 1e-9:
                    best, improved = candidate, True
    return best


def plan(stops: list[Stop], start_id: str | None = None) -> list[Stop]:
    """Return an improved visiting order. Starts at start_id, or at the first stop listed."""
    if not stops:
        raise ValueError("no stops to plan")
    start = stops[0]
    if start_id is not None:
        found = [s for s in stops if s.id == start_id]
        if not found:
            raise ValueError(f"start job {start_id!r} not found")
        start = found[0]
    return two_opt(nearest_neighbour(stops, start))


def load_stops(path: str) -> list[Stop]:
    """Read stops from a CSV with id, building, lat, lon and optional minutes."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = {"id", "building", "lat", "lon"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing column(s): {', '.join(sorted(missing))}")
        stops, seen = [], set()
        for number, row in enumerate(reader, start=2):
            try:
                lat, lon = float(row["lat"]), float(row["lon"])
                minutes = int(row.get("minutes") or 30)
            except ValueError:
                raise ValueError(f"line {number}: lat, lon and minutes must be numbers") from None
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"line {number}: coordinates out of range")
            if row["id"] in seen:
                raise ValueError(f"line {number}: duplicate job id {row['id']!r}")
            seen.add(row["id"])
            stops.append(Stop(row["id"], row["building"], lat, lon, minutes))
    return stops
