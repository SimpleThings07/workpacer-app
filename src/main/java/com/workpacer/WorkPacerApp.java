package com.workpacer;
import com.workpacer.adapter.controller.WorkPacerController;
import com.workpacer.adapter.controller.WorkPacerEventHandler;
import com.workpacer.adapter.presenter.WorkPacerPresenter;
import com.workpacer.adapter.presenter.WorkPacerViewModel;
import com.workpacer.application.boundary.input.WorkSessionInputBoundary;
import com.workpacer.application.boundary.interactor.StartWorkSessionInteractor;
import com.workpacer.application.boundary.output.WorkSessionOutputBoundary;
import com.workpacer.ui.MainWindow;
import javafx.application.Application;
import javafx.stage.Stage;
import javafx.scene.Scene;

/*

    <I>   = Interface
    <DS>  = Data Structure / Data Model

    ↓              runtime call / data flow
    --creates-->    produces a data structure
    ..implements..> implements an interface


    GUI input
       ↓
    EventHandler <I>
       ↑ implements
    Controller
       ↓ creates
    Request Model <DS>
       ↓
    Input Boundary <I>
       ↑ implements
    Interactor
       ↓
    Domain / Business Rules
       ↓
    Interactor
       ↓ creates
    Response Model <DS>
       ↓
    Output Boundary <I>
       ↑ implements
    Presenter
       ↓ creates / updates
    ViewModel <DS>
       ↓
    GUI output

*/

public class WorkPacerApp extends Application
{
    private static final String APP_NAME = "Work Pacer";
    private static final int DEFAULT_WINDOW_WIDTH = 500;
    private static final int DEFAULT_WINDOW_HEIGHT = 400;

    /**
     * Components forming the WorkPacer application without the GUI.
     */
    public record ApplicationEndpoints (
        WorkPacerEventHandler eventHandler,
        WorkPacerViewModel viewModel
    ) {
    }

    public static void main (String[] args)
    {
        launch (args);
    }

    /*
     * JavaFX application entry point after the JavaFX runtime
     * has been launched.
     */
    @Override
    public void start (Stage primaryWindow)
    {
        MainWindow mainWindow = createMainWindow ( );

        primaryWindow.setScene (
            new Scene ( mainWindow, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT )
        );
        primaryWindow.setTitle (APP_NAME);
        primaryWindow.show ( );
    }

    /**
     * Creates the complete application including the GUI.
     */
    private static MainWindow createMainWindow ( )
    {
        ApplicationEndpoints application = createApplicationEndpoints();

        return new MainWindow (
            application.eventHandler,
            application.viewModel
        );
    }


    /**
     * Creates and connects the non-GUI application object graph.
     *
     * Returns the application endpoints used to interact with and observe
     * the application: the event handler for input and the view model for output.
     */
    public static ApplicationEndpoints createApplicationEndpoints()
    {
        WorkPacerViewModel viewModel =
            new WorkPacerViewModel();

        WorkSessionOutputBoundary outputBoundary =
            new WorkPacerPresenter(viewModel);

        WorkSessionInputBoundary inputBoundary =
            new StartWorkSessionInteractor(outputBoundary);

        WorkPacerEventHandler eventHandler =
            new WorkPacerController(inputBoundary);

        return new ApplicationEndpoints (
            eventHandler,
            viewModel
        );
    }
}
