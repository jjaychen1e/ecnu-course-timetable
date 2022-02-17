import uuid
import pytz
import requests
import pytesseract
import os
import re
import execjs
from icalendar import Calendar, Event, Alarm

from typing import *
from PIL import Image
from time import time
from lxml import etree
from datetime import datetime, timedelta, timezone

from configurations.configurations import *
from models.course import Course
from models.lesson import Lesson
from utils.get_rsa import get_rsa_javascript_code

requests.packages.urllib3.disable_warnings()


class Crawler:
    username: str
    password: str
    year: int
    semester_index: int
    s: requests.Session

    def __init__(self, *, username: str, password: str, year: int,
                 semester_index: int) -> None:  # How to force user to input user_name and password?
        self.s: requests.Session = requests.Session()
        self.username = username
        self.password = password
        self.year = year
        self.semester_index = semester_index

    def get_semester_id(self) -> str:
        return str(801 + (self.year - 2019) * 96 + (self.semester_index - 1) * 32)

    def get_code(self) -> str:
        response = self.s.get(ECNU_CODE_URL)
        tmp_code_file_name: str = f"{time()}.png"
        code: str
        with open(tmp_code_file_name, "wb") as f:
            f.write(response.content)
            code = pytesseract.image_to_string(Image.open(tmp_code_file_name))[:4]
            os.remove(tmp_code_file_name)

        return code

    def get_rsa(self) -> str:
        get_rsa = execjs.compile(get_rsa_javascript_code)
        return get_rsa.call('strEnc', self.username + self.password, '1', '2', '3')

    @staticmethod
    def check_login_status(*, content: str) -> bool:
        if content.count('访问被拒绝') > 0:
            return False
        dom = etree.HTML(content)
        if len(dom.xpath("//*[@id='errormsg']")) == 0:
            return True
        else:
            return False

    def login(self) -> bool:
        code = self.get_code()
        rsa = self.get_rsa()
        data = {
            "code": code,
            "rsa": rsa,
            "ul": len(self.username),
            "pl": len(self.password),
            "lt": "LT-1665926-4VCedaEUwbuDuAPI7sKSRACHmInAcl-cas",
            "execution": "e1s1",
            "_eventId": "submit"
        }
        response = self.s.get(ECNU_PORTAL_URL, params=data, verify=False)
        return self.check_login_status(content=response.content.decode('utf-8'))

    def get_ids(self) -> str:
        response = self.s.get(ECNU_IDS_URL)
        content = response.content.decode('utf-8')
        match_results = re.findall(r"bg\.form\.addInput\(form,\"ids\",\"([0-9]*)", content)
        if len(match_results) == 0:
            return ""
        else:
            return match_results[0]

    def get_courses(self, *, ids: str) -> List[Course]:
        data = {
            "ignoreHead": "1",
            "setting.kind": "std",
            "startWeek": "1",
            "semester.id": self.get_semester_id(),
            "ids": ids,
        }
        response = self.s.get(ECNU_COURSE_TABLE_URL, params=data)
        content = response.content.decode('utf-8')

        course_id_list: List[str] = []
        course_name_list: List[str] = []
        course_instructor_list: List[str] = []
        course_list: List[Course] = []
        skipped_course_index_list: List[int] = []

        course_type_match_results: List[str] = re.findall(r"</a></td>\n<td>(.*?)</td><td>", content)
        for index, course_type_match_result in enumerate(course_type_match_results):
            if course_type_match_result == "&#30740;&#31350;&#29983;&#35838;&#31243;":
                # 存在研究生课程, 跳过
                skipped_course_index_list.append(index)

        course_id_match_results: List[str] = re.findall(r"<td>([A-Z]+[0-9]+\..{2})</td>", content)
        for index, course_id_match_result in enumerate(course_id_match_results):
            if index not in skipped_course_index_list:
                course_id_list.append(course_id_match_result)

        course_name_match_results: List[str] = re.findall(r"\">(.*)</a></td>", content)
        for index, course_name_match_result in enumerate(course_name_match_results):
            if index not in skipped_course_index_list:
                course_name_list.append(course_name_match_result)

        course_instructor_match_results: List[str] = re.findall(r"\t\t<td>(.*?)</td>\n\t", content)
        for index, course_instructor_match_result in enumerate(course_instructor_match_results):
            if index not in skipped_course_index_list:
                course_instructor_list.append(course_instructor_match_result.replace("<br/>", " "))

        if len(course_id_list) == len(course_name_list) == len(course_instructor_list):
            if len(course_id_list) == 0:
                raise Exception("课程信息为空")

            for course_id, course_name, course_instructor in zip(course_id_list, course_name_list,
                                                                 course_instructor_list):
                course_list.append(
                    Course(course_id=course_id, course_name=course_name, course_instructor=course_instructor))
        else:
            raise Exception("课程信息处理出错")

        return course_list

    def get_lessons(self, course: Course) -> List[Lesson]:
        data = {
            "lesson.semester.id": self.get_semester_id(),
            "lesson.no": course.course_id,
        }
        response = self.s.get(ECNU_COURSE_QUERY_URL, params=data)
        content = response.content.decode('utf-8')
        week_match_results = re.findall(r"<td>(星期.*?)</td>", content)
        if len(week_match_results) == 0:
            # e.g., 毕业实习
            return []

        lessons: List[Lesson] = []

        week_lines = week_match_results[0].split("<br>")
        for week_line in week_lines:
            week_string_chinese = week_line[:3]

            # Why not use a dictionary? Because copilot is a genius.
            if week_string_chinese == "星期一":
                day_offset = 0
            elif week_string_chinese == "星期二":
                day_offset = 1
            elif week_string_chinese == "星期三":
                day_offset = 2
            elif week_string_chinese == "星期四":
                day_offset = 3
            elif week_string_chinese == "星期五":
                day_offset = 4
            elif week_string_chinese == "星期六":
                day_offset = 5
            elif week_string_chinese == "星期日":
                day_offset = 6
            else:
                raise Exception("课程信息解析出错")

            lesson_time_offset_match_results = re.search(r"(\d+)-(\d+)", week_line)
            if len(lesson_time_offset_match_results.groups()) != 2:
                raise Exception("课程信息解析出错")

            lesson_time_offset_begin = int(lesson_time_offset_match_results.group(1))
            lesson_time_offset_end = int(lesson_time_offset_match_results.group(2))

            # 课程星期偏移值
            week_offset_list: [int] = []
            # 单次周的课
            single_week_match_results = re.findall(r"\[\d+]", week_line)
            for single_week_match_result in single_week_match_results:
                week_offset_list.append(int(single_week_match_result[1:-1]))

            other_week_match_results = re.findall(r"单?双?\[\d+-\d+]", week_line)
            for other_week_match_result in other_week_match_results:
                week_info_match_results = re.search(r"\[(\d+)-(\d+)]", other_week_match_result)
                if len(week_info_match_results.groups()) != 2:
                    raise Exception("课程信息解析出错")
                week_offset_begin = int(week_info_match_results.group(1))
                week_offset_end = int(week_info_match_results.group(2))

                if other_week_match_result[0] == "单" or other_week_match_result[0] == "双":
                    skip: bool = False
                    for week_offset in range(week_offset_begin, week_offset_end + 1):
                        if not skip:
                            week_offset_list.append(week_offset)
                            skip = True
                        else:
                            skip = False
                else:
                    for week_offset in range(week_offset_begin, week_offset_end + 1):
                        week_offset_list.append(week_offset)

            location = re.sub(r".*]", "", week_line)
            location = re.sub(r",", " ", location)
            location = location.strip()

            semester_begin_date_str = SEMESTER_DATE[str(self.year)][str(self.semester_index)] + " 00:00:00"
            semester_begin_date = datetime.strptime(semester_begin_date_str, "%Y-%m-%d %H:%M:%S")
            semester_begin_date = semester_begin_date.replace(tzinfo=pytz.timezone("Asia/Shanghai"))

            lesson_begin_time_hour_minute = LESSON_START_TIME[str(lesson_time_offset_begin)]
            lesson_begin_datetime_standard = semester_begin_date + timedelta(days=day_offset,
                                                                             hours=lesson_begin_time_hour_minute[0],
                                                                             minutes=lesson_begin_time_hour_minute[1])
            lesson_end_time_hour_minute = LESSON_END_TIME[str(lesson_time_offset_end)]
            lesson_end_datetime_standard = semester_begin_date + timedelta(days=day_offset,
                                                                           hours=lesson_end_time_hour_minute[0],
                                                                           minutes=lesson_end_time_hour_minute[1])
            for week_offset in week_offset_list:
                lesson_begin_datetime = lesson_begin_datetime_standard + timedelta(weeks=week_offset)
                lesson_end_datetime = lesson_end_datetime_standard + timedelta(weeks=week_offset)
                lesson = Lesson(course=course, location=location, start_date_time=lesson_begin_datetime,
                                end_date_time=lesson_end_datetime)
                lessons.append(lesson)
        return lessons

    def crawl(self) -> Tuple[bool, str]:
        print(f'crawling... {self.username}')
        self.s.get(ECNU_PORTAL_URL)

        login_status: bool = self.login()
        if not login_status:
            return False, "Failed to login"

        ids: str = self.get_ids()
        if ids == "":
            return False, "ids is null"

        try:
            courses = self.get_courses(ids=ids)
        except Exception as e:
            return False, str(e)

        lessons: List[Lesson] = []
        for course in courses:
            lessons.extend(self.get_lessons(course))

        if len(lessons) == 0:
            return False, "No lessons detected"

        cal = Calendar()
        cal.add("X-WR-CALNAME", f"{self.year}-{self.year + 1}学年第 {self.semester_index} 学期课表")
        cal.add("X-WR-CALDESC", f"Author: @jjaychen. Created at: {datetime.now()}")

        for lesson in lessons:
            event = Event()
            event.add("summary", lesson.course_name)
            event.add("description", lesson.course_instructor)
            event.add("location", lesson.location)
            event.add("uid", str(uuid.uuid4()))
            event.add("dtstart", lesson.start_date_time)
            event.add("dtend", lesson.end_date_time)

            alarm = Alarm()
            alarm.add("action", "audio")
            alarm.add("trigger", timedelta(minutes=-30))
            alarm.add("description", "30 minutes before")
            event.add_component(alarm)

            cal.add_component(event)

        return True, cal.to_ical().decode("utf-8")
