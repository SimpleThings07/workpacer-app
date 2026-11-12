package com.workpacer.application.boundary.interactor;

import com.workpacer.application.boundary.input.WorkSessionInputBoundary;
import com.workpacer.application.boundary.input.StartWorkSessionRequest;
import com.workpacer.application.boundary.output.StartWorkSessionResponse;
import com.workpacer.application.boundary.output.WorkSessionOutputBoundary;
import com.workpacer.domain.WorkSession;

public class StartWorkSessionInteractor implements WorkSessionInputBoundary
{
    private final WorkSessionOutputBoundary outputBoundary;

    public StartWorkSessionInteractor(WorkSessionOutputBoundary outputBoundary)
    {
        this.outputBoundary = outputBoundary;
    }

    @Override
    public void startWorkSession ( StartWorkSessionRequest sessionRequest )
    {
        WorkSession workSession = new WorkSession (
            sessionRequest.startTime(),
            sessionRequest.requiredWorkDuration()
        );

        StartWorkSessionResponse sessionResponse = new StartWorkSessionResponse (
            workSession.finishTime()
        );

        this.outputBoundary.present ( sessionResponse );
    }
}
