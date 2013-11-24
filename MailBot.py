#!/usr/bin/env python

##############################################################################
##  MailBot  ##  created by: persistence                                    ##
##############################################################################

##############################################################################
##  USER SETTINGS GO HERE                                                   ##
##############################################################################

# The server and port the bot should connect to.
SERVER = ""
PORT = 6667

# The bot's name on the server. Also used as username and real name.
HANDLE = "MailBot"

# The password for the bot to identify itself.
# This should be "" if the bot's nick is not registered
HANDLE_PASSWORD = "" 

# The nick of the bot's owner. This user will be able to send the bot commands.
# This user will also receive a private message from the bot once the bot
# connects to the server.
MASTER_NICK = "persistence" # Your real nick goes here to control the bot.
MASTER_NICK_PASSWORD = "" # Password used to authenticate admin commands.

# Auto-join these rooms on connect. It's ok to leave empty.
ROOMS = [ ] 

# Delay in seconds between multiple messages.
DELAY = 0.5

# Delay between initial connection commands to the server.
STARTUP_DELAY = 1.0

# Groups of nicks for sending mass messages.
# Each group's key is the name of that group.
# It's value is a list containing all the members.
NICK_GROUPS = {}

# Blacklist and whitelist of users who can send commands to the bot.
ENABLE_BLACKLIST = False
BLACKLISTED_NICKS = []

ENABLE_WHITELIST = False
WHITELISTED_NICKS = []

##############################################################################
## END OF USER SETTINGS                                                     ##
##############################################################################

import socket       # To build the connection.
import threading    # For the listening thread.
import time         # For delays between commands on connect.
import sys          # For sys.exit().
from datetime import datetime   # For timestamps.


# Global variables that should not be changed by the user. (Not settings.)
ENABLE_IRC_COMMANDS = True

# This semaphore keeps multiple streams of data from being sent
# simultaneously.
sendLock = threading.Semaphore(value=1)

# All nicknames are converted to lowercase to fix case-sensitivity.
MASTER_NICK = MASTER_NICK.lower()

# Kills all threads
def really_quit():
    # Terminate running threads
    for thread in threading.enumerate():
        if thread.isAlive():
            try:
                thread._Thread__stop()
            except:
                print(str(thread.getName()) + ' could not be terminated')
    sys.exit()


# Returns a human readable timestamp string: YYYY-MM-DD hh:mm:ss
def timestamp():
    timestamp = "%(year)s-%(month)s-%(day)s %(hour)s:%(minute)s:%(second)s" % {
                "year": datetime.now().year,
                "month": datetime.now().month,
                "day": datetime.now().day,
                "hour": datetime.now().hour,
                "minute": datetime.now().minute,
                "second": datetime.now().second, }
    return timestamp   
         

# Lowercases all strings in a list.
def lower(l):
    new_list = []
    for item in l:
        new_list.append(str(item).lower())
    return new_list


# Logs messages that are sent directly to the bot (as opposed to
# the room/channel) to a file. I did this to examine hack attempts.
def log_append(message):
    log_filename = sys.argv[0] + ".txt"
    log_file = open(log_filename, 'a')
    log_file.write(message + "\n")
    log_file.close()


# Reads a file into a list, stripping \r's and \n's along the way.
def file2list(filename):
    f = open(filename, 'r')
    l = f.readlines()

    for n in range(len(l)):
        l[n] = l[n].rstrip()

    return l


# Compares a username to the white and blacklists.
# Returns True if the user is allowed to access MailBot.
def user_allowed(username):
    accepted_users = [
        (ENABLE_BLACKLIST == False or username.lower() not in lower(BLACKLISTED_NICKS)),
        (ENABLE_WHITELIST == False or username.lower() in lower(WHITELISTED_NICKS)),
    ]

    if all(accepted_users):
        return True
    else:
        return False


# Saves messages to files for delivery later.
def record_message(sender, recipient, message):
    # Recipient names should be stored case insensitive.
    recipient = recipient.lower()

    outfile_name = "messages-%s.txt" % recipient
    outfile = open(outfile_name, 'a')
    full_message = "[%s] %s: %s\n" % (timestamp(), sender, message)
    outfile.write(full_message)
    outfile.close()


# Returns a list of messages for the user. If there is an error, returns an
# empty list.
def read_messages(recipient):
    # All recipient names are stored in lower case.
    recipient = recipient.lower()

    try:
        messages_filename = "messages-%s.txt" % recipient
        messages = file2list(messages_filename)

        return messages
    except:
        return []

# Erases the user's messages.
def clear_messages(nick):
    # Lower-case message storage only.
    nick = nick.lower()

    messages_filename = "messages-%s.txt" % nick
    f = open(messages_filename, 'w')
    f.write('')
    f.close


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


