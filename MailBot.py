#!/usr/bin/env python

##############################################################################
##  MailBot  ##  created by: persistence                                    ##
##############################################################################

import threading    # For the listening thread.
import time         # For delays between commands on connect.
import sys          # For sys.exit().

from lib.data_manipulation import *
from lib.irc import *
from lib.timestamp import *

# Import user settings by creating global variables from all the keys in the
# settings dictionary from MailBot_settings.py
from MailBot_settings import settings

# Global variables that should not be changed by the user. (Not settings.)
ENABLE_IRC_COMMANDS = True
_verified_nicks = {}

# Loads the settings imported from the settings file.
def load_settings(settings):
    for variable in settings.keys():
        value = settings[variable]

        if type(value) == type("string"):
            value = '"%s"' % value
        
        set_value = "global %s ; %s = %s" % (variable, variable, value)

        exec set_value


# Kills all threads
def kill_all_threads():
    # Terminate running threads
    for thread in threading.enumerate():
        if thread.isAlive():
            try:
                thread._Thread__stop()
            except:
                print(str(thread.getName()) + ' could not be terminated')
         

# Logs messages that are sent directly to the bot (as opposed to
# the room/channel) to a file. I did this to examine hack attempts.
def log_append(message):
    log_filename = sys.argv[0] + ".txt"
    log_file = open(log_filename, 'a')
    log_file.write(message + "\n")
    log_file.close()


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

