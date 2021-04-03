import pywikibot
from pywikibot import pagegenerators

from lib.functions import Functions


class WikiMandals:
    def __init__(self):
        self.functions = Functions()
        self.wikipedia = pywikibot.Site('en', 'wikipedia')

    def process(self):
        name = "{}:{}".format(self.wikipedia.namespace(1), 'Tadoor')
        tmpl_page = pywikibot.Page(self.wikipedia, name)

        print(tmpl_page)
        print(dir(tmpl_page))
        print(tmpl_page.text)

        # for template in tmpl_page.templates():
        #     if 'Template:WikiProject India' != template.title():
        #         continue
        #
        #     print(template)
        #     print(dir(template))
        #     print(template.botMayEdit())
        #     print(template.canBeEdited())
        #     print(template.title())

            # break

        # pagegenerators.PreloadingEntityGenerator()
        #
        # ref_gen = pagegenerators.ReferringPageGenerator(tmpl_page, onlyTemplateInclusion=True)
        # filter_gen = pagegenerators.NamespaceFilterPageGenerator(ref_gen, namespaces=[0])
        # generator = self.wikipedia.preloadpages(filter_gen, pageprops=True)
        #
        # for item in generator:
        #     print(item)
