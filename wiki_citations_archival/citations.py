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
from waybackpy.exceptions import WaybackError
from urllib.parse import unquote, urlparse, urljoin
from lib.functions import Functions

user_agent = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)' \
             f' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Safari/537.36'
headers = {'user-agent': user_agent, }
websites_disallowed = [
    'books.google.com',
    'entertainment.oneindia.in',
    'ibnlive.in.com',
    'ipr.ap.nic.in',
    'mha.nic.in',
    'pib.nic.in',
    'web.archive.org',
    'www.bharatwaves.com',
    'www.imdb.com',
    'www.indiaglitz.com',
    'www.thetelugufilmnagar.com',
    'www.weekendcreations.com',
]
websites_disallowed_regex = [
    'http\:\/\/www\.hindu\.com\/\d{4}\/([01]\d\/){2}stories\/[0-9]+\.htm',
]
websites_redirected = [
    'articles.timesofindia.indiatimes.com',
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


def enter_new_url(template: Template, i: int):
    answer = prompt(prompt_bool_question('Enter new URL manually?'))

    if not answer['confirm']:
        return

    answer_url = prompt(prompt_input_question('Enter the new 200-OK URL:'))

    template.add('url', answer_url['input'])

    print(f'{i}. New URL added {Fore.GREEN}manually{Style.RESET_ALL}')


def check_redirect(template: Template, i: int):
    url = template.get('url').value

    o = urlparse(str(url))

    if o.netloc in websites_redirected:
        enter_new_url(template, i)

        return

    if 'https' == o.scheme:
        return

    answer_should_check_redirect = prompt(prompt_bool_question('Should the URL redirect be checked?'))

    if not answer_should_check_redirect['confirm']:
        enter_new_url(template, i)

        return

    old_url = url
    new_url = None

    while True:
        try:
            response = requests.head(url, headers=headers)
        except:
            print(f'{i}. {Fore.RED}Exception{Style.RESET_ALL} while checking for URL redirect')

            return

        if 200 == response.status_code:
            if new_url is None:
                print(f'{i}. Old URL returned 200 OK')

                return

            break

        if not 'Location' in response.headers:
            print(f'{i}. URL is {Fore.CYAN}good{Style.RESET_ALL}')
            pprint(response.headers)

            return

        new_url = unquote(response.headers['Location']).strip()

        if not bool(urlparse(new_url).netloc):
            new_url = urljoin(url, new_url)

        if url == new_url:
            print(f'{i}. Old URL ({url}) and new URL ({new_url}) matches?')

            return

        url = new_url
        print(new_url)

    answer_should_update_url = prompt(prompt_bool_question('Should the URL be updated with new URL?'))

    if not answer_should_update_url['confirm']:
        enter_new_url(template, i)

        return

    template.add('url', new_url)

    print(f'{i}. {Fore.GREEN}URL updated{Style.RESET_ALL}')


def archive_url(template: Template, i: int):
    answer_should_archive = prompt(prompt_bool_question('Should process archiving this URL?'))

    if not answer_should_archive['confirm']:
        return

    wayback = waybackpy.Url(template.get('url').value, user_agent)

    try:
        archive = wayback.newest()
    except WaybackError:
        print(f'{i}. {Fore.RED}Not found{Style.RESET_ALL} in Wayback machine')
        answer_should_add = prompt(prompt_bool_question('Should save the URL in the Wayback Machine?'))

        if not answer_should_add['confirm']:
            print(f'{i}. {Fore.RED}Not saving in Wayback machine{Style.RESET_ALL}')

            return

        archive = wayback.save()

    print(archive.archive_url)

    answer_should_add = prompt(prompt_bool_question('Should this Archive URL be added to the Citation?'))

    if not answer_should_add['confirm']:
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

            if template.has_param('archive-url'):
                # print(template.params)
                # print(f'{i}. {Fore.CYAN}Already set{Style.RESET_ALL}')

                continue

            print()
            print(template.params)
            print(template.get('url').value)

            if not self.check_url_allowed(template):
                print(f'{i}. URL is {Fore.RED}not allowed{Style.RESET_ALL}')

                continue

            check_redirect(template, i)
            archive_url(template, i)

        print()
        answer_should_commit = prompt(prompt_bool_question('Final confirmation. Should the page be saved?'))

        if not answer_should_commit['confirm']:
            print(f'{Fore.RED}Page is not committed{Style.RESET_ALL}')
            print()

            return

        article.text = str(wikicode)
        article.save(summary='Add archived urls to citations')

        print()

    def check_url_allowed(self, template: Template):
        url = template.get('url').value
        o = urlparse(str(url))

        for rule in self.regex:
            if rule.match(str(url)) is not None:
                return False

        return o.netloc not in websites_disallowed
