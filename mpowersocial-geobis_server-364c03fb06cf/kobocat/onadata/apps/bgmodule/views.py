import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count,Q
from django.http import ( HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from django.forms.formsets import formset_factory
from django.db.models import ProtectedError
from django.db import connection
from onadata.apps.bgmodule.models import *
import json
from django.forms.models import inlineformset_factory
from collections import OrderedDict
import pandas as pd
from django.conf import settings
import os
import xlwt



'''
BLUE GOLD MODULE
'''



def index(request):
    current_user = request.user
    print "Hello!!"

    return render(request,'bgmodule/index.html')


"""
Prepare json of given query for data table
@persia
"""
def getDatatable(query):
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    col_names.append('Action')
    for eachval in fetchVal:
        #delete_button = '<a class="delete-program-item tooltips" data-placement="top" href="#" data-original-title="Delete Program"  onclick="delete_program('+ str(eachval[0]) +')"><i class="fa fa-2x fa-trash-o"></i></a>'
        delete_button = ''
        edit_button = '<a class="tooltips" data-placement="top" data-original-title="Edit Program" href="#" onclick="edit_entity('+str(eachval[0]) +');"><i class="fa fa-2x fa-pencil-square-o"></i></a>' + ' ' + delete_button
        eachval = eachval + (edit_button,)
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})


"""
Prepare Message for Ajax request message
@persia
"""
def getAjaxMessage(type, message):
    data = {}
    data['type'] = type
    data['messages'] = message
    return data



def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall()
    cursor.close()
    return fetchVal


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    return fetchVal[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]



def wmg_profile_list(request):
    query='select id as "Data ID",name_wmg  as "WMG Name", wmg_reg_num "Reg Numb",(select name from geo_zone where code=zone) as "Zone",(select name from geo_district where code=district) as "District" from vwwmg_registration'
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    col_names.append('Action')
    for eachval in fetchVal:
        view_button = '<a class="btn btn-info tooltips" data-placement="top" data-original-title="View WMG" href="/bgmodule/wmg_profile_details/'+str(eachval[0])+'/"><i class="fa fa-2x fa-th"></i> View </a>'
        eachval = eachval + (view_button,)
        data_list.append(list(eachval))
    data_list=json.dumps({'col_name': col_names, 'data': data_list})
    context={'col_name': col_names, 'datas': data_list}
    return render(request, 'bgmodule/wmg_profile_list.html',context)





def wmg_profile_details(request,wmg_id):
    query='select name_wmg as "WMG Name" ,wmg_reg_num as "Reg Numb", (select name from geo_zone where code=zone) as "Zone" ,(select name from geo_district where code=district)  as "District", polder  as "Polder" ,wmg_reg_date as "Registration Date",wmg_establistment_date as "WMG Establishment Date", wmg_reg_age as "Age upto this month" from vwwmg_registration   where id='+wmg_id
    df = pd.read_sql(query, connection)
    df=df.T
    df.columns=['Values']
    wmg_html=df.to_html(classes='table table-bordered table-hover')


    #wmg monitoring form
    query = 'select data_id as "Data ID",submitted_by as "Submitted By", start_time as "Start Time", end_time as "End Time" ,(end_time-start_time) as "Duration (Hour:Min:Sec)"  , \'<a  class="btn btn-info" href="/bg/forms/Participatory_Monitoring_Form/instance/#/\'||data_id ||\'">View</a>\' as "Action" from vwparticipatory_monitoring'
    pd.set_option('display.max_colwidth', -1)
    df = pd.read_sql(query, connection)
    monitoring_html = df.to_html(classes='tabbed_table table table-bordered table-hover', index=False, escape=False)

    # wmg Tracker form
    query = 'select id as "Data ID",submitted_by as "Submitted By", start_time as "Start Time", end_time as "End Time" ,(end_time-start_time) as "Duration (Hour:Min:Sec)"  , \'<a  class="btn btn-info" href="/bg/forms/WMG_tracker/instance/#/\'||id ||\'">View</a>\' as "Action" from vwwmg_tracker_1_2'
    pd.set_option('display.max_colwidth', -1)
    df = pd.read_sql(query, connection)
    tracker_html = df.to_html(classes='tabbed_table table table-bordered table-hover', index=False, escape=False)

    #Get GPS
    query="select unnest(string_to_array(wmg_gps, ' ')) from vwwmg_registration limit 2"
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    wmg_gps=[]
    for eachval in fetchVal:
        wmg_gps.append(eachval[0])



    context={'wmg_html': wmg_html, "monitoring_html":monitoring_html, "tracker_html":tracker_html,"wmg_gps": json.dumps(wmg_gps)}
    return render(request, 'bgmodule/wmg_profile_details.html',context)



