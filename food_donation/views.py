from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse,request
from django.views import View
from django.conf import settings
from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
import os
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from datetime import datetime
from database import create_connection

import smtplib
import string
import random
from datetime import datetime
from django.core.mail import EmailMessage

from lib_password_generator import make_password


conn = create_connection()
# Create your views here.

class index(View):
    def get(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        registration_number = request.session.get("registration_number")
        return render(request, "home.html",context={"user_id":household_id,"registration_number":registration_number})
    
class about(View):
    def get(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        registration_number = request.session.get("registration_number")
        return render(request, "about.html",context={"user_id":household_id,"registration_number":registration_number})
    
    def post(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        registration_number = request.session.get("registration_number")
        return render(request, "about.html",context={"user_id":household_id,"registration_number":registration_number})
    
class admin(View):
    def get(self, request, *args, **kwargs):
        return render(request, "admin_sidebar.html")
    
class admin_dashboard(View):
    def get(self, request, *args, **kwargs):
        
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')

        cur = conn.cursor(buffered=True)
        cur.execute("select count(id) as ngo_count from mstr_ngo")
        ngos = cur.fetchone()
        
        cur.execute("select count(id) as donation_count from donation")
        donations = cur.fetchone()
        
        cur.execute("select count(id) as household_count from mstr_household")
        households = cur.fetchone()
        
        return render(request, "admin_dashboard.html",context={"ngos":ngos[0],"donations":donations[0],"households":households[0]})

class admin_ngo_list(View):
    def get(self, request, *args, **kwargs):
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')
        
        cur = conn.cursor(buffered=True)
        cur.execute("select * from mstr_ngo")
        data = cur.fetchall()
        return render(request, "admin_ngo_list.html",context={"data":data})
    
    def post(self, request, *args, **kwargs):
        
        ngo_id = request.POST.get("edit")
        
        if ngo_id:
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_ngo where id = %s",(ngo_id,))
            ngo_data = cur.fetchone()
            
            cur.execute("select city_name from mstr_location where id = %s",(ngo_data[9],))
            city_name = cur.fetchone()
            
            return render(request,"admin_edit_ngo.html",context={"data":ngo_data,"city_name":city_name[0]})

        return render(request, "admin_ngo_list.html")

class admin_add_ngo(View):
    def get(self, request, *args, **kwargs):
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')
        return render(request, "admin_add_ngo.html")

    def post(self, request, *args, **kwargs):
        ngo_name = request.POST.get("ngo_name")
        founder_name = request.POST.get("founder_name")
        reg_number = request.POST.get("reg_number")
        reg_date = request.POST.get("reg_date")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city_name = request.POST.get("city")
        
        ngo_id = request.POST.get("ngo_id")
        
        cur = conn.cursor(buffered=True)
        
        if email and not ngo_id:
            cur.execute("select * from mstr_ngo where email = %s",(email,))
            fetched_email = cur.fetchone()

            if fetched_email is not None:
                messages.error(request, "Email id Already Exist")
                return redirect("admin_add_ngo")
        
        if city_name:
            cur.execute("select * from mstr_location where city_name = %s",(city_name,))
            city = cur.fetchone()

            if city is None:
                cur.execute("insert into mstr_location (city_name) values (%s)",(city_name,))
                conn.commit()
                cur.close()
                
                cur = conn.cursor(buffered=True)
                cur.execute("select * from mstr_location where city_name = %s",(city_name,))
                city = cur.fetchone()
                
                
            cur = conn.cursor(buffered=True)
            location_id = city[0]
            
            
            if ngo_id:
                cur.execute("update mstr_ngo set name = %s, founder_name = %s, registration_number = %s, registration_date = %s, email = %s, phone = %s, address = %s, location_id = %s where id = %s",
                            (ngo_name, founder_name, reg_number, reg_date, email, phone, address, location_id, int(ngo_id)))
                conn.commit()
                cur.close()
                
                return redirect('admin_ngo_list')
            
            # Generate random password
            cur = conn.cursor(buffered=True)
            #password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            password = make_password(10, use_special_chars=True)
            print(f"Generated Password: {password}")
            
            cur.execute("""insert into mstr_ngo (name, founder_name, registration_number, registration_date, email, password, phone, address, location_id) 
                        values (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(ngo_name, founder_name, reg_number, reg_date, email, password, phone, address, location_id))
            conn.commit()
            cur.close()
            
            
            # Send email with the password
            email_subject = "Your NGO Registration Details"
            email_body = f"""
            Hello {founder_name},

            Your NGO '{ngo_name}' has been successfully registered.
            Your temporary password is: {password}


            Best regards,
            Team ShareABite
            """
            
            email_message = EmailMessage(email_subject, email_body, to=[email])
            email_message.send()

        
        return render(request, "admin_add_ngo.html")

class admin_donations(View):
    def get(self, request, *args, **kwargs):
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')
        cur = conn.cursor(buffered=True)
        cur.execute("select * from donation order by datetime desc")
        data = cur.fetchall()

        donations = []

        for row in data:
            household_id = row[1]
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_household where id = %s",(household_id,))
            household = cur.fetchone()
            
            ngo_id = row[2]
            cur.execute("select * from mstr_ngo where id = %s",(ngo_id,))
            ngo = cur.fetchone()

            donation_info = {
                "donation" : row,
                "household_name":household[1],
                "household_address":household[5],
                "ngo_name":ngo[1] if ngo else "Not available"
            }
            donations.append(donation_info)

        return render(request, "admin_donations.html",context={"data":donations})
    
    def post(self, request, *args, **kwargs):
        export_pdf = request.POST.get("export_pdf")
        if export_pdf == "true":
            success = trigger_donation_report()
            if success:
                print("Lambda triggered successfully.")
            else:
                print("Failed to trigger Lambda.")
            return redirect('admin_donations')




class admin_assign_ngo(View):
    def get(self, request, *args, **kwargs):
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')
        donation_id = kwargs.get('donation_id')
        
        cur = conn.cursor(buffered=True)
        cur.execute("select * from donation where id = %s", (donation_id,))
        data = cur.fetchone()
        
        cur.execute("select * from mstr_household where id = %s",(data[1],))
        household_data = cur.fetchone() 
        
        cur.execute("select * from mstr_ngo where location_id = %s",(household_data[6],))
        ngos = cur.fetchall()
        
        return render(request,"admin_assign_ngo.html",context={"data":data,"ngos":ngos,"household":household_data})
    
    def post(self, request, *args, **kwargs):
        
        ngo_id = request.POST.get("ngo_id")
        donation_id = request.POST.get("donation_id")
        household_id = request.POST.get("household_id")
        
        if ngo_id and donation_id:
            cur = conn.cursor(buffered=True)
            cur.execute("update donation set ngo_id = %s , status = %s where id = %s",(ngo_id, "accepted", donation_id))
            conn.commit()
            cur.close()
            
            cur = conn.cursor(buffered=True)
            cur.execute("select name, email, phone from mstr_ngo where id = %s",(ngo_id,))
            ngo_data = cur.fetchone()
            
            cur = conn.cursor(buffered=True)
            cur.execute("select name, email, address from mstr_household where id = %s",(household_id,))
            household_data = cur.fetchone()
            
            
            # email to ngo
            email_subject = "Donation Assigned By Admin"
            email_body = f"""
            Hello {ngo_data[0]},

            Food donation is assigned to you by admin.
            here are household details.
            
            name : {household_data[0]},
            email : {household_data[1]},
            address : {household_data[2]}
            
            you can communicate with household for further process.

            Best regards,
            Team ShareABite
            """
            
            email_message = EmailMessage(email_subject, email_body, to=[ngo_data[1]])
            email_message.send()
            
            
            
            # email to household
            email_subject = f"Donation Assigned By Admin to NGO {ngo_data[0]}"
            email_body = f"""
            Hello {household_data[0]},

            Food donation is assigned to the NGO {ngo_data[0]}.
            NGO email: {ngo_data[1]},
            phone: {ngo_data[2]}
            
            you can communicate with NGO for further process

            Best regards,
            Team ShareABite
            """
            
            email_message = EmailMessage(email_subject, email_body, to=[household_data[1]])
            email_message.send()
            
            
            return redirect('admin_donations')
            
            
        return render(request,"admin_assign_ngo.html")

class admin_households(View):
    def get(self, request, *args, **kwargs):
        admin_id = request.session.get("user_id")
        if not admin_id:
            return redirect('logout')
        cur = conn.cursor(buffered=True)
        cur.execute("select * from mstr_household")
        data = cur.fetchall()
        return render(request, "admin_households.html",context={"data":data})

class login(View):
    def get(self, request, *args, **kwargs):
        return render(request, "login.html")
    
    def post(self, request, *args, **kwargs):
        user_tye = request.POST.get("user_type")
        email = request.POST.get("email")
        password = request.POST.get("password")

        cur = conn.cursor(buffered=True)

        if email and password:

            if user_tye == "ADMIN":
                cur.execute("select email , password from mstr_admin where email = %s and password = %s",(email,password))
                admin = cur.fetchone()

                if admin is not None:
                    cur.execute("select id from mstr_admin where email = %s and password = %s",(email,password))
                    admin = cur.fetchone()
                    request.session['user_id'] = admin[0]
                    return redirect("admin_dashboard")
                else:
                    messages.error(request, "Incorrect Email id or Password")
                    return redirect("login")

            
            if user_tye == "HOUSEHOLD":
                cur.execute("select id , email , password , location_id from mstr_household where email = %s and password = %s",(email,password))
                household = cur.fetchone()
                
                if household is not None:
                    request.session['email'] = email
                    request.session['password'] = password
                    request.session['user_id'] = household[0]
                    request.session['location_id'] = household[3]
                    return redirect("household_donations")
                else:
                    messages.error(request, "Incorrect Email id or Password")
                    return redirect("login")
            
            if user_tye == "NGO":
                cur.execute("select id , email , password , location_id , registration_number from mstr_ngo where email = %s and password = %s",(email,password))
                ngo = cur.fetchone()
                
                if ngo is not None:
                    request.session['email'] = email
                    request.session['password'] = password
                    request.session['user_id'] = ngo[0]
                    request.session['location_id'] = ngo[3]
                    request.session['registration_number'] = ngo[4]
                    return redirect("ngo_donations")
                else:
                    messages.error(request, "Incorrect Email id or Password")
                    return redirect("login")
        
        return render(request, "login.html")

class signup(View):
    def get(self, request, *args, **kwargs):
        return render(request, "signup.html")
    
    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        address = request.POST.get("address")
        city_name = request.POST.get("city")
        
        
        if city_name:
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_location where city_name = %s",(city_name,))
            city = cur.fetchone()
            
            if city is None:
                cur.execute("insert into mstr_location (city_name) values (%s)",(city_name,))
                conn.commit()
                cur.close()
                
                cur = conn.cursor(buffered=True)
                cur.execute("select * from mstr_location where city_name = %s",(city_name,))
                city = cur.fetchone()
            
            cur = conn.cursor(buffered=True)
            location_id = city[0]
            
            cur.execute("""insert into mstr_household (name, email, phone, password, address, location_id) 
                        values (%s,%s,%s,%s,%s,%s)""",(name, email, phone, password, address, location_id))
            conn.commit()
            cur.close()
            
            
            cur = conn.cursor(buffered=True)
            cur.execute("select id, email, password, location_id from mstr_household where email = %s and password = %s",(email, password))
            user_data = cur.fetchone()
            
            request.session['user_id'] = user_data[0]
            request.session['email'] = user_data[1]
            request.session['password'] = user_data[2]
            request.session['location_id'] = user_data[3]
            
            return redirect("household_donations")
        
        return render(request, "signup.html")

class household_donations(View):
    def post(self, request, *args, **kwargs):
        return render(request, "household_donations.html")
    
    def get(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        
        if not household_id:
            return redirect('login')
        cur = conn.cursor(buffered=True)
        cur.execute("select * from donation where household_id = %s order by datetime desc",(household_id,))
        data = cur.fetchall()
        
        donations = []
        for row in data:
            household_id = row[1]
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_household where id = %s",(household_id,))
            household = cur.fetchone()
            
            ngo_id = row[2]
                
            cur.execute("select * from mstr_ngo where id = %s",(ngo_id,))
            ngo = cur.fetchone()

            donation_info = {
                "donation" : row,
                "ngo_name":ngo[1] if ngo else "Not available",
                "ngo_address":ngo[7] if ngo else "Not available"
            }
            donations.append(donation_info)

        return render(request, "household_donations.html",context={"data":donations,"user_id":household_id})

class household_add_donation(View):
    def get(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        if not household_id:
            return redirect('login')
        return render(request, "household_add_donation.html")

    def post(self, request, *args, **kwargs):
        household_id = request.session.get("user_id")
        l_id = request.session.get("location_id")
        
        food_type = request.POST.get("food_type")
        quantity = request.POST.get("quantity")
        expiry = request.POST.get("expiry")
        
        if expiry:
        
            cur = conn.cursor(buffered=True)
            cur.execute(""" insert into donation (household_id, ngo_id, food_type, expiry, quantity, status, datetime)
                        values (%s, %s, %s, %s, %s, %s, NOW()) """,(household_id, 0, food_type, expiry, quantity,"initiated"))
            
            conn.commit()
            cur.close()
            
            
            cur = conn.cursor(buffered=True)
            cur.execute("select name,email from mstr_ngo where location_id = %s",(l_id,))
            ngo_emails = cur.fetchall()
            
            print(ngo_emails)
            
            # Send email with the password
            for i in ngo_emails:
                name = i[0]
                email = i[1]
                
                email_subject = "Donation request"
                email_body = f"""
                Hello {name},

                New Food donation is posted please check.

                Best regards,
                Team ShareABite
                """
                
                email_message = EmailMessage(email_subject, email_body, to=[email])
                email_message.send()
                
            return redirect('household_donations')
        
        
        return render(request, "household_add_donation.html",context={"user_id":household_id})

class ngo_requests(View):
    def get(self, request, *args, **kwargs):
        ngo_id = request.session.get("user_id")
        l_id = request.session.get("location_id")
        
        if not ngo_id:
            return redirect('logout')
        
        cur = conn.cursor(buffered=True)
        cur.execute("select * from donation where expiry > NOW() and ngo_id = %s order by datetime desc",(0,))
        data = cur.fetchall()
        
        donations = []
        for row in data:
            household_id = row[1]
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_household where id = %s and location_id = %s",(household_id,l_id))
            household = cur.fetchone()

            if not household:
                return render(request, "ngo_requests.html",context={"data":donations ,"user_id":ngo_id})

            donation_info = {
                "donation" : row,
                "household_name":household[1] if household else "Not available",
                "household_address":household[5] if household else "Not available",
            }
            donations.append(donation_info)
        
        return render(request, "ngo_requests.html",context={"data":donations,"user_id":ngo_id})

    def post(self, request, *args, **kwargs):
        """ in this make that row clickable which has status accepted """
        ngo_id = request.session.get("user_id")
        
        accept = request.POST.get("accept")


        if accept:
            
            cur = conn.cursor(buffered=True)
            cur.execute("select household_id from donation where id = %s",(accept,))
            household_id = cur.fetchone()
            
            cur.execute("select name,email from mstr_household where id = %s",(household_id[0],))
            household_details = cur.fetchone()
            
            cur.execute("select name, email, phone, address from mstr_ngo where id = %s",(ngo_id,))
            ngo_details = cur.fetchone()
            
            
            
            cur = conn.cursor(buffered=True)
            cur.execute("update donation set ngo_id = %s, status = %s where id = %s",(ngo_id,"accepted",accept))
            conn.commit()
            
            # send email notification to household
            email_subject = "Your donation request is accepted"
            email_body = f"""
            Hello {household_details[0]},

            Your food donation request is accepted by {ngo_details[0]}.
            
            here are the details,
            NGO Name : {ngo_details[0]},
            Email : {ngo_details[1]},
            Phone : {ngo_details[2]},
            Address : {ngo_details[3]}
            
            You can communicate with the {ngo_details[0]} NGO for further process.

            Best regards,
            Team ShareABite
            """
            
            email_message = EmailMessage(email_subject, email_body, to=[household_details[1]])
            email_message.send()
            
            
            return redirect("ngo_requests")

        return render(request, "ngo_requests.html")

class change_donation_status(View):
    def get(self, request, *args, **kwargs):
        pass
    def post(self, request, *args, **kwargs):
        pass

class ngo_donations(View):
    def get(self, request, *args, **kwargs):
        ngo_id = request.session.get("user_id")
        if not ngo_id:
            return redirect('logout')
        cur = conn.cursor(buffered=True)
        cur.execute("select * from donation where ngo_id = %s order by datetime desc",(ngo_id,))
        data = cur.fetchall()
        
        donations = []
        
        for row in data:
            household_id = row[1]
            cur = conn.cursor(buffered=True)
            cur.execute("select * from mstr_household where id = %s",(household_id,))
            household = cur.fetchone()

            donation_info = {
                "donation" : row,
                "household_name":household[1],
                "household_address":household[5],
            }
            donations.append(donation_info)
        
        return render(request, "ngo_donations.html",context={"data":donations, "user_id":ngo_id})
    
    def post(self, request, *args, **kwargs):
        donation_id = request.POST.get("donation_id")
        
        if donation_id:
            cur = conn.cursor(buffered=True)
            cur.execute("update donation set status = %s where id = %s",("complete", int(donation_id) ))
            conn.commit()
            cur.close()
            return redirect('ngo_donations')
        
        return render(request, "ngo_donations.html")

class logout(View):
    def get(self, request, *args, **kwargs):
        request.session.flush()
        return redirect("index")
    


import requests

def trigger_donation_report():
    try:
        lambda_url = "https://zpcpqm65i5.execute-api.us-east-1.amazonaws.com/trigger/trigger"
        response = requests.get(lambda_url)  # Use GET instead of POST

        print("Lambda Response:", response.status_code, response.text)

        return response.status_code == 200

    except Exception as e:
        print("Error triggering report:", str(e))
        return False

