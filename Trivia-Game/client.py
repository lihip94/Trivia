##############################################################################
# client
##############################################################################

import socket
import chatlib

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678


# HELPER SOCKET METHODS

def build_send_recv_parse(conn, cmd, data):
    """
    Builds a message, send it and recv and parse the recived message from the server.
    :return: cmd (str) and data (str) of the received message.
    """
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def build_and_send_message(conn, cmd, data):
    """
    Builds a new message using chatlib, wanted cmd and message.
    Prints debug info, then sends it to the given socket.
    Paramaters: conn (socket object), cmd (str), data (str)
    Returns: Nothing
    """
    full_msg = chatlib.build_message(cmd,data)
    conn.send(full_msg.encode())


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
    then parses the message using chatlib.
    Paramaters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    full_msg = conn.recv(1024).decode()

    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def connect():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket


def error_and_exit(error_msg):
    print(error_msg)
    exit()


def login(conn):

    cmd = ""
    while True:
        username = input("Please enter username: \n")
        password = input("Please enrer password: \n")
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], username + "#" + password)
        cmd, data = recv_message_and_parse(conn)
        if not cmd:
            error_and_exit("error")
        elif cmd != chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print(cmd + ": " + data)
        else:
            print("Logged in!")
            return


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


def get_score(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_score"], "")
    if cmd == chatlib.PROTOCOL_SERVER["your_score"]:
        print("Your score is " + data)
    else:
        error_and_exit(data)


def get_highscore(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["high_score"], "")
    if cmd == chatlib.PROTOCOL_SERVER["all_score"]:
        print("Highest score table:\n" + data)
    else:
        error_and_exit(data)

def get_logged_users(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_users"], "")
    if cmd == chatlib.PROTOCOL_SERVER["all_logged_users"]:
        print("All logged users: " + data)
    else:
        error_and_exit(data)


def play_question(conn):
    cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question"], "")
    msg_fields = chatlib.split_data(data, 6)
    if msg_fields == chatlib.ERROR_RETURN:
        print("Server message: ", data)
    else:
        print( "Q: " + msg_fields[1] + ":")
        for i in range(1,5):
            print( str(i) + ". " + msg_fields[i+1])
        answer = input("Please choose an answer [1-4]: ")
        cmd, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer"], msg_fields[0] + "#" + answer)
        if cmd == chatlib.PROTOCOL_SERVER["correct_answer"]:
            print("Yes!! correct answer")
        elif cmd == chatlib.PROTOCOL_SERVER["wrong_answer"]:
            print("Nope, the number of the corrent answer is: " + data)
        elif cmd == chatlib.PROTOCOL_SERVER["error_msg"]:
            print("Server message: ", data)
        else:
            error_and_exit(data)


def main():
    print("Connecting to " + SERVER_IP + " port " + str(SERVER_PORT))
    conn = connect()
    login(conn)
    while True:
        cmd = input("p      Play a trivia question \n"
                    "s      Get my score \n"
                    "h      Get scores table with the highest score \n"
                    "l      Get logged users \n"
                    "q      Quit\n"
                    "Please enter your request:\n")
        if cmd == 'p':
            play_question(conn)
        elif cmd == 's':
            get_score(conn)
        elif cmd == 'h':
            get_highscore(conn)
        elif cmd == 'l':
            get_logged_users(conn)
        elif cmd == 'q':
            logout(conn)
            break
        else:
            print("Error: please enter your request again")
    conn.close()
    print("Goodbye!")

if __name__ == '__main__':
    main()
