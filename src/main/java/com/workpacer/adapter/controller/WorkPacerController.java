package com.workpacer.adapter.controller;

import com.workpacer.application.boundary.input.WorkSessionInputBoundary;
import com.workpacer.application.boundary.input.StartWorkSessionRequest;

import java.time.Duration;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

public class WorkPacerController implements WorkPacerEventHandler
{
    private static final DateTimeFormatter INPUT_TIME_FORMATTER =
        DateTimeFormatter.ofPattern("H:mm");

    private final WorkSessionInputBoundary inputBoundary;

    public WorkPacerController ( WorkSessionInputBoundary interactor )
    {
        this.inputBoundary = interactor;
    }

    @Override
    public void startWorkSession (String startTime, String requiredWorkDuration)
    {
        StartWorkSessionRequest sessionRequest = new StartWorkSessionRequest (
            LocalTime.parse (startTime, INPUT_TIME_FORMATTER),
            parseDuration (requiredWorkDuration)
        );

        inputBoundary.startWorkSession ( sessionRequest );
    }

    private Duration parseDuration (String duration)
    {
        String[] parts = duration.split (":");

        long hours = Long.parseLong (parts[0]);
        long minutes = Long.parseLong (parts[1]);

        return Duration.ofHours(hours)
            .plusMinutes(minutes);
    }

}
