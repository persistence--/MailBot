# MailBot v0.26

by: **persistence**

An IRC bot used to send messages to one or more users who are offline. 


## Features:

* **Group Messaging** - Send messages to user-defined groups of nicks.

* **White/Blacklists** - Use whitelists and blacklists to enable or disable messaging from specific users.

* **URL Logging** - Log all URL's sent to rooms the bot is in so I don't miss any cool stuff shared while I'm gone.

* **Mention logging for the owner** - Log each time the owner's name is mentioned so they will know if someone was looking for them but did not leave a message.

* **Registered User Identification** - Users must register their nick with NickServ in order to use MailBot. Identity is checked on every command received.

## Advantages over memoserv:

* More obvious interface for new users unfamiliar with IRC.

* Depending on settings, nicks do not need to be registered/identified to send and receive messages. (Could be a good or a bad thing depending on your perspective.)

* Can be run by a non-operator or non-server-admin user independently of the underlying IRC server.

* Non-messaging features like mention logging and URL logging.

## Features to add:

* **Error logging** - Need a function for displaying output instead of print so that all server messages will be logged as they are displayed. Also need to move the interesting log to a different file than the error log.

* **NickServ/WHOIS verification** - Verify user identities (if that user is registered) before allowing them to send/receive messages.

* **User limits** - There needs to be a limit to how fast a user can send messages to another user.

* **Mention Logging** - Log every time the nick of a registered user is mentioned in a room so they will know if someone was looking for them, but maybe has not left me a message with MailBot.

* **Improve nick black/whitelisting** - Black/whitelist needs to be updatable with an admin command and saved to disk.

* **Password protection** - Give users the ability to protect their messages with a password instead of authenticating by nickname only.

* **Improve configuration file** - Right now it's just an imported .py file containing a dictionary, but at least it's better than the old way.


## Known bugs:

* Errors about 'data' following JOINs. 

* **Immediate** notification is still case sensitive. It needs to be fixed so if a username's case has changed and that user is in MailBot's room, the user will still get a notification. Notification on JOIN is still working properly.

* The data-receiving thread needs to be givng it's own function that reads data and then spits it back out to other data-handling threads. This will keep the bot from getting bogged down with requests from just one user.


## Ways the code needs to be cleaned up:

Basic stuff.

* Vocabulary for messages (received from the server) and messages (mail between users) has become muddled. There should be more differentiation between the two before this gets out of hand.

* Split up the program into more functions.

* Split functions across multiple files.


## Old bugs fixed in this version:

* All threads and main process now exit cleanly on quits and !QUITs.

* Timestamps now force two digit minimum for all fields.

* Data needs to break at \n's because I occasionally read in two lines at once when there is excessive data.

* Nicks need to be case-sensitive when sent to the server, but for message storage, make them all lower-case.