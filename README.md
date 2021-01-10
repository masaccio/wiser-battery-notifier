# wiser-battery-notifier

Script to check battery levels and email notifications about the Drayton Wiser Heat Hub.

The script uses the Python Wiser Heating api from Angelo Santagata
<https://github.com/asantaga/wiserheatingapi>

Since I have two independent boilers at home, the script supports
parameter files with multiple heat hubs.

## Installation

You'll need to extract your secret keys as described at
<https://github.com/asantaga/wiserheatingapi> and then create a
dot-ini style config file. If you pick the default ```wiser.params```
filename then you don't need to pass ```--params``` on the command-line.

```ini
[bedroom]
wiserkey=secret
wiserhubip=192.168.1.100

[lounge]
wiserkey=secret
wiserhubip=192.168.1.101
```

## crontab

One convenient way to run regularly is with a crontab such as:

```bash
@daily PYTHONPATH=/users/me/python/wiserheatingapi python3 /users/me/python/wiser-battery-notifier/notifier.py --params /users/me/python/wiser-battery-notifier/wiser.params
```
