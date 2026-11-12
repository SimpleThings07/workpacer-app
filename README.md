# WorkPacer

## About WorkPacer

WorkPacer is a JavaFX desktop application for managing and tracking work sessions. It helps users keep track of worked time, remaining work time, breaks, current session state, and the expected finish time throughout the workday.

---

## Running the Application

To start WorkPacer with Maven:

```bash
mvn javafx:run
```

This compiles the application if necessary and launches the JavaFX desktop application.

---

## Test Commands Summary

| Purpose | Linux command |
| --- | --- |
| Unit + application acceptance tests | `mvn test` |
| End-to-end tests only | `xvfb-run -a mvn test-compile failsafe:integration-test failsafe:verify` |
| Complete test suite | `xvfb-run -a mvn verify` |

---

## Build Commands Summary

| Purpose | Command |
| --- | --- |
| Build, run all tests, create JAR, and smoke-test JAR | `python3 build.py` |
| Create Linux release | `python3 release.py --target linux` |
| Create Windows release from Linux | `python3 release.py --target windows` |
| Create Linux and Windows releases from Linux | `python3 release.py --target all` |
| Create Windows release on Windows | `python release.py --target windows` |
| Preview GitHub commit/tag/push without making changes | `python3 push.py --test` |
| Commit, tag, and push the current release | `python3 push.py` |

---

## Build Prerequisites

The following tools are required on the build machine:

- JDK 25
- Maven
- Python 3

### Additional Linux Requirements

The complete build and JavaFX GUI tests require Xvfb.

Install it with:

```bash
sudo apt install xvfb
```

Verify that it is available:

```bash
which xvfb-run
```

### Additional Requirements for Windows Cross-Builds on Linux

Creating a Windows release from Linux additionally requires:

- Launch4j
- Windows x64 JDK 25
- Windows JDK 25 JMOD files

Launch4j must be available on the system `PATH`:

```bash
which launch4j
```

The default Windows JDK location expected by `release.py` is:

```text
/usr/lib/jvm/jdk-25-windows-x64
```

The directory must contain the Windows JDK together with its JMOD files:

```text
/usr/lib/jvm/jdk-25-windows-x64/
├── bin/
├── conf/
├── include/
├── jmods/
├── legal/
└── lib/
```

The `jmods` directory must contain files such as:

```text
java.base.jmod
java.desktop.jmod
java.logging.jmod
...
```

A different Windows JDK location can be supplied with:

```bash
python3 release.py \
    --target windows \
    --windows-jdk /path/to/windows/jdk
```

### Optional: Wine

Wine is optional.

If Wine is installed on Linux, `release.py` can smoke-test the generated Windows application after cross-building it.

The Linux-to-Windows cross-build workflow has been verified successfully on Windows 11.

---

## Build the Application

`build.py` creates and verifies the WorkPacer JAR.

It performs the complete build workflow:

```text
Compile application
        |
        v
Run unit tests
        |
        v
Run application acceptance tests
        |
        v
Run end-to-end tests
        |
        v
Create WorkPacer JAR
        |
        v
Smoke-test generated JAR
```

### Linux

```bash
python3 build.py
```

### Windows

```powershell
python build.py
```

A successful build creates the versioned JAR under:

```text
target/workpacer-<version>.jar
```

For example:

```text
target/workpacer-0.1.0.jar
```

The smoke test starts the generated JAR and verifies that the application remains running successfully.

`build.py` should be executed before `release.py`.

---

## Create Release Packages

`release.py` packages the already-built and verified WorkPacer JAR into a self-contained, ready-to-ship application.

It does not rebuild the application.

The responsibility split is:

```text
build.py
    |
    +-- compile
    +-- tests
    +-- create JAR
    +-- smoke-test JAR

release.py
    |
    +-- use existing verified JAR
    +-- create self-contained application
    +-- smoke-test packaged application
    +-- create release archive
```

The generated release packages contain their own Java runtime and JavaFX dependencies.

