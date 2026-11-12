package com.workpacer.e2e;

import javafx.stage.Stage;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.testfx.api.FxRobot;
import org.testfx.framework.junit5.ApplicationExtension;
import org.testfx.framework.junit5.Start;

@Tag("e2e")
@ExtendWith(ApplicationExtension.class)
public class WorkPacerE2eTest
{
    private ApplicationRunner application;

    // "Start" annotation - Called before each test method.
    @Start
    void startApplication (Stage mainWindow)
    {
        application = new ApplicationRunner();
        application.start (mainWindow);
    }

    /**
     * GIVEN no work session is active
     * WHEN the user starts a four-hour work session at 09:00
     * THEN the application shows the session as WORKING
     * AND worked time is 00:00
     * AND remaining working time is 04:00
     * AND break time is 00:00
     * AND expected finish time is 13:00
     */
    @Test
    void givenNoActiveWorkSession_whenUserStartsFourHourSessionAt0900_thenWorkingSessionIsDisplayed (
        FxRobot user
    )
    {

        // GIVEN
        // No active work session.

        // WHEN
        application.startWorkSession (
             user,
            "09:00",
            "04:00"
        );

        // THEN
        application.assertWorkingSession (
             "13:00"
        );
    }

    /**
     * GIVEN the application is started
     * WHEN the main window is displayed
     * THEN the work session input controls are clearly labelled
     */
    @Test
    void givenApplicationIsStarted_whenMainWindowIsDisplayed_thenWorkSessionControlsAreLabelled()
    {
        // ASSERT
        application.assertWorkSessionControlsAreLabelled();
    }
}