# Listens for incoming data and automatically responds where appropriate.
def listen(s):
    global ENABLE_IRC_COMMANDS
    messages = {}   # This is just a place to store messages until I put in 
                    # a database. It will be replaced eventually.

    # Keeps track of how many times the same user was kicked.
    kick_counter = {}

    # Verbose send.
    # Sends data to the socket connection and prints it to the screen.
    # Also handles aquiring and releasing the semaphore, sendLock.
    def vsend(data, socket_instance=s):
        print data.rstrip()
        data += "\r\n"

        sendLock.acquire()
        socket_instance.send(data)
        sendLock.release()


    while s:
        try:
            # Read received data into data_buffer, and in case we read in more
            # than one message, split it for each line.
            data_buffer = s.recv(1024).split("\n")
            for data in data_buffer:

                data = data.rstrip() # Clean whitespace off my data.
                if data == "": continue # Ignore empty lines

                print data # Display received data to the user

                message = parse_irc_data(data)

                # Only respond to messages understood by parse_irc_data().
                if not message: continue

                # The bot should never respond to a message it sends.
                if message.get("sender") == HANDLE: continue


                # Respond to server PING's
                if message["type"] == "PING":
                    vsend("PONG :%s" % message["data"])
                    continue    # PING's need no further processing.

                # Log interesting things.
                interesting_things = [
                    ( "http://" in message["data"].lower() ),
                    ( "https://" in message["data"].lower() ),
                    ( "ftp://" in message["data"].lower() ),
                    ( "www." in message["data"].lower() ),
                    ( ".com" in message["data"].lower() ),
                    ( ".org" in message["data"].lower() ),
                    ( ".net" in message["data"].lower() ),
                    ( ".us" in message["data"].lower() ),
                    ( MASTER_NICK in message["data"].lower() ),
                ]

                if (any(interesting_things) and message["type"] == "PRIVMSG" and
                    message["sender"] != MASTER_NICK and message["sender"] != HANDLE):
                    log_entry = "[%(timestamp)s] %(sender)s->%(recipient)s: %(message)s" % {
                        "timestamp": timestamp(),
                        "sender": message["sender"],
                        "recipient": message["recipient"],
                        "message": message["data"],
                    }

                    log_append(log_entry)


                # Since the white/blacklists are located below, messages from
                # the server will cause errors if I don't filter them out.
                if message["type"] != "JOIN" and message["type"] != "PRIVMSG":
                    continue

                # Everything below here is available to whitelisted/
                # non-blacklisted users only.
                if not user_allowed(message["sender"]): continue


                # Responses to users JOINing the current room.
                if message["type"] == "JOIN":

                    # Greet all users who enter the room.
                    vsend(privmsg(message["recipient"], "Hello, %s." % message["sender"]))

                    # Notify the user if they have any new messages.
                    messages = read_messages(message["sender"])
                    message_count = len(messages)

                    if message_count > 0:
                        vsend(privmsg(message["sender"], "*** You have %d messages. Type \"read\" to retrieve. ***" % message_count))


                # Responses to PRIVMSGs to rooms or to the bot
                if message["type"] == "PRIVMSG":

                    # Break up the message data into the command (the first word)
                    # and the parameters (all remaining words).

                    # Commands should be lowercase/case insensitive.
                    command = message["data"].split(" ")[0].lower()

                    # Parameters is everything following the command.
                    if len(message["data"]) > len(command):
                        parameters = message["data"][len(command):].strip()
                    else:
                        parameters = ""

                    # Responses to messages broadcast to rooms.
                    if message["recipient"] != HANDLE:

                        # Offer help to people using Watcher's !seen command.
                        if command == "!seen" and parameters.strip() != "":
                            looking_for = parameters.split(" ")[0]
                            reply = "%s: If you want to leave %s a message, I can do that for you. Just PM me." % (message["sender"], looking_for)
                            vsend(privmsg(message["room"], reply))


                    # Responses to private messages sent to the bot.
                    if message["recipient"] == HANDLE:

                        user_commands = lower(["help", "tell", "read", "erase"])

                        # Respond to anything with message count if the user has
                        # messages waiting. Anything except "erase" or "tell".
                        message_count = len(read_messages(message["sender"]))
                        if message_count > 0 and command != "erase" and \
                            command != "tell":
                            vsend(privmsg(message["sender"], "*** You have %d messages. ***" % message_count))
                            time.sleep(DELAY)

                        # Respond to unrecognized commands.
                        if command.lower() not in user_commands:
                            reply = "Hello there, %s. Type \"help\" if you need instructions." % message["sender"]
                            vsend(privmsg(message["sender"], reply))

                        # Valid commands go here.
                        else:
                            user_error = False

                            # "help" displays help.
                            if command == "help":
                                help_text = """Available commands:
                                               %s
                                               Send a user a message: tell username such and such message
                                               Send a group of users a message: tell @groupname such and such message
                                               Read your messages: read
                                               Erase all your messages: erase
                                               ---
                                               Currently available groups are: %s
                                               ---
                                               Be aware that the owner of this bot (like the owner of this server) can read all the messages you send, so please do not send anything private or sensitive.
                                               ---
                                               Please do not use this bot to spam other users or you will be added to the blacklist.""" % (user_commands, NICK_GROUPS.keys())

                                for line in help_text.split("\n"):
                                    if line.strip() != "":
                                        vsend(privmsg(message["sender"], line.strip()))
                                        time.sleep(DELAY)

                            # "tell" sends messages.
                            elif command == "tell" and len(parameters.split(" ")) > 1:
                                message_recipient = parameters.split(" ")[0]
                                message_to_send = parameters[len(message_recipient)+1:]

                                # Send a message to a group of users.
                                if message_recipient[0] == "@":
                                    recipients = NICK_GROUPS.get(message_recipient[1:])
                                    if recipients == None:
                                        vsend(privmsg(message["sender"], "That is an invalid group name."))
                                        continue
                                # Send a message to just one user.
                                else:
                                    recipients = [ message_recipient, ]

                                # Send the messages.
                                for recipient in recipients:
                                    record_message(message["sender"], recipient, message_to_send)

                                    time.sleep(DELAY)

                                # Notify the recipients that they have messages waiting.
                                for recipient in recipients:                                    
                                    vsend(privmsg(recipient, "You have a new message from %s. Say \"read\" to read your messages." % message["sender"]))
                                
                                    time.sleep(DELAY)

                                # Notify that the messages have been sent.    
                                vsend(privmsg(message["sender"], "Your message to %s has been sent!" % recipients))

                                    

                            # "read" displays stored messages.
                            elif command == "read":
                                user_messages = read_messages(message["sender"])
                                message_count = len(user_messages)

                                vsend(privmsg(message["sender"], "*** You have %d messages. ***" % message_count))
                                time.sleep(DELAY)

                                for m in user_messages:
                                    vsend(privmsg(message["sender"], m))
                                    time.sleep(DELAY)

                                if message_count > 0:
                                    vsend(privmsg(message["sender"], "*** End of messages. Say \"erase\" to erase all your messages. ***"))

                            # "erase" erases all messages.
                            elif command == "erase":
                                clear_messages(message["sender"])
                                vsend(privmsg(message["sender"], "*** Your messages have been erased. ***"))

                            # If the command was in user_commands but didn't meet
                            # one of these criteria, it was definitely an error.
                            else:
                                user_error = True

                            if user_error:
                                vsend(privmsg(message["sender"], "There was an error with your request. Please try again or say \"help\" for assistance."))

        except Exception, e:
            print "-----\nERROR in the receiving thread:"
            print e

    return


