import types
import psycopg2
import requests
from pywebio import input, output, start_server
from pywebio.input import select

# Создание таблицы
try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='1234',
        host='127.0.0.1',
        port='5432'
    )

    print("Подключение к базе данных выполнено")

    try:
        cur = conn.cursor()

        cur.execute("""CREATE TABLE vacancies (
        id SERIAL PRIMARY KEY, 
        hh_id VARCHAR(255), 
        name VARCHAR(255), 
        city VARCHAR(255), 
        company VARCHAR(255), 
        url TEXT, 
        description VARCHAR(255), 
        salary VARCHAR(255)
        );""")

        conn.commit()

        for x in range(1, 21):
            cur.execute("""INSERT INTO vacancies (hh_id, name, city, company, url, description, salary) 
                VALUES ('', '', '', '', '', '', '')""")

        print("таблица создана")

        conn.commit()

    except Exception as excep:
        print("Таблица с таким названием уже есть, или есть такие же строки")

except Exception as ex:
    print("не подключилась")
    print(ex)


# Функция получения вакансий
def get_vacancies(keyword, city):

    url = "https://api.hh.ru/vacancies"

    if city == 'Москва':
        params = {
            "text": keyword,
            "area": 1,  # (1 - Москва)
            "per_page": 20,
        }
        headers = {
            "User-Agent": "Your User Agent",
        }

    elif city == 'Санкт-Петербург':
        params = {
            "text": keyword,
            "area": 2,  # (2 - Санкт-Петербург)
            "per_page": 20,
        }
        headers = {
            "User-Agent": "Your User Agent",
        }

    # Парсинг вакансий
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        vacancies = data.get("items", [])
        num_vacancies = len(vacancies)

        if num_vacancies > 0:

            for i in range(len(vacancies)):
                salary_null: int = 0
                from_salary: int = 0
                to_salary: int = 0

                # Получение параметров
                vacancy_id = vacancies[i]["id"]

                vacancy_title = vacancies[i]["name"]

                vacancy_url = vacancies[i]["alternate_url"]

                company_name = vacancies[i]["employer"]["name"]

                if not (isinstance(vacancies[i]["snippet"]["responsibility"], types.NoneType)):
                    vacancy_desc = vacancies[i]["snippet"]["responsibility"]
                else:
                    vacancy_desc = "не указано"

                vacancy_area = vacancies[i]["area"]["name"]

                if not (isinstance(vacancies[i]["salary"], types.NoneType)):

                    if not (isinstance(vacancies[i]["salary"]["from"], types.NoneType)):
                        from_salary = vacancies[i]["salary"]["from"]

                    if not (isinstance(vacancies[i]["salary"]["to"], types.NoneType)):
                        to_salary = vacancies[i]["salary"]["to"]

                else:
                    salary_null = "не указана"


                if from_salary and to_salary:
                    salary = f"от {from_salary or ''} до {to_salary or ''}"

                elif from_salary:
                    salary = f"от {from_salary or ''}"

                elif to_salary:
                    salary = f"до {to_salary}"

                else:
                    salary = salary_null



                # Вывод вакансий по запросу пользователя
                output.put_text(f"ID: {vacancy_id}")
                output.put_text(f"Title: {vacancy_title}")
                output.put_text(f"City: {vacancy_area}")
                output.put_text(f"Company: {company_name}")
                output.put_link(name="URL", url=vacancy_url)
                output.put_text(f"Description: {vacancy_desc}")
                output.put_text(f"Salary: {salary}")

                if i < num_vacancies - 1:
                    output.put_text("----------------------------------------------------")

                # Обновление данных таблицы
                try:

                    conn = psycopg2.connect(
                        dbname='postgres',
                        user='postgres',
                        password='1234',
                        host='127.0.0.1',
                        port='5432'
                    )

                    cur = conn.cursor()

                    update_query = """UPDATE vacancies SET hh_id=%s, name=%s, city=%s, company=%s, url=%s, description=%s, salary=%s WHERE id=%s"""

                    record_to_update = (vacancy_id, vacancy_title, vacancy_area, company_name, vacancy_url, vacancy_desc, salary, i+1)

                    cur.execute(update_query, record_to_update)

                    conn.commit()

                    conn.close()


                except Exception as e:
                    print(f"Ошибка при добавлении вакансии: {e}")
                    conn.rollback()

        # Если вакансий нет:
        else:
            output.put_text("Нет вакансий по данному запросу")

    else:
        output.put_text(f"Request failed with status code: {response.status_code}")




# Поиск вакансий по запросу пользователя
def search_vacancies():
    keyword = input.input("Введите название вакансии:", type=input.TEXT)
    city = select("Выберите город:", ['Москва', 'Санкт-Петербург'])
    output.clear()
    output.put_text("Вакансии по вашему запросу:")
    output.put_text("----------------------------------------------------")
    get_vacancies(keyword, city)


if __name__ == '__main__':
    start_server(search_vacancies, port=8080)
