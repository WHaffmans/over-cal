import requests
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vCalAddress, vText
import pytz

def main():
    rest = 'https://abc.over.nu/over/data/rest.php/'
    sessionurl = rest + 'Session'
    calurl = rest + 'ContactAgenda'
    appurl= rest + 'ResPersonAppointment'

    try:
        with open('config.json','r') as fh:
            config = json.load(fh)
            username = config['username']
            password = config['password']
            weeks = config['weeks']
    except FileNotFoundError:
        username = input('username:')
        password = input('password:')
        weeks = int(input('Hoeveel weken wil je downloaden?'))
        config = {'username': username,'password': password, 'weeks': weeks}
        with open('config.json', 'w') as fh:
            json.dump(config,fh)
    

    payload = {"username": username, "password": password}
    session = requests.post(sessionurl, data=json.dumps(payload))
    userid = requests.get(sessionurl, cookies=session.cookies).json()['id']
    calres = requests.get(calurl, cookies=session.cookies, params={'id':userid}).json()

    appointments = calres['appointment']['item']
    dates = calres['appointment']['date']
    app_details = dict()
    for id,item in appointments.items():
        app_detail = requests.get(appurl, cookies=session.cookies, params={'id':id}).json()['item']
        app_details[id] = app_detail
    worktypes = ['','Afspraak:','Bijles:','Begeleiding']

    from_date = datetime.now()
    till_date = from_date + timedelta(weeks=weeks)

    cal = Calendar()
    cal.add('prodid', 'OVER Rooster')
    cal.add('version','2.0')


    for date, ids in sorted(dates.items()):
        date = datetime.strptime(date,'%Y-%m-%d')
        if len(ids) > 0 and date>from_date and date<till_date:
            datestr = date.strftime('%Y-%m-%d')
            for id in ids:
                start = app_details[id]['starton_time']
                startdate = datetime.strptime(datestr +' '+start, '%Y-%m-%d %H:%M')
                end = app_details[id]['endon_time']
                enddate = datetime.strptime(datestr +' '+end, '%Y-%m-%d %H:%M')

                desc = app_details[id]['description']
                worktype = worktypes[int(app_details[id]['typeid'])]
                people = []
                for person in app_details[id]['person']:
                    if person['id'] not in [userid, '1765']:
                        people.append(person['text'])
                
                event = Event()

                event.add('summary', f'{worktype} {desc}')
                event.add('dtstamp', from_date)
                event.add('dtstart', startdate)
                event.add('dtend', enddate)
                event.add('dtstamp', datetime.now())

                cal.add_component(event)
    write_ics(cal,from_date, username)

def write_ics(cal, from_date, username):
    f = open(f'{from_date.strftime("%Y-%m-%d")}_Rooster_{username}.ics','wb')
    f.write(cal.to_ical())
    f.close()

if __name__ == "__main__":
    main()