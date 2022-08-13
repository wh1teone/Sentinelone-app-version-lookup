import requests #For the GET requests to gather sites/apps site_json_response
from packaging import version #For the app version comparison
import csv #For writing the results to CSV file.


sites_name_id_dict = {} #store dict for site id to name key-value
user_chosen_app = ""  #store user's input for wanted app.
user_chosen_app_most_updated_version = str() #store user's input for app version.
app_nextcursor = ""  #used to store next cursor string for the APP response API calls.
site_nextcursor = "" #used to store next cursor string for the SITE response API calls.
app_dictionary = {} # nested dictionary for each row of csv to be created
app_dictionary_counter = 0 #for each row to be created
SENTINEL_ACCOUNT_DICT = {"Account name" : { "URL" : "",API_TOKEN: "",},
                         "Account name 2" : {"URL": "",API_TOEN: ""}} #used if there are more than one sentinelone server console used

}}

def get_site_ids(url,specific_headers):
    """
    API request to get_siteids endpoint - returns a dictionary of site id to site name.
    :return: dictionary of site id to site name.
    """
    global site_nextcursor
    global headers
    sites_request = requests.get(f"{url}/web/api/v2.1/sites", headers=specific_headers).json() #first response to populate dict
    site_nextcursor = sites_request['pagination']['nextCursor'] #response to populate next cursor for the while loop.
    add_sites_to_dict(sites_request)
    while site_nextcursor is None: #while loop to ensure all sites are inserted to dict.
        sites_request2 = requests.get(f"{url}/web/api/v2.1/sites?cursor={site_nextcursor}", headers=headers).json()
        site_nextcursor = sites_request2['pagination']['nextCursor']
        add_sites_to_dict(sites_request2)
    return sites_name_id_dict

def add_sites_to_dict(site_json_response):
    """
    iterates through the site api response and adds pairs to dict if not part of unwanted sites
    :param site_json_response: site endpoints json response
    :return:None
    """
    for site_dict in site_json_response['data']['sites']:
        if site_dict['id'] != '1137391321271125599' and site_dict['id'] != '1137393572622522068' and site_dict['id'] != '1106987814028903508':
            sites_name_id_dict[site_dict['name']] = site_dict['id']

def get_applications_first_request(user_app_first_request, site_id,url,specific_headers):
    """
    first request to gain the cursor for next requests.
    adds to the nested dictionary the first response of applications per site.
    :param user_app_first_request: chosen app to check via sentinelone api
    :param site_id: id of the site to be searched for the app
    :return: None.
    """
    global app_nextcursor
    initial_request_json = requests.get(
        f"{url}/web/api/v2.1/installed-applications?name__contains={user_app_first_request}"
        f"&siteIds={site_id}", headers=specific_headers).json()
    try:
        if initial_request_json["pagination"]["totalItems"] == 0: #skips the site if no results are found
            return
        else:
            app_nextcursor = initial_request_json['pagination']['nextCursor']
            insert_app_records_into_dict(initial_request_json)
    except KeyError:  #to avoid api errors from crashing the script
        site_name_with_error = get_site_name_from_id(site_id)
        print(f"error was found that belongs to the site {site_name_with_error}, here's the response: {initial_request_json}")


def get_application_second_request_and_beyond(user_app,site_id,url,specific_headers):
    """
    recieves cursor from first response. continues loop until no more cursors exist, and adds new apps in the process.
    :param user_app: user wanted app.
    :param site_id: site id currently in loop.
    :return: None. values are added directly to the class app dictionary.
    """
    global app_nextcursor
    while True:
        if app_nextcursor is None or app_nextcursor == "null" or app_nextcursor == "":
            break
        else:
            second_and_beyond_request_json = requests.get(
                f"{url}/web/api/v2.1/installed-applications?name__contains={user_app}"
                f"&siteIds={site_id}&cursor={app_nextcursor}", headers=specific_headers).json()
            app_nextcursor = second_and_beyond_request_json['pagination']['nextCursor']
            insert_app_records_into_dict(second_and_beyond_request_json)


