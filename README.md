# etr - Endre's Time/Task Recorder

This is my aim to create a hacker friendly time keeping system that haves heavy use of dmenu(1) and libnotify. It needs an SQL server or sqlite to store its data.

# TODO

Currently the main logic is located in the processmail.py which processes mails fed from mutt and makes created partners, contacts, tasks and the like in the DB. This is unfortunate in the sense of code reuse. In the next step it is highly desired to move out all the reusable code into utils.py or so.

