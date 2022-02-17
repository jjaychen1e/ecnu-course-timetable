from typing import *

SEMESTER_DATE: Dict[str, Dict[str, str]] = {
    "2021": {
        "1": "2021-09-06",
        "2": "2022-02-21",
        "3": "2022-06-27"
    },
}

LESSON_START_TIME: Dict[str, Tuple[int, int]] = {
    "1": (8, 0),
    "2": (8, 50),
    "3": (9, 50),
    "4": (10, 40),
    "5": (11, 30),
    "6": (13, 0),
    "7": (13, 50),
    "8": (14, 50),
    "9": (15, 40),
    "10": (16, 30),
    "11": (18, 0),
    "12": (18, 50),
    "13": (19, 40),
    "14": (20, 30)
}

LESSON_END_TIME: Dict[str, Tuple[int, int]] = {
    "1": (8, 45),
    "2": (9, 35),
    "3": (10, 35),
    "4": (11, 25),
    "5": (12, 15),
    "6": (13, 45),
    "7": (14, 35),
    "8": (15, 35),
    "9": (16, 25),
    "10": (17, 15),
    "11": (18, 45),
    "12": (19, 35),
    "13": (20, 25),
    "14": (21, 15),
}

ECNU_PORTAL_URL: final = "https://portal1.ecnu.edu.cn/cas/login?service=https://applicationnewjw.ecnu.edu.cn/eams/home.action"
ECNU_CODE_URL: final = "https://portal1.ecnu.edu.cn/cas/code"
ECNU_IDS_URL: final = "https://applicationnewjw.ecnu.edu.cn/eams/courseTableForStd!index.action"
ECNU_COURSE_TABLE_URL: final = "https://applicationnewjw.ecnu.edu.cn/eams/courseTableForStd!courseTable.action"
ECNU_COURSE_QUERY_URL = "https://applicationnewjw.ecnu.edu.cn/eams/publicSearch!search.action"
