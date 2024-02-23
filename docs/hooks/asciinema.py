import copy
import json
from bs4 import BeautifulSoup


def to_camel_case(snake_str):
    camel_case_str = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return camel_case_str[0].lower() + camel_case_str[1:]


def on_post_page(output, page, config):
    if 'alt="asciicast"' not in output:
        return output

    soup = BeautifulSoup(output, 'html.parser')
    asciicast_elements = soup.findAll("img", {"alt": "asciicast"})
    asciicasts = []
    for idx, element in enumerate(asciicast_elements):
        asciicast_id = f'asciicast-{idx}'
        asciicast_src = element.attrs['src']

        # asciinema options, see https://docs.asciinema.org/manual/player/options/
        options = {"fit": "width", "preload": True}

        for key, value in element.attrs.items():

            if key in ["src"]:
                continue

            if value == "true":
                value = True
            elif value == "false":
                value = False

            options[to_camel_case(key)] = value

        div_tag = soup.new_tag("div", id=asciicast_id)
        element.replace_with(div_tag)
        asciicasts.append(
            f'asciinema_create_player("{asciicast_src}", '
            f'document.getElementById("{asciicast_id}"), {json.dumps(options)});')

    asciicast_script = soup.new_tag("script")
    asciicast_script.append("\n".join(asciicasts))
    soup.body.append(asciicast_script)

    return str(soup)
