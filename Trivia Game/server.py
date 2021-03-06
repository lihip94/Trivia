##############################################################################
# server
##############################################################################

import socket
import chatlib
import select
import collections
import random
import json
import requests

# GLOBALS
users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
client_socekts = []
messages_to_send = []
DEBG_MSG = {
    "client": "[CLIENT]",
    "server": "[SERVER]"
}

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def build_and_send_message(conn, cmd, msg):
    full_msg = chatlib.build_message(cmd, msg)
    conn.send(full_msg.encode())
    print_debug_message(DEBG_MSG["server"],conn, full_msg)  # Debug print


def recv_message_and_parse(conn):
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    print_debug_message(DEBG_MSG["client"],conn, full_msg)  # Debug print
    return cmd, data


def print_debug_message(user, conn, message):
    print(user,conn.getpeername(), message)


# Data Loaders #
def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    with open('questions.txt') as questions_file:
        data = questions_file.read()
    questions = json.loads(data)
    return questions


def load_questions_from_web():
    data = requests.get('https://opentdb.com/api.php?amount=50&type=multiple')
    questions = data.json()
    questions = dict((result, 0) for result in questions['results'])


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    with open('users.txt') as users_file:
        data = users_file.read()
    users = json.loads(data)
    return users


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Setting up server...")
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    return server_socket


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], error_msg)

##### MESSAGE HANDLING


def handle_getscore_message(conn, username):
    global users
    score = users[username]["score"]
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_score"], str(score))


def handle_highscore_message(conn):
    global users
    all_scores = ""
    # new_list = sorted(users, key= users.get('score'))
    sorted_users = collections.OrderedDict(sorted(users.items(), key=lambda t: t[1]["score"],reverse= True))

    for username in sorted_users:
        all_scores += username + ": " + str(sorted_users[username]["score"]) + "\n"
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["all_score"], all_scores)


def handle_logged_message(conn):
    global logged_users
    all_logged_users = ""
    for user in logged_users:
        all_logged_users += logged_users[user] + ","
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["all_logged_users"], all_logged_users[:-1])


def handle_logout_message(conn):
    """
    Closes the given socket
    Recieves: socket
    Returns: None
    """
    global client_socekts
    global logged_users
    client_socekts.remove(conn)
    del logged_users[conn.getpeername()]
    print_debug_message(DEBG_MSG["server"], conn, "LOGOUT")
    conn.close()

def create_random_question(username):
    global questions
    global users
    new_questions = set(users[username]["questions_asked"]) ^ set(questions.keys())
    if list(new_questions):
        question_id = random.choice(list(new_questions))
    else:
        return "No more questions"
    users[username]["questions_asked"].append(question_id)
    full_msg = question_id + "#" + questions[question_id]["question"]
    for answer in questions[question_id]["answers"]:
        full_msg += "#" + answer
    return full_msg


def handle_question_message(conn):
    full_msg = create_random_question(logged_users[conn.getpeername()])
    if full_msg == "No more questions":
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], full_msg)
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_question"], full_msg)


def handle_answer_message(conn, username, data):
    global questions
    global users
    answer_fields = chatlib.split_data(data, 2)
    if answer_fields:
        question_id = answer_fields[0]
        user_answer = answer_fields[1]
        if question_id in questions.keys():
            correct_answer = str(questions[question_id]["correct"])
            if  users[username]["questions_asked"][-1] == question_id and correct_answer == user_answer:
                users[username]["score"] = users[username]["score"] + 5
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_answer"], "")
            else:
                build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_answer"], correct_answer)
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], "worng input")
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], "worng input")


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later
    msg_fields = chatlib.split_data(data, 2)
    user_name = msg_fields[0]
    user_password = msg_fields[1]
    if user_name in users:
        if users[user_name]["password"] == user_password:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
            logged_users.update({ conn.getpeername() : user_name})
        else:
            send_error(conn, "Password does not match!")
    else:
        send_error(conn, "Username does not exist!")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users  # To be used later
    if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
        handle_login_message(conn, data)
    elif cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
        handle_logout_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_score"]:
        handle_getscore_message(conn, logged_users[conn.getpeername()]);
    elif cmd == chatlib.PROTOCOL_CLIENT["high_score"]:
        handle_highscore_message(conn);
    elif cmd == chatlib.PROTOCOL_CLIENT["logged_users"]:
        handle_logged_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["get_question"]:
        handle_question_message(conn)
    elif cmd == chatlib.PROTOCOL_CLIENT["send_answer"]:
        handle_answer_message(conn, logged_users[conn.getpeername()], data)
    elif cmd == chatlib.ERROR_RETURN:
        handle_logout_message(conn)
    else:
        send_error(conn, "Unknown command")


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions
    users = load_user_database()
    questions = load_questions()
    print("Welcome to Trivia Server!", )
    server_socket = setup_socket()
    global client_socekts
    global messages_to_send
    while True:
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_socekts, client_socekts, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                (client_socket, client_address) = current_socket.accept()
                print("New client joind!")
                client_socekts.append(client_socket)
            else:
                try:
                    cmd, data = recv_message_and_parse(current_socket)
                except:
                    handle_logout_message(current_socket)
                messages_to_send.append((current_socket, data))
            if messages_to_send:
                for message in messages_to_send:
                    ready_socket, full_msg = message
                    if ready_socket in ready_to_write:
                        handle_client_message(ready_socket, cmd, full_msg)
                        messages_to_send.remove(message)
            else:
                print("Listening for clients")


if __name__ == '__main__':
    main()

