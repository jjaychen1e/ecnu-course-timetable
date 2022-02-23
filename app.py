from flask import Flask, request, Response
from typing import *
from crawler import Crawler

app = Flask(__name__)


@app.route('/ecnu-service/course-calendar', methods=['GET'])
def hello_world():
    username = request.args.get('username')
    password = request.args.get('password')
    year = request.args.get('year')
    semester_index = request.args.get('semester_index')
    if not semester_index:
        semester_index = request.args.get('semesterIndex')

    if username is None or password is None or year is None or semester_index is None:
        return Response("Missing parameters", status=400)

    if year.isdigit() is False or semester_index.isdigit() is False:
        return Response("year/semester_index should be a number", status=400)

    crawler = Crawler(username=username, password=password, year=int(year), semester_index=int(semester_index))
    result = crawler.crawl()
    if not result[0]:
        response = Response()
        response.content_encoding = "utf-8"
        response.data = "Failed to fetch calendar.".encode('utf-8')
        return response

    response = Response()
    response.content_type = "text/calendar"
    response.headers['Content-Disposition'] = 'attachment; filename="calendar.ics"'
    response.data = result[1].encode('utf-8')
    return response


if __name__ == '__main__':
    app.run(port=8181)
