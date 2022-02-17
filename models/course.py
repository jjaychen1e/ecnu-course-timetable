class Course:
    course_id: str
    course_name: str
    course_instructor: str

    def __init__(self, course_id: str, course_name: str, course_instructor: str):
        self.course_id = course_id
        self.course_name = course_name
        self.course_instructor = course_instructor
