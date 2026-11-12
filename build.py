#!/usr/bin/env python3

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent
SMOKE_TEST_DURATION_SECONDS = 3

JAVAFX_MODULE_NAMES = (
    "base",
    "graphics",
    "controls",
)


def main ():

    maven = find_maven ()

    build_and_verify (maven)

    jar = find_built_jar (maven)
    javafx_modules = find_javafx_modules (maven)

    smoke_test (jar, javafx_modules)

    report_success (jar)


def find_maven ():

    if command_exists("mvn"):
        return ["mvn"]

    raise RuntimeError ("Maven was not found.")


def build_and_verify (maven):

    print_step("Building and verifying WorkPacer")

    command = [
        *maven,
        "clean",
        "verify",
    ]

    run_gui_command (command)


def find_built_jar (maven):

    final_name = read_maven_property (
        maven,
        "project.build.finalName",
    )

    jar = (
            PROJECT_DIRECTORY
            / "target"
            / f"{final_name}.jar"
    )

    if not jar.exists ():
        raise RuntimeError (f"Expected JAR was not created:\n{jar}")

    return jar


def find_javafx_modules (maven):

    javafx_version = read_maven_property (
        maven,
        "javafx.version",
    )

    classifier = javafx_classifier()
    repository = maven_repository()

    modules = [
        javafx_module_jar (
            repository,
            module_name,
            javafx_version,
            classifier,
        )
        for module_name in JAVAFX_MODULE_NAMES
    ]

    missing_modules = [
        module
        for module in modules
        if not module.exists()
    ]

    if missing_modules:
        missing = "\n".join(
            str(module)
            for module in missing_modules
        )

        fail (
            "Required JavaFX modules were not found:\n"
            f"{missing}"
        )

    return modules


def maven_repository ( ):
    return (
            Path.home()
            / ".m2"
            / "repository"
            / "org"
            / "openjfx"
    )


def javafx_module_jar (
    repository,
    module_name,
    version,
    classifier,
):
    artifact = f"javafx-{module_name}"

    return (
        repository
        / artifact
        / version
        / f"{artifact}-{version}-{classifier}.jar"
    )


def javafx_classifier():

    if is_linux():
        return "linux"

    if is_windows():
        return "win"

    if is_macos():
        return "mac"

    raise RuntimeError (f"Unsupported operating system: {sys.platform}")


def smoke_test (
    jar,
    javafx_modules
):
    print_step ("Smoke-testing generated JAR")

    print (f"Starting {jar.name}")

    command = java_command(
        jar,
        javafx_modules,
    )

    process = start_gui_process(command)

    try:
        verify_process_stays_running(process)
    finally:
        stop_process(process)

    print("JAR smoke test passed.")


def java_command ( jar, javafx_modules):

    module_path = os.pathsep.join(
        str(module)
        for module in javafx_modules
    )

    return [
        "java",
        "--module-path",
        module_path,
        "--add-modules",
        "javafx.controls",
        "-jar",
        str (jar),
    ]


def verify_process_stays_running (process):

    time.sleep (SMOKE_TEST_DURATION_SECONDS)

    exit_code = process.poll()

    if exit_code is not None:
        raise RuntimeError (
            "The generated JAR terminated during startup "
            f"with exit code {exit_code}."
        )

    print (
        "Application remained running for "
        f"{SMOKE_TEST_DURATION_SECONDS} seconds."
    )


def start_gui_process (command):

    ensure_gui_environment_is_available()

    return subprocess.Popen (
        gui_command(command),
        cwd=PROJECT_DIRECTORY,
        start_new_session=is_posix(),
    )


def run_gui_command (command):

    ensure_gui_environment_is_available()

    subprocess.run (
        gui_command(command),
        cwd=PROJECT_DIRECTORY,
        check=True,
    )


def gui_command (command):
    if is_linux():
        return [
            "xvfb-run",
            "-a",
            *command,
        ]

    return command


def command_exists (command: str) -> bool:
    return shutil.which(command) is not None


def ensure_gui_environment_is_available ( ):

    if is_linux ( ) and not command_exists ("xvfb-run"):
        raise RuntimeError (
            "xvfb-run is required to execute "
            "the WorkPacer GUI tests."
        )


def stop_process (process):
    if process.poll() is not None:
        return

    if is_posix():
        os.killpg(
            process.pid,
            signal.SIGTERM,
        )
    else:
        process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        force_stop_process(process)


def force_stop_process ( process):
    if is_posix():
        os.killpg(
            process.pid,
            signal.SIGKILL,
        )
    else:
        process.kill()

    process.wait()


def read_maven_property (
        maven,
        property_name
):
    result = subprocess.run(
        [
            *maven,
            "help:evaluate",
            f"-Dexpression={property_name}",
            "-q",
            "-DforceStdout",
        ],
        cwd=PROJECT_DIRECTORY,
        text=True,
        capture_output=True,
        check=True,
    )

    value = result.stdout.strip()

    if not value:
        raise RuntimeError (
            f"Maven property '{property_name}' "
            "could not be determined."
        )

    return value


def report_success(jar):
    print()
    print("=" * 60)
    print("WorkPacer build successful")
    print("=" * 60)
    print(f"Artifact: {jar}")


def print_step(description):
    print()
    print("=" * 60)
    print(description)
    print("=" * 60)


def is_linux():
    return sys.platform.startswith("linux")


def is_windows():
    return sys.platform == "win32"


def is_macos():
    return sys.platform == "darwin"


def is_posix():
    return os.name == "posix"


if __name__ == "__main__":

    try:
        main()

    except subprocess.CalledProcessError as error:
        print()
        print(
            "BUILD FAILED: "
            f"command returned exit code {error.returncode}."
        )
        sys.exit(error.returncode)

    except RuntimeError as error:
        print()
        print(f"BUILD FAILED: {error}")
        sys.exit(1)