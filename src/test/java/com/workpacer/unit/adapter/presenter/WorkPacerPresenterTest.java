package com.workpacer.unit.adapter.presenter;

import com.workpacer.adapter.presenter.WorkPacerPresenter;
import com.workpacer.adapter.presenter.WorkPacerViewModel;
import com.workpacer.application.boundary.output.WorkSessionOutputBoundary;
import com.workpacer.application.boundary.output.StartWorkSessionResponse;
import org.junit.jupiter.api.Test;

import java.time.LocalTime;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.is;

class WorkPacerPresenterTest
{
    /**
     * GIVEN a work session response with expected finish time 13:00
     * WHEN the response is presented
     * THEN the view model contains finish time "13:00"
     */
    @Test
    void givenWorkSessionResponse_whenResponseIsPresented_thenViewModelContainsFormattedFinishTime()
    {
        // BUILD
        WorkPacerViewModel viewModel =
            new WorkPacerViewModel();

        WorkSessionOutputBoundary outputBoundary =
            new WorkPacerPresenter ( viewModel );

        StartWorkSessionResponse response =
            new StartWorkSessionResponse (
                LocalTime.of (
                    13,
                    0)
            );

        // OPERATE
        outputBoundary.present ( response );

        // ASSERT
        assertThat (
            viewModel.getFinishTime(),
            is ("13:00")
        );
    }
}