# Handle received PRIVMSG's
def privmsg_actions(s, message):
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
            s.vsend(privmsg(message["room"], reply))


    # Testing user verification with PM's
    if message["recipient"] == HANDLE:
        s.vsend("WHOIS %s" % message["sender"])

        time.sleep(5)

        registered_nick = _verified_nicks.get(message["sender"])
        if registered_nick != None:
            s.vsend(privmsg(message["sender"], "I see you are logged in as %s" %\
                                               registered_nick))
        else:
            s.vsend(privmsg(message["sender"], "You are not logged in with this nick."))

    # Responses to private messages sent to the bot.
    if message["recipient"] == HANDLE:

        user_commands = lower(["help", "tell", "read", "erase"])

        # Administrative commands
        if (message["sender"].lower() == MASTER_NICK.lower() and
            command[0] == "!"):

            # !quit : QUIT
            if command == "!quit":
                global AUTO_RECONNECT
                AUTO_RECONNECT = False
                
                s.send("QUIT\r\n")
                kill_all_threads()

            # !break : What happens if I break this?
            if command == "!break":
                s.close()


            # !interesting : Print the last 20 interesting things.
            if command == "!interesting":
                things = file2list(sys.argv[0] + ".txt")

                parameter_list = parameters.split(" ")

                # First parameter is the number of things to see.
                if parameters.split(" ")[0].isdigit():
                    number_of_things = int(parameters.split(" ")[0])
                else:
                    number_of_things = 20

                if len(things) > number_of_things:
                    things = things[(0 - number_of_things):]

                # Second parameter is the delay between messages.
                new_delay = DELAY

                if len(parameter_list) > 1:
                    if isfloat(parameter_list[1]):
                        new_delay = float(parameter_list[1])
                    

                # Display the interesting things.
                s.vsend(privmsg(message["sender"], "*** Displaying %s interesting lines. Delay between each = %s seconds. ***" % ( len(things), new_delay ) ) )

                for thing in things:
                    s.vsend(privmsg(message["sender"], thing))
                    time.sleep(new_delay)

            return False

        # Respond to unrecognized commands.
        if command.lower() not in user_commands:
            reply = "Hello there, %s. Type \"help\" if you need instructions." % message["sender"]
            s.vsend(privmsg(message["sender"], reply))

        # Valid commands go here.
        else:
            user_error = False

            # "help" displays help.
            if command == "help":
                help_text = """Available commands:
                               %(commands)s
                               Send a user a message: tell username such and such message
                               Send a group of users a message: tell @groupname such and such message
                               Read your messages: read
                               Erase all your messages: erase
                               ---
                               Currently available groups are: %(groups)s
                               ---
                               Be aware that the owner of this bot (like the owner of this server) can read all the messages you send, so please do not send anything private or sensitive.
                               ---
                               %(handle)s is run by me, %(master_nick)s. Please let me know if you want to be removed from %(handle)s's alerts or group messages. You can even use %(handle)s to contact me!
                               ---
                               Do not use this bot to spam other users or you will be added to the blacklist.""" % {
                               "commands": user_commands, 
                               "groups": NICK_GROUPS.keys(),
                               "handle": HANDLE,
                               "master_nick": MASTER_NICK,
                               }

                for line in help_text.split("\n"):
                    if line.strip() != "":
                        s.vsend(privmsg(message["sender"], line.strip()))
                        time.sleep(DELAY)

            # "tell" sends messages.
            elif command == "tell" and len(parameters.split(" ")) > 1:
                message_recipient = parameters.split(" ")[0]
                message_to_send = parameters[len(message_recipient)+1:]

                # Send a message to a group of users.
                if message_recipient[0] == "@":
                    recipients = NICK_GROUPS.get(message_recipient[1:])
                    if recipients == None:
                        s.vsend(privmsg(message["sender"], "That is an invalid group name."))
                        return False
                # Send a message to just one user.
                else:
                    recipients = [ message_recipient, ]

                # Send the messages.
                for recipient in recipients:
                    record_message(message["sender"], recipient, message_to_send)

                    time.sleep(DELAY)

                # Notify the recipients that they have messages waiting.
                for recipient in recipients:                                    
                    s.vsend(privmsg(recipient, "You have a new message from %s. Say \"read\" to read your messages." % message["sender"]))
                
                    time.sleep(DELAY)

                # Notify that the messages have been sent.    
                s.vsend(privmsg(message["sender"], "Your message to %s has been sent!" % recipients))

                    

            # "read" displays stored messages.
            elif command == "read":
                user_messages = read_messages(message["sender"])
                message_count = len(user_messages)

                for m in user_messages:
                    s.vsend(privmsg(message["sender"], m))
                    time.sleep(DELAY)

                if message_count > 0:
                    s.vsend(privmsg(message["sender"], "*** End of messages. Say \"erase\" to erase all your messages. ***"))

            # "erase" erases all messages.
            elif command == "erase":
                clear_messages(message["sender"])
                s.vsend(privmsg(message["sender"], "*** Your messages have been erased. ***"))

            # If the command was in user_commands but didn't meet
            # one of these criteria, it was definitely an error.
            else:
                user_error = True

            if user_error:
                s.vsend(privmsg(message["sender"], "There was an error with your request. Please try again or say \"help\" for assistance."))

        # Respond to anything with message count if the user has
        # messages waiting. Anything except "erase" or "tell".
        message_count = len(read_messages(message["sender"]))
        if command not in user_commands or command == "read":
            s.vsend(privmsg(message["sender"], "*** You have %d messages. ***" % message_count))
            time.sleep(DELAY)

# Decide what to do with data that is received from the server.
def process_incoming_data(s, message):
    try:


            # The bot should never respond to a message it sends.
            if message.get("sender") == HANDLE: return


            # Respond to server PING's
            if message["type"] == "PING":
                s.vsend("PONG :%s" % message["data"])
                return    # PING's need no further processing.

            # Log interesting messages regardless of sender/recipient.
            if message["type"] == "PRIVMSG":
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
                    ( ".uk" in message["data"].lower() ),
                    ( ".au" in message["data"].lower() ),
                    ( ".nz" in message["data"].lower() ),
                    ( MASTER_NICK.lower() in message["data"].lower() ),
                ]

            if ( message["type"] == "PRIVMSG" 
                 and message["sender"] != MASTER_NICK.lower()
                 and message["sender"] != HANDLE ):

                if (any(interesting_things)):
                    log_entry = "[%(timestamp)s] %(sender)s->%(recipient)s: %(message)s" % {
                        "timestamp": timestamp(),
                        "sender": message["sender"],
                        "recipient": message["recipient"],
                        "message": message["data"],
                    }

                    log_append(log_entry)

            # Keep track of users who are logged in for ID verification.
            if message["type"] == "330":
                global _verified_nicks
                _verified_nicks[message["registered_nick"]] = \
                    message["current_nick"]
                print "VERIFIED USERS: %s" % _verified_nicks

            # Since the white/blacklists are located below, messages from
            # the server will cause errors if I don't filter them out.
            if message["type"] != "JOIN" and message["type"] != "PRIVMSG":
                return

            # Everything below here is available to whitelisted/
            # non-blacklisted users only.
            if not user_allowed(message["sender"]): return


            # Responses to users JOINing the current room.
            if message["type"] == "JOIN":

                # Greet all users who enter the room.
                if GREET_JOINS:
                    s.vsend(privmsg(message["recipient"], "Hello, %s." % message["sender"]))

                # Notify the user if they have any new messages.
                message_count = len(read_messages(message["sender"]))

                if message_count > 0:
                    s.vsend(privmsg(message["sender"], "*** You have %d messages. Type \"read\" to retrieve. ***" % message_count))


            # Responses to PRIVMSGs to rooms or to the bot
            if message["type"] == "PRIVMSG":
                if not privmsg_actions(s, message): return

    except Exception, e:
        error_message = "-----\nERROR in the receiving thread:\n%s" % e
        print error_message
        log_append(error_message)
        #if e.errno == 107:







