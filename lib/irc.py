import socket


# Modifications to the socket.socket class specifically for IRC.
class IrcSocket(socket.socket):
    # Verbose send.
    # Sends data to the socket connection and prints it to the screen.
    # Also handles aquiring and releasing the semaphore, sendLock.
    def vsend(self, data):
        print data.rstrip()
        data += "\r\n"

        #sendLock.acquire()
        self.send(data)
        #sendLock.release()


# Given a string of data from the IRC server, returns a dictionary containing
# all the relevant parts of that string.
#
#               # These are valid for all messages.
# irc_message { type:   MESSAGE TYPE IN ALL CAPS 
#               data:   Message text/data
#
#               # These are valid for non-PING messages.
#               sender_header:  Full sender string (nick!username@host)
#               recipient:      The recipient of the message
#
#               # Valid for messages broadcast to a room:
#               room:   The room to which the message was sent.
#
#               # These are valid for messages from other users.
#               sender:             The user who sent the message
#               sender_username:    Username of the sender               
#               sender_host:        Hostname/IP of the sender
#
#               # Special type 330 - user ID verification.
#               current_nick        The current nick a user is using/
#               registered_nick     The nick the user is logged in as.
# }
def parse_irc_data(data):
    irc_message = {}
    parts = data.split(" ")

    if len(parts) == 2:
        irc_message["type"] = parts[0].upper()  # PING
        irc_message["data"] = parts[1][1:]  # Leading colon is removed.
    elif len(parts) > 2: 
        irc_message["sender_header"] = parts[0][1:] 
        irc_message["type"] = parts[1].upper()
        irc_message["recipient"] = parts[2]
        if len(parts) > 3: irc_message["data"] = " ".join(parts[3:]).lstrip()[1:]

        # 330: WHOIS response that a user is logged in.
        if irc_message["type"] == "330":
            irc_message["current_nick"] = parts[3]
            irc_message["registered_nick"] = parts[4]

        known_types = ['PRIVMSG', 'JOIN', 'PART', 'ACTION']

        # Only parse messages of a known type
        if irc_message["type"].upper() in known_types:
            # Things that are the same for all known_types
            irc_message["sender"] = irc_message["sender_header"].split("!")[0]

            (user, host) = irc_message["sender_header"].split("!")[1].split("@")
            irc_message["sender_username"] = user
            irc_message["sender_host"] = host

            # Special stuff for JOINs
            if irc_message["type"].upper() == "JOIN":
                if irc_message["recipient"][0] == ":":
                    irc_message["recipient"] = irc_message["recipient"][1:]
                
                irc_message["room"] = irc_message["recipient"]

            # Things that are the same for all but the above known_types    
            else:
                if irc_message["recipient"][0] == "#":
                    irc_message["room"] = irc_message["recipient"]
            
            

    else:
        return False

    return irc_message


### Functions for creating specific IRC command strings. ###
# Parameters for these should be in the following order:
#   recipient's nick, room (if applicable), message

# Returns a PRIVMSG command complete with \r\n that you can just s.send()
def privmsg(recipient, message):
    return "PRIVMSG %s :%s\r\n" % (recipient, message)

# Returns a KICK command string.
def kick(nick, room, reason):
    return "KICK %s %s %s\r\n" % (nick, room, reason)

### End of functions for creating specific IRC command strings. ###