def export_geobis_data(request):
    return render(request, "bgmodule/export_geobis_data.html");

def get_geobis_data(request):
    host = request.POST.get('host')
    port = request.POST.get('port')
    url_str = 'http://'+host+':'+port+'/media/'+request.user.username+'/attachments/'
    #print (url_str)
    query = "select id,date_created::date as receivedate,(select value_label from xform_extracted where xform_id=416 and field_name='F_Present_crop_name' and value_text=json->>'F_Present_crop_name') crop_name,json->>'F_Present_crop_name' crop_name_n,(select value_label from xform_extracted where xform_id=416 and field_name='District' and value_text=json->>'District') District, json->>'Upazila' Upazila_n,(select value_label from xform_extracted where xform_id=416 and field_name='Upazila' and value_text=json->>'Upazila') Upazila, (select value_label from xform_extracted where xform_id=416 and field_name='Union' and value_text=json->>'Union') as Union,json->>'Union' as Union_n, json->>'begin_group_c054f422/Village' Village, json->>'begin_group_c054f422/F_farmer_name' FarmerName, json->>'begin_group_c054f422/F_farmer_phone' mobile, json->>'Season' season, (json->>'sowingdate')::date Sowing_date,json->>'nextCrop' Next_crop,json->>'image' image, string_to_array(json->>'geoshape',';') geodata from logger_instance where xform_id=416 and deleted_at is null order by date_created DESC"
    #print query
    user_path_filename = os.path.join(settings.MEDIA_ROOT, 'geobis_excel_reports', request.user.username)
    # user_path_filename = os.path.join(user_path_filename, report_name+)
    if not os.path.exists(user_path_filename):
        os.makedirs(user_path_filename)
    filename = os.path.join(user_path_filename, 'geobis_geoarea_info.xls')
    book = xlwt.Workbook()
    sh = book.add_sheet('sheet1')

    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yyyy'

    k = 0
    sh.write(k, 0, 'Data id')
    sh.write(k, 1, 'District')
    sh.write(k, 2, 'Upazila')
    sh.write(k, 3, 'Union')
    sh.write(k, 4, 'Village')
    sh.write(k, 5, 'Farmer name')
    sh.write(k, 6, 'Mobile')
    sh.write(k, 7, 'Season')
    sh.write(k, 8, 'Crop type')
    sh.write(k, 9, 'Sowing date')
    sh.write(k, 10, 'Point')
    sh.write(k, 11, 'LAN')
    sh.write(k, 12, 'LON')
    sh.write(k, 13, 'accuracy')
    sh.write(k, 14, 'Next Crop')
    sh.write(k, 15, 'Image')
    sh.write(k, 16, 'Received date')
    dataset = __db_fetch_values_dict(query)
    for tmp in dataset:
    	#print "*********************"
    	#print "out-0 --- "+str(tmp['id'])
        #Remove empty value from list
        list_geodata = filter(None, tmp['geodata'])
        if list_geodata:
            #print "out-1 --- "+str(tmp['id'])
            list_size = len(list_geodata)
            point = 1
            for i in range(list_size-1):
                k = k + 1
                #remove leading & trailing spaces from string and split
                lst = list_geodata[i].strip().split(" ")
                #print "out-2 --- "+str(tmp['id'])
                sh.write(k, 0, tmp['id'])
                sh.write(k, 1, tmp['district'])
                sh.write(k, 2, tmp['upazila'])
                sh.write(k, 3, tmp['union'])
                sh.write(k, 4, tmp['village'])
                sh.write(k, 5, tmp['farmername'])
                sh.write(k, 6, tmp['mobile'])
                sh.write(k, 7, tmp['season'])
                sh.write(k, 8, tmp['crop_name'])
                sh.write(k, 9, tmp['sowing_date'],date_format)
                sh.write(k, 10, point)
                sh.write(k, 11, lst[0])
                sh.write(k, 12, lst[1])
                sh.write(k, 13, lst[3])
                sh.write(k, 14, tmp['next_crop'])
                sh.write(k, 15, url_str+tmp['image'])
                sh.write(k, 16, tmp['receivedate'],date_format)
                point = point+1

    book.save(filename)
    file_path = '/media/geobis_excel_reports/' + request.user.username + '/' + 'geobis_geoarea_info.xls'
    #file_path = filename
    return HttpResponse(simplejson.dumps(file_path), content_type="application/json")


