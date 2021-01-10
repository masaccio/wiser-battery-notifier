import argparse
import configparser
import smtplib
import ssl
import sys
import time

from wiserHeatingAPI import wiserHub

def get_battery_data(device):
    battery_voltage = device.get('BatteryVoltage')
    if battery_voltage is not None:
        battery_voltage = battery_voltage / 10
    else:
        battery_voltage = 0
    battery_level = device.get('BatteryLevel')
    if battery_level is None:
        battery_level = 'Unknown'
    return battery_voltage, battery_level

def get_low_battery_devices_for_hub(wiser_hub, low_battery_devices, verbose=False):
    for room in wiser_hub.getRooms():
        room_stat_id = room.get('RoomStatId')
        if verbose:
            room_name = room.get('Name')
            print(f"Room '{room_name}'")
        if room_stat_id:
            room_stat = wiser_hub.getDevice(room_stat_id)
            serial_number = room_stat.get('SerialNumber')
            battery_voltage, battery_level = get_battery_data(room_stat)
            if verbose:
                print(f'    Thermostat S/N={serial_number}, battery={battery_level}, voltage={battery_voltage}')
            if battery_level == 'Critical' or battery_level == 'Unknown':
                low_battery_devices.append({'room'   : room.get('Name'),
                                            'type'   : 'thermostat',
                                            'device' : serial_number,
                                            'status' : battery_level})

        trv_ids = room.get('SmartValveIds')
        if trv_ids is not None:
            for trv_id in trv_ids:
                trv = wiser_hub.getDevice(trv_id)
                battery_voltage, battery_level = get_battery_data(trv)
                serial_number = trv.get('SerialNumber')
                if verbose:
                    print(f'    TRV S/N={serial_number}, battery={battery_level}, voltage={battery_voltage}')
                if battery_level == 'Critical' or battery_level == 'Unknown':
                    low_battery_devices.append({'room'   : room.get('Name'),
                                                'type'   : 'TRV',
                                                'device' : serial_number,
                                                'status' : battery_level})


def get_low_battery_devices(config, verbose=False):
    low_battery_devices = []
    for section in config.sections():
        wiserip = config[section].get('wiserhubip')
        wiserkey = config[section].get('wiserkey')
        if wiserip is None or wiserkey is None:
            continue

        try:
            if verbose:
                print(f"Connecting to Wiser Hub '{section}' at {wiserip}")
            wiser_hub = wiserHub.wiserHub(wiserip, wiserkey)
        except:
            print('Unable to connect to Wiser Hub',  sys.exc_info()[1])
            print(f'Wiser Hub IP={wiserip}, WiserKey={wiserkey}')
        else:
            get_low_battery_devices_for_hub(wiser_hub, low_battery_devices, verbose)

    return low_battery_devices

def send_email(server, username, password, email, subject, message):
    port = 465
    message = (f'From: Wiser Notifier <{email}>\n'
               f'To: <{email}>\n'
               f'Subject: {subject}\n\n' + message)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(server, port, context=context) as server:
        server.login(username, password)
        server.sendmail(email, email, message)

parser = argparse.ArgumentParser()
parser.add_argument('--params', default='wiser.params',
                    help='Parameter file (default: wiser.params)')
parser.add_argument('--verbose', action='store_true')

args = parser.parse_args()

config = configparser.ConfigParser(interpolation=None)
config.read(args.params)

if args.verbose:
    verbose=True
else:
    verbose=False

low_battery_list = get_low_battery_devices(config, verbose)
if len(low_battery_list) > 0:
    if args.verbose:
        print('Sending email to', config['smtp']['email'])
    message = 'The following Wiser devices have critical batteries or are disconnected from the hub:\n\n'
    for low_battery in low_battery_list:
        room_name = low_battery['room']
        device_type = low_battery['type']
        device_id = low_battery['device']
        status = low_battery['status']
        message += f"    * {room_name}: {device_type} '{device_id}' battery status '{status}'\n"

    send_email(config['smtp']['server'], config['smtp']['username'],
               config['smtp']['password'], config['smtp']['email'],
               'Low battery warning for Wiser heating', message)
