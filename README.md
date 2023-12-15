# Distributed Algorithms (COSC-5010, EE-5885) Final Project

Repository for the University of Wyoming Distributed Algorithms Course.

# Table of Contents


# Requirements:
* python version 3.10 or newer
* pip
  * Python packages are in `requirements.txt`. The following can be installed at once by: `pip install -r requirements.txt`.
    * `beautifulsoup4`: Used to parse `.xml` files
    * `pandas`: Used for storing the data for results output
    * `z3-solver`: The SMT solver Z3, which will be used to validate these traces
    * `lxml`: Used with `beautifulsoup4` to parse `.xml` files
    * `tabulate`: Used to format pandas dataframes in a pleasing output
* NOTE: These files have only been tested on Ubuntu Linux Version 22.04 on an x86-64 machine.
  
# Project Files

Here are the files and a quick description of each of them:

* `n_queens.py`: This file runs the n queens problem and finds a solution (and prints it) using Z3. 
* `project.py`: This is the main project for the course.
* `trace.xml`: The trace of a distributed program that is used for `project.py`. Has no errors.
* `Incorrect_trace.xml`: A modified `trace.xml` that has random errors inserted. `project.py` will identify these errors.
* `requirements.txt`: Contains the pip package information for the files for this project.
* `README.md`: This file now that gives information about the project.

# N_Queens.py

This section involves the necessary information about `n_queens.py`.

## About

This file aims to solve the [N Queens Problem](https://en.wikipedia.org/wiki/Eight_queens_puzzle) using Z3.
It will prompt the user for a value of N (integer greater than or equal to 3) and print out a solution.

## How to Run

If the necessary packages have not been installed using pip, run:
```
pip install -r requirements.txt
```

After that, simply run 
```
python3 n_queens.py
```

The script will prompt for an integer greater than or equal to 3 to solve the N Queens problem.

It will then print out the locations on a n by n board of where the queens should be located (marked with a Q).

# Project.py