def insert_app_records_into_dict(json_response):
    """
    inserts the dictionaries received from responses into the nested dictionary of the app.
    :param json_response: response in json format
    :return: None
    """
    global app_dictionary_counter
    if json_response["pagination"]["totalItems"] == 0:
        return
    else:
        for dictionary in json_response["data"]:
            app_dictionary[app_dictionary_counter] = {"Domain": dictionary["agentDomain"],
                                                                "Computer name": dictionary["agentComputerName"],
                                                                "OS": dictionary["osType"],
                                                                "App name": dictionary["publisher"],
                                                                "App publisher": dictionary["name"],
                                                                "App Version": dictionary["version"],
                                                                "App last update": dictionary["updatedAt"],
                                                                }
            app_dictionary_counter += 1


def nested_dict_to_csv(site_id):
    """
    :param site_id:
    :return:
    """
    site_name = get_site_name_from_id(site_id)
    field_names = ["Domain",
                   "Computer name",
                   "OS",
                   "App name",
                   "App publisher",
                   "App Version",
                   "App last update"]
    file_name = f'{site_name} - {user_chosen_app} Application Report.csv'
    if is_writing_the_csv_relevant_based_on_app_versions_in_dict(app_dictionary) is True:
    #skips opening a file if dictionary doesnt contain relevant lines of versions.
        with open(f'{file_name}', 'a+') as unique_site_file: # opens a csv file to populate wanted app.
            writer = csv.DictWriter(unique_site_file, field_names)
            writer.writeheader()
            for single_row in app_dictionary.values():
                if check_app_version(single_row) is True:
                    writer.writerow(single_row)
                pass
    else:
        pass


def check_app_version(single_dict):
    """
    recieves an app dictionary and checks if the app version is lower than the one inserted by the user.
    :return: True or False
    """
    if version.parse(single_dict['App Version']) \
            <= version.parse(user_chosen_app_most_updated_version):
        return True
    return False


def get_site_name_from_id(site_id):
    """
    retrieves the site name from the site id_name dictionary.
    :param site_id: site id (value in dictionary)
    :return: site name (key in dictionary)
    """
    for key, value in sites_name_id_dict.items():
        if value == site_id:
            return key


def len_of_app_dict_for_version_control():
    """
    support function to provide length of the app dictionary. this helps accessing the nested dictionary and check version control.
    :return:
    """
    return len(app_dictionary)


def is_writing_the_csv_relevant_based_on_app_versions_in_dict(current_app_dict):
    """
    checks the dictionary and sees if its even relevant creating a csv
    (to avoid situation where a csv is created and versions are above the ones inputted by the user.
    :param current_app_dict: current app dicionary in line
    :return: False (no need to create) True (needs to create)
    """
    relevance_counter = 0
    for site_dict in current_app_dict.values():
        if version.parse(site_dict['App Version']) \
                <= version.parse(user_chosen_app_most_updated_version):
            relevance_counter += 1
        else:
            pass
    if relevance_counter > 0:
        return True
    return False


if __name__ == "__main__":
    user_app = input("Please choose the application you want to check vs SentinelOne API:\n")
    user_app_version = input("Please choose the app version you want to have all"
                             " results below that version to be in the CSV\n")
    for authentication_dict in SENTINEL_ACCOUNT_DICT.values():
            url = authentication_dict["URL"]
            token = authentication_dict["API_TOKEN"]
            app_nextcursor = ""
            site_nextcursor = ""
            app_dictionary = {}
            app_dictionary_counter = 0
            sites_name_id_dict = {}
            headers = {f"Authorization": f"Apitoken "+token}
            site_name_id_dict = get_site_ids(url,headers)
            user_chosen_app_most_updated_version = user_app_version
            print("Creating csv files...\n")
            for site in site_name_id_dict.values():
                app_dictionary = {}
                app_dictionary_counter = 0
                get_applications_first_request(user_app, site, url,headers)
                get_application_second_request_and_beyond(user_app, site, url,headers)
                if len(app_dictionary) == 0: #skips opening a new file if dict is empty
                    pass
                else:
                    nested_dict_to_csv(site)
            print("All done :)\nif csv's are created, please send"
                  " the csv in the client's communication channel along with the threat intelligence report")
