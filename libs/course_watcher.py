import aiohttp
import asyncio


async def watch_section(self, course):
    subject_code, course_code, section_code = course
    with aiohttp.ClientSession() as session:
        while True:
            with session.get(f"https://courses.students.ubc.ca/cs/courseschedu"
                    f"le?pname=subjarea&tname=subj-section&dept={subject_code}"
                    f"&course={course_code}&section={section_code}") as req:
                data = await req.text()
        
