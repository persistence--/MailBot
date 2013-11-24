MailBot v0.21
=============
by: **persistence**

An IRC bot used to send messages to one or more users who are offline. 

Features:
---------
* **Group Messaging** - Send messages to user-defined groups of nicks.

* **White/Blacklists** - Use whitelists and blacklists to enable or disable messaging from specific users.


Features to add:
----------------
* **User limits** - There needs to be a limit to how fast a user can send messages to another user.

* **Configuration file** - Configuration needs to be saved in a separate file so I don't accidentally upload my IRC credentials to github. :P

* **URL Logging** - Log all URL's sent to rooms the bot is in so I don't miss any cool stuff while I'm gone.

* **Mention Logging** - Log every time my nick (or the nick of a registered user) is mentioned in a room so I will know if someone was looking for me, but maybe has not left me a message with MailBot.

* **Improve nick black/whitelisting** - Black/whitelist needs to be updatable with an admin command and saved to disk.

* **Password protection** - Give users the ability to protect their messages with a password instead of authenticating by nickname only.


Known bugs:
-----------
* Instant notification is still case sensitive. It needs to be fixed so if a username's case has changed and that user is in MailBot's room, the user will still get a notification.


Old bugs fixed in this version:
-------------------------------
* Data needs to break at \n's because I occasionally read in two lines at once when there is excessive data.

* Nicks need to be case-sensitive when sent to the server, but for message storage, make them all lower-case.