package com.workpacer.application.boundary.input;

import java.time.Duration;
import java.time.LocalTime;

public record StartWorkSessionRequest (
    LocalTime startTime,
    Duration requiredWorkDuration
)
{
}