# Listens for incoming data and automatically responds where appropriate.
def listen(s):
    global ENABLE_IRC_COMMANDS
    messages = {}   # This is just a place to store messages until I put in 
                    # a database. It will be replaced eventually.

    # Keeps track of how many times the same user was kicked.
    kick_counter = {}

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
                if message: 
                    process_incoming_data(s, message)
        except:
            pass
    return

# Listens for commands from the terminal and passes them on to the IRC server.
def terminal_input(s):
    # Wait for user input on the console
    while True:
        user_in = raw_input("")

        # Execute python code preceded with >
        if user_in[0] == ">":
            exec(user_in[1:])

        # User defined commands
        elif user_in == "!ENABLE":
            ENABLE_IRC_COMMANDS = True
            print "<<< IRC commands have been ENABLED. >>>"
        elif user_in == "!DISABLE":
            ENABLE_IRC_COMMANDS = False
            print "<<< IRC commands have been DISABLED. >>>"

        # Commands that should be passed on to the server.
        else:    
            # Handle manually entered QUIT command
            if user_in[0:4].upper() == "QUIT":
                global AUTO_RECONNECT
                AUTO_RECONNECT = False

                s.vsend("QUIT")
                kill_all_threads()
            else:                
                s.send(user_in + "\r\n")





def main():
    load_settings(settings)
    global ENABLE_IRC_COMMANDS

    # Infinite loop that will be broken if AUTO_RECONNECT is not True.
    while True:

        log_append("====== [%s] %s online. ======" % (timestamp(), HANDLE))

        try:
            ip = socket.gethostbyname(SERVER)
            s = IrcSocket() #socket.socket()
            s.settimeout(1)
            s.connect((ip, PORT))

            print "CONNECTED TO %s" % SERVER

            listening_thread = threading.Thread(target=listen, args=(s,))
            listening_thread.start()

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
                s.vsend(cmd)
                time.sleep(STARTUP_DELAY)

            terminal_input_thread = threading.Thread(target=terminal_input, 
                                                     args=(s,))
            terminal_input_thread.start()

            # Check that all threads are still running ok.
            while True:
                if not (listening_thread.isAlive() and 
                        terminal_input_thread.isAlive()):
                    kill_all_threads()
                    break
                time.sleep(1)

        except Exception, e:
            error_message = "-----\nERROR in the main function:\n%s" % e
            log_append(error_message)
        finally:
            try:
                s.vsend("QUIT")
            except:
                pass
            s.close()

        # Auto-reconnect to the server unless this quit was intentional.
        if not AUTO_RECONNECT:
            sys.exit()
        else:
            error_message = \
                "\n\n[%s] Disconnected. Reconnecting in %s seconds...\n" % \
                (timestamp(), AUTO_RECONNECT_DELAY)
            log_append(error_message)
            time.sleep(AUTO_RECONNECT_DELAY)


if __name__ == "__main__":
    main()
