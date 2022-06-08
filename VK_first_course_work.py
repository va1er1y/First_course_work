import time
import requests
import os
import json
from pprint import pprint
import sys

BASE_PATH = os.getcwd()
FILE_NAME_JSON = 'log_download.json'
FILE_NAME_TXT = 'log_download.txt'
path = os.path.join(BASE_PATH, FILE_NAME_JSON)
path_log_txt = os.path.join(BASE_PATH, FILE_NAME_TXT)


#Функция загрузки файлов логов на Я.диск
def upload_file_json (file_path_Yadisk, path_json, token, path_txt):
        headers = {'Content-Type': 'application/json', 'Authorization': f'OAuth {token}'}
        parameters_json = {"path":f'{file_path_Yadisk}{FILE_NAME_JSON}', 'overwrite' : 'true'}
        res_json = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload', headers = headers, params = parameters_json, timeout = 5)
        if res_json.status_code == 200:
            href = res_json.json()['href']
            requests.put (href, data=open(path_json, 'rb'))
        else:
            print(f'Ошибка загрузки {FILE_NAME_JSON} на Я.диск - {res_json.status_code}')

        parameters_txt = {"path":f'{file_path_Yadisk}{FILE_NAME_TXT}', 'overwrite' : 'true'}
        res_txt = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload', headers = headers, params = parameters_txt, timeout = 5)
        if res_txt.status_code ==200:
            href_txt =  res_txt.json()['href']
            requests.put (href_txt, data=open(path_txt, 'rb'))
        else:
            print(f'Ошибка загрузки {FILE_NAME_TXT} на Я.диск - {res_txt.status_code}')   

#Создание папки если, не создана для фотографий с именем "foto_vk_даты загрузки"
def create_new_catalog (token):
    time_requests_struct = time.localtime() 
    time_requests = time.strftime("%d_%m_%Y", time_requests_struct)
    headers = {'Content-Type': 'application/json', 'Authorization': f'OAuth {token}'}
    parameters_catalog = {"path": {f'foto_vk_{time_requests}'}}
    res =  requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers = headers, params = parameters_catalog, timeout = 5)
#Добавил проверку на ответы по status_code
    if str(res.status_code) not in '409, 202, 201, 200':
        sys.exit("Ошибка запроса создания папки на Я.диске - {response.status_code}")
    return [time_requests, headers, res.status_code]

#Копирование фотографий на Я.диск   
def upload_on_Yadisk(name_foto, url_foto, time, headers):
    parameters = {"path": {f'foto_vk_{time}/{name_foto}'}, 'url' : f'{url_foto}'}
    response = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload', headers = headers, params = parameters,timeout = 120)
    if str(response.status_code) not in '409, 202, 201, 200':
        sys.exit("Ошибка запроса при загрузки фотографий на Я.диск - {response.status_code}")
    return ((f'foto_vk_{time}/'), str(response.status_code))

#Сбор данных по фотографиям из нужного альбома в VK:
def find_vk_photo(path_for_json, user_id, albom_id, path_txt, quanity_foto):
    URL = 'https://api.vk.com/method/photos.get'
    params = {
        'access_token' :'a67f00c673c3d4b12800dd0ba29579ec56d804f3c5f3bbcef5328d4b3981fa5987b951cf2c8d8b24b9abd',
        'v' : '5.131',
        'owner_id' : {user_id},
        'album_id' : {albom_id},
        'photo_sizes' : '1',
        'extended' : '1',
        'count' : {quanity_foto}
        }
    res = requests.get(URL, params = params, timeout = 1).json()
#Создание папки
    time_head = create_new_catalog (TOKEN)
#Получение списка данных о каждой фотографии
    list_foto = res ['response']['items']
    json_list = []
    likes_list = []
    path_for_json_Yadisk = ''
    status_code_list = []
    time_requests_struct = time.localtime() 
    time_requests = time.strftime("%d_%m_%Y", time_requests_struct)
    for data_photo in list_foto:
        info_foto_for_upload = {"file_name": None, "size": None}
        likes = str(data_photo ['likes']['count'])
        info_foto_for_upload ['size'] = data_photo ['sizes'][-1]['type']
