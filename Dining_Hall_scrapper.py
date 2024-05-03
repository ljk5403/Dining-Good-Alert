import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import pytz
import telegram
import asyncio
import os, sys
import json
import pprint




dinning_hall_tuple = ('rhetas-market', 'lizs-market', 'gordon-avenue-market', 'four-lakes-market', 'carsons-market', 'lowell-market')
#meals_tuple = ('breakfast', 'lunch', 'dinner')
meals_tuple = ('lunch', 'dinner')

T0_good_dish_list = ['Shrimp', 'Tuna', 'Salmon', 'Cod', 'Tilapia', 'lamb', 'curry', 'beef', 'pork', 'fish']



def xprint(message):
    print(message)


def get_dinning_hall_url(dinning_hall : str, meal : str, date : datetime):
    url_base = "https://wisc-housingdining.api.nutrislice.com/menu/api/weeks/school/"
    #url_example = "https://wisc-housingdining.api.nutrislice.com/menu/api/weeks/school/rhetas-market/menu-type/dinner/2024/04/25/"
    if dinning_hall not in dinning_hall_tuple:
        #xprint("Not correct meal! aborting")
        raise ValueError("results: meal must be one of: ", dinning_hall_tuple)
    if meal not in meals_tuple:
        raise ValueError("results: meal must be one of: ", meals_tuple)
    return url_base+dinning_hall+"/menu-type/"+meal+"/"+date.strftime('%Y/%m/%d')





def get_menu_raw(target_url):
    try:
        r=requests.get(target_url)
    except: #or more precisely: except requests.exceptions.RequestException as e:
        print("Lost connection!")
    else:
        data = r.json()
        return data

def get_menu_dict(data, date : datetime):
    menu_dict = {}
    target_menu=next((d for d in data["days"] if d["date"] == date.strftime('%Y-%m-%d')), None)
    for d in target_menu["menu_items"]:
        if isinstance(d["food"], dict):
            if "name" in d["food"]:
                #print(d["food"]["name"])
                food_name = d["food"]["name"]
                menu_dict[food_name] = ""
                if "synced_ingredients" in d["food"]:
                    menu_dict[food_name] = str(d["food"]["synced_ingredients"])
                    #print(d["food"]["name"], ": ", d["food"]["synced_ingredients"])
    return menu_dict

def find_dish(dish : str, menu_dict):
    exact_dishes = []
    relevent_dishes = []
    for key, value in menu_dict.items():
        if dish.casefold() in key.casefold():
            exact_dishes.append(key)
        elif dish.casefold() in value.casefold():
            relevent_dishes.append(key)
    return exact_dishes, relevent_dishes

def find_good_dishes(dish_list, menu_dict):
    good_dishes_menu = {}
    for dish in dish_list:
        a, b = find_dish(dish, menu_dict)
        if a != [] or b != []:
            good_dishes_menu[dish] = (a,b)
    return good_dishes_menu

def find_good_dishes_someday_somewhere_somemeal(dish_list, date, dinning_hall, meal):
    #format date in correct form: datetime
    if not isinstance(date, datetime):
        date = datetime.strptime(date_str, '%Y-%m-%d')
    target_url = get_dinning_hall_url(dinning_hall, meal, date)
    raw_data=get_menu_raw(target_url)
    menu_dict = get_menu_dict(raw_data, date)
    type(menu_dict)
    return find_good_dishes(dish_list, menu_dict)

def summary_of_good_dishes(date):
    summary={}
    for dinning_hall in dinning_hall_tuple:
        summary[dinning_hall]={}
        for meal in meals_tuple:
            summary[dinning_hall][meal] = find_good_dishes_someday_somewhere_somemeal(T0_good_dish_list, date, dinning_hall, meal)
    return summary


def summary_of_good_meal(date, meal):
    summary={}
    for dinning_hall in dinning_hall_tuple:
        summary[dinning_hall]={}
        summary[dinning_hall] = find_good_dishes_someday_somewhere_somemeal(T0_good_dish_list, date, dinning_hall, meal)
    return summary


# Write summary of meals to file
def summary_generator():
    today = datetime.now()
    for meal in meals_tuple:
        with open(meal+".md", 'w') as f:
            print("Update at: "+today.strftime('%Y-%m-%d %H:%M:%S'), file=f)
            pprint.pprint(summary_of_good_meal(today, meal), f)
        print("Successfully updated "+meal+".md")


# TODO: github workflow automate
# TODO: telegram bot auto push?




if __name__ == '__main__':
    #raw_test()
    today = datetime.now()


def raw_test3():
    summary = summary_of_good_dishes(today)
    pprint.pprint(json.dumps(summary, indent=4, sort_keys=True), compact=True)
    #find_good_dishes_someday_somewhere_somemeal(T0_good_dish_list, today, "rhetas-market", "dinner")



def raw_test2():
    today = datetime.now()
    target_url = get_dinning_hall_url("rhetas-market", "dinner", today)
    raw_data=get_menu_raw(target_url)
    menu_dict = get_menu_dict(raw_data, today)
    type(menu_dict)
    #print(find_dish("Cheese Pizza", menu_dict))
    print(find_good_dishes(T0_good_dish_list, menu_dict))



def raw_test():
    # Get webdata and reformulate as json
    url="https://wisc-housingdining.api.nutrislice.com/menu/api/weeks/school/rhetas-market/menu-type/dinner/2024/04/25/"
    r=requests.get(url)
    data = r.json()

    # Get target:
    data["days"]
    target_menu=next((d for d in data["days"] if d["date"] == "2024-04-25"), None)
    target_menu["menu_items"]

    #target1=next((d for d in target_menu["menu_items"] if "Normandy" in d["food"]["name"]), None)
    for d in target_menu["menu_items"]:
        if isinstance(d["food"], dict):
            if "name" in d["food"]:
                print((d["food"])["name"])
                if "synced_ingredients" in d["food"]:
                    print(d["food"]["name"], ": ", d["food"]["synced_ingredients"])
                    if "Normandy" in d["food"]["name"]:
                        print(d["food"]["name"], d["food"]["synced_ingredients"])
                        print("YES!")
                        #break

