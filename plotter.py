import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from matplotlib.figure import Figure
import pandas as pd
import os
import warnings

warnings.filterwarnings("ignore", lineno=114) # this is dirt cheap and I know it


class DataPage():
    ''' Manages one table of data, including how it is plotted'''
    def __init__(self, title, data, handler, xlabel = "Date", ylabel = "", log_allowed=True, per_capita_allowed=True, delta_allowed=True, suggested_scaling=None):
        self.title = title
        self.data = data
        self.headers = set(self.data.columns)
        self.figure = Figure()
        self.handler = handler
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.log_allowed = log_allowed
        self.per_capita_allowed = per_capita_allowed
        self.delta_allowed = delta_allowed
        self.suggested_scaling = suggested_scaling

    def set_handler(self, handler):
        '''
        Sets a DataHandler as the handler to manage this DataPage's data
        and settings. Used when a DataPage is created from a csv file without
        a handler.

        Params
        DataHandler `handler`: new manager for this DataPage
        '''
        self.handler = handler

    def modify_columns(self, headers):
        '''
        Filter data columns by headers, and apply any modifications selected
        by the user to prepare for plotting.
        Original table data is not modified.

        Params
        string list `headers`: list of column names to use

        Returns
        DataFrame `selected_colmns`: modified subset of data to plot
        '''
        selected_columns = self.data[headers]

        if self.handler.delta and self.delta_allowed:
            selected_columns = selected_columns.diff(axis='index')
            selected_columns = selected_columns.rolling(7, win_type="triang").mean()
        
        if self.handler.per_capita and self.per_capita_allowed:
            selected_columns = selected_columns.divide(state_populations_series[headers], axis="columns")
            if self.suggested_scaling is not None:
                selected_columns *= self.suggested_scaling
       
        return selected_columns

    def format_plot(self, ax):
        '''
        Formats the x and y axes and grid of a plot, according to DataPage
        settings.
        Called after plot is created, but before it is drawn in the main
        window update method.

        Params
        Axes ax: plot axes to configure
        '''
        # setting up y axis - scaling & labeling
        ylabel = self.ylabel

        if self.handler.delta and self.delta_allowed:
            ylabel = "Daily New " + ylabel

        if self.handler.per_capita and self.per_capita_allowed:
            if self.suggested_scaling is None:
                ylabel = ylabel + " per Capita"
            else:
                ylabel = ylabel + " per {:,} People".format(self.suggested_scaling)

        yticks = ax.get_yticks()
        if (not self.handler.log_scale) or (not self.log_allowed):
            if max(yticks) > 1000000:
                ax.yaxis.set_major_formatter(format_M)
                ylabel = ylabel + " (millions)"
            elif max(yticks) > 10000:
                ax.yaxis.set_major_formatter(format_K)
                ylabel = ylabel + " (thousands)"

        ax.set_ylabel(ylabel)

        # setting up x axis - dates
        ax.set_xlabel(self.xlabel)
        date_formatter = mdates.DateFormatter("%b %d")
        ax.xaxis.set_major_formatter(date_formatter)
        if self.handler.start_date is not None:
            ax.set_xlim(self.handler.start_date, self.handler.max_date)
        self.figure.autofmt_xdate()

        # draw a grid
        ax.grid(which='major', axis='both', color='lightgrey', linewidth=.5)

    def update_plot(self):
        '''
        Updates, re-plots, and re-formats a plot when changes are made.
        '''
        selected_headers = [h for h in self.handler.active_headers if h in self.headers]
        if len(selected_headers) == 0:
            self.clear_plot()
            return
        ax = self.figure.add_subplot()
        ax.clear()

        updated_columns = self.modify_columns(selected_headers)

        if self.handler.log_scale and self.log_allowed:
            ax.semilogy(updated_columns)
        else:
            ax.plot(updated_columns)

        self.format_plot(ax)

        if len(selected_headers) < 20:
            ax.legend(updated_columns.columns)

    def clear_plot(self):
        '''
        Clears the current figure.
        '''
        self.figure.clear()

    def save(self, file_name):
        '''
        Saves the current plot image to the given file name.
        Typically an image file from the main window's "save" method.

        Params
        string `file_name`: file path to save to
        '''
        self.figure.savefig(file_name)


