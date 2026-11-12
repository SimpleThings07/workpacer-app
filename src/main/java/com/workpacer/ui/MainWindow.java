package com.workpacer.ui;

import com.workpacer.adapter.controller.WorkPacerEventHandler;
import com.workpacer.adapter.presenter.WorkPacerViewModel;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TextField;
import javafx.scene.layout.VBox;

public class MainWindow extends VBox
{
    private final WorkPacerEventHandler eventHandler;
    private final WorkPacerViewModel viewModel;

    private final TextField startTimeField;
    private final TextField workDurationField;
    private final Label finishTimeLabel;

    public MainWindow(
        WorkPacerEventHandler eventHandler,
        WorkPacerViewModel viewModel
    )
    {
        this.eventHandler = eventHandler;
        this.viewModel = viewModel;

        Label startTimeLabel =
            createStartTimeLabel();

        this.startTimeField =
            createStartTimeField();

        Label workDurationLabel =
            createWorkDurationLabel();

        this.workDurationField =
            createWorkDurationField();

        Label finishTimeDescriptionLabel =
            createFinishTimeDescriptionLabel();

        this.finishTimeLabel =
            createFinishTimeLabel();

        Button startWorkSessionButton =
            createStartWorkSessionButton();

        super.getChildren().addAll (
            startTimeLabel,
            startTimeField,
            workDurationLabel,
            workDurationField,
            finishTimeDescriptionLabel,
            finishTimeLabel,
            startWorkSessionButton
        );
    }

    private void startWorkSession ( )
    {
        this.eventHandler.startWorkSession (
            this.startTimeField.getText(),
            this.workDurationField.getText()
        );

        this.finishTimeLabel.setText( this.viewModel.getFinishTime( ) );
    }

    private Label createStartTimeLabel()
    {
        Label label =
            new Label("Start time (HH:mm)");

        label.setId("startTimeLabel");

        return label;
    }

    private TextField createStartTimeField()
    {
        TextField textField =
            new TextField();

        textField.setId("startTimeField");

        return textField;
    }

    private Label createWorkDurationLabel()
    {
        Label label =
            new Label("Required work duration (HH:mm)");

        label.setId("workDurationLabel");

        return label;
    }

    private TextField createWorkDurationField()
    {
        TextField textField =
            new TextField();

        textField.setId("workDurationField");

        return textField;
    }

    private Label createFinishTimeDescriptionLabel()
    {
        Label label =
            new Label("Expected finish time:");

        label.setId("finishTimeDescriptionLabel");

        return label;
    }

    private Label createFinishTimeLabel()
    {
        Label label =
            new Label();

        label.setId("finishTimeLabel");

        return label;
    }

    private Button createStartWorkSessionButton()
    {
        Button button =
            new Button("Start Work Session");

        button.setId("startWorkSessionButton");

        button.setOnAction(
            event -> startWorkSession()
        );

        return button;
    }
}
