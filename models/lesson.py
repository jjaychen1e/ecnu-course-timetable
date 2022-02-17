from datetime import datetime

from models.course import Course


class Lesson:
    course_id: str
    course_name: str
    location: str
    course_instructor: str
    start_date_time: datetime
    end_date_time: datetime

    def __init__(self, *, course_id: str, course_name: str, location: str, course_instructor: str,
                 start_date_time: datetime, end_date_time: datetime):
        self.course_id = course_id
        self.course_name = course_name
        self.location = location
        self.course_instructor = course_instructor
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time

    def __init__(self, *, course: Course, location: str, start_date_time: datetime, end_date_time: datetime):
        self.course_id = course.course_id
        self.course_name = course.course_name
        self.course_instructor = course.course_instructor
        self.location = location
        self.start_date_time = start_date_time
        self.end_date_time = end_date_time
