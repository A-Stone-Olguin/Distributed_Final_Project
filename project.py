import pandas as pd
from z3 import *
from tqdm import trange
from bs4 import BeautifulSoup
import re
from tabulate import tabulate

def true_false_string_to_bool(tf_str):
    """
    Returns a boolean from a string that is true or false.

    Parameters:
    - tf_str (str): A string that is true or false

    Returns:
    - bool: The boolean value of the string

    """
    ret_val = False
    match tf_str.lower():
        case "true":
            ret_val = True 
        case "false":
            ret_val = False
        case _:
            print(f"There was an error: input string {tf_str} is not a string of true or false")
    return ret_val

def get_data_from_xml(filename):
    """
    Reads a given xml file for the trace and returns the relevant information.

    Parameters:
    - filename (str): A string that the name of the .xml file

    Returns:
    - dict: a dictionary containing the relevant information of the distributed trace

    """
    processes_data = {}
    for i in range(10):
        processes_data[str(i)] = {}
        processes_data[str(i)]["interval"] = {}
        processes_data[str(i)]["sent_info"] = {}
        processes_data[str(i)]["receive_info"] = {}

    ## Open the file to be parsed
    with open(filename) as f:
        data = f.read()

    # Grab the data from BeautifulSoup
    print("Grabbing data with beautiful soup (this could take a little while)")
    bs_data = BeautifulSoup(data, "xml")
    print("Finished collecting data with beautiful soup!\n")

    # Find all information from the interval:
    b_interval = bs_data.find_all("interval")
    for i in trange(len(b_interval), desc="Grabbing Interval tag information", leave=True):
        tag = b_interval[i]
        ## Grab the info from each tag in an interval:
        start = tag.find("start_time").contents[0]
        end = tag.find("end_time").contents[0]
        current_val = tag.find("associated_variable")["value"]
        old_val = tag.find("associated_variable")["old_value"]

        # Current_val and old_val are both strings, convert to booleans
        current_val = true_false_string_to_bool(current_val)
        old_val = true_false_string_to_bool(old_val)

        # If there is a cut for communication, note it
        if tag.find("misc"):
            misc_to_comm = True
        else:
            misc_to_comm = False

        # Add the interval information for the tag
        processes_data[tag["process"]]["interval"][end] = (start, current_val, old_val, misc_to_comm)

    print("\n")
    # Find all information about messages (send/receive)
    b_message = bs_data.find_all("message")
    for i in trange(len(b_message), desc="Grabbing Message tag information", leave=True):
        tag = b_message[i]
        match tag["type"]:
            case "send":
                timestamp_send = tag.find("sender_time").contents[0] 
                sent_to = tag.find("to").contents[0]
                processes_data[tag["process"]]["sent_info"][timestamp_send] = sent_to
            case "receive":
                timestamp_send = tag.find("sender_time").contents[0] 
                timestamp_receive = tag.find("receiver_time").contents[0]
                from_msg = tag.find("from").contents[0]
                processes_data[tag["process"]]["receive_info"][timestamp_receive] = (from_msg, timestamp_send)
            case _:
                print("ERROR!!")

    print("\n")

    # After adding all the data into the dictionary, return it
    return processes_data

def received_message(d, process, receive_time):
    """
    Returns a boolean on whether a given process received a message (or sent it)

    Parameters:
    - d (dict): Dictionary containing information about the distributed trace
    - process (str): The string name of the process
    - receive_time (str): An integer string that is the time a process cut to communication

    Returns:
    - bool: A boolean that determines whether that process received a message

    Raises:
    - KeyError: An error that says communication occurred, but it does not exist

    """
    # Check if a message was received at the given time
    if receive_time in d[process]["receive_info"]:
        return True 
    # That must mean it was sent, double check here: (checks for existence at send time)
    elif receive_time in d[process]["sent_info"]:
        return False
    else:
        raise KeyError(f"Misc to communication when no communication occurred! Process, time: ({process}, {receive_time})") 
    

