"""The runner launcher's decisions that need no root and no /proc (the rest runs in tests/linux)."""
import json

from ultra96 import model_runner_launch as launcher


def test_a_runner_that_cannot_start_leaves_the_previous_one_untouched_and_names_it(tmp_path, monkeypatch,
                                                                                     capsys):
    pidfile = tmp_path / "model-runner.json"
    pidfile.write_text(json.dumps(dict(pid=4242, start_ticks="99")))
    monkeypatch.setattr(launcher, "alive", lambda pid, ticks: (pid, ticks) == (4242, "99"))
    monkeypatch.setattr(launcher, "stop_previous", lambda *a: (_ for _ in ()).throw(AssertionError))
    options = dict(script=str(tmp_path / "runnr.py"), python=str(tmp_path), args=[],
                   log=str(tmp_path / "runner.log"), pidfile=str(pidfile))
    assert launcher.main([json.dumps(options)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "failed" and "runner script not found" in result["error"]
    assert result["previous"] == "untouched" and result["previous_running"] == 4242


def test_the_recorded_runner_counts_only_while_its_start_time_matches(tmp_path, monkeypatch):
    pidfile = tmp_path / "model-runner.json"
    assert launcher.recorded_runner(pidfile) is None
    pidfile.write_text(json.dumps(dict(pid=7, start_ticks="5")))
    monkeypatch.setattr(launcher, "alive", lambda pid, ticks: ticks == "5")
    assert launcher.recorded_runner(pidfile) == 7
    pidfile.write_text(json.dumps(dict(pid=7, start_ticks="6")))
    assert launcher.recorded_runner(pidfile) is None
    pidfile.write_text("not json")
    assert launcher.recorded_runner(pidfile) is None


def test_the_launcher_reads_the_bridge_lines_it_waits_for(tmp_path):
    log = tmp_path / "server.log"
    log.write_text("old line: " + launcher.REPLACED + "\n")
    offset = log.stat().st_size
    with open(log, "a") as stream:
        stream.write("INFO model runner connected (pid 12)\n")
    text = launcher._log_since(str(log), offset)
    assert "{} (pid 12)".format(launcher.CONNECTED) in text and launcher.REPLACED not in text
    assert launcher._log_since(str(tmp_path / "missing.log"), 0) == ""
