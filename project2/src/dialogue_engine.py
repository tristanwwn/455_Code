import shlex
import re
import os
import random
import argparse


from flask import Flask, request, jsonify
from flask_cors import CORS
from maestro_testing import Controller



file_path = "../dialogue/testDialogFileForPractice.txt"
current_level = 0
error_count = 0
line_number = 0
unmatched_count = 0
current_parent = None
current_scope = None
definitions = {}
rules = []
rule_stack = [None] * 7
user_info = {}



#Start robot in boot state, until dialogue engine done parsing.
state = "BOOT"

#Set to true to print error log. Stack holds error messages
debug_logging = True
debug_stack = []

# NEED TO HANDLE '_' IN INPUT: THIS IS WILDCARD THAT USER CAN REPLACE WITH ANYTHING
# NEED TO HANDLE $STRING IN RESPONSE, ROBOT REPLACES THIS WITH STORED USER INFO

app = Flask(__name__)

@app.route('/')
def index():
    return open('../templates/index.html').read()


@app.route('/input', methods=['POST'])
def handle_input():
    data = request.json
    user_text = data.get('text')
    #print(f"Received: {user_text}")  # just print for now
    response_text, actions = process_user_input(user_text)


    os.system(f'espeak "{response_text}"')
    for action in actions:
        print(f"ACTION: {action}")
    return jsonify({'response': response_text, 'state': state})





# Handles user text input, matching it to rules
# Also stores user info when wilcards encountered.
def process_user_input(input_string):
    global state
    global current_scope
    global unmatched_count
    pattern = r"[.,!?]"

    # Sanitize user input
    cleaned_input = input_string.strip().lower()
    cleaned_input = re.sub(pattern, "", cleaned_input)

    #return "yuh", []
    # Handle user input request to end execution
    if cleaned_input in ['stop', 'cancel', 'reset', 'quit']:
        print("Stop request. State moved to IDLE, shutting down")
        state = "IDLE"
        current_scope = None
        unmatched_count = 0
        return "Stopping execution.", []

    # Ready for input and determining valid rules
    if state == "IDLE":
         current_rules = rules
    else:
        current_rules = current_scope.children

    # Try to match user input to rule input
    matched_rule = None
    for r in current_rules:
        for p in r.input:
            if p in cleaned_input:
                matched_rule = r
                break
            # Have to check definitions if tilda
            elif p.startswith('~'):
                definition = p.strip('~')
                patterns = definitions.get(definition, [])
            # Handle wildcards. Replace the _ with relevant text inputted by the user.
            elif '_' in p:
                escaped = re.escape(p).replace(r'_', r'(.+)')
                match = re.search(escaped, cleaned_input)

                print(f"DEBUG pattern: {escaped}")
                print(f"DEBUG input: {cleaned_input}")

                if match:
                    matched_rule = r
                    captured_text = match.group(1).strip()
                    for output in r.output:
                        var_names = re.findall(r'\$(\w+)', output)
                        for var_name in var_names:
                            user_info[var_name] = captured_text
                    break

            else:
                patterns = [p]

            for i in patterns:
                if i in cleaned_input:
                    matched_rule = r
                    break
            if matched_rule:
                break
        if matched_rule:
            break

    # Safety catch to exit from scope if 4 or more mismatches from user input to rule
    if not matched_rule:
        unmatched_count += 1
        if unmatched_count >= 4 and state != "IDLE":
            state = "IDLE"
            current_scope = None
            print("Unmatched counts =4, STATE moved to IDLE")
            return "Lets end this conversation here.",[]
        return "I don't understand.", []


    unmatched_count = 0
    response = random.choice(matched_rule.output) if matched_rule.output else "I don't understand."

    # Replace $ wildcards with user info, if applicable
    for var_name, value in user_info.items():
        response = response.replace(f'${var_name}', value)

    actions = matched_rule.actions

    # Does the matched rule have children? Check and move into scope if so.
    if matched_rule.children:
        state = f"IN_SCOPE({matched_rule.level + 1})"
        current_scope = matched_rule
        print(f"STATE -> {state}")
    # Otherwise, we're done with this execution path and need to return
    else:
        state = "EXEC_ACTIONS"
        print(f"STATE moved to EXEC_ACTIONS")
        state = "IDLE"
        print(f"STATE moved to IDLE")

    return response, actions


# Class to create objects of each rule, and hold it.
class DialogueRule:
    def __init__(self):
        self.level = 0
        self.input = []
        self.output = []
        self.robot_action = []
        self.children = []

# Reads the stack for error logs, and prints them out if debug_loggin set to T
def debug_log():
    global error_count
    global line_number
    global debug_stack

    if debug_logging:
        for bugs in debug_stack:
            print(bugs)


# This is for parsing the definitions only, not rules, such as:
# ~greet: [hello hi howdy "hi there" "hey robot"]
def parse_definitions(string_line):
    indexed_line = string_line.split(":")
    global line_number
    global error_count


    # Cant only have keys with no values
    if len(indexed_line) < 2:
        debug_stack.append(f"ERROR at line {line_number}: while parsing definitions")
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
        debug_stack.append(f"ERROR at line number {line_number}: List values must be surrounded with open and closing brackets.")
        return None
    else:
        stripped_vals = string_vals.strip('[]')
        stripped_vals = shlex.split(stripped_vals)
        stripped_vals = [v.strip('"') for v in stripped_vals]
        return stripped_vals



# Parses rules and creates rule object for each applicable line in the file
def parse_rules(string_line):
        global error_count
        global line_number
        global current_parent
        global current_level
        global rules
        global rule_stack

        indexed_line = string_line.split(':')
        #print(indexed_line)

        # -------- ERROR CATCHING --------
        if len(indexed_line) < 3:
            error_count += 1
            debug_stack.append(f"ERROR at line number {line_number}: Missing minimum arguments for rule.")
            return

        # u: (~greet): [hi hello "what up" sup] < arm_raise >    -- Example of string
        # Error checking passed. Create rule object and set fields
        rule = DialogueRule()

        # -------- SET LEVEL OF RULE --------
        # Check the integer depth of the rule, empty string indicates its a root level
        # Keep track of depth and the current parent

        depth = indexed_line[0].strip()[1:]
        if depth == "":
            #Reset the stack if we see top level rule, append that rule to rules, then set the top of stack to root rule
            rules.append(rule)

            rule_stack = [None] * 7
            rule_stack[0] = rule

            rule.level = 0
            current_parent = None
            current_level = 0

        # Error catch if we're > 6 rules deep
        elif int(depth) > 6:
            error_count += 1
            debug_stack.append(f"ERROR at line number {line_number}: Over max depth level of 6. (Depth at max 6 deep)")
            return

        # Otherwise we add child rule.
        else:
            previous_level = int(depth) -1
            rule.level = int(depth)
            current_level = int(depth)
            rule_stack[previous_level].children.append(rule)
            rule_stack[int(depth)] = rule

        #print(current_level)


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
        stripped_outputs = re.sub(r'<\w+>', '', stripped_outputs).strip()

        #print(repr(stripped_outputs))
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

    for rule in rules:
        print(f"Rule: {rule.input} -> {rule.output} actions={rule.actions} children={len(rule.children)}")

    debug_log()
    state = "IDLE"

except FileNotFoundError:
    print("ERROR: Couldn't read the input file.")
except Exception as e:
    print(e)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        print(f"Random seed set to {args.seed}")



    app.run(host='0.0.0.0', port=5001)