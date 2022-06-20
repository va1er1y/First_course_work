import time
import requests
import os
import json
from pprint import pprint
import sys
import configparser

class Ya_disk():
    """ 
    class Ya_disk

    Данный класс выполняет загрузку фотографий и log файлына яндекс диск пользователя. 
    Данный класс является родительским для vk_ru. Методы данного класса используются в классе vk_ru.

    Атрибуты
    --------
    Входных атрибутов нет

    Методы
    ------
        read_token_ya_disk 
        Чтение токена пользователя с документа .ini для доступа на Я.диск

        Возвращает значение токена : str
        ------
        upload_file_json
        Запись log файлов на Я.диск
    
        Параметры
        file_path_Yadisk : str #Путь сохранения на Я.диске
        path_json : str        #Путь расположения на ПК пользователя файла json
        path_txt : str         #Путь расположения на ПК пользователя log файла
        --------
        create_new_catalog
        Создание каталога на Я.диске с датой загрузки. Если католог существует - действие игнорируется сервером Я.диска
        --------
        upload_on_Yadisk
        Загрузка фотографий на Я.диск.
    
        Параметры
            name_foto : str #имя фотографии
            url_foto : str  #ссылка для скачивания на Я.диск
            time : str      #дата для определения пути каталога  (смотри метод  create_new_catalog)
            headers : str   #заголовок для http запроса

        Возвращает имя загруженного фото и статус код : str 
    """
#Функция загрузки файлов логов на Я.диск
    def read_token_ya_disk (self):
        config = configparser.ConfigParser()  # создаём объекта парсера
        config.read("start_data.ini")  # читаем конфиг
        return str(config ["Poligon"]["token_poligon"].strip('"'))
    
    def upload_file_json (self, file_path_Yadisk, path_json, path_txt):
        FILE_NAME_JSON = 'log_download.json'
        FILE_NAME_TXT = 'log_download.txt'
        headers = {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.read_token_ya_disk()}'}
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
            a = requests.put (href_txt, data=open(path_txt, 'rb'))
        else:
            print(f'Ошибка загрузки {FILE_NAME_TXT} на Я.диск - {res_txt.status_code}')   

    def create_new_catalog (self):
        time_requests_struct = time.localtime() 
        time_requests = time.strftime("%d_%m_%Y", time_requests_struct)
        headers = {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.read_token_ya_disk()}'}
        parameters_catalog = {"path": {f'foto_vk_{time_requests}'}}
        res =  requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers = headers, params = parameters_catalog, timeout = 5)
        if str(res.status_code) not in '409, 202, 201, 200':
            sys.exit("Ошибка запроса создания папки на Я.диске - {response.status_code}")
        return [time_requests, headers, res.status_code]

    def upload_on_Yadisk (self, name_foto, url_foto, time, headers):
        parameters = {"path": {f'foto_vk_{time}/{name_foto}'}, 'url' : f'{url_foto}'}
        response = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload', headers = headers, params = parameters,timeout = 120)
        if str(response.status_code) not in '409, 202, 201, 200':
            sys.exit("Ошибка запроса при загрузки фотографий на Я.диск - {response.status_code}")
        return ((f'foto_vk_{time}/'), str(response.status_code))

