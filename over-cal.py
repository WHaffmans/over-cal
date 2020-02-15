import requests
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vText


def main():
    rest_url = 'https://abc.over.nu/over/data/rest.php/'
    url = {
        'session':      rest_url + 'Session',
        'calendar':     rest_url + 'ContactAgenda',
        'appointment':  rest_url + 'ResPersonAppointment',
        'contact':      rest_url + 'ResContactHeader'
    }
    config = getConfig()
    from_date = datetime.now()
    till_date = from_date + timedelta(weeks=config['weeks'])

    userid, session = login(config, url)

    appointments = requests.get(
        url['calendar'],
        cookies=session,
        params={'id': userid}
        ).json()['appointment']

    app_details = dict()
    locations = dict()
    for id, item in appointments['item'].items():
        app_detail = requests.get(
            url['appointment'],
            cookies=session,
            params={'id': id}
            ).json()
        app_details[id] = app_detail['item']
        if len(locations) == 0:
            for location in app_detail['location']:
                locations[location['id']] = location['fullname']
    worktypes = ['', 'Afspraak:', 'Bijles:', 'Begeleiding']

    calendar = Calendar()
    calendar.add('prodid', '-//OVER Rooster//NOSGML//NL')
    calendar.add('version', '2.0')
    contacts = dict()

    for date, ids in sorted(appointments['date'].items()):
        date = datetime.strptime(date, '%Y-%m-%d')
        if len(ids) > 0 and date > from_date and date < till_date:
            datestr = date.strftime('%Y-%m-%d')
            for id in ids:
                start = app_details[id]['starton_time']
                startdate = datetime.strptime(
                    datestr + start, '%Y-%m-%d%H:%M'
                    )
                end = app_details[id]['endon_time']
                enddate = datetime.strptime(
                    datestr + end, '%Y-%m-%d%H:%M'
                    )
                people = ''
                for person in app_details[id]['person']:
                    if person['id'] not in [userid, '1765']:
                        if person['id'] not in contacts:
                            contact = requests.get(
                                url['contact'],
                                cookies=session,
                                params={'contactid': person['id']}
                                ).json()['contact']
                            contacts[person['id']] = contact
                        else:
                            contact = contacts[person['id']]
                        people += f"{contact['fullname']}, "
                        people += f"{contact['mobile']}, "
                        people += f"{contact['email']}\n"

                summary = (
                    worktypes[int(app_details[id]['typeid'])]
                    + ' '
                    + app_details[id]['description']
                    )

                event = Event()
                event.add('uid', f"{id}{startdate.strftime('%Y%m%d')}")
                event.add('summary', summary)
                event.add('dtstamp', from_date)
                event.add('dtstart', startdate)
                event.add('dtend', enddate)
                event.add('description', vText(people))
                event.add('location', locations[app_details[id]['locationid']])
                calendar.add_component(event)

    write_ics(calendar, from_date, config['username'])


def getConfig():
    try:
        with open('config.json', 'r') as fh:
            config = json.load(fh)

    except FileNotFoundError:
        config = {
            'username': input('username:'),
            'password': input('password:'),
            'weeks': int(input('Hoeveel weken wil je downloaden?'))
            }

        with open('config.json', 'w') as fh:
            json.dump(config, fh)

    return config


def write_ics(cal, from_date, username):
    f = open('rooster.ics', 'wb')
    f.write(cal.to_ical())
    f.close()


def login(config, url):
    login_data = {
        "username": config['username'],
        "password": config['password']
        }
    session = requests.post(url['session'], data=json.dumps(login_data))
    userid = requests.get(url['session'], cookies=session.cookies).json()['id']
    return userid, session.cookies


if __name__ == "__main__":
    main()
