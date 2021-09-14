import aiohttp

def parse_courses(data):
    courses = []
    for course in data.split(
            '<table class="sortable table table-striped" id="mainTable" >'
            )[1].split("<tr class=section")[1:]:
        code, title, school = course.split("</tr>")[0].split("<td")[1:]
        code = code[1:].split("</td>")[0].split(">", 1)[1].split("</")[0]
        if code.endswith("*"):
            continue
        courses.append({
            "code": code,
            "title": title.split(">", 1)[1].split("</td>")[0].strip(),
            "school": school.split(">", 1)[1].split("</td>")[0].strip()
            })
    return courses


def parse_course(data):
    subcourses = []
    for subcourse in data.split(
            '<table class="sortable table table-striped" id="mainTable">'
            )[1].split("</tbody>")[0].split("<tr class=section")[1:]:
        subcourse, title = subcourse.split("<td")[1:]
        subcourses.append({
            "code": subcourse[1:].split(">", 1)[1].split("</a>")[0].split()[1],
            "title": title[1:].split("</td")[0]
            })
    return subcourses


def parse_sections(data):
    sections = []
    for section in map(lambda s: s[2:], data.split(
            '<table class="table table-striped section-summary" >'
            )[1].split('</thead>', 1)[1].split("</table>")[0]\
                .split("<tr class=section")[1:]):
        status, name, activity, term, *_ = section.split("<td>")[1:]
        sections.append({
            "status": status.split("</td")[0],
            "section": name.split(">", 1)[1].split("</a")[0],
            "activity": activity.split("</td")[0],
            "term": term.split("</td")[0]
            })
    return sections


async def load_sections(self, data):
    subject_code, subcourse_code = data
    async with aiohttp.ClientSession() as session:
        async with session.get("https://courses.students.ubc.ca/cs/coursesched"
                            "ule?pname=subjarea&tname=subj-course&dept="
                           f"{subject_code}&course={subcourse_code}") as data:
            return parse_sections(await data.text())


async def load_course(self, code):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://courses.students.ubc.ca/cs/coursesched"
                            "ule?tname=subj-department&sessyr=2021&sesscd=W&de"
                           f"pt={code}&pname=subjarea") as course:
            return parse_course(await course.text())


async def load_courses(self):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://courses.students.ubc.ca/cs/coursesched"
                          "ule?tname=subj-all-departments&sessyr=2021&sesscd=W"
                          "&pname=subjarea") as courses:
            return parse_courses(await courses.text())

