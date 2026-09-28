"""Offline recording helpers use one capture and preserve failed observations."""
import importlib
import importlib.util
import json
import struct

import pytest


def api():
    assert importlib.util.find_spec("tools.video_evidence") is not None, "video evidence helpers are missing"
    return importlib.import_module("tools.video_evidence")


def capture(tmp_path, name="capture", *, completed=(0, 0)):
    folder = tmp_path / name
    folder.mkdir()
    devices = {}
    for device, count, commands in ((1, 3, completed[0]), (2, 4, completed[1])):
        devices[str(device)] = {
            "clean": True, "protected_ble": True, "unfinished": False,
            "input": "physical", "received": count, "sent": count, "acked": count,
            "source": {"device_id": device, "boot_id": 100 + device,
                       "complete": True, "clean": True, "generated": count,
                       "source_submitted": count, "received": count, "acked": count,
                       "missing_received": 0, "missing_acked": 0},
            "commands": {"accepted": commands, "rejected": 0, "completed": commands,
                         "failed": 0, "pending": 0},
        }
    report = {"clean": True, "mock_input": False, "report_saved": True,
              "session_id": "video-session", "devices": devices,
              "run": {"mode": "physical", "session_id": "video-session"}}
    write_json(folder / "report.json", report)
    (folder / "exit-code.txt").write_text("0\n", encoding="utf-8")
    return folder


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def sensor(device, *, boot=None, seq=7):
    boot = 100 + device if boot is None else boot
    values = [32767, -32768, -1, 0, 1, 123, -456, 789]
    return {"timestamp_utc": "2026-09-29T00:00:00+00:00", "monotonic_seconds": 1.0,
            "type": "sensor", "device_id": device, "direction": "ESP->laptop",
            "version": 2, "boot_id": boot, "seq": seq, "uptime_ms": 100,
            "values": values, "raw_hex": struct.pack("<2sBBIII8h", b"W7", 2, device,
                boot, seq, 100, *values).hex(), "validation": "decoded",
            "received_monotonic": 1.0}


def ack(device, *, boot=None, seq=7):
    return {"timestamp_utc": "2026-09-29T00:00:00.1+00:00", "monotonic_seconds": 1.1,
            "type": "sensor_ack", "device_id": device, "direction": "Ultra96->laptop",
            "seq": seq, "boot_id": 100 + device if boot is None else boot,
            "validation": "accepted"}


