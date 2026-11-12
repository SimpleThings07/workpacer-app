#!/usr/bin/env python3

"""
Create self-contained WorkPacer release packages.

release.py packages an already built and verified WorkPacer JAR into
ready-to-ship, self-contained applications.

Before creating a release, run:

    python3 build.py

build.py is responsible for:
    - building the application
    - running all automated tests
    - creating the WorkPacer JAR
    - smoke-testing the generated JAR

release.py is responsible for:
    - using the existing WorkPacer JAR
    - creating self-contained applications
    - smoke-testing the packaged applications
    - creating the final release archives


Usage on Linux
--------------

Create a Linux release:

    python3 release.py --target linux

Create a Windows release from Linux using the default Windows JDK:

    python3 release.py --target windows

The default Windows JDK location on Linux is:

    /usr/lib/jvm/jdk-25-windows-x64

Override the default Windows JDK:

    python3 release.py \
        --target windows \
        --windows-jdk /path/to/windows/jdk

Create Linux and Windows releases:

    python3 release.py --target all

Create both releases using another Windows JDK:

    python3 release.py \
        --target all \
        --windows-jdk /path/to/windows/jdk


Usage on Windows
----------------

Create a native Windows release:

    python release.py --target windows

The --windows-jdk argument is not required when running release.py
natively on Windows.


Supported host/target combinations
----------------------------------

Linux host:
    --target linux      supported
    --target windows    supported
    --target all        supported

Windows host:
    --target windows    supported
    --target linux      not supported
    --target all        not supported


Release artifacts
-----------------

Linux:

    target/release/WorkPacer-<version>-linux.zip

Windows:

    target/release/WorkPacer-<version>-windows.zip

The generated release packages are self-contained. The target machine
does not need a separately installed Java runtime, JavaFX SDK, Maven,
or Python.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import textwrap
import time

from dataclasses import dataclass
from pathlib import Path


APPLICATION_NAME = "WorkPacer"

PROJECT_DIRECTORY = Path(__file__).resolve().parent
TARGET_DIRECTORY = PROJECT_DIRECTORY / "target"
STAGING_DIRECTORY = TARGET_DIRECTORY / "release-staging"
RELEASE_DIRECTORY = TARGET_DIRECTORY / "release"

DEFAULT_WINDOWS_JDK = Path (
    "/usr/lib/jvm/jdk-25-windows-x64"
)

SMOKE_TEST_DURATION_SECONDS = 3

JAVAFX_MODULES = (
    "javafx-base",
    "javafx-graphics",
    "javafx-controls",
)


@dataclass(frozen=True)
class ProjectMetadata:
    version: str
    final_name: str
    main_class: str
    javafx_version: str


def main():
    arguments = parse_arguments()

    validate_release_target(
        arguments.target
    )

    validate_release_environment(
        arguments.target
    )

    windows_jdk = resolve_windows_jdk(
        arguments
    )

    metadata = read_project_metadata()
    jar = find_built_jar(metadata)

    prepare_release_directories()

    if arguments.target in ("linux", "all"):
        release_linux(
            jar,
            metadata,
        )

    if arguments.target in ("windows", "all"):
        release_windows(
            jar,
            metadata,
            windows_jdk,
        )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create self-contained WorkPacer release packages."
    )

    parser.add_argument(
        "--target",
        choices=("linux", "windows", "all"),
        required=True,
        help="Release target to create.",
    )

    parser.add_argument(
        "--windows-jdk",
        type=Path,
        help=(
            "Windows JDK used when cross-building Windows from Linux. "
            f"Default: {DEFAULT_WINDOWS_JDK}"
        ),
    )

    return parser.parse_args()


def validate_release_target(
        target,
):
    if is_windows() and target in ("linux", "all"):
        raise RuntimeError(
            "Linux releases cannot currently be created "
            "from a Windows host."
        )

    if not is_linux() and not is_windows():
        raise RuntimeError(
            f"Unsupported build host: {sys.platform}"
        )


def validate_release_environment(
        target,
):
    require_command(
        maven_command(),
        "Maven is required to create a release.",
    )

    if target in ("linux", "all"):
        require_command(
            "jpackage",
            "jpackage is required to create the Linux release.",
        )

        require_command(
            "xvfb-run",
            "xvfb-run is required to smoke-test the Linux release.",
        )

    if target in ("windows", "all"):
        validate_windows_release_environment()


def validate_windows_release_environment():
    if is_windows():
        require_command(
            "jpackage",
            "jpackage is required to create the Windows release.",
        )

        return

    require_command(
        "jlink",
        "jlink is required to cross-build the Windows release.",
    )

    require_command(
        "launch4j",
        "Launch4j is required to cross-build the Windows release.",
    )


def resolve_windows_jdk(
        arguments,
):
    if arguments.target not in ("windows", "all"):
        return None

    if is_windows():
        return None

    windows_jdk = (
            arguments.windows_jdk
            or DEFAULT_WINDOWS_JDK
    )

    return require_windows_jdk(
        windows_jdk
    )


def require_windows_jdk(
        windows_jdk,
):
    windows_jdk = (
        windows_jdk
        .expanduser()
        .resolve()
    )

    jmods = (
            windows_jdk
            / "jmods"
    )

    if not jmods.is_dir():
        raise RuntimeError(
            "The Windows JDK was not found or does not "
            "contain a jmods directory.\n"
            f"Windows JDK: {windows_jdk}\n"
            "Use --windows-jdk <path> to specify another JDK."
        )

    return windows_jdk


def read_project_metadata():
    return ProjectMetadata(
        version=read_maven_property(
            "project.version"
        ),
        final_name=read_maven_property(
            "project.build.finalName"
        ),
        main_class=read_maven_property(
            "main.class"
        ),
        javafx_version=read_maven_property(
            "javafx.version"
        ),
    )


def find_built_jar(
        metadata,
):
    jar = (
            TARGET_DIRECTORY
            / f"{metadata.final_name}.jar"
    )

    if not jar.exists():
        raise RuntimeError(
            "No built WorkPacer JAR was found.\n"
            f"Expected: {jar}\n"
            "Run build.py before creating a release."
        )

    return jar


def prepare_release_directories():
    STAGING_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    RELEASE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def release_linux(
        jar,
        metadata,
):
    print_step(
        "Creating Linux release"
    )

    application = create_native_application(
        jar,
        metadata,
        platform="linux",
        javafx_classifier="linux",
    )

    smoke_test_linux_application(
        application
    )

    archive = create_archive(
        application,
        f"{APPLICATION_NAME}-{metadata.version}-linux",
    )

    report_release(
        "Linux",
        application,
        archive,
    )


def release_windows(
        jar,
        metadata,
        windows_jdk,
):
    if is_windows():
        release_windows_natively(
            jar,
            metadata,
        )

        return

    release_windows_from_linux(
        jar,
        metadata,
        windows_jdk,
    )


def release_windows_natively(
        jar,
        metadata,
):
    print_step(
        "Creating Windows release"
    )

    application = create_native_application(
        jar,
        metadata,
        platform="windows",
        javafx_classifier="win",
    )

    smoke_test_native_windows_application(
        application
    )

    archive = create_archive(
        application,
        f"{APPLICATION_NAME}-{metadata.version}-windows",
    )

    report_release(
        "Windows",
        application,
        archive,
    )


def release_windows_from_linux(
        jar,
        metadata,
        windows_jdk,
):
    print_step(
        "Creating Windows release"
    )

    application = create_cross_built_windows_application(
        jar,
        metadata,
        windows_jdk,
    )

    smoke_test_cross_built_windows_application(
        application
    )

    archive = create_archive(
        application,
        f"{APPLICATION_NAME}-{metadata.version}-windows",
    )

    report_release(
        "Windows",
        application,
        archive,
    )


def create_native_application(
        jar,
        metadata,
        platform,
        javafx_classifier,
):
    input_directory = prepare_native_input(
        jar,
        metadata,
        platform,
        javafx_classifier,
    )

    output_directory = (
            RELEASE_DIRECTORY
            / platform
    )

    recreate_directory(
        output_directory
    )

    run([
        "jpackage",
        "--type",
        "app-image",
        "--name",
        APPLICATION_NAME,
        "--app-version",
        metadata.version,
        "--input",
        str(input_directory),
        "--main-jar",
        jar.name,
        "--main-class",
        metadata.main_class,
        "--java-options",
        "--module-path=$APPDIR/javafx",
        "--java-options",
        "--add-modules=javafx.controls",
        "--java-options",
        "--enable-native-access=javafx.graphics",
        "--dest",
        str(output_directory),
    ])

    application = (
            output_directory
            / APPLICATION_NAME
    )

    launcher = native_launcher(
        application,
        platform,
    )

    if not launcher.exists():
        raise RuntimeError(
            f"{platform.capitalize()} application launcher "
            f"was not created: {launcher}"
        )

    return application


def prepare_native_input(
        jar,
        metadata,
        platform,
        javafx_classifier,
):
    input_directory = (
            STAGING_DIRECTORY
            / platform
            / "input"
    )

    recreate_directory(
        input_directory
    )

    shutil.copy2(
        jar,
        input_directory / jar.name,
        )

    copy_non_javafx_runtime_dependencies(
        input_directory
    )

    javafx_directory = (
            input_directory
            / "javafx"
    )

    javafx_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    copy_javafx_dependencies(
        javafx_classifier,
        metadata.javafx_version,
        javafx_directory,
    )

    return input_directory


def native_launcher(
        application,
        platform,
):
    if platform == "linux":
        return (
                application
                / "bin"
                / APPLICATION_NAME
        )

    if platform == "windows":
        return (
                application
                / f"{APPLICATION_NAME}.exe"
        )

    raise RuntimeError(
        f"Unsupported native release platform: {platform}"
    )


def smoke_test_linux_application(
        application,
):
    print_step(
        "Smoke-testing Linux release"
    )

    process = subprocess.Popen(
        [
            "xvfb-run",
            "-a",
            str(
                native_launcher(
                    application,
                    "linux",
                )
            ),
        ],
        cwd=application,
        start_new_session=True,
    )

    try:
        verify_application_starts(
            process
        )
    finally:
        stop_process(
            process
        )


def smoke_test_native_windows_application(
        application,
):
    print_step(
        "Smoke-testing Windows release"
    )

    process = subprocess.Popen(
        [
            str(
                native_launcher(
                    application,
                    "windows",
                )
            )
        ],
        cwd=application,
    )

    try:
        verify_application_starts(
            process
        )
    finally:
        stop_process(
            process
        )


def create_cross_built_windows_application(
        jar,
        metadata,
        windows_jdk,
):
    application = (
            RELEASE_DIRECTORY
            / "windows"
            / APPLICATION_NAME
    )

    recreate_directory(
        application
    )

    app_directory = (
            application
            / "app"
    )

    library_directory = (
            app_directory
            / "lib"
    )

    javafx_directory = (
            app_directory
            / "javafx"
    )

    library_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    javafx_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        jar,
        app_directory / jar.name,
        )

    copy_non_javafx_runtime_dependencies(
        library_directory
    )

    copy_javafx_dependencies(
        "win",
        metadata.javafx_version,
        javafx_directory,
    )

    create_windows_runtime(
        application,
        windows_jdk,
    )

    create_windows_launcher(
        application,
        jar,
        metadata.main_class,
    )

    launcher = (
            application
            / f"{APPLICATION_NAME}.exe"
    )

    if not launcher.exists():
        raise RuntimeError(
            f"Windows launcher was not created: {launcher}"
        )

    return application


def create_windows_runtime(
        application,
        windows_jdk,
):
    print_step(
        "Creating Windows Java runtime"
    )

    runtime = (
            application
            / "runtime"
    )

    run([
        "jlink",
        "--module-path",
        str(windows_jdk / "jmods"),
        "--add-modules",
        "ALL-MODULE-PATH",
        "--strip-debug",
        "--no-header-files",
        "--no-man-pages",
        "--output",
        str(runtime),
    ])


def create_windows_launcher(
        application,
        jar,
        main_class,
):
    print_step(
        "Creating Windows executable"
    )

    configuration = (
            application
            / "launch4j.xml"
    )

    configuration.write_text(
        launch4j_configuration(
            application,
            jar,
            main_class,
        ),
        encoding="utf-8",
    )

    try:
        run([
            "launch4j",
            str(configuration),
        ])
    finally:
        configuration.unlink(
            missing_ok=True
        )


def launch4j_configuration(
        application,
        jar,
        main_class,
):
    launcher = (
            application
            / f"{APPLICATION_NAME}.exe"
    )

    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>

        <launch4jConfig>
            <dontWrapJar>true</dontWrapJar>

            <headerType>gui</headerType>

            <outfile>{launcher}</outfile>

            <errTitle>{APPLICATION_NAME}</errTitle>

            <chdir>.</chdir>

            <classPath>
                <mainClass>{main_class}</mainClass>
                <cp>app/{jar.name}</cp>
                <cp>app/lib/*</cp>
            </classPath>

            <jre>
                <path>runtime</path>

                <opt>--module-path="%EXEDIR%\\app\\javafx"</opt>
                <opt>--add-modules=javafx.controls</opt>
                <opt>--enable-native-access=javafx.graphics</opt>
            </jre>
        </launch4jConfig>
        """
    )


