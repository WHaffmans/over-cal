import requests
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vCalAddress, vText
import pytz




rest = 'https://abc.over.nu/over/data/rest.php/'
sessionurl = rest + 'Session'
calurl = rest + 'ContactAgenda'

username = input('username:')
password = input('password:')

payload = {"username": username, "password": password}
session = requests.post(sessionurl, data=json.dumps(payload))
userid = '1200'
calres = requests.get(calurl, cookies=session.cookies, params={'id':userid}).json()
appointments = calres['appointment']['item']
dates = calres['appointment']['date']

appurl= rest + 'ResPersonAppointment'
app_details = dict()
for id,item in appointments.items():
    app_detail = requests.get(appurl, cookies=session.cookies, params={'id':id}).json()['item']
    app_details[id] = app_detail
worktypes = ['','Afspraak:','Bijles:','Begeleiding']

from_date = datetime.now()
till_date = from_date + timedelta(weeks=1)

cal = Calendar()
cal.add('prodid', 'OVER Rooster')
cal.add('version','2.0')


for date, ids in sorted(dates.items()):
    date = datetime.strptime(date,'%Y-%m-%d')
    if len(ids) > 0 and date>from_date and date<till_date:
        datestr = date.strftime('%Y-%m-%d')
        for id in ids:
            event = Event()
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

            event.add('summary', f'{worktype} {desc}')
            event.add('dtstamp', from_date)
            event.add('dtstart', startdate)
            event.add('dtend', enddate)
            #event.add('dtstamp', datetime(2005,4,4,0,10,0,tzinfo=pytz.utc))

            print(start + ' - ' + end,worktype,', '.join(people), desc)
            cal.add_component(event)

f = open('rooster.ics','wb')
f.write(cal.to_ical())
f.close()