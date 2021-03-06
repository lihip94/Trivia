# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",
    "logout_msg": "LOGOUT",
    "get_score": "MY_SCORE",
    "high_score": "HIGHSCORE",
    "logged_users": "LOGGED",
    "get_question": "GET_QUESTION",
    "send_answer": "SEND_ANSWER"
}  # .. Add more commands if needed

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",
    "error_msg": "ERROR",
    "login_failed_msg": "ERROR",  ################
    "your_score": "YOUR_SCORE",
    "all_score": "ALL_SCORE",
    "all_logged_users": "LOGGED_ANSWER",
    "your_question": "YOUR_QUESTION",
    "correct_answer": "CORRECT_ANSWER",
    "wrong_answer": "WRONG_ANSWER"
}  # ..  Add more commands if needed

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
    """
    Gets command name (str) and data field (str) and creates a valid protocol message
    Returns: str, or None if error occured
    """
    cmd_length = len(cmd)
    data_length = len(data)
    if cmd_length > CMD_FIELD_LENGTH:
        return ERROR_RETURN
    if data_length > MAX_DATA_LENGTH:
        return  ERROR_RETURN

    num_of_zeros = LENGTH_FIELD_LENGTH - len(str(data_length))
    full_msg = cmd + " "*(CMD_FIELD_LENGTH -cmd_length) + DELIMITER + num_of_zeros*"0" + str(data_length) + DELIMITER + data
    if len(full_msg) > MAX_MSG_LENGTH:
        return ERROR_RETURN
    return full_msg


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occurred, returns None, None
    """
    if len(data) > MAX_MSG_LENGTH:
        return ERROR_RETURN, ERROR_RETURN
    cmd = data[0:CMD_FIELD_LENGTH].strip()
    length_field = data[CMD_FIELD_LENGTH + 1: CMD_FIELD_LENGTH + LENGTH_FIELD_LENGTH + 1]
    data = data[MSG_HEADER_LENGTH:]
    if len(data) > MAX_DATA_LENGTH:
        return ERROR_RETURN, ERROR_RETURN
    # data = data.strip()
    if not check_length_field(length_field):
        return ERROR_RETURN, ERROR_RETURN
    elif int(length_field) != len(data):
        return ERROR_RETURN, ERROR_RETURN
    # elif cmd not in PROTOCOL_SERVER.values or cmd not in PROTOCOL_CLIENT.values(): ############################
    #       return ERROR_RETURN, ERROR_RETURN
    return cmd, data


def check_length_field(length_field):
    for char in length_field:
        if not (char == " " or (char.isdigit()) ):
            return False
    if len(length_field) != LENGTH_FIELD_LENGTH:
        return False
    return True

def split_data(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's data field delimiter (|#) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occured, returns None
    """
    msg_fields = str(msg).split('#')
    if len(msg_fields) != expected_fields:
        return ERROR_RETURN
    return msg_fields


def join_data(msg_fields):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
    Returns: string that looks like cell1#cell2#cell3
    """
    msg = ""
    for element in msg_fields:
        msg += str(element) + DATA_DELIMITER
    return msg[:-1]