def smoke_test_cross_built_windows_application(
        application,
):
    print_step(
        "Smoke-testing Windows release"
    )

    if not command_exists(
            "wine"
    ):
        print(
            "Wine is not installed. "
            "Windows smoke test skipped."
        )

        print(
            "The generated Windows release should "
            "be verified on a Windows 11 machine."
        )

        return

    process = subprocess.Popen(
        [
            "xvfb-run",
            "-a",
            "wine",
            str(
                application
                / f"{APPLICATION_NAME}.exe"
            ),
        ],
        cwd=application,
        start_new_session=True,
    )

    try:
        verify_application_starts(
            process
        )
    finally:
        stop_process(
            process
        )


def copy_javafx_dependencies(
        classifier,
        javafx_version,
        destination,
):
    for module in JAVAFX_MODULES:
        copy_javafx_dependency(
            module,
            classifier,
            javafx_version,
            destination,
        )


def copy_javafx_dependency(
        module,
        classifier,
        javafx_version,
        destination,
):
    artifact = (
        f"org.openjfx:{module}:"
        f"{javafx_version}:jar:{classifier}"
    )

    run([
        maven_command(),
        "dependency:copy",
        f"-Dartifact={artifact}",
        f"-DoutputDirectory={destination}",
    ])


def copy_non_javafx_runtime_dependencies(
        destination,
):
    run([
        maven_command(),
        "dependency:copy-dependencies",
        "-DincludeScope=runtime",
        "-DexcludeGroupIds=org.openjfx",
        f"-DoutputDirectory={destination}",
    ])


