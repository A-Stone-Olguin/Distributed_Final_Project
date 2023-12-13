from math import *
from z3 import *
import re
import itertools
import time

def print_matrix(matrix):
    """
    Prints a matrix row by row.

    :param matrix: An m-sized array of n-sized arrays.
    """
    for row in matrix:
        formatted_row = ["{0: >3}".format(i) for i in row]
        row_string = "["
        for i in range(len(formatted_row)-1):
            row_string += formatted_row[i] + ", "
        row_string += formatted_row[len(formatted_row)-1] + "]"
        print(row_string)

def n_queens(n):
    cells = []
    ## Represent as bools
    for i in range(0,n):
        for j in range(0,n):
            name = f"row_{i}_col{j}"
            cells.append(Bool(name))
    s = Solver();
    s.set("timeout", 1000000)

    ## Ensure at least one queen per row (n queens)
    for i in range(0,n):
        row = [cells[i*n + j] for j in range(0,n)]
        s.add(Or (*row))

    ## Ensure not two in the same row
    for i in range(0, n):
        args = [cells[i*n + j] for j in range(0,n)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or (*new_args)))

    ## Ensure not two in the same column
    for j in range(0, n):
        args = [cells[i*n + j] for i in range(0,n)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or(*new_args)))

    ## Ensure not two in the same diagonal left to right
    for i in range(0,n):
        args = [cells[i + j*(n+1)] for j in range(0,n-i)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or(*new_args)))
        # print([i + j*(n+1) for j in range(0,n-i)])
    for j in range(1, n):
        args = [cells[n*j + i*(n+1)] for i in range(0,n-j)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or(*new_args)))
        # print([n*j + i*(n+1) for i in range(0,n-j)])

    # Ensure not two in same diagonal right to left
    for i in range(0,n):
        args = [cells[(n-1)*(j+1) - i] for j in range(0, n-i)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or(*new_args)))
        # print([ (n-1)*(j+1) - i  for j in range(0, n-i)])
    for j in range(1, n):
        args = [cells[(n-1)*(i+1) + n*j]  for i in range(0, n-j)]
        new_args = [And(x[0], x[1]) for x in itertools.combinations(args, 2)]
        s.add(Not (Or(*new_args)))
        # print([(n-1)*(i+1) + n*j for i in range(0,n-j)])


    #Check if it found a solution:
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    pattern = r'\d+'
    if(s.check() == sat):
        print(f"Constraints Satisified! Solution for {n}-Queens problem:"), 
        m = s.model()
        for d in m.decls():
            nums = re.findall(pattern, d.name())
            row = int(nums[0])
            col = int(nums[1])
            if m[d] == True:
                val = "Q"
            else:
                val = "_"
            matrix[row][col] = val
        
        print_matrix(matrix)
    else:
        print("Constraints Not Satisified!")
        sys.stdout.flush()




def main():
    for n in [4,8]:
        start = time.time()
        n_queens(n)
        end = time.time()
        print(f"The time for {n}-queens solution took {end-start} seconds")
    return


if __name__ == "__main__":
    main()