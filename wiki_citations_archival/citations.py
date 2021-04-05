import re
from pprint import pprint

import mwparserfromhell
import pywikibot
import requests
import waybackpy
from PyInquirer import prompt
from colorama import Fore, Style
from mwparserfromhell.nodes import Template
from pywikibot import Page
from requests import Response
from waybackpy.exceptions import WaybackError
from urllib.parse import unquote, urlparse, urljoin
from lib.functions import Functions

user_agent = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)' \
             f' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Safari/537.36'
headers = {'user-agent': user_agent, }
websites_disallowed = [
    'archive.org',
    'bie.ap.gov.in',
    'books.google.com',
    'censusindia.gov.in',
    'cherryfans.com',
    'cse.ap.gov.in',
    'downloads.movies.indiatimes.com',
    'eci.nic.in',
    'entertainment.oneindia.in',
    'en.climate-data.org',
    'ficci.in',
    'filmfaremagazine.indiatimes.com',
    'guntur.cdma.ap.gov.in',
    'gunturdivision.blogspot.in',
    'ibnlive.in.com',
    'iffi.nic.in',
    'ipr.ap.nic.in',
    'irrigationap.cgg.gov.in',
    'mha.nic.in',
    'nationalconferences.org',
    'pib.nic.in',
    'publiclibraries.ap.nic.in',
    'rmsaap.nic.in',
    'swachhsurvekshan2018.org',
    'timesofap.com',
    'web.archive.org',
    'www.agmarknet.nic.in',
    'www.ap.gov.in',
    'www.bharatwaves.com',
    'www.censusindia.gov.in',
    'www.dtcp.ap.gov.in',
    'www.earlytollywood.com',
    'www.espncricinfo.com',
    'www.fallingrain.com',
    'www.gunturcorporation.org',
    'www.gunturncc.com',
    'www.humsurfer.com',
    'www.imdb.com',
    'www.indiaglitz.com',
    'www.judicialpreview.ap.gov.in',
    'www.merinews.com',
    'www.sakshipost.com',
    'www.scr.indianrailways.gov.in',
    'www.thetelugufilmnagar.com',
    'www.weekendcreations.com',
    'www.yourarticlelibrary.com',
]
websites_disallowed_regex = [
    'http\:\/\/www\.(the)?hindu\.com\/(thehindu\/fr\/)?\d{4}\/[01]\d\/[0-3][0-9]\/stories\/[0-9]+\.htm',
]
websites_redirected = [
    'articles.timesofindia.indiatimes.com',
]
websites_trusted = [
    'www.thehansindia.com',
    'www.thehindu.com',
    'www.thehindubusinessline.com',
]


def prompt_input_question(question: str):
    return {
        'type': 'input',
        'name': 'input',
        'message': question,
        'validate': lambda val: len(val) > 0
    }


def prompt_bool_question(question: str):
    return {
        'type': 'confirm',
        'name': 'confirm',
        'message': question,
        'default': False,
    }


def can_edit(article: Page):
    if not article.botMayEdit():
        print('Bot may not edit')
        print()

        return False

    if not article.has_permission('edit'):
        print('Cannot be edited')
        print()

        return False

    return True


def already_set(template: Template):
    return template.has_param('archive-url') and template.has_param('archive-date') and template.has_param('url-status')


def is_trusted_website(template: Template, i: int):
    url = template.get('url').value.strip()
    o = urlparse(url)

    trusted = o.netloc in websites_trusted

    if trusted:
        print(f'{i}. {Fore.CYAN}Trusted{Style.RESET_ALL} website')

    return trusted


def url_response(url: str, i: int):
    new_url = None

    while True:
        try:
            response = requests.head(url, headers=headers)
        except:
            print(f'{i}. {Fore.RED}Exception{Style.RESET_ALL} while fetching URL HEAD')

            return None

        if 200 == response.status_code:
            if new_url is None:
                print(f'{i}. {Fore.CYAN}Old{Style.RESET_ALL} URL returned {Fore.GREEN}200 OK{Style.RESET_ALL} and matches')

            return response

        if not 'Location' in response.headers:
            print(f'{i}. Location header is not found')
            new_url = response.url.strip()
            print(response.status_code)
            print(response.headers)
            print(new_url)

            return response

        new_url = unquote(response.headers['Location']).strip()

        # Relative URL
        if not bool(urlparse(new_url).netloc):
            new_url = urljoin(url, new_url)

        if url == new_url:
            print(f'{i}. Old URL ({url}) and new URL ({new_url}) matches?')

            return response

        url = new_url
        print(new_url)


def check_url(template: Template, i: int, response: Response):
    if response is None:
        return

    if template.get('url').value.strip() == response.url.strip():
        return

    if not prompt(prompt_bool_question('Should update URL?'))['confirm']:
        enter_new_url(template, i)
        return

    template.add('url', response.url.strip())

    print(f'{i}. URL {Fore.GREEN}updated{Style.RESET_ALL}')


