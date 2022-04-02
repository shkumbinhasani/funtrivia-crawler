import json
import os
import re
import sqlite3
import requests
from bs4 import BeautifulSoup
import copy

con = sqlite3.connect('database.db')
cur = con.cursor()


def scrape_quiz(url):
    x = re.search("\-([0-9]*).html", url)
    if os.path.isfile("quizes/" + str(x.group(1)) + ".json"):
        print("Already crawled")
        return

    response = requests.get(url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                              "like Gecko) Chrome/100.0.4896.60 Safari/537.36 "
                            })

    if "Multiple Choice" not in response.text:
        print("Not multiple choice")
        return
    soup = BeautifulSoup(response.text, 'html.parser')

    quiz_model = {
        "id": "",
        "name": "",
        "type": "",
        "difficulty": "Very Easy",
        "tags": [],
        "questions": []
    }

    question_model = {
        "text": "",
        "correct": "",
        "options": [],
        "explanation": ""
    }

    question_divs = soup.findAll('div', attrs={"class": "playquiz_qnbox"})
    answers_divs = soup.findAll('div', attrs={"itemprop": "acceptedAnswer"})
    quiz_id = soup.find('input', attrs={"name": "qid"})["value"]

    tags_tag = soup.findAll('span', attrs={"property": "name"})
    jsun = soup.find("script", attrs={"type": "application/ld+json"})
    author = (json.loads(jsun.text)["author"]["name"])
    try:
        cur.execute("INSERT INTO authors VALUES (null, ?)", (author,))
    except:
        print("Author exists")
    title = soup.find('title')

    quiz_model["name"] = title.text
    quiz_model["id"] = quiz_id

    tags = []
    for tagTag in tags_tag:
        tags.append(tagTag.text)

    quiz_model["tags"] = tags

    i = 0

    for questionDiv in question_divs:
        question_object = copy.copy(question_model)

        text = questionDiv.find("div", {"class": "playquiz_qntxtbox"}).find("b").text

        question_object["text"] = re.sub('^[0-9]*. ', '', text)

        correct = answers_divs[i].find("b").text
        question_object["correct"] = correct
        question_object["options"] = []
        correct_and_explanation = answers_divs[i].text
        question_object["explanation"] = correct_and_explanation

        options = questionDiv.findAll("input", {"type": "radio"})
        for option in options:
            if correct != option["value"]:
                question_object["options"].append(option["value"])
        quiz_model["questions"].append(question_object)
        i += 1

    print(json.dumps(quiz_model))
    with open('quizes/' + str(quiz_id) + '.json', 'x') as outfile:
        json.dump(quiz_model, outfile)


def scrape_by_search(keyword):
    response = requests.get("https://www.funtrivia.com/search2_act.cfm?type=quizzes&searchstring=" + keyword,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                              "like Gecko) Chrome/100.0.4896.60 Safari/537.36 "
                            })

    soup = BeautifulSoup(response.text, 'html.parser')
    anchors = soup.findAll("a", {"class": "qldesc"})
    for anchor in anchors:
        scrape_quiz("https://www.funtrivia.com/" + anchor["href"])
        print(anchor["href"])


def all_quizzes_of_authors():
    authors = cur.execute("SELECT username from authors ORDER BY RANDOM()").fetchall()
    for author in authors:
        try:
            all_quizzes_of_author(author[0])
        except:
            print("Failed")


def all_quizzes_of_author(author):
    list_from = 1
    while True:
        response = requests.get(
            "https://www.funtrivia.com/profile_quizzes.cfm?player=" + author + "&listfrom=" + str(list_from),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                              "like Gecko) Chrome/100.0.4896.60 Safari/537.36 "
            })

        soup = BeautifulSoup(response.text, 'html.parser')
        quizzes = soup.findAll("a", {"class": "qldesc"})
        for quizz in quizzes:
            try:
                scrape_quiz("https://www.funtrivia.com/" + quizz["href"])
            except:
                print("Failed scoping Quiz")
            print(quizz["href"])

        if len(quizzes) < 50:
            break
        list_from = list_from + 50


# scrape_by_search("DC Comics")
all_quizzes_of_authors()
# scrape_quiz("https://www.funtrivia.com/trivia-quiz/General/Madges-Magic-Places-399177.html")
con.commit()
