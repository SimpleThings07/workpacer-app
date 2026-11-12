package com.workpacer.adapter.presenter;

import com.workpacer.application.boundary.output.WorkSessionOutputBoundary;
import com.workpacer.application.boundary.output.StartWorkSessionResponse;

import java.time.format.DateTimeFormatter;

public class WorkPacerPresenter implements WorkSessionOutputBoundary
{
    private final WorkPacerViewModel viewModel;
    private static final DateTimeFormatter TIME_FORMATTER =
        DateTimeFormatter.ofPattern("HH:mm");

    public WorkPacerPresenter ( WorkPacerViewModel viewModel )
    {
        this.viewModel = viewModel;
    }

    @Override
    public void present ( StartWorkSessionResponse response )
    {
        this.viewModel.setFinishTime ( response.finishTime().format ( TIME_FORMATTER ) );
    }
}
