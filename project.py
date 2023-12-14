import pandas as pd
from z3 import *
from tqdm import trange
from bs4 import BeautifulSoup

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

    # After adding all the data into the dictionary, return as a pandas dataframe
    df = pd.DataFrame.from_dict(processes_data).T
    return df

# Runs z3 on the xml trace, and it returns whether it is satisified or not
def run_z3(d):

    s = Solver();
    s.set("timeout", 1000000)
    # Add each past and current value to its index
    z3_bools = {}
    for process in d.keys():
        # z3_bools[process] = {}
        proc_i_intervals = d[process]["interval"]
        for end_time in proc_i_intervals.keys():
            (start_time, current_val, old_val, misc_to_comm) = proc_i_intervals[end_time]
            ## If no communication, that means it is an event that changed the value
            if start_time != "0":
                if not misc_to_comm and not d[process]["interval"][start_time][3]:
                    previous = BoolVal(old_val)
                    if start_time == "0":
                        # Ensure that each process starts with x = True
                        curr_of_previous = BoolVal(True)
                    else:
                        # The start time of this one is the end_time of the previous
                        curr_of_previous = BoolVal(d[process]["interval"][start_time][1])
                    # print(previous == curr_of_previous)
                    s.add(previous == curr_of_previous)

            # z3_bools[process][end_time] = BoolVal(old_val)
            # z3_bools[process][end_time] = BoolVal(current_val)
        # print(z3_bools[process])

    if(s.check() == sat):
        print(f"Constraints Satisified!"), 
    else:
        print("Constraints Not Satisified!")
        sys.stdout.flush()



    return

## Main function
def main():
    df = get_data_from_xml("trace.xml")
    print(df)
    d = pd.DataFrame.to_dict(df.T)

    run_z3(d)
    return



if __name__ == "__main__":
    main()