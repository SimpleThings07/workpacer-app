package com.workpacer.adapter.controller;

public interface WorkPacerEventHandler
{
    void startWorkSession (
        String startTime,
        String requiredWorkDuration
    );
}