def main():
    global ENABLE_IRC_COMMANDS

    log_append("====== [%s] %s online. ======" % (timestamp(), HANDLE))

    try:
        ip = socket.gethostbyname(SERVER)
        s = socket.socket()
        s.connect((ip, PORT))

        print "CONNECTED TO %s" % SERVER

        t = threading.Thread(target=listen, args=(s,))
        t.start()

        # Stuff to do after connecting...
        startup_commands = ["NICK %s" % HANDLE,
                            "USER %(handle)s 8 * : %(handle)s" % {"handle": HANDLE}, ]        

        # This is just junk to help with making sure I am registered, which I
        # have broken somehow. Hopefully this can be removed eventually.
        #startup_commands.append("PRIVMSG NickServ HELP")

        if HANDLE_PASSWORD != "":
            startup_commands.append("PRIVMSG NickServ identify %s" % HANDLE_PASSWORD)

        for room in ROOMS:
            startup_commands.append("JOIN %s" % room)

        startup_commands.append("PRIVMSG %s :%s online." % (MASTER_NICK, HANDLE))

        for cmd in startup_commands:
            sendLock.acquire()
            print cmd
            s.send(cmd + "\r\n")
            sendLock.release()

            time.sleep(STARTUP_DELAY)

        # Wait for user input on the console
        while True:
            user_in = raw_input("")

            # User defined commands
            if user_in == "!ENABLE":
                ENABLE_IRC_COMMANDS = True
                print "<<< IRC commands have been ENABLED. >>>"
            elif user_in == "!DISABLE":
                ENABLE_IRC_COMMANDS = False
                print "<<< IRC commands have been DISABLED. >>>"

            # Commands that should be passed on to the server.
            else:    
                s.send(user_in + "\r\n")

                # Handle manually entered QUIT command
                if user_in[0:4].upper() == "QUIT":
                    really_quit()

    except Exception, e:
        print "-----\nERROR in the main function:"
        print e
    finally:
        try:
            s.send("QUIT")
        except:
            pass
        s.close()

        exit()


if __name__ == "__main__":
    main()