class DataHandler():
    ''' Manages pages of similar data sets, as well as formatting options
    which apply to all pages of data'''
    def __init__(self):
        self.num_pages = 0
        self.pages = []
        self.headers = []
        self.active_headers = []
        self.log_scale = False
        self.per_capita = False
        self.delta = False
        self.min_date = None
        self.max_date = None
        self.start_date = None

    def add_page(self, page=None, title=None, data=None, xlabel="Date", ylabel="", log_allowed=True, per_capita_allowed=True, delta_allowed=True, suggested_scaling=None):
        '''
        Adds a DataPage to this DataHandler, either as an existing DataPage
        or as a DataFrame with settings.

        Params
        DataPage `page`: page to add. If given, all other params are ignored.
        string `title`: title of data, shown at top of plot tab
        DataFrame `data`: date-indexed table of data
        string `xlabel`: label for x-axis
        string `ylabel`: label for y-axis
        bool `log_allowed`: setting to allow y-axis log plotting
        bool `per_capita_allowed`: setting to allow population scaling
        bool `delta_allowed`: setting to allow differential plotting
        int `suggested_scaling`: if scaled by population, displays "per ___ people"
        '''
        if page is not None:
            newpage = page
            newpage.set_handler(self)
            new_headers = newpage.headers
        else:
            newpage = DataPage(title, data, self, xlabel=xlabel, ylabel=ylabel, log_allowed=log_allowed, per_capita_allowed=per_capita_allowed, delta_allowed=delta_allowed, suggested_scaling=suggested_scaling)
            new_headers = list(data.columns)

        if self.min_date is not None:
            self.min_date = min(self.min_date, page.data.index[0])
            self.max_date = max(self.max_date, page.data.index[-1])
        else:
            self.min_date = page.data.index[0]
            self.max_date = page.data.index[-1]
        self.start_date = self.min_date

        if newpage not in self.pages:
            self.pages.append(newpage)
            self.headers.extend(h for h in new_headers if h not in self.headers)
            self.headers.sort()
            self.num_pages += 1
            self.active_headers = self.headers[:] # all selected after data loads

    def get_page_titles(self):
        '''
        Get all the titles of contained DataPages, for labeling tabs.

        Returns
        string list: list of table titles
        '''
        return [p.title for p in self.pages]


def millions(val, tick_pos):
    '''
    Formatting function. When Y values are in the millions, this is used
    to convert Y axis labels to a shortened format.
    '''
    return "%.1fM" % (val / 1e6)

def thousands(val, tick_pos):
    '''
    Formatting function. When Y values are in the thousands, this is used
    to convert Y axis labels to a shortened format.
    '''
    return "%iK" % (val / 1e3)

format_M = FuncFormatter(millions)

format_K = FuncFormatter(thousands)


def page_from_csv(file_name):
    '''
    Reads a csv file to create a DataPage object. The file should be indexed
    by dates, and any comments or DataPage options should be specified at the
    top of the file using the format "&attr_name:,attr_value," creating a row
    of 2 cells for each attribute.
    The resulting DataPage will have no DataHandler and will need to have it
    set using set_handler in order to plot.

    Params
    string `file_name`: file path of .csv file
    
    Returns
    DataPage `page`: new page of data
    '''
    data = pd.read_csv(file_name, index_col=0, parse_dates=True, infer_datetime_format=True, comment='&')
    title = os.path.basename(file_name).split('.')[0].replace('_', ' ')
    log, delta, per_capita= False, False, False
    ylabel, scaling = None, None
    f = open(file_name)
    line = f.readline()
    while line[0] == '&':
        key, val = line.split(',')[:2]
        if (key.lower().find('y') > -1) and (key.lower().find('label') > -1):
            ylabel = val
        elif key.lower().find('log') > -1:
            log = bool(val.title())
        elif key.lower().find('delta') > -1:
            delta = bool(val.title())
        elif key.lower().find('per') > -1:
            per_capita = bool(val.title())
        elif key.lower().find('scaling') > -1:
            scaling = int(val)
        line = f.readline()
    f.close()
    page = DataPage(title, data, None, ylabel=ylabel, log_allowed=log, per_capita_allowed=per_capita, delta_allowed=delta, suggested_scaling=scaling)
    return page

# For use when scaling data by population
state_populations = pd.read_csv("./state_info/Population_US.csv", index_col=0)
state_populations_series = state_populations.squeeze(axis="columns")