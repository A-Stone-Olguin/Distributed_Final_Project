import pandas as pd
from z3 import *
from tqdm import trange
from bs4 import BeautifulSoup
import re

# Converts a boolean string to the boolean type
def true_false_string_to_bool(tf_str):
    ret_val = False
    match tf_str:
        case "true":
            ret_val = True 
        case "false":
            ret_val = False
        case _:
            print(f"There was an error: input string {tf_str} is not a string of true or false")
    # Return the converted boolean
    return ret_val

# Reads through a given xml file and returns a pandas dataframe with the relevant data
def get_data_from_xml(filename):
    ## processes_data will store all of the relevant data from tags:
    ##      Interval
    ##      Sent_Info
    ##      Receive_Info
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

# Determines whether the split to communication at receive time was a send or a receive
# Returns a boolean
def received_message(d, process, receive_time):
    # Check if a message was received at the given time
    if receive_time in d[process]["receive_info"]:
        return True 
    # That must mean it was sent, double check here: (checks for existence at send time)
    elif receive_time in d[process]["sent_info"]:
        return False
    else:
        exit(f"Misc to communication when no communication occurred! Process, time: ({process}, {receive_time})") 
    

# Runs z3 on the xml trace, and it returns whether it is satisified or not
def run_z3(d):

    # Names of each entries' interval for debugging if failed:
    invalid_info = []
    s = Solver();
    s.set("timeout", 1000000)
    # Add each past and current value to its index
    for process in d.keys():
        proc_i_intervals = d[process]["interval"]
        for end_time in proc_i_intervals.keys():
            (start_time, current_val, old_val, _) = proc_i_intervals[end_time]
            previous = old_val

            # Used to determine if we need to check both previous and current values match
            previous_and_current = False
            
            # Ensure that each process starts with x = True
            if start_time == "0":
                curr_of_previous = True
            else:
                # p_int is the previous interval (the start time of this is the end time of the last)
                p_int = d[process]["interval"][start_time]

                # If the previous interval involved communication:
                if p_int[3]:
                    received = received_message(d, process, start_time)

                    # If the previous sent a message, grab its old value
                    if not received:
                        # Sending a message changes old to new
                        curr_of_previous = p_int[2]

                    # If the previous received a message, want to make sure the current_value is the same as the one received
                    elif received: 
                        # Previous entry's received value is the same current value
                        current = current_val
                        curr_of_previous = p_int[1]
                        prev_of_previous = p_int[2]
                        previous_and_current = True

                    # Error
                    else:
                        exit("Error on saying communication, but could't find if it received the message!")
                # Otherwise, just check the previous interval's value
                else:
                    curr_of_previous = p_int[1]
                    
            # If we have to add previous and current checks
            if previous_and_current:
                bv = BoolVal(current == curr_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    # First True is to say tested previous and current, second true to to say current and current compared
                    invalid_info.append((process, start_time, end_time, current, curr_of_previous, True, True))
                bv = BoolVal(previous == prev_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    invalid_info.append((process, start_time, end_time, previous, prev_of_previous, True, False))
            else:
                bv = BoolVal(previous == curr_of_previous)
                s.add(bv)
                if (is_false(bv)):
                    invalid_info.append((process, start_time, end_time, previous, curr_of_previous, False, False))


    if(s.check() == sat):
        print(f"Constraints Satisified! The predicate maintained its value correctly!"), 
    else:
        print("Constraints Not Satisified! Here is where it went wrong: ")
        for val in invalid_info:

            if val[5]:
                if val[6]:
                    ## Had current and current compares
                    print(f"\tProcess {val[0]} (start, end) ({val[1]}, {val[2]}): Current Value is {val[3]} when it should be {val[4]}")
                else:
                    print(f"\tProcess {val[0]} (start, end) ({val[1]}, {val[2]}): Old Value is {val[3]} when it should be {val[4]}")
            else:
                print(f"\tProcess {val[0]} (start, end) ({val[1]}, {val[2]}): Old Value is {val[3]} when it should be {val[4]}")
        sys.stdout.flush()

        rerun_z3(d, invalid_info)

    return

def rerun_z3(d, prev_run_info):
    print("\nRerunning the solver!\n\n")
    # Set up z3 solver
    s = Solver();
    s.set("timeout", 1000000)

    # Add each past and current value to its index
    for process in d.keys():
        proc_i_intervals = d[process]["interval"]
        for end_time in proc_i_intervals.keys():
            invalid_curr = False
            invalid_prev = False
            (start_time, current_val, old_val, _) = proc_i_intervals[end_time]
            if len(prev_run_info) > 0:
                (p, s_t, e_t, _, _ , _, _) = prev_run_info[0]
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
                    
            if previous_and_current and not invalid_prev and not invalid_curr:
                bv = BoolVal(current == curr_of_previous)
                s.add(bv)
                bv = BoolVal(previous == prev_of_previous)
                s.add(bv)
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


    if(s.check() == sat):
        print(f"Constraints Satisified! The predicate maintained its value correctly!")
        print("Here are the fixes suggested for the errors: \n")
        m = s.model()
        pattern = r'\d+'
        for d in m.decls():
            nums = re.findall(pattern, d.name())
            if re.search(r'Old', d.name()):
                val = "Old"
            else: 
                val = "New"
            if len(nums) != 3:
                print("ERROR: Not three numbers in name!")
            else:                     ## We have the name of the old value too
                process = nums[0]
                start_time = nums[1]
                end_time = nums[2]
                solution = m[d]
                print(f"\tProcess {process}: (start, end): ({start_time}, {end_time}):")
                print(f"\t\tChange {val} value to {solution}")
    else:
        print("Constraints Not Satisified!\n ERROR: It should not go wrong again!")
        sys.stdout.flush()

## Main function
def main():
    d = get_data_from_xml("trace.xml")

    run_z3(d)
    return



if __name__ == "__main__":
    main()