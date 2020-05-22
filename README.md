
## Installation

You'll need Python 3 installed to run this program.

To get the program, clone this repository:

`git clone https://github.com/jsieving/data_playground.git`

This will download all of the code into a folder called `data_playground`, within the folder where you ran the clone command.

Next, you'll need to make sure you have the required Python modules to run the program. As of this writing, the following are required:

* pandas - for working with data tables/spreadsheets
* matplotlib - plotting library
* PySide2 - graphical user interface (GUI) library
* scipy - handy math tools

Change directory into the repository folder:
`cd data-playground`

***Optional***: if you want to keep these requirements specific to this project, rather than installing them globally, you should create a virtual environment. Here's one way to do that, using `venv`:

`python3 -m venv env`

This tells Python 3 to run the `venv` module as a script (`-m`), which will create a virtual environment named `env`.

To activate the environment (i.e., to install modules or run code using that environment), you can run

`source env/bin/activate`

Where `env` is the path to the environment, whatever you named it and wherever you created it. You can tell whether you are in a venv by typing `which python`. The output should have the path to the virtual environment if it's active.

To deactivate the environment, just run `deactivate`.

So, create and activate an environment if you'd like, then run `pip install -r requirements.txt` to install these requirements.

After that, run `python3 app.py` to run the program.

## Data Sources Included

Yes, the data is all about COVID-19.

Before you draw any conclusions from the graphs you create, keep in mind that all data is imperfect, especially in a situation where testing and reporting are very inconsistent. I just created this to have a few more options for looking at the progression of the disease in US states, and I don't expect the data to be super reliable.

The data I used was aggregated from a lot of different sources, so while the maintainers put in a lot of effort to find data and keep it up to date, the sources could still be imperfect or different in how they count. Anyway, here's that:

#### Confirmed cases and deaths:
Accessed from https://github.com/CSSEGISandData/COVID-19

#### Testing and populations:
    Accessed from https://covidtracking.com/
        - Population is calculated as the sum of populations for all locales
        within a state or territory.
        - Test positivity is computed as the ratio of reported positive tests to
        reported tests, as aggregated in this source.
