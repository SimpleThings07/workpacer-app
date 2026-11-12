package com.workpacer.unit.domain;

import com.workpacer.domain.WorkSession;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;

import java.time.Duration;
import java.time.LocalTime;
import java.util.List;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

class WorkSessionTest
{
    /* Test fixture/data definitions */
    private record WorkSessionTestCase (
        LocalTime startTime,
        Duration requiredWorkDuration,
        LocalTime expectedFinishTime
    )
    {
    }

    private static List<WorkSessionTestCase> workSessionTestCases()
    {
        return List.of (
            new WorkSessionTestCase (
                LocalTime.of(9, 0),
                Duration.ofHours(4),
                LocalTime.of(13, 0)
            ),
            new WorkSessionTestCase (
                LocalTime.of(8, 30),
                Duration.ofHours(2),
                LocalTime.of(10, 30)
            ),
            new WorkSessionTestCase (
                LocalTime.of(10, 15),
                Duration.ofHours(1).plusMinutes(45),
                LocalTime.of(12, 0)
            )
        );
    }


    /**
     * GIVEN a work session starts at a given time
     * AND a given amount of working time is required
     * WHEN the expected finish time is calculated
     * THEN the expected finish time is calculated correctly
     */
    @ParameterizedTest
    @MethodSource("workSessionTestCases")
    void givenStartTimeAndRequiredWorkDuration_whenExpectedFinishTimeIsCalculated_thenCorrectFinishTimeIsProduced(
        WorkSessionTestCase testCase
    )
    {
        // BUILD
        WorkSession workSession = new WorkSession (
            testCase.startTime,
            testCase.requiredWorkDuration
        );

        // OPERATE
        LocalTime finishTime = workSession.finishTime ( );

        // ASSERT
        assertThat (
            finishTime,
            is (testCase.expectedFinishTime)
        );
    }
}
