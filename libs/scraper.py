import aiohttp

def parse_courses(data):
    courses = []
    for course in data.split(
            '<table class="sortable table table-striped" id="mainTable" >'
            )[1].split("<tr class=section")[1:]:
        code, title, school = course.split("</tr>")[0].split("<td")[1:]
        courses.append({
            "code": code[1:].split("</td>")[0].split(">", 1)[1].split("</")[0],
            "title": title.split(">", 1)[1].split("</td>")[0].strip(),
            "school": school.split(">", 1)[1].split("</td>")[0].strip()
            })
    return courses


async def load_courses(self):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://courses.students.ubc.ca/cs/coursesched"
                          "ule?tname=subj-all-departments&sessyr=2021&sesscd=W"
                          "&pname=subjarea") as courses:
            return parse_courses(await courses.text())

