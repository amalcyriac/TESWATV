import csv,io
from django.http import HttpResponse
from django.shortcuts import render,redirect
from rating_app.models import credited_courses_table,rating_table
from . import forms
from django.contrib.auth import logout

def home(request):
    logout(request)
    request.session.set_test_cookie()
    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()
        return render(request,'home.html')
    else:
        return HttpResponse('Your browser does not accept cookies.')

def success(request):
        if not request.user.is_authenticated:
            return HttpResponse('Login to Google first')
        mail=str(request.user.email)
        if not (mail[-11:] == '@nitc.ac.in'):
            return HttpResponse('You are not authenticated to evaluate any courses. Ensure that you are using NITC mail id.')
        roll=mail[-20:-11]
        obj=credited_courses_table.objects.filter(roll_no=roll)
        if not len(obj):
            return HttpResponse("You don't seem to have registered for any courses. Contact your faculty advisor.")
        request.session['roll']=roll
        request.session.set_expiry(1200)
        return redirect('/rate/')

def rate(request):
    if not request.user.is_authenticated:
            return HttpResponse('Login to Google first')
    if not request.session.get('roll'):
        return HttpResponse('Please go to login page. The session might have expired')
    request.session.set_expiry(1200)
    roll=str(request.session['roll'])

    if request.method=='GET':
        obj=credited_courses_table.objects.filter(roll_no=roll,feedback_status=0)
        if not obj.exists():
            return HttpResponse('You have completed the evaluation. Thank you.')
        listt=[]
        for o in obj:
            listt.append(o.course_name + ' - ' + o.faculty_name)
        return render(request,'rate.html',{'listt':listt})
    else:
        pair = request.POST['pair']
        pos = pair.find('-')
        cname = pair[:pos-1]
        fname = pair[pos+2:]
        obj=credited_courses_table.objects.filter(roll_no = roll, course_name = cname, faculty_name = fname)
        obj = obj[0]
        if obj.feedback_status == 1:
            return HttpResponse('You have already rated this course.')
        obj.feedback_status = 1
        obj.save()
        obj = rating_table.objects.filter(course_name = cname, faculty_name = fname)
        obj = obj[0]
        rep = request.POST
        obj.question_1 = obj.question_1 + int(rep['star1'])
        obj.question_2 = obj.question_2 + int(rep['star2'])
        obj.question_3 = obj.question_3 + int(rep['star3'])
        obj.question_4 = obj.question_4 + int(rep['star4'])
        obj.question_5 = obj.question_5 + int(rep['star5'])
        obj.question_6 = obj.question_6 + int(rep['star6'])
        obj.question_7 = obj.question_7 + int(rep['star7'])
        obj.count = obj.count + 1
        obj.save()

        obj=credited_courses_table.objects.filter(roll_no=roll,feedback_status=0)
        if not obj.exists():
            return HttpResponse('You have completed the evaluation. Thank you.')
        listt=[]
        for o in obj:
            listt.append(o.course_name + ' - ' + o.faculty_name)
        return render(request,'rate.html',{'listt':listt})


def admin(request):
    template="admin.html"
    return render(request,template)

def database(request):
    template="database.html"
    return render(request,template)

def save_database(request):
    template="save_database.html"
    return render(request,template)

def evaluation_progress(request):
    if request.method=="GET":
        template="evaluation_progress_test.html"
        form=forms.progress()
        return render(request,template,{'form':form})
    else:
        form=forms.progress(request.POST)
        template="evaluation_progress_test.html"
        if form.is_valid():
            status=form.cleaned_data['Status']
            department=form.cleaned_data['Department']
            status=int(status)
            if status == 1 :
                statusname = 'Completed'
            elif status == 0 :
                statusname = 'Pending'

            if credited_courses_table.objects.filter(feedback_status=status).exists() :
                q1 = credited_courses_table.objects.filter(roll_no__endswith=department).distinct()
                q2 = q1.filter(feedback_status=status).values('roll_no')
                abcd=q2.values_list('roll_no', flat=True).order_by('roll_no')
                return render(request,template,{'abcd':abcd,'status':statusname,'department':department,'form':form})
            else :
                return HttpResponse('No matching rows')

