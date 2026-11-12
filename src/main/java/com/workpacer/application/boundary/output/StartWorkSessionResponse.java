package com.workpacer.application.boundary.output;

import java.time.LocalTime;

public record StartWorkSessionResponse (
    LocalTime finishTime
)
{

}
