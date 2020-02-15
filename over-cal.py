import requests
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText


def main():
    rest_base_url = 'https://abc.over.nu/over/data/rest.php/'
    session_url = rest_base_url + 'Session'
    calendar_url = rest_base_url + 'ContactAgenda'
    appointment_url = rest_base_url + 'ResPersonAppointment'
    contact_url = rest_base_url + 'ResContactHeader'

    try:
        with open('config.json', 'r') as fh:
            config = json.load(fh)
            username = config['username']
            password = config['password']
            weeks_to_download = config['weeks']
    except FileNotFoundError:
        username = input('username:')
        password = input('password:')
        weeks_to_download = int(input('Hoeveel weken wil je downloaden?'))
        config = {
            'username': username,
            'password': password,
            'weeks': weeks_to_download
            }
        with open('config.json', 'w') as fh:
            json.dump(config, fh)

    login_data = {"username": username, "password": password}
    session = requests.post(session_url, data=json.dumps(login_data))
    userid = requests.get(session_url, cookies=session.cookies).json()['id']

    calres = requests.get(
        calendar_url,
        cookies=session.cookies,
        params={'id': userid}
        ).json()

    appointments_item = calres['appointment']['item']
    appointment_dates = calres['appointment']['date']
    app_details = dict()
    locations = dict()
    for id, item in appointments_item.items():
        app_detail = requests.get(
            appointment_url,
            cookies=session.cookies,
            params={'id': id}
            ).json()
        app_details[id] = app_detail['item']
        if len(locations) == 0:
            for location in app_detail['location']:
                locations[location['id']] = location['fullname']
    worktypes = ['', 'Afspraak:', 'Bijles:', 'Begeleiding']

    from_date = datetime.now()
    till_date = from_date + timedelta(weeks=weeks_to_download)

    calendar = Calendar()
    calendar.add('prodid', '-//OVER Rooster//NOSGML//NL')
    calendar.add('version', '2.0')
    contacts = dict()

    for date, ids in sorted(appointment_dates.items()):
        date = datetime.strptime(date, '%Y-%m-%d')
        if len(ids) > 0 and date > from_date and date < till_date:
            datestr = date.strftime('%Y-%m-%d')
            for id in ids:
                start = app_details[id]['starton_time']
                startdate = datetime.strptime(
                    datestr + ' ' + start, '%Y-%m-%d %H:%M'
                    )
                end = app_details[id]['endon_time']
                enddate = datetime.strptime(
                    datestr + ' ' + end, '%Y-%m-%d %H:%M'
                    )

                desc = app_details[id]['description']
                worktype = worktypes[int(app_details[id]['typeid'])]
                people = ''

                event = Event()
                event.add('uid', f"{id}{startdate.strftime('%Y%m%d')}")
                event.add('summary', f'{worktype} {desc}')
                event.add('dtstamp', from_date)
                event.add('dtstart', startdate)
                event.add('dtend', enddate)

                for person in app_details[id]['person']:
                    if person['id'] not in [userid, '1765']:
                        if person['id'] not in contacts:
                            contact = requests.get(
                                contact_url,
                                cookies=session.cookies,
                                params={'contactid': person['id']}
                                ).json()['contact']
                            contacts[person['id']] = contact
                        else:
                            contact = contacts[person['id']]
                        people += f"{contact['fullname']}, "
                        people += f"{contact['mobile']}, "
                        people += f"{contact['email']}\n"

                event.add('description', vText(people))
                event.add('location', locations[app_details[id]['locationid']])
                calendar.add_component(event)

    write_ics(calendar, from_date, username)


def write_ics(cal, from_date, username):
    f = open(f'{from_date.strftime("%Y-%m-%d")}_Rooster_{username}.ics', 'wb')
    f.write(cal.to_ical())
    f.close()


if __name__ == "__main__":
    main()