def run_z3(d, prev_run_info = [], run_again = False):
    """
    Runs Z3 on a distributed program trace and satisfies the message passing predicate.

    Parameters:
    - d (dict): Dictionary containing information about the distributed trace

    Optional Parameters:
    - prev_run_info (List 3-Tuple): Information about the previous run (used only in rerunning). Default is []
    - run_again (bool): Boolean that states whether this function is being run again (used only in rerun). Default is False

    Returns:
    - None

    """
    # Names of each entries' interval for debugging if failed:
    invalid_info = []
    if run_again:
        print("Rerunning the solver!\n")

    # Set up z3 solver
    s = Solver();
    s.set("timeout", 1000000)

    # Add each past and current value to its index
    for process in d.keys():
        proc_i_intervals = d[process]["interval"]
        for end_time in proc_i_intervals.keys():

            # Information for rerunning to solve the errors
            invalid_curr = False
            invalid_prev = False
            (start_time, current_val, old_val, _) = proc_i_intervals[end_time]
            if len(prev_run_info) > 0:
                (p, s_t, e_t) = prev_run_info[0]
                if p == process and s_t == start_time and e_t == end_time:
                    invalid_curr = True
                    current = Bool(f"Current_{p}_{s_t}_{e_t}")
                    previous = Bool(f"Old_{p}_{s_t}_{e_t}")
                    prev_run_info.pop(0)
                else:
                    previous = old_val
            else:
                previous = old_val

            # Used to determine if we need to check both previous and current values match
            previous_and_current = False
            
            # Ensure that each process starts with x = True
            if start_time == "0":
                curr_of_previous = True
            else:
                # p_int is the previous interval (the start time of this is the end time of the last)
                p_int = d[process]["interval"][start_time]

                # Check whether we need to update previous booleans too
                if invalid_curr :
                    invalid_prev = True
                    prev_start = d[process]["interval"][s_t][0]
                    curr_of_previous = Bool(f"Current_{p}_{prev_start}_{s_t}")
                    prev_of_previous = Bool(f"Old_{p}_{prev_start}_{s_t}")



                # If the previous interval involved communication:
                if p_int[3]:
                    received = received_message(d, process, start_time)

                    # If the previous sent a message, grab its old value
                    if not received:
                        # Sending a message changes old to new
                        if not invalid_prev:
                            curr_of_previous = p_int[2]

                    # If the previous received a message, want to make sure the current_value is the same as the one received
                    elif received: 
                        previous_and_current = True
                        if not invalid_curr:
                            # Previous entry's received value is the same current value
                            current = current_val
                            curr_of_previous = p_int[1]
                            prev_of_previous = p_int[2]

                    # Error
                    else:
                        exit("Error on saying communication, but could't find if it received the message!")
                # Otherwise, just check the previous interval's value
                else:
                    curr_of_previous = p_int[1]
                    
            # Case statements to determine how to pass the argument to Z3:
            if previous_and_current and not invalid_prev and not invalid_curr:
                bv = BoolVal(current == curr_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    invalid_info.append((process, start_time, end_time))
                bv = BoolVal(previous == prev_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    invalid_info.append((process, start_time, end_time))
            elif previous_and_current and not invalid_prev and invalid_curr:
                s.add(current == BoolVal(curr_of_previous))
                s.add(previous == BoolVal(prev_of_previous))
            elif previous_and_current and invalid_prev and invalid_curr:
                s.add(current == curr_of_previous)
                s.add(previous == prev_of_previous)
            elif not invalid_prev and invalid_curr:
                s.add(previous == BoolVal(curr_of_previous))
            elif invalid_prev and invalid_curr:
                s.add(previous == curr_of_previous)
            else:
                bv = BoolVal(previous == curr_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    invalid_info.append((process, start_time, end_time))


    # If we satisfied
    if(s.check() == sat):
        print(f"Constraints Satisified! The predicate maintained its value correctly!")

        # If we ran again, show how to fix the errors
        if run_again:
            print("Here are the changes and checks suggested for the errors: \n")
            m = s.model()
            pattern_vals = r'\d+'
            pattern_old = r'Old'
            # Solutions dictionary to print after
            solutions_print = {}

            for i, d in enumerate(m.decls()):
                # Grab information about the solution and add it to table
                solutions_print[str(i)] = {}
                nums = re.findall(pattern_vals, d.name())
                if len(nums) != 3:
                    print("ERROR: Not three numbers in name!")
                else:          
                    process = nums[0]
                    start_time = nums[1]
                    end_time = nums[2]
                    solution = m[d]
                    if re.search(pattern_old, d.name()):
                        val = "Old"
                    else: 
                        val = "New"
                    solutions_print[str(i)]["Process"] = process
                    solutions_print[str(i)]["Start_Time"] = start_time
                    solutions_print[str(i)]["End_Time"] = end_time
                    solutions_print[str(i)]["Change:"] = f"{val} value to {str(solution).lower()}"

            # Print solutions
            df = pd.DataFrame.from_dict(solutions_print).T
            df = tabulate(df, headers="keys", tablefmt = 'grid', showindex=True, \
                          colalign=("center", "center", "center", "center", "center"))
            print(df)
            return
        
    # If we ran again and failed: is an error
    elif run_again:
        print("Constraints Not Satisified!\nERROR: It should not go on the second run!")
        sys.stdout.flush()
        return
    # If we ran the first time and didn't satisfy: Display what is wrong and ask if it wants to be solved
    else:
        print("Constraints Not Satisified! Here is where it went wrong: ")

        # Print information about failed intervals:
        invalid_print = {}
        for i, val in enumerate(invalid_info):
            invalid_print[str(i)] = {}
            invalid_print[str(i)]["Process"] = val[0]
            invalid_print[str(i)]["Start_Time"] = val[1]
            invalid_print[str(i)]["End_Time"] = val[2] 
        sys.stdout.flush()
        df = pd.DataFrame.from_dict(invalid_print).T 
        df = tabulate(df, headers="keys", tablefmt = 'grid', showindex=True, \
                      colalign=("center", "center", "center", "center"))
        print(df)

        # Prompt the user to run again
        print("\nWant to run again? Y for yes, N for no")
        while not run_again:
            response = input("\t").strip().lower()
            if response in ('y', 'yes'):
                run_again=True
                run_z3(d, invalid_info, True)
            elif response in ('n', 'no'):
                return
            else:
                print("Ivalid input. Please enter Y for yes or N for no. ")
        return


## Main function
def main():
    # Get the data from the trace
    d = get_data_from_xml("trace.xml")

    # Run z3 on the data
    run_z3(d)
    return



if __name__ == "__main__":
    main()