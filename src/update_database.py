# -*- coding: utf-8 -*-

import urllib.request 
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64
import ssl
import requests
from bs4 import BeautifulSoup
import datetime
import os
import json
import sys
import logging
import click
import re

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

def filter_medias(config, elements, limit, names):
    # filtres:
    ## medias seulement
    elements = [el for el in elements if el[0] == 1]

    ## non présent
    already_downloaded = read_already_download(config)
    elements = [el for el in elements if el[2] not in already_downloaded]
    
    if names:
        names_elements = []
        for name in names:
            name = name.replace('.', '\.')
            names_elements += [el for el in elements if re.match(name, el[2], re.I)]
        print(names_elements)
        exit()
        return names_elements
        
    ## datant d'une semaine
    today = datetime.datetime.now().date()
    elements = [el for el in elements if (today - el[3].date()).days <= config.getint('download', 'diff_days')]

    if limit:
        elements = elements[:limit]

    return elements


def update_medias(config, elements):
    
    for medias in elements:
        fileout = os.path.join(config.get('directory', 'downloads'), medias[2])

        with request_server(config, medias[1], stream=True) as req:
            req.raise_for_status()
            with open(fileout, 'wb') as openfile:
                for chunk in req.iter_content(chunk_size=config.getint('download', 'chunk_size')):
                    openfile.write(chunk)
                    if config.getint('download', 'test') == 1:
                        break
                add_to_already_downloaded(config, medias)


def add_to_already_downloaded(config, element):

    infile = os.path.join(config.get('download', 'already_downloaded'))
    with open(infile, 'a') as outfile:
        outfile.write(str(element[2]))
        outfile.write("\n")


def read_already_download(config):

    return [line.strip() for line in open(config.get('download', 'already_downloaded'), 'r').readlines()]


@click.command()
@click.option('--limit', default=None, show_default=True, type=int)
@click.argument('names', nargs=-1)
def main(limit, names):

    # logs
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logging.basicConfig(filename=config.get('log', 'filename'), level=logging.DEBUG, format='%(asctime)s %(message)s')

    # récupérer les différents éléments présent sur le serveur
    rows = find_rows(config, config.get('server', 'uri'))
    elements = parse_rows(config, config.get('server', 'uri'), rows)

    # filtrer les éléments à télécharger
    elements = filter_medias(config, elements, limit, names)

    # téléchargement
    update_medias(config, elements)


if __name__ == '__main__':
    main()
