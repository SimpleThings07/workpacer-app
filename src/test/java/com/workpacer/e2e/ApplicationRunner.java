package com.workpacer.e2e;

import com.workpacer.WorkPacerApp;
import javafx.stage.Stage;
import org.testfx.api.FxRobot;

import static org.testfx.api.FxAssert.verifyThat;
import static org.testfx.matcher.control.LabeledMatchers.hasText;


/**
 * Test-side facade for interacting with the running WorkPacer application
 * in end-to-end tests.
 *
 * <p>The runner starts the real application and exposes user actions and
 * expectations using WorkPacer domain language, while hiding low-level
 * JavaFX/TestFX interaction details from the test cases.</p>
 *
 * <p>Examples of responsibilities:</p>
 * <ul>
 *     <li>Start the application under test</li>
 *     <li>Perform user actions such as starting a work session</li>
 *     <li>Assert user-visible application state</li>
 * </ul>
 *
 * <p>This class is part of the test infrastructure and is not used by
 * production code.</p>
 */

/*
┌────────────────────────────────────┐
│ TEST                               │
│                                    │
│ WorkPacerEndToEndTest              │
│          │                         │
│          ▼                         │
│ ApplicationRunner                  │
└──────────┬─────────────────────────┘
           │
           │
           ▼
┌────────────────────────────────────┐
│ PRODUCTION                         │
│                                    │
│ WorkPacerApp                       │
│      │                             │
│      ▼                             │
│ MainWindow                         │
└────────────────────────────────────┘
* */



/*
    GUI input
       ↓
    EventHandler
       ↓
    Controller
       ↓
    Request Model
       ↓
    Input Boundary
       ↓
    Interactor
       ↓
    Domain
       ↓
    Presenter / ViewModel
       ↓
    GUI output
       ↓
    E2E assertion
*
* */


public class ApplicationRunner
{
    public void start (Stage primaryWindow)
    {
        WorkPacerApp workPacerApp = new WorkPacerApp();
        workPacerApp.start (primaryWindow);
    }

    public void startWorkSession (
        FxRobot user,
        String startTime,
        String workDuration
    )
    {
        user.clickOn("#startTimeField");
        user.write(startTime);

        user.clickOn("#workDurationField");
        user.write(workDuration);

        user.clickOn("#startWorkSessionButton");
    }

    public void assertWorkingSession (
        String finishTime
    )
    {
        verifyThat (
            "#finishTimeLabel",
            hasText(finishTime)
        );
    }

    public void assertWorkSessionControlsAreLabelled()
    {

        verifyThat (
            "#startTimeLabel",
            hasText("Start time (HH:mm)")
        );

        verifyThat (
            "#workDurationLabel",
            hasText("Required work duration (HH:mm)")
        );

        verifyThat (
            "#finishTimeDescriptionLabel",
            hasText("Expected finish time:")
        );

        verifyThat (
            "#startWorkSessionButton",
            hasText("Start Work Session")
        );

    }
}