def details(request):
    if request.method=="GET":
        template="details.html"
        form=forms.details()
        return render(request,template,{'form':form})
    else:
        form=forms.details(request.POST)
        if form.is_valid():
            a=form.cleaned_data['faculty_name']
            b=form.cleaned_data['course_name']
            if rating_table.objects.filter(faculty_name=a,course_name=b).exists() :
                abcd = rating_table.objects.get(faculty_name=a,course_name=b)
                ans=abcd.question_1+abcd.question_2+abcd.question_3+abcd.question_4+abcd.question_5+abcd.question_6+abcd.question_7
                ans=ans/7
                ans=ans/abcd.count
                perc=ans/5
                perc=perc*100
                text = str(perc) + "%"
                return render(request,'details.html',{'text':text,'abcd':abcd,'form':form,'fname':a,'cname':b})
            else :
                return HttpResponse('Does not exist')

def overall(request):
    num1=0
    for a in rating_table.objects.all():
        num1=num1+a.count
    num2=0
    for b in credited_courses_table.objects.values('roll_no').distinct():
        num2=num2+1
    num3=0
    for c in rating_table.objects.values('faculty_name').distinct().exclude(count=0):
        num3=num3+1
    num4=0
    for d in rating_table.objects.values('course_name').distinct().exclude(count=0):
        num4=num4+1
    num5=0
    for e in credited_courses_table.objects.filter(feedback_status=False):
        num5=num5+1
    return render(request,'overall_statistics.html',{'num1':num1,'num2':num2,'num3':num3,'num4':num4,'num5':num5})

def save_database_1(request):
    response1 = HttpResponse(content_type='text/csv')
    response1['Content-Disposition'] = 'attachment; filename="credited_courses_table.csv"'
    writer = csv.writer(response1)
    writer.writerow(['roll_no', 'faculty_name', 'course_name', 'feedback_status'])
    rows = credited_courses_table.objects.all()
    for row in rows:
        writer.writerow([row.roll_no,row.faculty_name,row.course_name,row.feedback_status])
    return response1

def save_database_2(request):
    response2 = HttpResponse(content_type='text/csv')
    response2['Content-Disposition'] = 'attachment; filename="rating_table.csv"'
    writer = csv.writer(response2)
    writer.writerow(['faculty_name', 'course_name', 'question_1', 'question_2', 'question_3', 'question_4', 'question_5', 'question_6', 'question_7', 'count'])
    rows = rating_table.objects.all()
    for row in rows:
        writer.writerow([row.faculty_name,row.course_name,row.question_1,row.question_2,row.question_3,row.question_4,row.question_5,row.question_6,row.question_7,row.count])
    return response2

def delete_database(request):
    credited_courses_table.objects.all().delete()
    rating_table.objects.all().delete()
    return HttpResponse('all tables cleared')

def update_database(request):
    template="update_database_options.html"
    return render(request,template)

def update_database_dss(request):
    template="update_database_dss.html"
    prompt={
        'order' : 'Order of CSV file should be roll no., faculty name, course name.'
    }
    if request.method == "GET":
        return render(request,template,prompt)
    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'This is not a csv file')
    data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        _, created = credited_courses_table.objects.update_or_create(
            roll_no=column[0],
            faculty_name=column[1],
            course_name=column[2],
            feedback_status = False
        )
        _, created = rating_table.objects.update_or_create(
            faculty_name=column[1],
            course_name=column[2],
            question_1 = 0,
            question_2 = 0,
            question_3 = 0,
            question_4 = 0,
            question_5 = 0,
            question_6 = 0,
            question_7 = 0,
            count = 0
        )
    context = {
    'order' : 'Successfully uploaded'
    }
    return HttpResponse('Successfully uploaded')

def update_database_saved(request):
    template="update_database_saved.html"
    prompt={
        'order1' : 'Order of CSV file should be roll no., faculty name, course name, feedback_status',
        'order2' : 'Order of CSV file should be faculty name,course name,question 1,question 2,question 3,question 4,question 5,question 6,question 7,count'
    }
    if request.method == "GET":
        return render(request,template,prompt)
    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'This is not a csv file')
    data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        _, created = credited_courses_table.objects.update_or_create(
            roll_no=column[0],
            faculty_name=column[1],
            course_name=column[2],
            feedback_status = False
        )
        _, created = rating_table.objects.update_or_create(
            faculty_name=column[1],
            course_name=column[2],
            question_1 = 0,
            question_2 = 0,
            question_3 = 0,
            question_4 = 0,
            question_5 = 0,
            question_6 = 0,
            question_7 = 0,
            count = 0
        )
    context = {
    'order' : 'Successfully uploaded'
    }
    return HttpResponse('Successfully uploaded')
