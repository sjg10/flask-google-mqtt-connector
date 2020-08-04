from flask import render_template, redirect, flash
from wtforms.form import Form
from wtforms.fields import *
from wtforms_alchemy import ModelForm
from .models import db, Device, DBArray

class DeviceForm(ModelForm):
    class Meta:
        model = Device

class DevicesForm(Form):
    devices = FieldList(FormField(DeviceForm))

def admin_post(request):
    pass

class MultiDict(dict):
    def getlist(self, key):
        return [self[key]]

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
            form.populate_obj(device)
            if form.validate(): 
                for key, value in form.data.items():
                    setattr(device, key, value)
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
        md = member.__dict__
        # Convert arrays to newline arrays
        for col, content in md.items():
            if isinstance(Device.get_col_type(col), DBArray):
                md[col] = "\n".join(content)
        device = DeviceForm(MultiDict(md))
        device.id = member.id
        devicesform.append(device)
    emptyRow = DeviceForm()
    emptyRow.id = "NEW"
    devicesform.append(emptyRow)

    return render_template('admin.html', devicesform = devicesform, columnnames=columns)
