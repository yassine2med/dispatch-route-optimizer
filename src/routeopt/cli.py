"""Command line entry: python -m routeopt jobs.csv"""
from __future__ import annotations

import argparse
import sys

from .planner import load_stops, plan, route_length


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="routeopt", description="Order technician visits by location")
    parser.add_argument("csv", help="columns: id, building, lat, lon, minutes (optional)")
    parser.add_argument("--start", help="job id to visit first (default: first row)")
    parser.add_argument("--speed", type=float, default=30.0, help="average driving speed in km/h")
    args = parser.parse_args(argv)
    if args.speed <= 0:
        print("error: --speed must be positive", file=sys.stderr)
        return 1
    try:
        stops = load_stops(args.csv)
        route = plan(stops, args.start)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    before = route_length(stops if args.start is None else
                          [s for s in stops if s.id == args.start] + [s for s in stops if s.id != args.start])
    after = route_length(route)
    print(f"{'Stop':<5}{'Job':<7}{'Building':<14}{'Leg km':>7}")
    for index, stop in enumerate(route):
        leg = 0.0 if index == 0 else route_length(route[index - 1:index + 1])
        print(f"{index + 1:<5}{stop.id:<7}{stop.building:<14}{leg:>7.2f}")
    drive_min = after / args.speed * 60
    work_min = sum(s.minutes for s in route)
    saved = (before - after) / before * 100 if before else 0.0
    print(f"\nListed order: {before:.2f} km | Planned order: {after:.2f} km | saved {saved:.0f}%")
    print(f"Driving about {drive_min:.0f} min, on-site {work_min} min, day total {drive_min + work_min:.0f} min")
    return 0
