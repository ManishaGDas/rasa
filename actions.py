from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import pandas as pd
import json
import smtplib
from email.message import EmailMessage

ZomatoData = pd.read_csv('zomato.csv')
ZomatoData = ZomatoData.drop_duplicates().reset_index(drop=True)
WeOperate = ['Agra',
 'Ahmedabad',
 'Allahabad',
 'Amritsar',
 'Aurangabad',
 'Bangalore',
 'Bhopal',
 'Bhubaneshwar',
 'Chandigarh',
 'Chennai',
 'Coimbatore',
 'Dehradun',
 'Faridabad',
 'Gangtok',
 'Ghaziabad',
 'Goa',
 'Gurgaon',
 'Guwahati',
 'Hyderabad',
 'Indore',
 'Jaipur',
 'Kanpur',
 'Kochi',
 'Kolkata',
 'Lucknow',
 'Ludhiana',
 'Mangalore',
 'Mohali',
 'Mumbai',
 'Mysore',
 'Nagpur',
 'Nasik',
 'New Delhi',
 'Noida',
 'Ooty',
 'Panchkula',
 'Patna',
 'Puducherry',
 'Pune',
 'Ranchi',
 'Secunderabad',
 'Shimla',
 'Surat',
 'Vadodara']

Cuisine_lookup= ['Chinese', 'Mexican', 'Italian', 'American', 'South Indian', 'North Indian']

def edits_one(word):
	    "Create all edits that are one edit away from `word`."
	    alphabets    = 'abcdefghijklmnopqrstuvwxyz'
	    splits     = [(word[:i], word[i:])                   for i in range(len(word) + 1)]
	    deletes    = [left + right[1:]                       for left, right in splits if right]
	    inserts    = [left + c + right                       for left, right in splits for c in alphabets]
	    replaces   = [left + c + right[1:]                   for left, right in splits if right for c in alphabets]
	    transposes = [left + right[1] + right[0] + right[2:] for left, right in splits if len(right)>1]
	    return set(deletes + inserts + replaces + transposes)


def possible_correction_city(City):
    for City_operate in WeOperate:
        if (City.lower() != City_operate.lower()):
            if City.lower() in edits_one(City_operate.lower()):
                City = City_operate
    return City


def possible_correction_cuisine(Cuisine):
    for Cuisine_choice in Cuisine_lookup:
        if (Cuisine.lower() != Cuisine_choice.lower()):
            if Cuisine.lower() in edits_one(Cuisine_choice.lower()):
                Cuisine = Cuisine_choice
    return Cuisine


def RestaurantSearch(City,Cuisine,Budget='mid'):
    City= possible_correction_city(City)
    Cuisine = possible_correction_cuisine(Cuisine)
    TEMP = ZomatoData[(ZomatoData['Cuisines'].apply(lambda x: Cuisine.lower() in x.lower())) & (ZomatoData['City'].apply(lambda x: City.lower() in x.lower()))]
    if type(Budget) == str:
        if Budget == 'low':
            Budget_amt =250
        elif Budget == 'mid':
            Budget_amt =500
        else:
            Budget_amt = 1000

    if Budget_amt<=300:
        Temp_budgeted = TEMP[(TEMP['Average Cost for two']<=300)]
    elif Budget_amt<=700:
        Temp_budgeted = TEMP[((TEMP['Average Cost for two'])>300) & ((TEMP['Average Cost for two'])<=700)]
    else: 
        Temp_budgeted = TEMP[((TEMP['Average Cost for two'])>700)]


class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_search_restaurants'

	def run(self, dispatcher, tracker, domain):
		#config={ "user_key":"f4924dc9ad672ee8c4f8c84743301af5"}
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		
		Price = tracker.get_slot('price')
		results = RestaurantSearch(City=loc,Cuisine=cuisine, Budget = Price)
		response=""
		if results.shape[0] == 0:
			response= "no results"
		else:
			for restaurant in RestaurantSearch(loc,cuisine,Price).iloc[:5].iterrows():
				restaurant = restaurant[1]
				response=response + F"Found {restaurant['Restaurant Name']} in {restaurant['Address']} rated {restaurant['Address']} with avg cost {restaurant['Average Cost for two']} \n\n"
				
		dispatcher.utter_message("-----"+response)
		return [SlotSet('location',loc)]

class ActionSendMail(Action):
	def name(self):
		return 'action_send_mail'
    
	def run(self, dispatcher, tracker, domain):
		# Import smtplib for the actual sending function

        # Import the email modules we'll need
		MailID = tracker.get_slot('email')
		cuisine = tracker.get_slot('cuisine')
		Price = tracker.get_slot('price')
		loc = tracker.get_slot('location')
		results = RestaurantSearch(City=loc,Cuisine=cuisine, Budget = Price)
		response=""
		if results.shape[0] == 0:
			response= "no results"
		else:
			for restaurant in RestaurantSearch(loc,cuisine,Price).iloc[:5].iterrows():
				restaurant = restaurant[1]
				nl = '\n'
				response=response + f"Found {restaurant['Restaurant Name']} in {restaurant['Address']} rated {restaurant['Aggregate rating']} with avg cost {restaurant['Average Cost for two']} {nl}{nl}"
		sender_address= 'mgd.mlc20iiitb@gmail.com'
		sender_pass= 'abcde@12345'
		receiver_address= 'tan.batra@gmail.com'
		message = EmailMessage()
		message.set_content(response)
		message['From']= sender_address
		message['To']= receiver_address
		message['Subject']= 'Chatbot: Zomato Restaurant Results'
        # message.attach(MIMEText(response,'plain'))
		session= smtplib.SMTP('smtp.gmail.com',587)
		session.starttls()
		session.login(sender_address, sender_pass)
        # text= message.as_string()
		session.sendmail(sender_address, receiver_address, message.as_bytes())
		session.quit()
		print('Mail Sent')