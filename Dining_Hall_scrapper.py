import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
#import telegram
import os, sys
import shutil
import json
import pprint


zone = ZoneInfo("America/Chicago")

dinning_hall_tuple = ('rhetas-market', 'lizs-market', 'gordon-avenue-market', 'four-lakes-market', 'carsons-market', 'lowell-market')
#meals_tuple = ('breakfast', 'lunch', 'dinner')
meals_tuple = ('lunch', 'dinner')


# Read Favorates Dishes from JSON
with open('fav_dishes.json', 'r') as f:
    fav_data = json.load(f)

good_dish_category_rare = fav_data['good_dish_category_rare']
good_dish_category_favorite = fav_data['good_dish_category_favorite']
good_dish_category_common = fav_data['good_dish_category_common']
good_dish_name_T0 = fav_data['good_dish_name_T0']
good_dish_name_T1 = fav_data['good_dish_name_T1']


good_dish_list = (
        good_dish_name_T0
        + good_dish_category_rare
        + good_dish_category_favorite
        + good_dish_name_T1
        + good_dish_category_common
        )


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


def get_menu_url_for_human_read(dinning_hall, meal, date):
    url_base = "https://wisc-housingdining.nutrislice.com/menu/"
    return url_base+dinning_hall+"/"+meal+"/"+date.strftime('%Y-%m-%d')




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
    menu_info = target_menu["menu_info"]
    for d in target_menu["menu_items"]:
        if isinstance(d["food"], dict):
            if "name" in d["food"]:
                #print(d["food"]["name"])
                food_name = d["food"]["name"]
                location_name = menu_info[str(d["menu_id"])]["section_options"]["display_name"]
                menu_dict[food_name] = {
                        "location": location_name
                        }
                if "synced_ingredients" in d["food"]:
                    menu_dict[food_name]["ingredients"] = str(d["food"]["synced_ingredients"])
                    #print(d["food"]["name"], ": ", d["food"]["synced_ingredients"])
    #print("menu_dict: ",menu_dict)
    #sys.exit()
    return menu_dict #TODO: add "location" to menu_dict

def find_dish(dish : str, menu_dict):
    exact_dishes = {}
    relevant_dishes = {}
    for key, value in menu_dict.items():
        #print(value)
        dish_name = key
        dish_ingredients = value.get("ingredients", "") or ""
        if dish.casefold() in dish_name.casefold():
            exact_dishes[key] = value
        elif dish.casefold() in dish_ingredients.casefold():
            relevant_dishes[key] = value
    return exact_dishes, relevant_dishes #TODO: add "location" to xx_dishes

def find_good_dishes(dish_list, menu_dict):
    good_dishes_menu = {}
    for dish in dish_list:
        a, b = find_dish(dish, menu_dict)
        if a != {} or b != {}:
            good_dishes_menu[dish] = (a,b)
    return good_dishes_menu

def find_good_dishes_someday_somewhere_somemeal(dish_list, date, dinning_hall, meal):
    #format date in correct form: datetime
    if not isinstance(date, datetime):
        date = datetime.strptime(date, '%Y-%m-%d')
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
            summary[dinning_hall][meal] = find_good_dishes_someday_somewhere_somemeal(good_dish_list, date, dinning_hall, meal)
    return summary


def summary_of_good_meal(date, meal):
    summary={}
    for dinning_hall in dinning_hall_tuple:
        summary[dinning_hall]={}
        summary[dinning_hall] = find_good_dishes_someday_somewhere_somemeal(good_dish_list, date, dinning_hall, meal)
    return summary

# for Markdown
def add_spaces_to_file(file_path):
    # Read the original file and collect lines
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Add two spaces at the beginning of each line
    modified_lines = [line.rstrip('\n') + '  \n' for line in lines]

    # Write the modified lines back to the same file
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

# Write summary of meals to file
def summary_generator(date : datetime = None, reldate : str =None):
    if date is None :
        date = datetime.now(zone)
        reldate="today"
    for meal in meals_tuple:
        filename = reldate + "_" + meal+".md"
        with open(filename, 'w') as f:
            print("# "+date.strftime('%Y-%m-%d') + " " + meal, file=f)
            print("*THERE COULD BE MISTAKES AND LAST-MINIUTE CHANGES! CHECK THE MENU BEFORE YOU GO!*", file=f)
            print("Updated at: "+datetime.now(zone).strftime('%Y-%m-%d %H:%M:%S'), file=f)
            summary = summary_of_good_meal(date, meal)
            for dhall, dishes in summary.items():
                menu_link = get_menu_url_for_human_read(dhall, meal, date)
                print("## ["+dhall+"]"+"("+menu_link+")", file=f)
                #pprint.pprint(dishes, f)
                for keyword, dish_list in dishes.items() :
                    print("**" + keyword + "**", file=f)
                    print("In name: ", file = f)
                    print_as_list_in_md(dish_list[0], f)
                    if dish_list[1]:
                        print("In description: ", file = f) 
                        print_as_list_in_md(dish_list[1], f)
            print("", file = f)
        add_spaces_to_file(filename)
        print("Successfully updated " + filename)

def print_as_list_in_md(my_dict:dict, my_file):
    for key, value in my_dict.items():
        print(f" - {key} @ *{value["location"]}*", file=my_file)
    print("", file=my_file  )

# TODO: telegram bot auto push?

def old_menu_archiver():
    for meal in meals_tuple:
        source_file = "today_" + meal + '.md'
        if os.path.exists(source_file):
            yesterday = datetime.now(zone) - timedelta(days=1)
            destination_directory = 'archive'
            new_file_name = yesterday.strftime('%Y-%m-%d') + "_" + source_file
            destination_file_path = os.path.join(destination_directory, new_file_name)
            shutil.move(source_file, destination_file_path)
        else:
            print("Not found: " + source_file)


def github_autoUpdater():
    old_menu_archiver()
    for _ in range (3):
        try:
            summary_generator()
            now = datetime.now(zone)
            summary_generator(now + timedelta(days=1), "tomorrow")
            summary_generator(now + timedelta(days=2), "overmorrow")           
        except:
            print("Error, will retry in 5 seconds...")
            time.sleep(5)
            continue
        else:
            break

if __name__ == '__main__':
    #raw_test3()
    print("")



# Below are tests

def raw_test4(): #20250912
    #today = datetime.now(zone)
    fixed_date = datetime(2025, 9, 12, tzinfo=zone)
    summary_generator()
    #summary = find_good_dishes_someday_somewhere_somemeal(good_dish_list, fixed_date, "gordon-avenue-market", "dinner")
    #pprint.pprint(json.dumps(summary, indent=4, sort_keys=True), compact=True)




def raw_test3():
    today = datetime.now(zone)
    summary = summary_of_good_dishes(today)
    pprint.pprint(json.dumps(summary, indent=4, sort_keys=True), compact=True)
    #find_good_dishes_someday_somewhere_somemeal(good_dish_list, today, "rhetas-market", "dinner")



def raw_test2():
    today = datetime.now(zone)
    target_url = get_dinning_hall_url("rhetas-market", "dinner", today)
    raw_data=get_menu_raw(target_url)
    menu_dict = get_menu_dict(raw_data, today)
    type(menu_dict)
    #print(find_dish("Cheese Pizza", menu_dict))
    print(find_good_dishes(good_dish_list, menu_dict))



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

