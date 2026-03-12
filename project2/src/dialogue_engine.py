# Dialogue engine
import shlex
import re

file_path = "../dialogue/testDialogFileForPractice.txt"
current_level = 0
error_count = 0
line_number = 0
current_parent = None
definitions = {}
rules = []

# NEED TO HANDLE '_' IN INPUT: THIS IS WILDCARD THAT USER CAN REPLACE WITH ANYTHING
# NEED TO HANDLE $STRING IN RESPONSE, ROBOT REPLACES THIS WITH STORED USER INFO


# Class to hold each rule
class DialogueRule:
    def __init__(self):
        self.level = 0
        self.input = []
        self.output = []
        self.robot_action = None
        self.children = []


# This is for parsing the definitions only, not rules, such as:
# ~greet: [hello hi howdy "hi there" "hey robot"]
def parse_definitions(string_line):
    indexed_line = string_line.split(":")
    global line_number
    global error_count

    # Cant only have keys with no values
    if len(indexed_line) < 2:
        print(f"ERROR at line {line_number}: while parsing definitions")
        error_count += 1
        return


    # -------- PARSE KEY --------
    key = indexed_line[0].strip().strip('~')
    #print(key)

    # -------- PARSE VALS --------
    stripped_vals = indexed_line[1].strip()
    stripped_vals = strip_args(stripped_vals)
    if stripped_vals is not None:
        definitions[key] = stripped_vals
    else:
        return

    #print(vals)

# Helper function to properly separate list of arguments with respect to args encapsulated in quotes
def strip_args(string_vals):
    global error_count

    if not string_vals.startswith("[") or not string_vals.endswith("]"):
        error_count += 1
        print(f"ERROR at line number {line_number}: List values must be surrounded with open and closing brackets.")
        return None
    else:
        stripped_vals = string_vals.strip('[]')
        stripped_vals = shlex.split(stripped_vals)
        stripped_vals = [v.strip('"') for v in stripped_vals]
        return stripped_vals




def parse_rules(string_line):
        global error_count
        global line_number
        global current_parent
        global current_level

        indexed_line = string_line.split(':')
        #print(indexed_line)

        # -------- ERROR CATCHING --------
        if len(indexed_line) < 3:
            error_count += 1
            print(f"ERROR at line number {line_number}: Missing minimum arguments for rule.")
            return

        # u: (~greet): [hi hello "what up" sup] < arm_raise >    -- Example of string
        # Error checking passed. Create rule object and set fields
        rule = DialogueRule()

        # -------- SET LEVEL OF RULE --------
        # Check the integer depth of the rule, empty string indicates its a root level
        # Keep track of depth and the current parent

        depth = indexed_line[0].strip()[1:]
        if depth == "":
            rule.level = 0
            current_parent = rule
            current_level = 0
        elif int(depth) > 6:
            error_count += 1
            print(f"ERROR at line number {line_number}: Over max depth level of 6. (Depth at max 6 deep)")

            return
        else:
            rule.level = int(depth)
            current_level = int(depth)

        print(current_level)


        # -------- PARSE INPUTS --------
        # Set the possible user inputs for this level
        # If brackets present, we have multiple user inputs. Must separate them into array list. Otherwise wrap the one arg in list

        stripped_inputs = indexed_line[1].strip('()')
        if stripped_inputs.startswith('['):
            stripped_inputs = strip_args(stripped_inputs)
            if stripped_inputs is not None:
                rule.input = stripped_inputs
            else:
                return
        else:
            stripped_inputs = [stripped_inputs]
            rule.input = stripped_inputs

        #print(len(stripped_inputs))

        # -------- PARSE DIALOGUE OUTPUTS --------
        stripped_outputs = indexed_line[2]

        # Extract the angled bracket robot movement actions from the dialogue string
        rule.actions = re.findall(r'<(\w+)>', stripped_outputs)

        # Remove the angled bracket movement actions from the dialogue string
        stripped_outputs = re.sub(r'<\w+>', '', stripped_outputs.strip())

        if stripped_outputs.startswith('['):
            list_outputs = strip_args(stripped_outputs)
            if list_outputs is not None:
                rule.output = list_outputs
            else:
                return
        else:
            stripped_outputs = [stripped_outputs]
            rule.output = stripped_outputs



try:
    for line in open(file_path, "r"):
        if line.strip().startswith("#") or line.strip() == "":
            line_number += 1
            continue
        elif line.startswith('~'):
            line_number += 1
            parse_definitions(line)
        else:
            line_number += 1
            parse_rules(line)


    print(error_count)

except FileNotFoundError:
    print("ERROR: Couldn't read the input file.")
except Exception as e:
    print(e)
