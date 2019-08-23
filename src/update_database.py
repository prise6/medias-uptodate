# -*- coding: utf-8 -*-

import urllib.request 
import base64
import ssl
import requests
from bs4 import BeautifulSoup
import datetime
import os
import json
import sys
import logging
from requests.packages.urllib3.exceptions import InsecureRequestWarning



from src import config

def request_server(config, uri, stream=False):
    return requests.get(uri,
    verify=False,
    stream=stream,
    auth=(config.get('server', 'login'), config.get('server', 'password')))


def parse_cells(config, uri, row):
    cells = row.find_all('td')
    
    type_file = cells[0].find('img')['alt'].strip()
    if type_file == '[VID]':
        type_file_id = 1
    elif type_file == '[DIR]':
        type_file_id = 2
    else:
        type_file_id = 3
    
    return [
        type_file_id, # 0. type de l'element
        os.path.join(uri, cells[1].find('a')['href'].strip()), # 1. url
        cells[1].find('a').text.strip(), # 2. nom
        datetime.datetime.strptime(cells[2].text.strip(), '%d-%b-%Y %H:%M'), # 3. date
        cells[3].text.strip() # 4. taille
    ]


def find_rows(config, uri):
    webpage = request_server(config, uri)

    webpage_parser = BeautifulSoup(webpage.text, 'html.parser')

    webpage_table = webpage_parser.find_all('table')

    webpage_row = webpage_table[0].find_all('tr')

    return webpage_row


def parse_rows(config, uri, rows):

    elements = list()
    length_elements = len(rows)

    for i in range(3, length_elements-1):
        elements.append(parse_cells(config, uri, rows[i]))

    # recupération des medias dans les repertoires
    directories = [el for el in elements if el[0] == 2]
    if directories:
        for dir in directories:
            rows = find_rows(config, dir[1])
            medias_tmp = parse_rows(config, dir[1], rows)
            elements += medias_tmp


    return elements

def filter_medias(config, elements):

    # filtres:
    ## medias seulement
    elements = [el for el in elements if el[0] == 1]
    ## datant d'une semaine
    today = datetime.datetime.now().date()
    elements = [el for el in elements if (today - el[3].date()).days <= config.getint('download', 'diff_days')]
    ## non présent
    already_downloaded = os.listdir(config.get('directory', 'medias'))
    elements = [el for el in elements if el[2] not in already_downloaded]

    return elements


def update_medias(config, elements):
    
    for medias in elements:
        fileout = os.path.join(config.get('directory', 'medias'), medias[2])

        with request_server(config, medias[1], stream=True) as req:
            req.raise_for_status()
            with open(fileout, 'wb') as openfile:
                for chunk in req.iter_content(chunk_size=config.getint('download', 'chunk_size')):
                    openfile.write(chunk)


if __name__ == '__main__':

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logging.basicConfig(filename=config.get('log', 'filename'), level=logging.DEBUG, format='%(asctime)s %(message)s')

    # récupérer les différents éléments présent sur le serveur
    rows = find_rows(config, config.get('server', 'uri'))
    elements = parse_rows(config, config.get('server', 'uri'), rows)

    # filtrer les éléments à télécharger
    elements = filter_medias(config, elements)

    # téléchargement
    update_medias(config, elements)

    # list
    infile = os.path.join(config.get('directory', 'datas'), 'elements')
    with open(infile, 'w+') as outfile:
        for el in elements:
            for item in el:
                outfile.write(str(item))
                outfile.write(", ")
            outfile.write("\n") 
    