def packets(folder, rows):
    (folder / "packets.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def observations(folder):
    return [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(folder.glob("phone-observation-*.json"))]


def test_packet_examples_pair_exact_boot_and_sequence_and_show_all_values(tmp_path, capsys):
    folder = capture(tmp_path)
    packets(folder, [sensor(1, boot=99), ack(1), sensor(2), sensor(1), ack(2)])
    assert api().show_packet_examples(folder) is True
    output = capsys.readouterr().out
    assert str(folder.resolve()) in output
    assert "32767, -32768, -1, 0, 1, 123, -456, 789" in output
    assert '"device_id": 1' in output and '"device_id": 2' in output
    assert '"boot_id": 99' not in output
    assert "sensor_ack" in output and "accepted" in output
    assert "video-session" in output and "report.json" in output
    assert "request_id" in output and "null" in output


@pytest.mark.parametrize("change", ["wrong_boot", "wrong_seq", "wrong_device"])
def test_packet_examples_do_not_match_partial_identity(tmp_path, capsys, change):
    folder = capture(tmp_path)
    wrong = ack(1)
    wrong[{"wrong_boot": "boot_id", "wrong_seq": "seq", "wrong_device": "device_id"}[change]] += 1
    packets(folder, [sensor(1), wrong, sensor(2), ack(2)])
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("extra", [
    {"session_id": "another-session"}, {"request_id": 7}, {"version": 1},
])
def test_packet_examples_reject_conflicting_extended_ack_identity(tmp_path, capsys, extra):
    folder = capture(tmp_path)
    packets(folder, [sensor(1), dict(ack(1), **extra), sensor(2), ack(2)])
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("tail", ["{broken\n", "[]\n", '{"type":"sensor","device_id":1}\n',
                                    '{"type":"sensor_ack","device_id":1,"device_id":2}\n'])
def test_packet_examples_reject_corruption_even_after_both_examples(tmp_path, capsys, tail):
    folder = capture(tmp_path)
    packets(folder, [sensor(1), ack(1), sensor(2), ack(2)])
    with (folder / "packets.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(tail)
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


def test_packet_examples_never_fill_a_missing_device_from_another_capture(tmp_path, capsys):
    requested, other = capture(tmp_path, "requested"), capture(tmp_path, "other")
    packets(requested, [sensor(1), ack(1)])
    packets(other, [sensor(2), ack(2)])
    assert api().show_packet_examples(requested) is False
    assert "NOT PASSED" in capsys.readouterr().out


def test_packet_examples_reject_raw_and_decoded_value_disagreement(tmp_path, capsys):
    folder = capture(tmp_path)
    row = sensor(1)
    row["values"][7] = 800
    packets(folder, [row, ack(1), sensor(2), ack(2)])
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


def test_packet_examples_need_a_session_context_and_both_files(tmp_path, capsys):
    folder = capture(tmp_path)
    packets(folder, [sensor(1), ack(1), sensor(2), ack(2)])
    write_json(folder / "report.json", {"session_id": ""})
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


def test_phone_observation_matches_source_and_completed_commands_with_manual_provenance(tmp_path, capsys):
    folder = capture(tmp_path, completed=(1, 2))
    original_report = (folder / "report.json").read_bytes()
    assert api().record_phone_observation(folder, 50, 60) == 0
    output = capsys.readouterr().out
    record, = observations(folder)
    assert record["source"] == "operator-entered"
    assert record["capture_directory"] == str(folder.resolve())
    assert record["p0"] == 50 and record["p1"] == 60
    assert record["delta"] == 10 and record["expected"] == 10
    assert record["capture_clean"] is True and record["matched"] is True
    assert record["passed"] is True and record["timestamp_utc"]
    assert "P0=50" in output and "P1=60" in output and "delta=10" in output
    assert "expected=10" in output and "MATCH" in output
    assert "operator-entered" in output and "per-result" in output
    assert (folder / "report.json").read_bytes() == original_report


def test_phone_mismatch_is_saved_without_overwriting_prior_observations(tmp_path, capsys):
    folder = capture(tmp_path)
    assert api().record_phone_observation(folder, 0, 7) == 0
    first = next(folder.glob("phone-observation-*.json"))
    before = first.read_bytes()
    assert api().record_phone_observation(folder, 0, 6) != 0
    assert first.read_bytes() == before
    records = observations(folder)
    assert len(records) == 2
    failed, = [row for row in records if not row["passed"]]
    assert failed["delta"] == 6 and failed["expected"] == 7
    assert failed["matched"] is False and failed["reason"]
    assert "NOT PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("launcher_exit", [7, True, "0"])
def test_launcher_failure_cannot_match_an_otherwise_clean_capture(tmp_path, capsys, launcher_exit):
    folder = capture(tmp_path)
    assert api().record_phone_observation(folder, 0, 7, launcher_exit_code=launcher_exit) != 0
    record, = observations(folder)
    assert record["launcher_exit_code"] == launcher_exit
    assert record["passed"] is False and record["matched"] is False
    assert record["expected"] is None
    assert record["p0"] == 0 and record["p1"] == 7 and record["delta"] == 7
    assert "launcher" in record["reason"].lower()
    output = capsys.readouterr().out
    assert "NOT PASSED" in output and "MATCH:" not in output


def test_successful_launcher_exit_is_preserved_with_matching_phone_observation(tmp_path, capsys):
    folder = capture(tmp_path)
    assert api().record_phone_observation(folder, 0, 7, launcher_exit_code=0) == 0
    record, = observations(folder)
    assert record["launcher_exit_code"] == 0
    assert record["passed"] is True and record["matched"] is True
    assert "MATCH:" in capsys.readouterr().out


@pytest.mark.parametrize("failure", ["dirty", "mock", "missing_report", "corrupt_report",
                                     "missing_exit", "nonzero_exit", "invalid_exit", "unclean_device"])
def test_phone_matching_count_cannot_pass_invalid_capture_and_still_saves_record(tmp_path, capsys, failure):
    folder = capture(tmp_path)
    report = json.loads((folder / "report.json").read_text())
    if failure == "dirty":
        report["clean"] = False
    elif failure == "mock":
        report["mock_input"] = True
    elif failure == "unclean_device":
        report["devices"]["2"]["source"]["acked"] = 3
    write_json(folder / "report.json", report)
    if failure == "missing_report":
        (folder / "report.json").unlink()
    elif failure == "corrupt_report":
        (folder / "report.json").write_text("{broken", encoding="utf-8")
    elif failure == "missing_exit":
        (folder / "exit-code.txt").unlink()
    elif failure in ("nonzero_exit", "invalid_exit"):
        (folder / "exit-code.txt").write_text("7" if failure == "nonzero_exit" else "bad")
    assert api().record_phone_observation(folder, 0, 7) != 0
    record, = observations(folder)
    assert record["passed"] is False and record["capture_clean"] is False
    assert record["expected"] is None and record["matched"] is False
    assert record["reason"]
    assert "NOT PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("p0,p1", [(-1, 7), (0, -1), (8, 7), (False, 7), (0, True),
                                  (0.0, 7), (0, "7"), (float("nan"), 7), (0, float("inf"))])
def test_phone_invalid_counter_input_is_not_coerced_and_is_saved(tmp_path, capsys, p0, p1):
    folder = capture(tmp_path)
    assert api().record_phone_observation(folder, p0, p1) != 0
    record, = observations(folder)
    assert record["passed"] is False and record["delta"] is None
    assert record["reason"]
    assert "NOT PASSED" in capsys.readouterr().out


def test_packet_examples_reject_overflowing_json_number_in_metadata(tmp_path, capsys):
    folder = capture(tmp_path)
    packets(folder, [sensor(1), ack(1), sensor(2), ack(2)])
    with (folder / "packets.jsonl").open("a", encoding="utf-8") as stream:
        stream.write('{"type":"BLE_disconnected","monotonic_seconds":1e999}\n')
    assert api().show_packet_examples(folder) is False
    assert "NOT PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("commands", [{"completed": True}, {"completed": -1},
                                     {"completed": "2"}, {"completed": 1, "failed": 1}, []])
def test_phone_rejects_corrupt_command_counts_before_computing_expected(tmp_path, capsys, commands):
    folder = capture(tmp_path)
    report = json.loads((folder / "report.json").read_text())
    report["devices"]["1"]["commands"] = commands
    write_json(folder / "report.json", report)
    assert api().record_phone_observation(folder, 0, 7) != 0
    record, = observations(folder)
    assert record["passed"] is False and record["expected"] is None
    assert "NOT PASSED" in capsys.readouterr().out
