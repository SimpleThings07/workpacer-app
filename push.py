#!/usr/bin/env python3

"""
Commit, tag, and push a WorkPacer release to GitHub.

Sources of truth:
- pom.xml       -> application version
- CHANGELOG.md  -> release date and commit body

Commit title:
    [<version>] - <YYYY-MM-DD>

Git tag:
    v<version>

Usage:
    Linux:
        python3 push.py
        python3 push.py --test

    Windows:
        python push.py
        python push.py --test

Test mode:
    Performs all read-only checks, parses the release metadata, lists the files
    that would be committed, and asks for confirmation. It does NOT stage,
    commit, tag, or push anything.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent
POM_FILE = PROJECT_DIRECTORY / "pom.xml"
CHANGELOG_FILE = PROJECT_DIRECTORY / "CHANGELOG.md"
REMOTE_NAME = "origin"
GENERATED_DIRECTORY = "target/"


@dataclass(frozen=True)
class ReleaseMetadata:
    version: str
    date: str
    changelog_body: str

    @property
    def tag(self) -> str:
        return f"v{self.version}"

    @property
    def commit_title(self) -> str:
        return f"[{self.version}] - {self.date}"

    @property
    def tag_message(self) -> str:
        return f"WorkPacer {self.version} - {self.date}"


def main() -> None:
    arguments = parse_arguments()

    verify_git_is_available()
    verify_git_repository()
    verify_required_files_exist()
    verify_origin_exists()
    verify_generated_files_are_ignored()

    release = read_release_metadata()

    verify_tag_does_not_exist(release.tag)

    changed_files = read_changed_files()

    if not changed_files:
        fail("There are no changes to commit.")

    show_release_preview(release, changed_files, arguments.test)

    if not user_accepts_push(arguments.test):
        print("\nPush cancelled. No files were committed or pushed.")
        return

    if arguments.test:
        show_test_mode_success(release)
        return

    stage_all_changes()
    verify_staged_files_match_reviewed_files(changed_files)

    create_commit(release)
    create_annotated_tag(release)
    push_current_branch()
    push_tag(release.tag)

    show_success(release)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commit, tag, and push the current WorkPacer release."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help=(
            "Run in test mode. Perform all read-only checks and show what would "
            "be committed, but do not stage, commit, tag, or push anything."
        ),
    )
    return parser.parse_args()


def verify_git_is_available() -> None:
    if shutil.which("git") is None:
        fail("Git is not installed or is not available on PATH.")


def verify_git_repository() -> None:
    result = run_git(
        "rev-parse",
        "--is-inside-work-tree",
        capture_output=True,
        check=False,
    )

    if result.returncode != 0 or result.stdout.strip() != "true":
        fail(
            "The project directory is not inside a Git repository.\n"
            f"Project directory: {PROJECT_DIRECTORY}"
        )


def repository_has_commits() -> bool:
    result = run_git(
        "rev-parse",
        "--verify",
        "HEAD",
        capture_output=True,
        check=False,
    )

    return result.returncode == 0


def verify_required_files_exist() -> None:
    missing_files = [
        path.name
        for path in (POM_FILE, CHANGELOG_FILE)
        if not path.is_file()
    ]

    if missing_files:
        formatted = "\n".join(f"  - {name}" for name in missing_files)
        fail(
            "Required project files are missing:\n"
            f"{formatted}"
        )


def verify_origin_exists() -> None:
    result = run_git(
        "remote",
        "get-url",
        REMOTE_NAME,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        fail(
            f"Git remote '{REMOTE_NAME}' is not configured.\n"
            "Configure the GitHub remote before running push.py."
        )


def verify_generated_files_are_ignored() -> None:
    result = run_git(
        "check-ignore",
        "-q",
        GENERATED_DIRECTORY,
        check=False,
    )

    if result.returncode != 0:
        fail(
            "The generated 'target/' directory is not ignored by Git.\n"
            "Add 'target/' to .gitignore before using push.py."
        )


def read_release_metadata() -> ReleaseMetadata:
    version = read_project_version()
    date, changelog_body = read_changelog_entry(version)

    return ReleaseMetadata(
        version=version,
        date=date,
        changelog_body=changelog_body,
    )


def read_project_version() -> str:
    try:
        tree = ET.parse(POM_FILE)
    except ET.ParseError as error:
        fail(f"Cannot parse pom.xml: {error}")

    root = tree.getroot()

    namespace_match = re.match(r"\{(.+)\}", root.tag)
    namespace = namespace_match.group(1) if namespace_match else ""

    version_tag = f"{{{namespace}}}version" if namespace else "version"
    version_element = root.find(version_tag)

    if version_element is None or not version_element.text:
        fail(
            "Cannot find the project version in pom.xml.\n"
            "Expected a project-level <version> element."
        )

    version = version_element.text.strip()

    if not version:
        fail("The project version in pom.xml is empty.")

    return version


def read_changelog_entry(version: str) -> tuple[str, str]:
    changelog = CHANGELOG_FILE.read_text(encoding="utf-8")

    heading_pattern = re.compile(
        rf"^##\s+\[{re.escape(version)}\]\s+-\s+"
        rf"(\d{{4}}-\d{{2}}-\d{{2}})\s*$",
        re.MULTILINE,
    )

    match = heading_pattern.search(changelog)

    if match is None:
        fail(
            f"CHANGELOG.md does not contain an entry for version {version}.\n\n"
            "Add an entry in this format:\n\n"
            f"    ## [{version}] - YYYY-MM-DD\n\n"
            "Then describe the release changes below that heading."
        )

    date = match.group(1)
    verify_iso_date(date)

    body_start = match.end()
    next_release = re.search(
        r"^##\s+",
        changelog[body_start:],
        re.MULTILINE,
    )

    if next_release is None:
        body = changelog[body_start:].strip()
    else:
        body_end = body_start + next_release.start()
        body = changelog[body_start:body_end].strip()

    if not body:
        fail(
            f"The CHANGELOG.md entry for version {version} is empty.\n"
            "Add the release details before running push.py."
        )

    return date, body


def verify_iso_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        fail(
            f"Invalid release date '{value}' in CHANGELOG.md.\n"
            "Use the ISO format YYYY-MM-DD."
        )


def verify_tag_does_not_exist(tag: str) -> None:
    if local_tag_exists(tag):
        fail_existing_version(tag, "locally")

    if remote_tag_exists(tag):
        fail_existing_version(tag, f"on '{REMOTE_NAME}'")


def local_tag_exists(tag: str) -> bool:
    result = run_git(
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/tags/{tag}",
        check=False,
    )

    return result.returncode == 0


def remote_tag_exists(tag: str) -> bool:
    result = run_git(
        "ls-remote",
        "--exit-code",
        "--tags",
        REMOTE_NAME,
        f"refs/tags/{tag}",
        capture_output=True,
        check=False,
    )

    if result.returncode == 0:
        return True

    if result.returncode == 2:
        return False

    details = result.stderr.strip() or result.stdout.strip()

    fail(
        f"Could not check whether Git tag '{tag}' exists on '{REMOTE_NAME}'."
        + (f"\n\nGit reported:\n{details}" if details else "")
    )


def fail_existing_version(tag: str, location: str) -> None:
    version = tag.removeprefix("v")

    fail(
        f"Git tag '{tag}' already exists {location}.\n\n"
        f"Version {version} has already been released and must not be overwritten.\n\n"
        "Increment the application version in:\n\n"
        "    pom.xml\n\n"
        "For example:\n\n"
        f"    <version>{next_patch_version(version)}</version>\n\n"
        "Then add the corresponding release entry to:\n\n"
        "    CHANGELOG.md\n\n"
        "After updating the version, run build.py and release.py again before pushing."
    )


def next_patch_version(version: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)

    if match is None:
        return "<new-version>"

    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def read_changed_files() -> set[str]:
    if not repository_has_commits():
        return read_git_paths(
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
        )

    tracked_changes = read_git_paths(
        "diff",
        "--name-only",
        "--no-renames",
        "--relative",
        "HEAD",
        "--",
    )

    untracked_files = read_git_paths(
        "ls-files",
        "--others",
        "--exclude-standard",
    )

    return tracked_changes | untracked_files


def read_staged_files() -> set[str]:
    if not repository_has_commits():
        return read_git_paths(
            "ls-files",
            "--cached",
        )

    return read_git_paths(
        "diff",
        "--cached",
        "--name-only",
        "--no-renames",
        "--relative",
        "HEAD",
        "--",
    )


def read_git_paths(*arguments: str) -> set[str]:
    result = run_git(
        *arguments,
        capture_output=True,
        check=True,
    )

    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    }


def show_release_preview(
    release: ReleaseMetadata,
    changed_files: set[str],
    test_mode: bool,
) -> None:
    print_header("Push Preview")

    if test_mode:
        print("TEST MODE: no Git changes will be made and nothing will be pushed.\n")

    print(f"Commit: {release.commit_title}")
    print(f"Tag:    {release.tag}")
    print(f"Branch: {current_branch()}")

    if not repository_has_commits():
        print("State:  first commit")

    print()
    print("Files to be committed:")
    print()

    show_git_status()

    print()
    print("Commit body from CHANGELOG.md:")
    print()
    print(release.changelog_body)

    print()
    print(f"Total files: {len(changed_files)}")


def show_git_status() -> None:
    result = run_git(
        "status",
        "--short",
        "--untracked-files=all",
        capture_output=True,
        check=True,
    )

    status = result.stdout.rstrip()

    if status:
        print(status)


def user_accepts_push(test_mode: bool) -> bool:
    action = "simulate commit and push" if test_mode else "commit, tag, and push"

    try:
        answer = input(f"\nProceed with {action}? [y/N]: ").strip().lower()
    except EOFError:
        return False

    return answer in {"y", "yes"}


def stage_all_changes() -> None:
    print_header("Staging Changes")
    run_git("add", "--all", check=True)


def verify_staged_files_match_reviewed_files(
    reviewed_files: set[str],
) -> None:
    staged_files = read_staged_files()

    if staged_files == reviewed_files:
        return

    newly_staged = staged_files - reviewed_files
    missing = reviewed_files - staged_files

    details = []

    if newly_staged:
        details.append(
            "Unexpected files were staged:\n"
            + "\n".join(f"  + {path}" for path in sorted(newly_staged))
        )

    if missing:
        details.append(
            "Reviewed files are missing from the staged commit:\n"
            + "\n".join(f"  - {path}" for path in sorted(missing))
        )

    fail(
        "The staged files do not match the files you reviewed.\n\n"
        + "\n\n".join(details)
        + "\n\nNothing has been committed or pushed."
    )


def create_commit(release: ReleaseMetadata) -> None:
    print_header("Creating Commit")

    run_git(
        "commit",
        "-m",
        release.commit_title,
        "-m",
        release.changelog_body,
        check=True,
    )


def create_annotated_tag(release: ReleaseMetadata) -> None:
    print_header(f"Creating Tag {release.tag}")

    run_git(
        "tag",
        "-a",
        release.tag,
        "-m",
        release.tag_message,
        check=True,
    )


def push_current_branch() -> None:
    branch = current_branch()

    print_header(f"Pushing Branch '{branch}'")

    if has_upstream_branch():
        run_git("push", check=True)
    else:
        run_git(
            "push",
            "--set-upstream",
            REMOTE_NAME,
            branch,
            check=True,
        )


def push_tag(tag: str) -> None:
    print_header(f"Pushing Tag '{tag}'")

    run_git(
        "push",
        REMOTE_NAME,
        tag,
        check=True,
    )


def current_branch() -> str:
    result = run_git(
        "branch",
        "--show-current",
        capture_output=True,
        check=True,
    )

    branch = result.stdout.strip()

    if not branch:
        fail("Cannot push from a detached HEAD.")

    return branch


def has_upstream_branch() -> bool:
    result = run_git(
        "rev-parse",
        "--abbrev-ref",
        "@{upstream}",
        capture_output=True,
        check=False,
    )

    return result.returncode == 0


def show_test_mode_success(release: ReleaseMetadata) -> None:
    print_header("Test Mode Successful")

    print("All push checks passed.")
    print()
    print(f"Would create commit: {release.commit_title}")
    print(f"Would create tag:    {release.tag}")
    print()
    print("No files were staged.")
    print("No commit was created.")
    print("No tag was created.")
    print("Nothing was pushed to GitHub.")


def show_success(release: ReleaseMetadata) -> None:
    print_header("Push Successful")

    print(f"Commit: {release.commit_title}")
    print(f"Tag:    {release.tag}")
    print()
    print("The changes and release tag were pushed successfully.")


def run_git(
    *arguments: str,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=PROJECT_DIRECTORY,
            capture_output=capture_output,
            text=True,
            check=check,
        )
    except subprocess.CalledProcessError as error:
        command = "git " + " ".join(arguments)

        details = ""
        if error.stderr:
            details = f"\n\nGit reported:\n{error.stderr.strip()}"
        elif error.stdout:
            details = f"\n\nGit reported:\n{error.stdout.strip()}"

        fail(
            f"Command failed:\n\n    {command}"
            f"{details}"
        )


def print_header(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def fail(message: str) -> None:
    print()
    print("=" * 60)
    print("PUSH FAILED")
    print("=" * 60)
    print()
    print(message)
    sys.exit(1)


if __name__ == "__main__":
    main()
