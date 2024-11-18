import re

from requests import Session
from requests.models import Response
from word2number import w2n  # type: ignore

URL: str = "https://intramural.nih.gov/search/index.taf"
QUESTION_RE: re.Pattern = re.compile(r"The sum of \d+ \+ .+ =")


def parse_annual_ic_pubs(serachyear: str, ic: str) -> Response:
    session: Session = Session()
    response: Response = session.get(url=URL)
    found: list[str] = QUESTION_RE.findall(response.text)
    first_number: int = int(found[0].split()[-4])
    second_number: int = w2n.word_to_num(found[0].split()[-2])
    solution: str = str(first_number + second_number)
    post_payload: dict = {"showheader": "Y", "from": "", "checknum": solution}
    _: Response = session.post(
        "https://intramural.nih.gov/search/allreports.taf", data=post_payload
    )
    search_payload: dict = {"searchyear": serachyear, "ic": ic}
    response_3: Response = session.post(
        "https://intramural.nih.gov/search/allreports.taf?_function=search",
        data=search_payload,
    )
    return response_3