The target machine therefore does not need Java, JavaFX, Maven, or Python installed separately.

---

## Create a Linux Release

On Linux:

```bash
python3 release.py --target linux
```

This creates a self-contained Linux application and smoke-tests it using Xvfb.

The resulting archive is:

```text
target/release/WorkPacer-<version>-linux.zip
```

For example:

```text
target/release/WorkPacer-0.1.0-linux.zip
```

The unpacked application is created under:

```text
target/release/linux/WorkPacer/
```

---

## Create a Windows Release (from Linux)

Run:

```bash
python3 release.py --target windows
```

The Windows cross-build uses:

- Windows JavaFX dependencies
- Windows JDK JMOD files
- `jlink`
- Launch4j

The default Windows JDK location is:

```text
/usr/lib/jvm/jdk-25-windows-x64
```

To use a different Windows JDK:

```bash
python3 release.py \
    --target windows \
    --windows-jdk /path/to/windows/jdk
```

The resulting archive is:

```text
target/release/WorkPacer-<version>-windows.zip
```

For example:

```text
target/release/WorkPacer-0.1.0-windows.zip
```

The unpacked Windows application is created under:

```text
target/release/windows/WorkPacer/
```

and contains:

```text
WorkPacer/
├── WorkPacer.exe
├── app/
└── runtime/
```

The Windows user starts:

```text
WorkPacer.exe
```

No separately installed Java or JavaFX runtime is required.

If Wine is available on the Linux build machine, the Windows executable is smoke-tested automatically.

Otherwise, the smoke test is skipped and the release should be verified on a Windows 11 machine.

---

## Create Linux and Windows Releases

On Linux, both release packages can be created with:

```bash
python3 release.py --target all
```

To override the default Windows JDK:

```bash
python3 release.py \
    --target all \
    --windows-jdk /path/to/windows/jdk
```

This produces:

```text
target/release/WorkPacer-<version>-linux.zip
target/release/WorkPacer-<version>-windows.zip
```

---

## Create a Windows Release on Windows

On a Windows build machine:

```powershell
python release.py --target windows
```

The Windows application is packaged natively.

The `--windows-jdk` argument is not required when building the Windows release on Windows.

---

## Supported Release Targets

| Build host | Linux target | Windows target |
| --- | --- | --- |
| Linux | Supported | Supported |
| Windows | Not supported | Supported |

Linux can therefore create both Linux and Windows release packages.

Windows currently creates Windows release packages only.

---

## Publish to GitHub

`push.py` prepares and publishes a WorkPacer release to GitHub.

It uses:

- `pom.xml` as the source of truth for the application version
- `CHANGELOG.md` as the source of truth for the release date and commit body

For example:

```text
pom.xml
    -> 0.1.0

CHANGELOG.md
    -> ## [0.1.0] - 2026-11-11
```

The generated Git commit title is:

```text
[0.1.0] - 2026-11-11
```

and the corresponding annotated Git tag is:

```text
v0.1.0
```

### Preview the Push

Before performing a real push, run:

```bash
python3 push.py --test
```

Test mode performs the release checks and shows what would be committed, but it does not modify the Git repository or GitHub.

It verifies:

- Git is installed
- the project is a Git repository
- the `origin` remote exists
- `target/` is ignored by Git
- the current version exists in `CHANGELOG.md`
- the corresponding `v<version>` tag does not already exist locally
- the corresponding `v<version>` tag does not already exist on `origin`

It then displays:

- commit title
- Git tag
- current branch
- whether this is the first commit
- all files that would be committed
- commit body parsed from `CHANGELOG.md`

The user must explicitly approve the preview.

Example:

```text
============================================================
Push Preview
============================================================

Commit: [0.1.0] - 2026-11-11
Tag:    v0.1.0
Branch: main

Files to be committed:

?? CHANGELOG.md
?? README.md
?? build.py
?? pom.xml
?? push.py
?? release.py
?? src/...

Commit body from CHANGELOG.md:

### Application
- ...

Proceed with simulate commit and push? [y/N]:
```

