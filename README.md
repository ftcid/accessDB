# accessDB
This program is intended to connect to a bank account from the deutsche bank (GE version in english language) via
HTTPS protocol and via web scrapping technique by using Selenium, retrieve the account balance and send back per 
email through the redmail module.

This will serve as an example on how to alert for a condition to occur, as for instance, to inform about a limit
saldo. The example could be modified to permit a certain action to occur when the condition is fulfilled.

Data of the bank account, email and conditions to be satisfied are stored in a configuration file (bankcredentials.ini)
and read through the module ConfigParser.