def verify_application_starts(
        process,
):
    time.sleep(
        SMOKE_TEST_DURATION_SECONDS
    )

    exit_code = process.poll()

    if exit_code is not None:
        raise RuntimeError(
            "Released application terminated during startup "
            f"with exit code {exit_code}."
        )

    print(
        "Application remained running for "
        f"{SMOKE_TEST_DURATION_SECONDS} seconds."
    )


def stop_process(
        process,
):
    if process.poll() is not None:
        return

    if is_windows():
        process.terminate()

    else:
        os.killpg(
            process.pid,
            signal.SIGTERM,
        )

    try:
        process.wait(
            timeout=5
        )

    except subprocess.TimeoutExpired:
        force_stop_process(
            process
        )


def force_stop_process(
        process,
):
    if is_windows():
        process.kill()

    else:
        os.killpg(
            process.pid,
            signal.SIGKILL,
        )

    process.wait()


def create_archive(
        application,
        archive_name,
):
    print_step(
        f"Creating {archive_name}.zip"
    )

    archive_path = (
            RELEASE_DIRECTORY
            / archive_name
    )

    archive = shutil.make_archive(
        str(archive_path),
        "zip",
        root_dir=application.parent,
        base_dir=application.name,
    )

    return Path(
        archive
    )


def recreate_directory(
        directory,
):
    shutil.rmtree(
        directory,
        ignore_errors=True,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


def read_maven_property(
        property_name,
):
    result = subprocess.run(
        [
            maven_command(),
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
        raise RuntimeError(
            f"Maven property '{property_name}' "
            "could not be determined."
        )

    return value


def maven_command():
    if is_windows():
        return "mvn.cmd"

    return "mvn"


def require_command(
        command,
        error_message,
):
    if not command_exists(
            command
    ):
        raise RuntimeError(
            error_message
        )


def command_exists(
        command,
):
    return shutil.which(
        command
    ) is not None


def run(
        command,
):
    subprocess.run(
        command,
        cwd=PROJECT_DIRECTORY,
        check=True,
    )


def report_release(
        platform,
        application,
        archive,
):
    print()
    print("=" * 60)
    print(
        f"WorkPacer {platform} release successful"
    )
    print("=" * 60)
    print()
    print(
        f"Application: {application}"
    )
    print(
        f"Archive:     {archive}"
    )


def print_step(
        description,
):
    print()
    print("=" * 60)
    print(
        description
    )
    print("=" * 60)


def is_linux():
    return sys.platform.startswith(
        "linux"
    )


def is_windows():
    return sys.platform == "win32"


if __name__ == "__main__":
    try:
        main()

    except subprocess.CalledProcessError as error:
        print()
        print(
            "RELEASE FAILED: "
            f"command returned exit code {error.returncode}."
        )

        sys.exit(
            error.returncode
        )

    except RuntimeError as error:
        print()
        print(
            f"RELEASE FAILED: {error}"
        )

        sys.exit(1)