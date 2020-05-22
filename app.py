import sys, glob, os
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
from plotter import DataHandler, page_from_csv
import data_prep

class MainWindow(QMainWindow):
    ''' The main application window, which handles user interaction,
    manages the plot tabs, and manages the overall controls. '''
    def __init__(self, title):
        ''' Set up the layout and UI of the application, and initialize variables
        for managing different datasets and plots. 
        
        Params
        string `title`: title for the application window
        '''
        super().__init__()

        self.setWindowTitle(title)
        self.data_handler = DataHandler()
        self.location_names = []

        main_w = QWidget() # create a widget to contain canvas and all controls
        main_l = QHBoxLayout()
        main_w.setLayout(main_l)

        self.plot_w = QTabWidget() # plots to choose from
        controls_l = QGridLayout() # layout for plotting controls
        main_l.addWidget(self.plot_w) # add plot views, left
        main_l.addLayout(controls_l) # add controls, right
     
        # create an empty tab
        spacer = QLabel()
        spacer.setPixmap(QtGui.QPixmap(800, 600))
        spacer.pixmap().fill(Qt.white)
        self.plot_w.addTab(spacer, "No data")
        self.canvas_pages = []
        self.current_page_index = None
        self.current_page = None
        self.plot_w.currentChanged.connect(self.change_page) # update plots when page changed

        # initialize toggle features
        self.log_disabled = False
        self.delta_disabled = False
        self.scaling_disabled = False
        self.log_label = QLabel("Scale: Linear")
        self.log_switch = QCheckBox("Use log scale")
        self.log_switch.stateChanged.connect(self.toggle_log_scale)
        self.scaling_label = QLabel("Not scaled by population")
        self.scaling_switch = QCheckBox("Scale by population")
        self.scaling_switch.stateChanged.connect(self.toggle_per_capita)
        self.delta_label = QLabel("Showing cumulative totals")
        self.delta_switch = QCheckBox("Show daily change")
        self.delta_switch.stateChanged.connect(self.toggle_delta)
        controls_l.addWidget(self.log_label, 1, 0, Qt.AlignTop)
        controls_l.addWidget(self.log_switch, 2, 0, Qt.AlignTop)
        controls_l.addWidget(self.scaling_label, 4, 0, Qt.AlignTop)
        controls_l.addWidget(self.scaling_switch, 5, 0, Qt.AlignTop)
        controls_l.addWidget(self.delta_label, 7, 0, Qt.AlignTop)
        controls_l.addWidget(self.delta_switch, 8, 0, Qt.AlignTop)

        # create start date picker
        start_date_label = QLabel("Start Date:")
        start_date_picker = QDateEdit()
        start_date_picker.setMinimumDate(QDate(2020, 1, 1))
        start_date_picker.setMaximumDate(QDate.currentDate())
        start_date_picker.setCalendarPopup(True)
        start_date_picker.userDateChanged.connect(self.change_start_date)
        controls_l.addWidget(start_date_label, 10, 0, Qt.AlignTop)
        controls_l.addWidget(start_date_picker, 11, 0, Qt.AlignTop)

        # set up location chooser
        self.location_drop = QComboBox()
        self.location_drop.addItems(["[All]", "[None]"])
        self.location_drop.activated[str].connect(self.add_location)
        location_label = QLabel("Location:")
        controls_l.addWidget(location_label, 0, 2, Qt.AlignTop)
        controls_l.addWidget(self.location_drop, 0, 3, Qt.AlignTop)
        # set up list of locations
        self.locations_list_w = QListWidget()
        self.locations_list_w.itemClicked.connect(self.remove_location)
        location_remove_label = QLabel("Click items to remove.")
        controls_l.addWidget(location_remove_label, 1, 2, 1, 2, Qt.AlignTop)
        controls_l.addWidget(self.locations_list_w, 2, 2, 11, 2, Qt.AlignTop)

        # add buttons to save plots & load data
        buttons_l = QHBoxLayout()
        controls_l.addLayout(buttons_l, 13, 0, 1, 2)
        
        load_b = QPushButton('Load data')
        load_b.clicked.connect(self.on_load_click)

        save_b = QPushButton('Save')
        save_b.clicked.connect(self.save_image)

        buttons_l.addWidget(load_b)
        buttons_l.addWidget(save_b)

        # add info about data sources
        about_text = '''
<strong>Data sources</strong>
<hr>
<i>Confirmed cases and deaths:</i><br>
Accessed from <a href="https://github.com/CSSEGISandData/COVID-19">https://github.com/CSSEGISandData/COVID-19</a>
<hr>
<i>Testing and populations:</i><br>
    Accessed from <a href="https://covidtracking.com/">https://covidtracking.com/</a><br>
        -  Population is calculated as the sum of populations for all locales within a state or territory.<br>
        -  Test positivity is computed as the ratio of reported positive tests to reported tests, as aggregated in this source.'''

        about_label = QTextEdit()
        about_label.setAcceptRichText(True)
        about_label.setReadOnly(True)
        about_label.setHtml(about_text)
        controls_l.addWidget(about_label, 14, 0, 1, 4)

        self.setCentralWidget(main_w)
        

    def load_pages(self, file_list):
        '''
        Creates DataPage objects from a list of .csv file paths, adds them to
        the DataHandler, and creates tabs for them.
        Tables should have locations as column names and dates as row labels.

        Params
        string list `file_list`: list of file paths
        '''
        if len(file_list) == 0:
            return

        # if a single name is passed in, wrap it in a list
        if isinstance(file_list, str):
            file_list = [file_list]

        new_pages = []
        for file_name in file_list:
            page = page_from_csv(file_name)
            self.data_handler.add_page(page)
            new_pages.append(page)
        
        for data_page in new_pages:
            page_canvas = FigureCanvas(data_page.figure)
            self.plot_w.addTab(page_canvas, data_page.title)
            self.canvas_pages.append(page_canvas)

        all_locations = self.data_handler.headers
        new_locations = [name for name in all_locations if name not in self.location_names]
        self.location_names.extend(new_locations)
        self.location_drop.addItems(new_locations)

        if len(self.canvas_pages) > 0 and self.current_page_index is None:
            # if pages successfully loaded, remove empty tab
            self.plot_w.removeTab(0)
            self.current_page_index = self.plot_w.currentIndex()

        self.on_update()

    def change_page(self, page_index):
        '''
        Changes the current page in order to display a different table of data.
        Configures toggle options according to what options are allowed for the
        new DataPage.

        Params
        int `page_index`: index of current page
        '''
        self.current_page_index = page_index
        if self.current_page_index is not None:
            self.current_page = self.data_handler.pages[self.current_page_index]

            if self.current_page.log_allowed and self.log_disabled:
                self.toggle_log_scale(disabled=False)
            elif not self.current_page.log_allowed:
                self.toggle_log_scale(0, disabled=True)

            if self.current_page.delta_allowed and self.delta_disabled:
                self.toggle_delta(disabled=False)
            elif not self.current_page.delta_allowed:
                self.toggle_delta(0, disabled=True)
                
            if self.current_page.per_capita_allowed and self.scaling_disabled:
                self.toggle_per_capita(disabled=False)
            elif not self.current_page.per_capita_allowed:
                self.toggle_per_capita(0, disabled=True)
            
        self.on_update()

    def on_load_click(self):
        '''
        Allows user to add a new DataPage from a .csv file when the "load"
        button is clicked.
        '''
        options = QFileDialog.Options()
        file_names, _ = QFileDialog.getOpenFileNames(self,"Open File","","CSV files (*.csv *.CSV)", options=options)
        if len(file_names) > 0:
            self.load_pages(file_names)

    def on_update(self):
        '''
        When changes are made, the visible DataPage updates its plot and the
        corresponding tab is redrawn to show the change.
        '''
        if self.current_page_index is not None:
            self.current_page.update_plot()
            self.canvas_pages[self.current_page_index].draw()

    def save_image(self):
        '''
        Opens a file saving dialog and saves the current plot to a chosen
        image file.
        '''
        if self.current_page is not None:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self,"Save File","","Image files (*.jpeg *.jpg *.png *.JPEG *.JPG *.PNG)", options=options)
            if file_name:
                self.current_page.save(file_name)

    def add_location(self, location_name):
        '''
        Adds a location selected from the location drop-down to the list of
        locations displayed in the plot.

        Params
        string `location_name`: name of a location to include
        '''
        if location_name == "[None]":
            self.locations_list_w.clear()
            self.data_handler.active_headers = []
        elif location_name == "[All]":
            self.locations_list_w.clear() # no duplicates
            self.locations_list_w.addItems(self.location_names)
            self.data_handler.active_headers = self.location_names[:] # make a copy
        elif location_name not in self.data_handler.active_headers:
            location_item = QListWidgetItem(location_name)
            self.locations_list_w.addItem(location_item)
            self.data_handler.active_headers.append(location_name)
        elif len(self.data_handler.active_headers) == len(self.location_names):
            self.locations_list_w.clear()
            self.data_handler.active_headers = [location_name]
            location_item = QListWidgetItem(location_name)
            self.locations_list_w.addItem(location_item)

        self.on_update()

    def remove_location(self, item):
        '''
        Removes a clicked location from the list of locations displayed in the
        plot.

        Params
        QListWidgetItem `item`: location list item to remove
        '''
        if item.text() in self.data_handler.active_headers:
            self.locations_list_w.takeItem(self.locations_list_w.row(item))
            self.data_handler.active_headers.remove(item.text())

        self.on_update()

    def change_start_date(self, date):
        '''
        Updates the date to begin plotting at when a date is selected in the 
        date picker.
        Date will not be set earlier than the first date where any data is
        available.

        Params 
        QDate `date`: the selected start date
        '''
        new_start_date = datetime(date.year(), date.month(), date.day())
        self.data_handler.start_date = max(new_start_date, self.data_handler.min_date)
        self.on_update()

    def toggle_log_scale(self, value=None, disabled=None):
        '''
        Toggles whether plotting the y-axis on a log scale is allowed.
        This can depend on the settings of the DataPage, user selections,
        or other toggle values.

        Params
        int `value`: (optional) log plotting enabled if >0, disabled otherwise
        bool `disabled`: (optional) temporarily disables/enables this toggle
        '''
        if disabled is False:
            self.log_disabled = False
            self.log_switch.setCheckable(True)
            self.log_label.setText("Scale: Linear")
        elif disabled is True or self.log_disabled:
            self.log_disabled = True
            self.data_handler.log_scale = False
            self.log_switch.setCheckable(False)
            self.log_switch.setChecked(False)
            self.log_label.setText("Scale: Linear\n(Logarithmic disabled)")
            return
        
        if value == 0:
            self.data_handler.log_scale = False
            self.log_switch.setChecked(False)
            self.log_label.setText("Scale: Linear")
        elif (value is not None) and (value > 0):
            self.data_handler.log_scale = True
            self.log_label.setText("Scale: Logarithmic")
            self.toggle_delta(0)

        self.on_update()

    def toggle_per_capita(self, value=None, disabled=None):
        '''
        Toggles whether scaling plots according to population is allowed.
        This can depend on the settings of the DataPage, user selections,
        or other toggle values.

        Params
        int `value`: (optional) population scaling enabled if >0, disabled otherwise
        bool `disabled`: (optional) temporarily disables/enables this toggle
        '''
        if disabled is False:
            self.scaling_disabled = False
            self.scaling_switch.setCheckable(True)
            self.scaling_label.setText("Not scaled by population")
        elif disabled is True or self.scaling_disabled:
            self.scaling_disabled = True
            self.data_handler.per_capita = False
            self.scaling_switch.setCheckable(False)
            self.scaling_switch.setChecked(False)
            self.scaling_label.setText("Not scaled by population\n(Population scaling disabled)")
            return
        
        if value == 0:
            self.data_handler.per_capita = False
            self.scaling_switch.setChecked(False)
            self.scaling_label.setText("Not scaled by population")
        elif (value is not None) and (value > 0):
            self.data_handler.per_capita = True
            self.scaling_label.setText("Scaled by population")

        self.on_update()

    def toggle_delta(self, value=None, disabled=None):
        '''
        Toggles whether plotting day-by-day changes in values is allowed.
        This can depend on the settings of the DataPage, user selections,
        or other toggle values.

        Params
        int `value`: (optional) difference plotting enabled if >0, disabled otherwise
        bool `disabled`: (optional) temporarily disables/enables this toggle
        '''
        if disabled is False:
            self.delta_disabled = False
            self.delta_switch.setCheckable(True)
            self.delta_label.setText("Showing cumulative totals")
        elif disabled is True or self.delta_disabled:
            self.delta_disabled = True
            self.data_handler.delta = False
            self.delta_switch.setCheckable(False)
            self.delta_switch.setChecked(False)
            self.delta_label.setText("Showing cumulative totals\n(Daily change disabled)")
            return
        
        if value == 0:
            self.data_handler.delta = False
            self.delta_switch.setChecked(False)
            self.delta_label.setText("Showing cumulative totals")
        elif (value is not None) and (value > 0):
            self.data_handler.delta = True
            self.delta_label.setText("Showing daily change\n(7-day rolling average)")
            self.toggle_log_scale(0)
    
        self.on_update()


if __name__ == "__main__":

    # Look for tables in here
    files = glob.glob("./tables/*.csv")

    if len(files) == 0:
        response = input('''    No files were found in the expected directory, ./tables.
    Would you like to download data from online? [Y]
    If not, you can import data from another directory. [N]
    Enter y/[N] ''')
        if (len(response) > 0) and (response.lower()[0] == 'y'):
            data_prep.prepare()
            files = glob.glob("./tables/*.csv")
    else:
        response = input('''    Files were found in the expected directory, ./tables.
    However, more recent updated data may be available.
    Would you like to download the newest data from online? [Y]
    If not, the current data will be used. [N]
    Enter y/[N] ''')
        if (len(response) > 0) and (response.lower()[0] == 'y'):
            data_prep.prepare()
            files = glob.glob("./tables/*.csv")

    app = QApplication([]) # create the application
    window = MainWindow("COVID-19 Data") # create the main window

    # load data from files
    window.load_pages(files)

    window.show() # display the window
    sys.exit(app.exec_()) # run the main event loop
