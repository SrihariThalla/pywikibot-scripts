from dataclasses import dataclass

from mwparserfromhell.nodes import Template
from requests import Response


@dataclass
class TemplateData:
    url_cited: str
    template: Template
    response: Response = None
    trusted: bool = False
    schema_changed: bool = False
    url_changed: str = None
    url_status: bool = None
    archive_url: str = None
    archive_date: str = None
    url_has_query: bool = False
    website_redirected: bool = False

    def url_finalized(self):
        return self.url_changed or self.url_cited

    def should_enter_url(self):
        return self.website_redirected or self.url_has_query