def check_url_status(template: Template, i: int, response: Response = None):
    # @todo Should be overrideable
    if template.has_param('url-status'):
        return

    if not prompt(prompt_bool_question('Should URL status be added?'))['confirm']:
        return

    if response is None:
        if not prompt(prompt_bool_question('URL is not checked. Check now? If not URL-status will be skipped'))['confirm']:
            print(f'{i}. URL-status {Fore.RED}skipped{Style.RESET_ALL} as response is not available')

            return

        response = url_response(template.get('url').value.strip(), i)

        # Error while fetching URL
        if response is None:
            return

    if 200 == response.status_code:
        template.add('url-status', 'live')
        print(f'{i}. URL status is {Fore.GREEN}set{Style.RESET_ALL}')

        url = template.get('url').value.strip()
        if response.url != url:
            check_url(template, i, response)

        return

    print(response.status_code)
    pprint(response.headers)
    pprint(response.url)

    answer_override = prompt(prompt_bool_question('Should url-status override to live?'))

    if answer_override['confirm']:
        template.add('url-status', 'live')
        print(f'{i}. URL status is {Fore.GREEN}set{Style.RESET_ALL}')
    else:
        print(f'{i}. URL status is {Fore.RED}not set{Style.RESET_ALL}')


def enter_new_url(template: Template, i: int):
    if not prompt(prompt_bool_question('Enter new URL manually?'))['confirm']:
        return None

    answer_url = prompt(prompt_input_question('Enter the new 200-OK URL:'))

    response = url_response(answer_url['input'], i)

    if response is None:
        print(f'{i}. New URL {Fore.RED}not added{Style.RESET_ALL}')

        return None

    template.add('url', answer_url['input'])

    print(f'{i}. New URL added {Fore.GREEN}manually{Style.RESET_ALL}')

    return response


def check_redirect(template: Template, i: int):
    o = urlparse(template.get('url').value.strip())

    return o.netloc in websites_redirected


def archive_url(template: Template, i: int):
    if template.has_param('archive-url'):
        print(f'{i}. {Fore.CYAN}Already set{Style.RESET_ALL}')

        return

    if not prompt(prompt_bool_question('Should process archiving this URL?'))['confirm']:
        return

    url = template.get('url').value.strip()
    wayback = waybackpy.Url(url, user_agent)

    try:
        archive = wayback.newest()
    except WaybackError:
        print(f'{i}. {Fore.RED}Not found{Style.RESET_ALL} in Wayback machine')

        if not prompt(prompt_bool_question('Should save the URL in the Wayback Machine?'))['confirm']:
            print(f'{i}. {Fore.RED}Not saving in Wayback machine{Style.RESET_ALL}')

            return

        try:
            archive = wayback.save()
        except:
            print(f'{i}. {Fore.RED}Error while saving in Wayback machine{Style.RESET_ALL}')

            return

    print(archive.archive_url)

    if not prompt(prompt_bool_question('Should this Archive URL be added to the Citation?'))['confirm']:
        print(f'{i}. {Fore.RED}Not setting archive url{Style.RESET_ALL}')

        return

    template.add('archive-url', archive.archive_url)
    template.add('archive-date', archive.timestamp.strftime("%-d %B %Y"))

    print(f'{i}. {Fore.GREEN}Archive URL added{Style.RESET_ALL}')


class Citations:
    def __init__(self):
        self.functions = Functions()
        self.wikipedia = pywikibot.Site('en', 'wikipedia')

        self.regex = []
        for rule in websites_disallowed_regex:
            self.regex.append(re.compile(rule))

    def process(self):
        answer_input_article = prompt(prompt_input_question('Enter the name of the EN article (namespace=0):'))

        name = "{}:{}".format(self.wikipedia.namespace(0), answer_input_article['input'])
        article = pywikibot.Page(self.wikipedia, name)

        if not can_edit(article):
            return

        wikicode = mwparserfromhell.parse(article.text)

        if len(wikicode.filter_templates()) == 0:
            print(f'Article has {Fore.RED}no citations{Style.RESET_ALL}')

            return

        i = 0
        for template in wikicode.filter_templates():
            if not template.name.matches('Cite news') and not template.name.matches('Cite web'):
                continue

            i += 1

            if not template.has_param('url'):
                print()
                pprint(template.params)
                print(f'{i}. URL is {Fore.RED}malformed{Style.RESET_ALL}')
                print()

                continue

            # URL-status, Archive-URL, Archive-date already set
            if already_set(template):
                print(f'{i}. {Fore.CYAN}Already set{Style.RESET_ALL}')

                continue

            print()
            print(f'{i}. {template.name}')
            print(template.params)
            print(template.get('url').value.strip())

            if not self.check_url_allowed(template):
                print(f'{i}. URL is {Fore.RED}not allowed{Style.RESET_ALL}')

                continue

            if check_redirect(template, i):
                enter_new_url(template, i)

            # URL redirect verification
            # @todo Check if URL has parameters
            if is_trusted_website(template, i) or prompt(prompt_bool_question('Should the URL be checked?'))['confirm']:
                response = url_response(template.get('url').value.strip(), i)
            else:
                # Mandatory after entering new URL manually
                response = enter_new_url(template, i)

            # URL
            check_url(template, i, response)

            # URL-status
            check_url_status(template, i, response)

            # Archive
            # @todo Override option to input manually
            archive_url(template, i)

            pprint(template.params)
            print()

        print()
        answer_should_commit = prompt(prompt_bool_question('Final confirmation. Should the page be saved?'))

        if not answer_should_commit['confirm']:
            print(f'{Fore.RED}Page is not committed{Style.RESET_ALL}')
            print()

            return

        article.text = str(wikicode)
        article.save(summary='Add archival urls to citations')

        print()

    def check_url_allowed(self, template: Template):
        url = template.get('url').value
        o = urlparse(str(url))

        for rule in self.regex:
            if rule.match(str(url)) is not None:
                return False

        return o.netloc not in websites_disallowed