class vk_ru(Ya_disk):
    """
    class vk_ru(Ya_disk)
    Данный класс работает с фотографиями пользователя  - выбор альбома, получение ссылок для 
    скачивания фотографий

    Атрибуты
    --------
        username_or_id : str #имя или id пользователя
        name_album : str     #имя альбома для загрузки фотографий
        quanity_foto : str   #количество фотографий для загрузки, если не указано - по умолчанию 5

    Методы
    -------
        path_for_file_txt_log
        Получение пути расположения log файла

        Возвращает готовый абсолютный путь : str
        -------
        path_for_file_json
        Получение пути расположения log файла

        Возвращает готовый абсолютный путь : str
        --------
        read_token_vk
        Чтение токена пользователя с документа .ini для доступа на VK

        Возвращает токен : str
        ---------
        find_in_from_user_name
        Проверка id введенного пользователем, если это username - определение id по username
        
        Возвращает id пользователя : str
        ----------
        choose_alboms
        Получение id альбома пользователя по имени

        Возвращает id альбома пользователя : str
        ----------
        find_vk_photo
        Основная функция для поиска фотографий пользователя, формирование файлов json, txt.
        Вызов методов класса Ya_disk для загрузки файлов и фотографий.
        
    """  

    def __init__ (self, username_or_id, name_album, quanity_foto):
        self.username_or_id = username_or_id
        self.name_album = name_album
        self.quanity_foto = quanity_foto
        if quanity_foto.isdigit():
            if int(quanity_foto) < 0:
                self.quanity_foto = '5'
        else:
            self.quanity_foto = '5'

    def path_for_file_txt_log (self):
        BASE_PATH = os.getcwd()
        FILE_NAME_TXT = 'log_download.txt'
        return os.path.join(BASE_PATH,FILE_NAME_TXT)

    def path_for_file_json (self):
        BASE_PATH = os.getcwd()
        FILE_NAME_JSON = 'log_download.json'
        return os.path.join(BASE_PATH, FILE_NAME_JSON)
        
    def read_token_vk (self):
        config = configparser.ConfigParser()
        config.read("start_data.ini")
        return str(config ["VK"]["token_vk"].strip('"'))

    def find_in_from_user_name(self):
        if self.username_or_id and self.username_or_id.strip():
                if not self.username_or_id.isdigit():
                    URL = 'https://api.vk.com/method/users.get'
                    params = {
                                   'access_token' :{self.read_token_vk()},
                                   'v' : '5.131',
                                   'user_ids' : {self.username_or_id}
                                    }
                    res = requests.get(URL, params = params, timeout = 1).json()
                    if res['response'] == []:
                        sys.exit("Неверно введено id или username")
                    self.username_or_id =  str(res['response'][0]['id'])
                else:
                    return str(self.username_or_id)
        else:
            sys.exit("Неверно введен id или username")  
        return str(self.username_or_id)
    def choose_alboms(self):
        if not self.name_album:
            sys.exit("Не введено имя альбома")
        lists = ['profile','профиль', 'профиля', 'с профиля', 'с аваторок', 'аватарки']
        if self.name_album.lower() in lists:
            return ('profile')
        else:
            URL = 'https://api.vk.com/method/photos.getAlbums'
            params = {
                      'access_token' :{self.read_token_vk()},
                      'v' : '5.131',
                      'owner_id' : {self.find_in_from_user_name()},
                      }
            res = requests.get(URL, params = params, timeout = 5)
            if 'error' in res.json():
                with open (self.path_for_file_txt_log(), "w", encoding='utf-8') as file_log_txt:
                    file_log_txt.write(f"Ошибка запроса поиска альбома с фотографиями {res.json()['error']['error_code']}. Подробности смотри на https://vk.com/dev/errors")
                    file_log_txt.write('\n')
                sys.exit(f"Ошибка запроса поиска альбома с фотографиями {res.json()['error']['error_code']}. Подробности смотри на https://vk.com/dev/errors")
            if str(res.status_code) not in '409, 202, 201, 200':
                sys.exit("Ошибка запроса поиска альбома с фотографиями {res.status_code}")
            data_for_alboms = (res.json()['response']['items'])
            albom_id = None
            for title in data_for_alboms:
                if self.name_album.lower() in title['title'].lower():
                    albom_id = title['id']
            if albom_id == None:
                sys.exit ('Не найден. Вероятно введено неправильное имя альбома') 
            return albom_id
    def find_vk_photo(self):

        URL = 'https://api.vk.com/method/photos.get'
        params = {
            'access_token' : {self.read_token_vk()},
            'v' : '5.131',
            'owner_id' : {self.find_in_from_user_name()},
            'album_id' : {self.choose_alboms()},
            'photo_sizes' : '1',
            'extended' : '1',
            'count' : {self.quanity_foto}
            }
        res = requests.get(URL, params = params, timeout = 1).json()
        time_head = Ya_disk.create_new_catalog (self)
        list_foto = res ['response']['items']
        json_list = []
        likes_list = []
        names_foto_list = []
        path_for_json_Yadisk = ''
        status_code_list = []
        time_requests_struct = time.localtime() 
        time_requests = time.strftime("%d_%m_%Y", time_requests_struct)
        for data_photo in list_foto:
            info_foto_for_upload = {"file_name": None, "size": None}
            likes = str(data_photo ['likes']['count'])
            info_foto_for_upload ['size'] = data_photo ['sizes'][-1]['type']
            if likes not in likes_list:
                info_foto_for_upload ["file_name"] =  likes +'.jpg'
                likes_list.append(likes)
            else:
                time_create_struct = time.localtime() 
                time_create = time.strftime("%H_%M_%S", time_create_struct)
                info_foto_for_upload ["file_name"] =  likes + ' likes ' + time_create + '.jpg'
                if info_foto_for_upload ["file_name"] in names_foto_list:
                    time.sleep(1)
                    time_create_struct = time.localtime() 
                    time_create = time.strftime("%H_%M_%S", time_create_struct)
                    info_foto_for_upload ["file_name"] =  likes + ' likes ' + time_create + '.jpg'
            names_foto_list.append(info_foto_for_upload["file_name"])
            path_for_json_Yadisk = Ya_disk.upload_on_Yadisk (self, info_foto_for_upload ["file_name"], data_photo ['sizes'][-1]['url'], time_head[0],time_head[1])
            status_code_list.append(path_for_json_Yadisk[1])
            json_list.append(info_foto_for_upload)
        with open (self.path_for_file_json(), "w", encoding='utf-8') as file_log_json:
            json.dump(json_list, file_log_json, indent= 4)
        with open (self.path_for_file_txt_log(), "w", encoding='utf-8') as file_log_txt:
            file_log_txt.write(str(time_requests))
            file_log_txt.write('\n')
            file_log_txt.write('Статус код создания папки на Я.диске - ')
            file_log_txt.write(str(time_head[2]))
            file_log_txt.write('\n')
            file_log_txt.write('Id альбома из которого загружали - ')
            file_log_txt.write(str(self.choose_alboms()))
            file_log_txt.write('\n')
            for count, i in enumerate(json_list):
                file_log_txt.write(str(i['file_name']))
                file_log_txt.write(' - Статус код - ')
                file_log_txt.write(str(status_code_list[count]))
                file_log_txt.write('\n')
        Ya_disk.upload_file_json (self, path_for_json_Yadisk[0], self.path_for_file_json(), self.path_for_file_txt_log())

def main(id_vk_user, choose_download, quanity_foto_download):
    """
    Функция создания одного экземпляра класса vk_ru и вызова первоначального метода для выполнения 
    загрузки фотографий
        Параметры:
            id_vk_user : str
            choose_download : str
            quanity_foto_download : str

    
    """
    user_vk_download = vk_ru(id_vk_user, choose_download, quanity_foto_download)
    user_vk_download.find_vk_photo()

if __name__ == "__main__":
    id_vk_user = input('Введите Ваш id или username VK.RU:  ')
    choose_download = input('Укажите имя альбома для загрузки фотографий: ')
    quanity_foto_download = input('Укажите количество фотографий для загрузки: ')
    main(id_vk_user, choose_download, quanity_foto_download)

# pprint (Ya_disk.__doc__)
# print()
# pprint (vk_ru.__doc__)
# py -m pip install -r requirements.txt