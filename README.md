# Dustbunny

* **Author:** Jefferson Heard 
* **Version:** 0.0.1

## Introduction

Dustbunny creates random records for SQL databases. It's based on [Hypothesis](http://hypothesis.works/) and uses it to 
generate random values for data columns. The difference between using Dustbunny vs. Hypothesis directly is that it's 
easier to generate values that are relative to an already generated value, and it's easier to manage relationships 
between tables, such as foreign key relationships. 

Dustbunny also records the primary keys of the records it generates, so you can remove them from the database when you 
are done with them.

## Example:

The following generates a random set of appointments with start times distributed throughout the day, and with amounts 
of time distributed between even increments of fifteen minutes, across a predetermined sample of attendees (defined 
elsewhere), and across a predetermined sample of dates.  It builds 50 records using the model's controller class 
attribute to create the record. It exercises the facility for generating fixed values, random values from strategies,
 and relative values based on the previous two:

```python
from app.extensions import db
import importlib
from hypothesis import strategies as st, settings, given
from dustbunny.hyp.strategies import *
from dustbunny import Generate
from dustbunny.hyp.strategies import gfywords, gfycodes, words

import_upon_configure(db.Model, here)

# ...
# initialize the database ...
# ...

use_controller = lambda M, **kwargs: M.controller_class.create(_commit=False, **kwargs)

# ... do stuff ,,,

# Grab some initial records we're goin gto use in our fixed values
org = Org.query.first()
appointment_type = AppointmentType.query.first()

gen = Generate(db, Appointment)\
    .by_method(use_controller)\  # this is called instead of create
    .num(50)\   # generate 50 records
    .with_fixed_values_for(  # use fixed values for the following record attributes
        calendar_sync_google=False,  
        is_private=False,
        is_all_day=False,
        enable_notifications=False,
        organization=org,
        appointment_type_id=appointment_type.pk,
    ).using(  # use hypothesis strategies for generating the following attributes
        appointment_registration_type_id=st.sampled_from([x.pk for x in AppointmentRegistrationType.query.all()]),
        title=gfywords(),  # a dustbunny strategy for generating adj-adj-noun triplets that are unique
        location=gfywords(),
        appt_date=st.sampled_from(date_range),
        notes=words(),  # generate random words
        wage_minutes=st.sampled_from((15, 30, 45, 60, 90)),
        wage_code_id=st.sampled_from([x.pk for x in WageCode.query.all()]),
        members = st.lists(st.sampled_from(workers), average_size=5, min_size=1, max_size=25)
    ).with_relative_values_for(
        start_hour=lambda **k: k['appt_date'].hour,
        end_hour=lambda **k: (k['appt_date'] + timedelta(minutes=k['wage_minutes'])).hour,
        start_minute=lambda **k: k['appt_date'].minute,
        end_minute=lambda **k: (k['appt_date'] + timedelta(minutes=k['wage_minutes'])).minute,
        wage_start_hour=lambda **k: k['appt_date'].hour,
        wage_end_hour=lambda **k: (k['appt_date'] + timedelta(minutes=k['wage_minutes'])).hour,
        wage_start_minute=lambda **k: k['appt_date'].minute,
        wage_end_minute=lambda **k: (k['appt_date'] + timedelta(minutes=k['wage_minutes'])).minute,
        is_mandatory=lambda **k: k['wage_minutes'] > 0,
        start_date=lambda **k: k['appt_date'],
        end_date=lambda **k: k['appt_date'] + timedelta(minutes=k['wage_minutes']),
    )
    
worker_appointments.extend(gen.execute())  # actually create the records

db.session.commit()  # we don't commit during the generation because it takes forever.
```