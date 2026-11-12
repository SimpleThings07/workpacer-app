package com.workpacer.domain;

import java.time.Duration;
import java.time.LocalTime;

public class WorkSession
{

    private final LocalTime startTime;
    private final Duration requiredWorkDuration;

    public WorkSession (
        LocalTime startTime,
        Duration requiredWorkDuration
    )
    {
        this.startTime = startTime;
        this.requiredWorkDuration = requiredWorkDuration;
    }

    public LocalTime finishTime ( )
    {
        return this.startTime.plus ( this.requiredWorkDuration );
    }
}
