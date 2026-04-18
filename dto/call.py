class Call:
    def __init__(self, parsed_message):
        self.message_type_id = parsed_message[0]
        self.message_id = parsed_message[1]
        self.action = parsed_message[2]
        self.payload = parsed_message[3]