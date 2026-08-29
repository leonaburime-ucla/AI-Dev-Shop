#!/usr/bin/env python3
"""Executable proof for every counting rule in co_change.py.

A history metric that has never been run against a known answer is a number
generator, not a measurement. Each test below fixes one rule from the Co-Change
Coupling section of ../change-history.md.

The negative controls are load-bearing. The cheap way to get this wrong is to
count things that should not count -- a lockfile that moves with every commit, a
directory rename that pairs a hundred files at once, or a pair called `hidden`
because the import scanner never read its language.

Run:  python3 -m pytest harness-engineering/sensors/scripts/ -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from co_change import (  # noqa: E402
    analyse,
    build_history,
    classify_link,
    git_log,
    is_shallow,
    load_import_graph,
    main,
    module_for,
    parse_log,
    Pair,
)

SCRIPT = Path(__file__).parent / "co_change.py"


# ------------------------------------------------------------------ fixtures


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def init_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "config", "commit.gpgsign", "false")


def commit(root: Path, files: dict[str, str], message: str = "change") -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


def history_from(commits: list[list[str]], **kwargs):
    return build_history(
        commits,
        max_commit_files=kwargs.get("max_commit_files", 50),
        extra_excludes=frozenset(kwargs.get("extra_excludes", ())),
    )


def pairs_from(commits: list[list[str]], **kwargs) -> list[Pair]:
    history = history_from(commits, **kwargs)
    return analyse(
        history=history,
        depth=kwargs.get("depth", 0),
        min_support=kwargs.get("min_support", 1),
        min_coupling=kwargs.get("min_coupling", 0.0),
        adjacency=kwargs.get("adjacency"),
        cross_module_only=kwargs.get("cross_module_only", False),
    )


# -------------------------------------------------------------- log parsing


HASH_A = "a" * 40
HASH_B = "b" * 40


def log_text(*commits: list[str]) -> str:
    """Reproduce the NUL field layout `git log -z --pretty=format:\\x01%H%x00` emits."""
    out = []
    for index, paths in enumerate(commits):
        out.append(f"\x01{'ab'[index % 2] * 40}\0")
        for position, path in enumerate(paths):
            out.append(("\n" if position == 0 else "") + path + "\0")
        out.append("\0")
    return "".join(out)


def test_parse_log_splits_on_a_whole_field_header() -> None:
    assert parse_log(log_text(["src/a.py", "src/b.py"], ["src/a.py"])) == [
        ["src/a.py", "src/b.py"],
        ["src/a.py"],
    ]


def test_parse_log_keeps_a_commit_that_touched_nothing() -> None:
    # An empty commit still exists; it just contributes no pairs. Dropping it
    # here would make the commit count disagree with `git log --oneline | wc -l`.
    assert parse_log(log_text([], ["src/a.py"])) == [[], ["src/a.py"]]


def test_parse_log_preserves_a_filename_containing_a_newline() -> None:
    # The whole reason for -z. Line-based parsing turned this into two paths,
    # neither of which named a real file.
    assert parse_log(log_text(["src/line\nbreak.py"])) == [["src/line\nbreak.py"]]


def test_parse_log_preserves_leading_and_trailing_whitespace_in_a_name() -> None:
    # Stripping would rename the file. Only git's own separator newline is removed.
    assert parse_log(log_text([" spaced .py", "b.py"])) == [[" spaced .py", "b.py"]]


def test_parse_log_does_not_treat_a_filename_as_a_commit_header() -> None:
    # A path that merely starts with the sentinel is not a header; only a field
    # that is entirely \x01<hash> is.
    forged = f"\x01{HASH_A} not-a-header.py"
    assert parse_log(log_text([forged, "src/b.py"])) == [[forged, "src/b.py"]]


def test_parse_log_strips_the_separator_newline_from_the_first_path_only() -> None:
    # REGRESSION. The separator newline git writes between the pretty format and
    # the file list precedes the FIRST path only. Removing a leading newline from
    # every field corrupted a file legitimately named "\nsecond.py" into
    # "second.py" -- a path naming no real file.
    raw = "\x01" + "a" * 40 + "\0" + "\n\tfirst.py\0" + "\nsecond.py\0" + "\0"
    assert parse_log(raw) == [["\tfirst.py", "\nsecond.py"]]


def test_parse_log_ignores_noise_before_the_first_commit() -> None:
    assert parse_log("warning: something\0" + log_text(["src/a.py"])) == [["src/a.py"]]


# ------------------------------------------------------------------ counting


def test_support_counts_commits_touching_both_files() -> None:
    commits = [
        ["src/a.py", "src/b.py"],
        ["src/a.py", "src/b.py"],
        ["src/a.py"],
    ]
    history = history_from(commits)
    assert history.pairs[("src/a.py", "src/b.py")] == 2
    assert history.revs["src/a.py"] == 3
    assert history.revs["src/b.py"] == 2


def test_coupling_divides_by_the_busier_file() -> None:
    # b moves only with a; a moves constantly. Dividing by b would call this a
    # perfect 1.00 pair and put a hot file at the top against everything it
    # happens to brush past.
    commits = [["src/a.py", "src/b.py"]] + [["src/a.py"]] * 9
    pair = pairs_from(commits)[0]
    assert pair.revs_a == 10 and pair.revs_b == 1
    assert pair.coupling == pytest.approx(0.1)
    assert pair.confidence_a == pytest.approx(0.1)
    assert pair.confidence_b == pytest.approx(1.0)


def test_a_file_paired_with_itself_is_never_recorded() -> None:
    history = history_from([["src/a.py", "src/a.py"]])
    assert history.pairs == {}


def test_duplicate_paths_in_one_commit_count_once() -> None:
    history = history_from([["src/a.py", "src/b.py", "src/a.py"]])
    assert history.revs["src/a.py"] == 1
    assert history.pairs[("src/a.py", "src/b.py")] == 1


# --------------------------------------------------------- negative controls


def test_bulk_commit_is_dropped_and_counted() -> None:
    sweep = [f"src/f{index}.py" for index in range(60)]
    history = history_from([sweep, ["src/a.py", "src/b.py"]], max_commit_files=50)
    assert history.dropped_bulk == 1
    assert history.commits == 1
    assert history.pairs == {("src/a.py", "src/b.py"): 1}


def test_the_file_cap_applies_after_filtering_not_before() -> None:
    # Three real files plus a lockfile, cap of 3. Applying the cap to the raw
    # list would drop a commit that was only oversized because of a file the
    # filter was about to remove.
    noisy = ["src/a.py", "src/b.py", "src/c.py", "package-lock.json"]
    history = history_from([noisy], max_commit_files=3)
    assert history.dropped_bulk == 0
    assert history.commits == 1


def test_lockfiles_never_produce_pairs() -> None:
    commits = [["src/a.py", "package-lock.json"]] * 5
    assert history_from(commits).pairs == {}


def test_generated_suffixes_never_produce_pairs() -> None:
    commits = [["src/a.py", "src/bundle.min.js", "src/t.snap"]] * 5
    assert history_from(commits).pairs == {}


def test_excluded_directories_are_dropped() -> None:
    commits = [["src/a.py", "node_modules/pkg/index.js"]] * 5
    assert history_from(commits).pairs == {}


def test_extra_excludes_are_honoured() -> None:
    commits = [["src/a.py", "generated/api.py"]] * 5
    assert history_from(commits, extra_excludes=("generated",)).pairs == {}


def test_a_file_in_an_excluded_directory_name_is_kept_when_it_is_the_filename() -> None:
    # `vendor` as a *directory* is excluded; `src/vendor.py` is a source file
    # whose name merely matches. Matching on any path part would eat it.
    history = history_from([["src/vendor.py", "src/a.py"]])
    assert history.pairs == {("src/a.py", "src/vendor.py"): 1}


# ------------------------------------------------------------------ filtering


def test_min_support_filters_thin_pairs() -> None:
    commits = [["src/a.py", "src/b.py"]] * 3
    assert pairs_from(commits, min_support=5) == []
    assert len(pairs_from(commits, min_support=3)) == 1


def test_min_coupling_filters_weak_pairs() -> None:
    commits = [["src/a.py", "src/b.py"]] * 2 + [["src/a.py"]] * 8
    assert pairs_from(commits, min_support=1, min_coupling=0.5) == []
    assert len(pairs_from(commits, min_support=1, min_coupling=0.2)) == 1


def test_cross_module_only_drops_same_directory_pairs() -> None:
    commits = [["src/a.py", "src/b.py"], ["src/a.py", "web/c.py"]] * 5
    kept = pairs_from(commits, cross_module_only=True)
    assert {(p.a, p.b) for p in kept} == {("src/a.py", "web/c.py")}


def test_depth_collapses_modules() -> None:
    commits = [["src/core/a.py", "src/web/b.py"]] * 5
    assert pairs_from(commits, depth=1, cross_module_only=True) == []
    assert len(pairs_from(commits, depth=2, cross_module_only=True)) == 1


def test_module_for_handles_a_root_level_file() -> None:
    assert module_for("README.md", 0) == "."
    assert module_for("src/core/a.py", 0) == "src/core"
    assert module_for("src/core/a.py", 1) == "src"


# --------------------------------------------------------------- import link


def graph(components: dict[str, list[str]]) -> dict:
    return {
        "components": [
            {"name": name, "depends_on": deps, "depended_on_by": []}
            for name, deps in components.items()
        ]
    }


def test_pair_with_an_import_edge_is_linked(tmp_path: Path) -> None:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"web": ["src"], "src": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["src/a.py", "web/c.py"]] * 5
    assert pairs_from(commits, adjacency=adjacency)[0].link == "linked"


def test_import_edge_is_undirected(tmp_path: Path) -> None:
    # Co-change has no direction, so an edge either way explains the pair.
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"src": ["web"], "web": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["src/a.py", "web/c.py"]] * 5
    assert pairs_from(commits, adjacency=adjacency)[0].link == "linked"


def test_pair_with_no_import_edge_is_hidden(tmp_path: Path) -> None:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"src": [], "web": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["src/a.py", "web/c.py"]] * 5
    assert pairs_from(commits, adjacency=adjacency)[0].link == "hidden"


def test_components_absent_from_the_graph_are_ungraphed_not_hidden(tmp_path: Path) -> None:
    # A Go and a Ruby directory in a repo whose import scanner reads Python.
    # Calling that `hidden` turns a coverage gap into a finding.
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"py": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["go/a.go", "rb/b.rb"]] * 5
    assert pairs_from(commits, adjacency=adjacency)[0].link == "ungraphed"


def test_one_side_ungraphed_is_ungraphed_not_hidden(tmp_path: Path) -> None:
    # REGRESSION. An earlier version required *both* endpoints to be absent
    # before saying `ungraphed`, so one Python component paired with one Go
    # component returned `hidden` -- reporting "this language was never scanned"
    # as an undeclared dependency. A scanner that never read `go/` could not
    # have found an edge to it, so its absence is not evidence.
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"src": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["src/a.py", "go/b.go"]] * 5
    assert pairs_from(commits, adjacency=adjacency)[0].link == "ungraphed"


def test_both_endpoints_present_and_no_edge_is_hidden(tmp_path: Path) -> None:
    # Positive control. It does NOT prove the both-endpoints rule -- that is
    # `test_one_side_ungraphed_is_ungraphed_not_hidden` -- it proves the rule
    # did not over-correct into never reporting `hidden` at all.
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"src": [], "web": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    assert pairs_from([["src/a.py", "web/c.py"]] * 5, adjacency=adjacency)[0].link == "hidden"


def test_truncated_import_graph_is_rejected(tmp_path: Path) -> None:
    # A --top-truncated graph is missing components, and every missing one makes
    # its pairs look unlinked. Loading it would convert truncation into findings.
    payload = graph({"src": []})
    payload["run"] = {"components": 12, "components_shown": 1}
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_import_graph(path) is None


def test_complete_import_graph_is_accepted(tmp_path: Path) -> None:
    payload = graph({"src": [], "web": []})
    payload["run"] = {"components": 2, "components_shown": 2}
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_import_graph(path) is not None


def test_same_module_pair_is_never_hidden() -> None:
    pair = Pair(a="src/a.py", b="src/b.py", module_a="src", module_b="src")
    assert classify_link(pair, {"src": set()}) == "same-module"


def test_link_is_unknown_without_a_graph() -> None:
    commits = [["src/a.py", "web/c.py"]] * 5
    assert pairs_from(commits, adjacency=None)[0].link == "unknown"


def test_malformed_import_graph_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "graph.json"
    path.write_text("not json", encoding="utf-8")
    assert load_import_graph(path) is None
    path.write_text(json.dumps({"components": "wrong shape"}), encoding="utf-8")
    assert load_import_graph(path) is None


def test_hidden_pairs_sort_above_stronger_linked_pairs(tmp_path: Path) -> None:
    path = tmp_path / "graph.json"
    path.write_text(json.dumps(graph({"a": ["b"], "b": [], "c": [], "d": []})), encoding="utf-8")
    adjacency = load_import_graph(path)
    commits = [["a/1.py", "b/1.py"]] * 10 + [["c/1.py", "d/1.py"]] * 5
    ranked = pairs_from(commits, adjacency=adjacency)
    assert ranked[0].link == "hidden"
    assert ranked[0].module_a == "c"


# ------------------------------------------------------------------ end-to-end


def real_history(root: Path, **kwargs) -> object:
    return build_history(
        git_log(root, kwargs.get("since", "10 years ago"), kwargs.get("allow_shallow", False)),
        max_commit_files=kwargs.get("max_commit_files", 50),
        extra_excludes=frozenset(kwargs.get("extra_excludes", ())),
    )


def test_reads_a_real_repository(tmp_path: Path) -> None:
    init_repo(tmp_path)
    for index in range(4):
        commit(tmp_path, {"src/a.py": f"a{index}\n", "web/c.py": f"c{index}\n"})
    commit(tmp_path, {"src/a.py": "solo\n"})

    history = real_history(tmp_path)
    assert history.status == "ok"
    assert history.raw_commits == 5
    assert history.commits == 5
    assert history.revs["src/a.py"] == 5
    assert history.revs["web/c.py"] == 4
    assert history.pairs[("src/a.py", "web/c.py")] == 4


def test_merge_commits_do_not_pair_a_whole_branch(tmp_path: Path) -> None:
    init_repo(tmp_path)
    commit(tmp_path, {"src/a.py": "base\n"})
    git(tmp_path, "checkout", "-q", "-b", "feature")
    commit(tmp_path, {"src/b.py": "b\n"})
    commit(tmp_path, {"src/c.py": "c\n"})
    git(tmp_path, "checkout", "-q", "-")
    commit(tmp_path, {"src/d.py": "d\n"})
    git(tmp_path, "merge", "-q", "--no-ff", "-m", "merge", "feature")

    # b and c were committed separately; only the merge would ever pair them.
    assert ("src/b.py", "src/c.py") not in real_history(tmp_path).pairs


def test_a_rename_does_not_pair_a_file_with_its_former_name(tmp_path: Path) -> None:
    # REGRESSION. Under --no-renames git emits BOTH paths on the rename commit,
    # so old.py and new.py became a co-change pair -- a file coupled to itself.
    # The previous default did exactly that while its help text claimed the
    # opposite. Renames are now always detected.
    init_repo(tmp_path)
    commit(tmp_path, {"src/old.py": "a\n", "src/other.py": "z\n"})
    git(tmp_path, "mv", "src/old.py", "src/new.py")
    git(tmp_path, "commit", "-q", "-m", "rename")

    pairs = real_history(tmp_path).pairs
    assert ("src/new.py", "src/old.py") not in pairs


def test_a_filename_needing_git_quoting_survives_round_trip(tmp_path: Path) -> None:
    # Without -z git renders this as "src/line\nbreak.py" (with quotes and an
    # escape), and line-based parsing produced two paths naming no real file.
    init_repo(tmp_path)
    odd = 'src/we"ird.py'
    commit(tmp_path, {odd: "x\n", "src/plain.py": "y\n"})

    history = real_history(tmp_path)
    assert odd in history.revs
    assert not any(name.startswith('"') for name in history.revs)


def test_shallow_clone_is_inactive_not_measured(tmp_path: Path) -> None:
    # REGRESSION. Git reports a shallow boundary commit as touching every file
    # in the snapshot, so one commit paired the whole tree at coupling 1.00.
    origin = tmp_path / "origin"
    origin.mkdir()
    init_repo(origin)
    commit(origin, {"a/x.py": "1\n", "b/y.py": "1\n", "c/z.py": "1\n"})
    commit(origin, {"a/x.py": "2\n"})

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{origin}", str(clone)],
        check=True,
        capture_output=True,
    )
    assert is_shallow(clone) is True

    history = real_history(clone)
    assert history.status == "shallow"
    assert history.inactive is True
    assert history.pairs == {}

    # The override measures it, and the artefact it produces is exactly why the
    # default refuses: one commit, the whole tree, every pair at 1.00.
    overridden = real_history(clone, allow_shallow=True)
    assert overridden.status == "ok"
    assert ("a/x.py", "b/y.py") in overridden.pairs


def test_an_empty_window_is_not_reported_as_an_empty_repository(tmp_path: Path) -> None:
    # REGRESSION. Both collapsed to "no commits in the window". They implicate
    # different things: only the second is a reason to check --since. Git does
    # not reject an unparseable date, it silently substitutes a window, so an
    # empty window is exactly what a typo looks like.
    init_repo(tmp_path)
    commit(tmp_path, {"src/a.py": "a\n"})
    # 2099, not 3000: a year past git's representable range overflows and
    # silently returns *everything*, which is itself the hazard being guarded.
    result = git_log(tmp_path, "2099-01-01", False)
    assert result.status == "empty-window"
    assert "--since" in result.detail
    assert git_log(tmp_path, "10 years ago", False).status == "ok"


def test_empty_repository_reports_no_history(tmp_path: Path) -> None:
    # An unborn branch makes `git log` exit 128. That is a fact about the
    # repository, not a tool failure, and must not be reported as `git-error`.
    init_repo(tmp_path)
    assert git_log(tmp_path, "10 years ago", False).status == "no-history"


def test_not_a_git_repository_is_inactive_not_a_crash(tmp_path: Path) -> None:
    assert git_log(tmp_path, "10 years ago", False).status == "git-error"


def test_all_bulk_history_is_not_reported_as_no_history(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # REGRESSION. `commits` counted only retained commits, so a window whose
    # every commit was dropped as bulk printed "No commits in the window" and
    # never mentioned the dropped commits.
    init_repo(tmp_path)
    commit(tmp_path, {f"src/f{i}.py": "x\n" for i in range(8)})

    history = real_history(tmp_path, max_commit_files=3)
    assert history.raw_commits == 1
    assert history.commits == 0
    assert history.dropped_bulk == 1
    assert history.inactive is False

    assert main([str(tmp_path), "--since", "10 years ago", "--max-commit-files", "3"]) == 0
    out = capsys.readouterr().out
    assert "1 bulk commit(s) dropped" in out
    assert "INACTIVE" not in out


def test_commits_touching_only_excluded_files_are_counted_separately(tmp_path: Path) -> None:
    init_repo(tmp_path)
    commit(tmp_path, {"package-lock.json": "{}\n"})
    commit(tmp_path, {"src/a.py": "a\n", "src/b.py": "b\n"})

    history = real_history(tmp_path)
    assert history.raw_commits == 2
    assert history.dropped_empty == 1
    assert history.commits == 1


def test_no_history_reports_inactive_rather_than_zero(tmp_path: Path) -> None:
    init_repo(tmp_path)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    # Assert the SPECIFIC reason, not just the word INACTIVE. Every status
    # renders as INACTIVE, so the bare check passed even when an unborn
    # repository was misclassified as a git failure.
    assert "repository has no commits" in completed.stdout
    assert "git error" not in completed.stdout.lower()


# ------------------------------------------------------------------------ cli


def test_cli_json_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    init_repo(tmp_path)
    for index in range(5):
        commit(tmp_path, {"src/a.py": f"a{index}\n", "web/c.py": f"c{index}\n"})

    assert main([str(tmp_path), "--since", "10 years ago", "--json", "--min-support", "3"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run"]["commits"] == 5
    assert payload["config"]["min_support"] == 3
    assert len(payload["pairs"]) == 1
    pair = payload["pairs"][0]
    assert (pair["a"], pair["b"]) == ("src/a.py", "web/c.py")
    assert pair["support"] == 5
    assert pair["coupling"] == 1.0
    assert pair["link"] == "unknown"


def test_cli_top_limits_rows_but_not_the_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    init_repo(tmp_path)
    for index in range(5):
        commit(
            tmp_path,
            {"src/a.py": f"a{index}\n", "web/c.py": f"c{index}\n", "api/d.py": f"d{index}\n"},
        )

    assert main([str(tmp_path), "--since", "10 years ago", "--json", "--top", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run"]["pairs_shown"] == 1
    assert payload["run"]["pairs_above_threshold"] == 3
    # The ROW COUNT is the thing --top controls. Asserting only the summary let
    # a table that ignored --top pass.
    assert len(payload["pairs"]) == 1


def test_cli_rejects_an_unreadable_import_graph(tmp_path: Path) -> None:
    init_repo(tmp_path)
    with pytest.raises(SystemExit):
        main([str(tmp_path), "--import-graph", str(tmp_path / "missing.json")])


def test_cli_rejects_a_non_directory(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main([str(tmp_path / "nope")])


def test_cli_always_exits_zero_on_a_real_repo(tmp_path: Path) -> None:
    init_repo(tmp_path)
    commit(tmp_path, {"src/a.py": "a\n"})
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "--since", "10 years ago"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
