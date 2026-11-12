package com.workpacer.application.acceptance;

import com.workpacer.WorkPacerApp;
import com.workpacer.WorkPacerApp.ApplicationEndpoints;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

/**
    Application Acceptance Test
        ↓
    Application fixture / runner
        ↓
    EventHandler <I>
        ↑ implements
     Controller
        ↓ creates
     Request Model <DS>
        ↓
     Input Boundary <I>
        ↑ implements
     Interactor
        ↓
     Domain / Business Rules
        ↓
     Interactor
        ↓ creates
     Response Model <DS>
        ↓
     Output Boundary <I>
        ↑ implements
     Presenter
        ↓ creates / updates
     ViewModel <DS>
*/

public class WorkPacerAcceptanceTest
{

    /**
     * GIVEN no work session is active
     * WHEN a work session is requested with a given start time
     * AND a given required work duration
     * THEN the expected finish time is calculated correctly
     */
    @ParameterizedTest
    @CsvSource ({
        "09:00, 04:00, 13:00",
        "07:15, 05:00, 12:15",
        "06:33, 05:04, 11:37"
    })
    void givenNoActiveWorkSession_whenWorkSessionIsStarted_thenExpectedFinishTimeIsProduced (
        String startTime,
        String requiredWorkDuration,
        String expectedFinishTime
    )
    {
        // BUILD
        ApplicationEndpoints application = WorkPacerApp.createApplicationEndpoints();

        // OPERATE
        application.eventHandler().startWorkSession (
            startTime,
            requiredWorkDuration
        );

        // ASSERT
        assertThat (
            application.viewModel().getFinishTime(),
            is (expectedFinishTime)
        );
    }

    /**
     * GIVEN the user enters the start time and work duration
     *       with or without a leading zero in the hour
     * WHEN the work session is started
     * THEN no exception is thrown
     */
    @ParameterizedTest
    @CsvSource({
        "09:00, 04:00, 13:00",
        "5:25, 04:00, 09:25",
        "05:25, 4:00, 09:25",
        "5:25, 4:00, 09:25"
    })
    void givenTimeInputsWithOptionalLeadingZeros_whenWorkSessionIsStarted_thenNoExceptionThrown (
        String startTime,
        String requiredWorkDuration,
        String expectedFinishTime
    )
    {
        // BUILD
        ApplicationEndpoints application = WorkPacerApp.createApplicationEndpoints();

        // OPERATE & ASSERT
        assertDoesNotThrow (
            () -> application.eventHandler().startWorkSession (
                startTime,
                requiredWorkDuration
            )
        );

        assertThat (
            application.viewModel().getFinishTime(),
            is ( expectedFinishTime )
        );
    }
}
