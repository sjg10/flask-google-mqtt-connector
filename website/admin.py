from flask import render_template, redirect, flash
from wtforms.form import Form
from wtforms.fields import *
from wtforms import validators as v
from .models import db, Device, DeviceType


class Unique():
    """ validator that checks field uniqueness """
    def __init__(self, model, message='this element already exists'):
        self.model = model
        self.message = message
    def __call__(self, form, field):
        if field.object_data == field.data: # When loading default data, pass an OK!
            return
        check = self.model.query.filter(getattr(self.model, field.short_name) == field.data).first()
        if check:
            raise v.ValidationError("Inputted", field.data, self.message)

class DeviceForm(Form):
    id = StringField('id', [v.DataRequired(), v.Length(max=50), Unique(Device)])
    name = StringField('name', [v.DataRequired(), v.Length(max=50), Unique(Device)])
    nicknames = TextAreaField('nicknames', [v.Length(max=200)])
    roomHint = StringField('roomHint', [v.DataRequired(), v.Length(max=50)])
    device_type = SelectField("device_type")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_type.choices = [(x.classname, x.classname) for x in DeviceType.query.all()] 

class DevicesForm(Form):
    devices = FieldList(FormField(DeviceForm))

def commit(request):
    idd = request.form["commitbtn"].split("Commit ")[-1]
    print("com", idd, flush=True)
    if idd == "NEW":
        form = DeviceForm(request.form)
        if form.validate():
            device=Device(**form.data)
            db.session.add(device)
            db.session.commit()
            return None
        else:
            return str(form.errors)
    else:
        device = Device.query.get(idd)
        if device is None:
            return "Device " + str(idd) +" to be updated not found"
        else:
            form = DeviceForm(request.form, obj=device)
            if form.validate(): 
                device.update(form.data)
                db.session.commit()
                return None
            else:
                return str(form.errors)


def delete(request):
    idd = request.form["deletebtn"].split("Delete ")[-1]
    print("del", idd, flush=True)
    if idd=="NEW":
        return "Cannot delete empty row"
    else:
        device = Device.query.get(idd)
        if device is None:
            return "Device " + str(idd) +" to be deleted not found"
        else:
            db.session.delete(device)
            db.session.commit()
            return None

def admin_render(request):
    devicesform = []
    columns = [m.key for m in Device.__table__.columns]
    if request.method == 'POST':
        if "commitbtn" in request.form:
            resp = commit(request)
        elif "deletebtn" in request.form:
            resp = delete(request)
        else:
            resp = "Unknown button pressed"
        if resp:
            flash(resp)
        else:
            return redirect('/admin')
    for member in db.session.query(Device):
        device = DeviceForm(obj=member)
        device.keyid = member.keyid
        devicesform.append(device)
    emptyRow = DeviceForm(obj=Device())
    emptyRow.keyid = "NEW"
    devicesform.append(emptyRow)

    return render_template('admin.html', devicesform = devicesform, columnnames=columns)