Answering anything other than `y` or `yes` cancels the operation.

In test mode, even after confirmation:

```text
No files were staged.
No commit was created.
No tag was created.
Nothing was pushed to GitHub.
```

### Push the Release

After reviewing the test-mode output, run:

```bash
python3 push.py
```

`push.py` will again show the files and release metadata before making changes.

Only after explicit confirmation will it:

```text
Stage all reviewed changes
        |
        v
Verify the staged files still match the reviewed files
        |
        v
Create the Git commit
        |
        v
Create the annotated version tag
        |
        v
Push the current branch
        |
        v
Push the version tag
```

### Existing Version Safeguard

Released versions are treated as immutable.

If the current version already exists as a Git tag, for example:

```text
v0.1.0
```

`push.py` stops and asks for the application version to be incremented in:

```text
pom.xml
```

For example:

```xml
<version>0.1.1</version>
```

A corresponding entry must then be added to:

```text
CHANGELOG.md
```

For example:

```markdown
## [0.1.1] - 2026-11-12
```

After changing the version, rebuild and recreate the release packages before pushing:

```bash
python3 build.py
python3 release.py --target all
python3 push.py --test
python3 push.py
```

### GitHub Repository Setup

For the first publication, create an empty GitHub repository and connect it as `origin`.

Example:

```bash
git remote add origin https://github.com/<username>/workpacer-app.git
```

Verify the remote:

```bash
git remote -v
```

The repository can then be published through `push.py`.

### Generated Build Artifacts

Generated build artifacts are not committed to Git.

The following remain under Maven's `target/` directory and are ignored by Git:

```text
target/workpacer-<version>.jar
target/release/WorkPacer-<version>-linux.zip
target/release/WorkPacer-<version>-windows.zip
```

The Git repository contains the source code, tests, project configuration, documentation, and automation scripts.

---

## Automated Tests

The project contains three types of automated tests:

- Unit tests
- Application acceptance tests
- End-to-end tests

Unit and application acceptance tests are executed by Maven Surefire.

End-to-end tests are executed by Maven Failsafe and are marked with:

```java
@Tag("e2e")
```

The end-to-end tests use TestFX and therefore require a graphical environment.

---

## Run Unit and Application Acceptance Tests

To run all unit and application acceptance tests:

```bash
mvn test
```

This runs tests such as:

```text
WorkSessionTest
WorkPacerPresenterTest
WorkPacerAcceptanceTest
```

Tests tagged with:

```java
@Tag("e2e")
```

are excluded from this test phase.

This command is suitable for the normal TDD development cycle because it does not start the JavaFX GUI tests.

---

## Run End-to-End Tests Only

The JavaFX end-to-end tests use TestFX.

On Linux, the tests are executed inside a virtual X display using Xvfb:

```bash
xvfb-run -a mvn test-compile failsafe:integration-test failsafe:verify
```

`test-compile` ensures that the test classes are compiled before Failsafe runs the E2E tests.

Failsafe is configured in `pom.xml` to execute tests tagged with:

```java
@Tag("e2e")
```

The TestFX robot is configured through Maven to use the Glass robot.

---

## Run All Tests

To run the complete WorkPacer test suite on Linux:

```bash
xvfb-run -a mvn verify
```

This executes the complete Maven verification lifecycle:

```text
Maven test phase
    |
    v
Surefire
    |
    +-- Unit tests
    +-- Application acceptance tests

    |
    v
Maven integration-test phase
    |
    v
Failsafe
    |
    +-- JavaFX end-to-end tests

    |
    v
Maven verify phase
    |
    v
Final build verification
```

A successful run ends with:

```text
BUILD SUCCESS
```

---

## Testing on Windows

Xvfb is Linux-specific and is not used on Windows.

Unit and application acceptance tests can be run with:

```powershell
mvn test
```

The complete Maven verification lifecycle can be run with:

```powershell
mvn verify
```

The JavaFX end-to-end tests require a Windows environment in which the application can obtain GUI focus.