#Проверка имени, если такое количество лайков уже было при загрузке добавляем дату
        if likes not in likes_list:
            info_foto_for_upload ["file_name"] =  likes +'.jpg'
            likes_list.append(likes)
        else: 
            info_foto_for_upload ["file_name"] =  likes + ' likes ' + time_requests + '.jpg'
# Вызов функции для копировани файлов на Я.диск
        path_for_json_Yadisk = upload_on_Yadisk(info_foto_for_upload ["file_name"], data_photo ['sizes'][-1]['url'], time_head[0],time_head[1])
        status_code_list.append(path_for_json_Yadisk[1])
#Составление данных в json формате для будущего файла
        json_list.append(info_foto_for_upload)
    with open (path_for_json, "w", encoding='utf-8') as file_log_json:
        json.dump(json_list, file_log_json, indent= 4)
       
#Создание лога копирования фотографий
    with open (path_txt, "w", encoding='utf-8') as file_log_txt:
        file_log_txt.write(str(time_requests))
        file_log_txt.write('\n')
        file_log_txt.write('Статус код создания папки на Я.диске - ')
        file_log_txt.write(str(time_head[2]))
        file_log_txt.write('\n')
        for count, i in enumerate(json_list):
            file_log_txt.write(str(i['file_name']))
            file_log_txt.write(' - Статус код - ')
            file_log_txt.write(str(status_code_list[count]))
            file_log_txt.write('\n')
        return path_for_json_Yadisk[0]

#Функция выбора id альбома по названию введеного пользователем
def choose_alboms(name_albom, id_user, path_txt):
    URL = 'https://api.vk.com/method/photos.getAlbums'
    params = {
        'access_token' :'a67f00c673c3d4b12800dd0ba29579ec56d804f3c5f3bbcef5328d4b3981fa5987b951cf2c8d8b24b9abd',
        'v' : '5.131',
        'owner_id' : {id_user},
               }
    res = requests.get(URL, params = params, timeout = 5)
#Данная обработка на случай неправильного ID введеного пользователем.
    if 'error' in res.json():
        with open (path_txt, "w", encoding='utf-8') as file_log_txt:
            file_log_txt.write(f"Ошибка запроса поиска альбома с фотографиями {res.json()['error']['error_code']}. Подробности смотри на https://vk.com/dev/errors")
            file_log_txt.write('\n')
        sys.exit(f"Ошибка запроса поиска альбома с фотографиями {res.json()['error']['error_code']}. Подробности смотри на https://vk.com/dev/errors")
    if str(res.status_code) not in '409, 202, 201, 200':
        sys.exit("Ошибка запроса поиска альбома с фотографиями {res.status_code}")
    data_for_alboms = (res.json()['response']['items'])
    albom_id = None
    for title in data_for_alboms:
        if name_albom.lower() in title['title'].lower():
            albom_id = title['id']
            return albom_id
    if albom_id == None:
            sys.exit ('Не найден. Вероятно введено неправильное имя альбома') 
TOKEN = input('Введите токен Я.диска (полигона)') 
id_vk_user = input('Введите ваш id с VK.RU:  ')
choose_download = input('Откуда вы хотите загрузить фотографии: ')
quanity_foto_download = input('Количество фотографий для загрузки: ')
if quanity_foto_download.isdigit():
    if int(quanity_foto_download) < 0:
        quanity_foto_download = '5'
else:
    sys.exit ('Не правильный ввод количества фотографий')
lists = ['profile','профиль', 'профиля', 'с профиля', 'с аваторок', 'аватарки']
if choose_download.lower() in lists:
    path_downlod_Yadisk = find_vk_photo(path, id_vk_user, 'profile', path_log_txt, quanity_foto_download)
    upload_file_json(path_downlod_Yadisk, path, TOKEN, path_log_txt)
else:
    albom_id = choose_alboms(choose_download.lower(), id_vk_user, path_log_txt)
    path_downlod_Yadisk = find_vk_photo(path, id_vk_user, albom_id, path_log_txt, quanity_foto_download)
    upload_file_json(path_downlod_Yadisk, path, TOKEN, path_log_txt)

# py -m pip install -r requirements.txt