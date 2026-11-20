import pytest

from routeopt.cli import main
from routeopt.planner import (Stop, haversine_km, load_stops, nearest_neighbour, plan,
                              route_length, two_opt)


def line(n):
    """n stops on a line of longitude, spaced 0.01 degrees apart."""
    return [Stop(f"J{i}", f"B{i}", 38.9, -77.0 + i * 0.01) for i in range(n)]


def test_haversine_zero_and_symmetric():
    a, b = Stop("a", "A", 38.9, -77.0), Stop("b", "B", 38.95, -77.05)
    assert haversine_km(a, a) == 0
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a))


def test_haversine_known_distance():
    # one degree of latitude is about 111.2 km
    a, b = Stop("a", "A", 0, 0), Stop("b", "B", 1, 0)
    assert haversine_km(a, b) == pytest.approx(111.2, abs=0.2)


def test_route_length_single_stop_is_zero():
    assert route_length(line(1)) == 0


def test_nearest_neighbour_starts_at_start():
    stops = line(4)
    assert nearest_neighbour(stops, stops[2])[0] is stops[2]


def test_plan_orders_a_line():
    stops = line(5)
    shuffled = [stops[0], stops[3], stops[1], stops[4], stops[2]]
    assert [s.id for s in plan(shuffled)] == ["J0", "J1", "J2", "J3", "J4"]


def test_plan_never_longer_than_listed():
    stops = load_stops("examples/jobs.csv")
    assert route_length(plan(stops)) <= route_length(stops)


def test_plan_visits_every_stop_once():
    stops = load_stops("examples/jobs.csv")
    assert sorted(s.id for s in plan(stops)) == sorted(s.id for s in stops)


def test_two_opt_keeps_first_stop():
    stops = line(6)
    assert two_opt(stops[::1])[0] is stops[0]


def test_plan_start_id():
    stops = line(4)
    assert plan(stops, "J2")[0].id == "J2"


def test_plan_unknown_start():
    with pytest.raises(ValueError, match="not found"):
        plan(line(3), "ZZ")


def test_plan_empty():
    with pytest.raises(ValueError):
        plan([])


def test_load_bad_number(tmp_path):
    p = tmp_path / "j.csv"
    p.write_text("id,building,lat,lon\n1,A,abc,-77\n")
    with pytest.raises(ValueError, match="line 2"):
        load_stops(str(p))


def test_load_out_of_range(tmp_path):
    p = tmp_path / "j.csv"
    p.write_text("id,building,lat,lon\n1,A,95,-77\n")
    with pytest.raises(ValueError, match="range"):
        load_stops(str(p))


def test_load_duplicate_id(tmp_path):
    p = tmp_path / "j.csv"
    p.write_text("id,building,lat,lon\n1,A,38,-77\n1,B,38,-77\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_stops(str(p))


def test_cli_runs(capsys):
    assert main(["examples/jobs.csv"]) == 0
    assert "Planned order" in capsys.readouterr().out


def test_cli_bad_speed(capsys):
    assert main(["examples/jobs.csv", "--speed", "0"]) == 1
