#!/usr/bin/env python3
import json
import requests
import zipfile
import io
from itertools import zip_longest

"""
archive_observations.py creates or updates user backups of observations on the Mushroom Observer website.
"""

# Update these 2 vars before executing the script
user = "" # username or id to archive the observations of
backup_archive = f"{user}-mo-bkp.zip" # name of the archive to create or update, ex. "4786" or "alsmith"

# Only change these if you know what you're doing
image_size = "orig" # string one of 480, 640, 1280, orig
page_size = 10


def isdir(z, name):
    """ Find out if we already have a directory for an observation """
    return any(x.startswith("%s/" % name) for x in z.namelist())

def get_user_observation_ids(user):
    """ Get the list of Observation IDs belonging to the User """
    user_observations_url = f"https://mushroomobserver.org/api/observations?format=json&user={user}"
    # Get observations by the user
    response = requests.get(user_observations_url)
    # If we got them
    if response.status_code == 200:
        if response.json()['number_of_pages'] == 1:
            # get the IDs
            observation_ids = response.json()['results']
            return observation_ids
        else:
            for page in response.json()['number_of_pages']:
                user_observations_url = f"https://mushroomobserver.org/api/observations?format=json&user={user}&page={page}"
                # Get observations by the user
                r = requests.get(user_observations_url)
    else:
        # or complain and short circuit
        print(f"Couldn't find MO user: {user}")
        exit(1)

def get_user_observation_data(user_ids):
    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=0)
    # get user's observations
    ids = get_user_observation_ids(f"{user}")
    obs_urls = []
    for group in grouper(ids, page_size):
        observation_url = f"https://mushroomobserver.org/api/observations?format=json&detail=high&id={','.join(str(i) for i in group)}"
        obs_urls.append(observation_url)
    data = [requests.get(url).json()['results'] for url in obs_urls]
    flat_data = [item for sublist in data for item in sublist]
    return flat_data

def get_image(image_id, i_size=image_size):
    """ Get a given image by ID"""
    image_url = f"https://mushroomobserver.org/images/{i_size}/{image_id['id']}.jpg"
    filename = image_url.split("/")[-1]
    r = requests.get(image_url, stream=True)
    # if we got the image
    if r.status_code == 200:
        # decode and return it
        r.raw.decode_content = True
        return filename, r.raw
    else:
        print(f'Image {image_url} could not be retrieved')


def get_observation(id):
    """ Archive an observation by ID """
    # URL to fetch from
    observation_url = f"https://mushroomobserver.org/api/observations?format=json&detail=high&id={id}"
    # fetch
    response = requests.get(observation_url)
    # if we got an ob
    if response.status_code == 200:
        # iterate over any pictures
        print(f"Archiving: {id}.json")
        zip.writestr(f"{id}/{id}.json", json.dumps(*response.json(), sort_keys=True, indent=4))
        for image in response.json()['results'][0]['images']:
            # add them to the zip archive in a folder named {id}, where ID is the observation ID
            print(f"Archiving: {image['id']}.jpg")
            img_name, img = get_image(image)
            zip.writestr(f"{id}/{img_name}", img.read())
    else:
        # or complain we can't
        print(f"Could not backup observation: {id}")


# Open the zipfile
with zipfile.ZipFile(backup_archive, 'a', compression=zipfile.ZIP_STORED) as zip:
    zip.writestr(f"{user}.json", json.dumps(get_user_observation_data(get_user_observation_ids(user)), indent=4))