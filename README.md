# Distributed Algorithms (COSC-5010, EE-5885) Final Project

Repository for the University of Wyoming Distributed Algorithms Course's Final Project.

# Table of Contents
- [Distributed Algorithms (COSC-5010, EE-5885) Final Project](#distributed-algorithms-cosc-5010-ee-5885-final-project)
- [Table of Contents](#table-of-contents)
- [Requirements:](#requirements)
- [Project Files](#project-files)
- [N\_Queens.py](#n_queenspy)
  - [About](#about)
  - [How to Run](#how-to-run)
- [Project.py](#projectpy)
  - [About](#about-1)
  - [How to Run](#how-to-run-1)
  - [Output](#output)
  - [Notes](#notes)


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
It will prompt the user for a value of N (integer greater than or equal to 4) and print out a solution.

## How to Run

If the necessary packages have not been installed using pip, run:
```
pip install -r requirements.txt
```

After that, simply run 
```
python3 n_queens.py
```

The script will prompt for an integer greater than or equal to 4 to solve the N Queens problem.

It will then print out the locations on a n by n board of where the queens should be located (marked with a Q).

# Project.py

This section involves the necessary informatio about `project.py`.

## About 

This project aims to detect if any errors have occurred in a trace of distributed program. 
The SMT solver Z3 is applied to verify that errors have not occurred.

## How to Run

If the necessary packages have not been installed using pip, run:
```
pip install -r requirements.txt
```

After that, run 
```
python3 project.py
```

The script will prompt the user which `.xml` file they would like to test: 
1. `trace.xml`
2. `Incorrect_trace.xml`

Choosing the index number, the user can see if it correctly moved the predicte around.

## Output

If the user chose `trace.xml`, the output will say that the predicate value was satisfied in the communication.

If the user chose the `Incorrect_trace.xml` file with errors, they will see what processes on which intervals failed to satisfy.
The user will be prompted to have Z3 run again to suggest solutions to the errors, which will be run if the user says yes.

Selecting `Yes` will have Z3 output another table suggesting how to fix some intervals based on the previous errors.

Selecting `No` will have the program terminate.

## Notes

The Z3 suggestion solver has some bugs, it can suggest changes to values that are already satisfied (this is because it double-checks values).

Additionally, it might be that fixing some problems introduces new ones.
