import re
from pprint import pprint
from urllib.parse import unquote, urlparse, urljoin

import mwparserfromhell
import pywikibot
import requests
import waybackpy
from PyInquirer import prompt
from colorama import Fore, Style
from pywikibot import Page
from waybackpy.exceptions import WaybackError

from template import TemplateData

user_agent = f'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)' \
             f' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Safari/537.36'
headers = {'user-agent': user_agent, }
websites_disallowed = [
    'ac.in',
    'archive.org',
    'asiamattersforamerica.org',
    'badmintonindia.org',
    'blessingsonthenet.com',
    'books.google.com',
    'cdia.asia',
    'cherryfans.com',
    'cricketarchive.com',
    'downloads.movies.indiatimes.com',
    'edu.in',
    'en.climate-data.org',
    'entertainment.oneindia.in',
    'ficci.in',
    'filmfaremagazine.indiatimes.com',
    'gov.in',
    'gunturdivision.blogspot.in',
    'ibnlive.in.com',
    'nationalconferences.org',
    'nic.in',
    'postnoon.com',
    'swachhsurvekshan2018.org',
    'timesofap.com',
    'www.aplegislature.org',
    'www.bharatwaves.com',
    'www.census2011.co.in',
    'www.censusindia.net',
    'www.cia.gov',
    'www.dataforcities.org',
    'www.docstoc.com',
    'www.earlytollywood.com',
    'www.espncricinfo.com',
    'www.fallingrain.com',
    'www.gunturcorporation.org',
    'www.gunturncc.com',
    'www.humsurfer.com',
    'www.imdb.com',
    'www.indiaglitz.com',
    'www.ipsos.com',
    'www.kanakadurgamma.org',
    'www.merinews.com',
    'www.ourvmc.org',
    'www.quora.com',
    'www.sakshipost.com',
    'www.thetelugufilmnagar.com',
    'www.travelkhana.com',
    'www.vikasinstitutionsnunna.org',
    'www.weekendcreations.com',
    'www.yourarticlelibrary.com',
]
websites_disallowed_regex = [
    'http\:\/\/www\.(the)?hindu\.com\/(thehindu\/(fr|yw|mp|pp|mag)\/)?\d{4}\/[01]\d\/[0-3][0-9]\/stories\/[0-9]+\.htm',
]
websites_redirected = [
    'articles.timesofindia.indiatimes.com',
]
websites_trusted = [
    'auto.economictimes.indiatimes.com',
    'economictimes.indiatimes.com',
    'indianexpress.com',
    'techcrunch.com',
    'theprint.in',
    'timesofindia.indiatimes.com',
    'www.business-standard.com',
    'www.cbsnews.com',
    'www.deccanchronicle.com',
    'www.deccanherald.com',
    'www.dnaindia.com',
    'www.financialexpress.com',
    'www.firstpost.com',
    'www.hindustantimes.com',
    'www.ibtimes.co.in',
    'www.indiatoday.in',
    'www.indiatvnews.com',
    'www.livemint.com',
    'www.ndtv.com',
    'www.newindianexpress.com',
    'www.news18.com',
    'www.reuters.com',
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


def already_set(template_data: TemplateData):
    return (template_data.template.has_param('archive-url')
            and template_data.template.has_param('archive-date')
            and template_data.template.has_param('url-status')
            )


def is_trusted_website(template_data: TemplateData, i: int):
    o = urlparse(template_data.url_finalized())

    template_data.trusted = o.netloc in websites_trusted and '' == o.query

    if template_data.trusted:
        print(f'{i}. {Fore.CYAN}Trusted{Style.RESET_ALL} website')


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


def check_url(template_data: TemplateData, i: int):
    if template_data.response is None:
        return

    if template_data.url_finalized() == template_data.response.url.strip():
        return

    old_url_parsed = urlparse(template_data.url_finalized())
    new_url_parsed = urlparse(template_data.response.url.strip())

    if (template_data.trusted
            and 200 == template_data.response.status_code
            and 'http' == old_url_parsed.scheme
            and 'https' == new_url_parsed.scheme
            and old_url_parsed.netloc == new_url_parsed.netloc
            and old_url_parsed.path == new_url_parsed.path
            and old_url_parsed.params == new_url_parsed.params
            and old_url_parsed.query == new_url_parsed.query
            and old_url_parsed.fragment == new_url_parsed.fragment
        ):

        template_data.url_changed = template_data.response.url.strip()

        print(f'{i}. {Fore.CYAN}Schema{Style.RESET_ALL} change for trusted website. '
              f'URL {Fore.GREEN}updated{Style.RESET_ALL}')

        return

    if not prompt(prompt_bool_question('Should update URL?'))['confirm']:
        template_data.trusted = False
        enter_new_url(template_data, i)

        return

    template_data.url_changed = template_data.response.url.strip()
    template_data.trusted = False

    print(f'{i}. URL {Fore.GREEN}updated{Style.RESET_ALL}')


def check_url_status(template_data: TemplateData, i: int):
    # @todo Should be overrideable
    if template_data.template.has_param('url-status'):
        return

    # Short-circuit trusted websites
    if not template_data.trusted and not prompt(prompt_bool_question('Should URL status be added?'))['confirm']:
        return

    if template_data.response is None:
        if not prompt(prompt_bool_question('URL is not checked. Check now? If not URL-status will be skipped'))['confirm']:
            print(f'{i}. URL-status {Fore.RED}skipped{Style.RESET_ALL} as response is not available')

            return

        template_data.response = url_response(template_data.url_finalized(), i)

        # Error while fetching URL
        if template_data.response is None:
            return

    if 200 == template_data.response.status_code:
        template_data.url_status = True

        print(f'{i}. URL status is {Fore.GREEN}set{Style.RESET_ALL}')

        if template_data.response.url.strip() != template_data.url_finalized():
            check_url(template_data, i)

        return

    print(template_data.response.status_code)
    pprint(template_data.response.headers)
    pprint(template_data.response.url.strip())

    if template_data.response.status_code in [404, 500]:
        if prompt(prompt_bool_question('Should URL status be updated to dead?')):
            template_data.url_status = False
            print(f'{i}. URL returned {Fore.RED}404{Style.RESET_ALL}. Status updated to {Fore.GREEN}dead{Style.RESET_ALL}')

            return

    answer_override = template_data.trusted or prompt(prompt_bool_question('Should url-status override to live?'))['confirm']

    if answer_override:
        template_data.url_status = True

        print(f'{i}. URL status is {Fore.GREEN}set{Style.RESET_ALL}')
    else:
        print(f'{i}. URL status is {Fore.RED}not set{Style.RESET_ALL}')


def enter_new_url(template_data: TemplateData, i: int):
    if not prompt(prompt_bool_question('Enter new URL manually?'))['confirm']:
        return

    answer_url = prompt(prompt_input_question('Enter the new 200-OK URL:'))

    response = url_response(answer_url['input'], i)

    if response is None:
        print(f'{i}. New URL {Fore.RED}not added{Style.RESET_ALL}')

        return

    template_data.url_changed = answer_url['input']
    template_data.response = response

    print(f'{i}. New URL added {Fore.GREEN}manually{Style.RESET_ALL}')


def archive_url(template_data: TemplateData, i: int):
    if template_data.template.has_param('archive-url'):
        print(f'{i}. {Fore.CYAN}Already set{Style.RESET_ALL}')

        return

    if not template_data.trusted and not prompt(prompt_bool_question('Should process archiving this URL?'))['confirm']:
        return

    wayback = waybackpy.Url(template_data.url_finalized(), user_agent)

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

    archive_date = archive.timestamp.strftime('%-d %B %Y')

    print(f'  {archive_date}')
    print(f'  {archive.archive_url}')

    regex_archive_url = 'https:\/\/web\.archive\.org\/web\/[0-9]{14}\/(.*)'
    o = re.search(regex_archive_url, archive.archive_url)

    archive_url_match = len(o.groups()) == 1 and o.groups()[0] == template_data.url_finalized()

    if archive_url_match:
        if template_data.trusted:
            template_data.archive_url = archive.archive_url
            template_data.archive_date = archive_date

            print(f'{i}. {Fore.GREEN}Archive URL added{Style.RESET_ALL}')

            return
    else:
        print(f'{i}. Archive URL {Fore.RED}does not{Style.RESET_ALL} match with cited URL')

    # @todo Manual input of archive URL
    if not prompt(prompt_bool_question('Should this Archive URL be added to the Citation?'))['confirm']:
        print(f'{i}. {Fore.RED}Not setting archive url{Style.RESET_ALL}')

        return

    template_data.archive_url = archive.archive_url
    template_data.archive_date = archive_date

    print(f'{i}. {Fore.GREEN}Archive URL added{Style.RESET_ALL}')


class Citations:
    def __init__(self):
        self.wikipedia = pywikibot.Site('en', 'wikipedia')

        self.regex_archive_url = 'https:\/\/web\.archive\.org\/web\/[0-9]{14}\/(.*)'
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

            template_data = TemplateData(
                url_cited=template.get('url').value.strip(),
                template=template
            )

            # URL-status, Archive-URL, Archive-date already set
            if already_set(template_data):
                print(f'{i}. {Fore.CYAN}Already set{Style.RESET_ALL}')

                continue

            print()
            print(f'{i}. {template_data.template.name}')
            print(template_data.template.params)
            print(template_data.url_finalized())

            if not self.check_url_allowed(template_data, i):
                print(f'{i}. URL is {Fore.RED}not allowed{Style.RESET_ALL}')
                print()

                continue

            if template_data.should_enter_url():
                enter_new_url(template_data, i)

            is_trusted_website(template_data, i)

            # URL redirect verification
            # @todo Check if URL has parameters
            if template_data.trusted or prompt(prompt_bool_question('Should the URL be checked?'))['confirm']:
                template_data.response = url_response(template_data.url_finalized(), i)
            else:
                # Mandatory after entering new URL manually
                enter_new_url(template_data, i)

            # URL
            check_url(template_data, i)

            # URL-status
            check_url_status(template_data, i)

            # Archive
            # @todo Override option to input manually
            archive_url(template_data, i)

            template.add('url', template_data.url_finalized())

            if template_data.url_status is True:
                template.add('url-status', 'live')
            elif template_data.url_status is False:
                template.add('url-status', 'dead')

            if template_data.archive_url is not None:
                template_data.template.add('archive-url', template_data.archive_url)
                template_data.template.add('archive-date', template_data.archive_date)

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

    def check_url_allowed(self, template_data: TemplateData, i: int):
        url = template_data.url_finalized()
        o = urlparse(url)

        for rule in self.regex:
            if rule.match(url) is not None:
                return False

        if o.netloc in websites_disallowed:
            return False

        domain_parts = o.netloc.split('.')

        while len(domain_parts):
            domain_parts.pop(0)

            if '.'.join(domain_parts) in websites_disallowed:
                return False

        template_data.website_redirected = o.netloc in websites_redirected

        if '' != o.query:
            template_data.url_has_query = True
            print(f'{i}. URL has {Fore.RED}query{Style.RESET_ALL}')

        if o.path.endswith('.pdf'):
            print(f'{i}. Link is {Fore.CYAN}PDF{Style.RESET_ALL}')

            return True

        return True
