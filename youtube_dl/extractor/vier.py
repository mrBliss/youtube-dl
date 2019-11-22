# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    int_or_none,
    remove_end,
)


class VierIE(InfoExtractor):
    IE_NAME = 'vier'
    IE_DESC = 'vier.be and vijf.be'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?(?P<site>vier|vijf)\.be/
                        (?:
                            (?:
                                [^/]+/videos|
                                video(?:/[^/]+)*
                            )/
                            (?P<display_id>[^/]+)(?:/(?P<id>\d+))?|
                            (?:
                                video/v3/embed|
                                embed/video/public
                            )/(?P<embed_id>\d+)
                        )
                    '''
    _NETRC_MACHINE = 'vier'
    # TODO update
    _TESTS = [{
        'url': 'http://www.vier.be/planb/videos/het-wordt-warm-de-moestuin/16129',
        'md5': 'e4ae2054a6b040ef1e289e20d111b46e',
        'info_dict': {
            'id': '16129',
            'display_id': 'het-wordt-warm-de-moestuin',
            'ext': 'mp4',
            'title': 'Het wordt warm in De Moestuin',
            'description': 'De vele uren werk eisen hun tol. Wim droomt van assistentie...',
            'upload_date': '20121025',
            'series': 'Plan B',
            'tags': ['De Moestuin', 'Moestuin', 'meisjes', 'Tomaat', 'Wim', 'Droom'],
        },
    }, {
        'url': 'http://www.vijf.be/temptationisland/videos/zo-grappig-temptation-island-hosts-moeten-kiezen-tussen-onmogelijke-dilemmas/2561614',
        'info_dict': {
            'id': '2561614',
            'display_id': 'zo-grappig-temptation-island-hosts-moeten-kiezen-tussen-onmogelijke-dilemmas',
            'ext': 'mp4',
            'title': 'md5:84f45fe48b8c1fa296a7f6d208d080a7',
            'description': 'md5:0356d4981e58b8cbee19355cbd51a8fe',
            'upload_date': '20170228',
            'series': 'Temptation Island',
            'tags': list,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.vier.be/janigaat/videos/jani-gaat-naar-tokio-aflevering-4/2674839',
        'info_dict': {
            'id': '2674839',
            'display_id': 'jani-gaat-naar-tokio-aflevering-4',
            'ext': 'mp4',
            'title': 'Jani gaat naar Tokio - Aflevering 4',
            'description': 'md5:aa8d611541db6ae9e863125704511f88',
            'upload_date': '20170501',
            'series': 'Jani gaat',
            'episode_number': 4,
            'tags': ['Jani Gaat', 'Volledige Aflevering'],
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'Requires account credentials',
    }, {
        # Requires account credentials but bypassed extraction via v3/embed page
        # without metadata
        'url': 'http://www.vier.be/janigaat/videos/jani-gaat-naar-tokio-aflevering-4/2674839',
        'info_dict': {
            'id': '2674839',
            'display_id': 'jani-gaat-naar-tokio-aflevering-4',
            'ext': 'mp4',
            'title': 'jani-gaat-naar-tokio-aflevering-4',
        },
        'params': {
            'skip_download': True,
        },
        'expected_warnings': ['Log in to extract metadata'],
    }, {
        # Without video id in URL
        'url': 'http://www.vier.be/planb/videos/dit-najaar-plan-b',
        'only_matching': True,
    }, {
        'url': 'http://www.vier.be/video/v3/embed/16129',
        'only_matching': True,
    }, {
        'url': 'https://www.vijf.be/embed/video/public/4093',
        'only_matching': True,
    }, {
        'url': 'https://www.vier.be/video/blockbusters/in-juli-en-augustus-summer-classics',
        'only_matching': True,
    }, {
        'url': 'https://www.vier.be/video/achter-de-rug/2017/achter-de-rug-seizoen-1-aflevering-6',
        'only_matching': True,
    }]

    def _real_initialize(self):
        self._logged_in = False

    def _login(self, site):
        return
        # TODO redo
        username, password = self._get_login_info()
        if username is None or password is None:
            return

        login_page = self._download_webpage(
            'http://www.%s.be/user/login' % site,
            None, note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata({
                'form_id': 'user_login',
                'name': username,
                'pass': password,
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

        login_error = self._html_search_regex(
            r'(?s)<div class="messages error">\s*<div>\s*<h2.+?</h2>(.+?)<',
            login_page, 'login error', default=None)
        if login_error:
            self.report_warning('Unable to log in: %s' % login_error)
        else:
            self._logged_in = True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        embed_id = mobj.group('embed_id')
        display_id = mobj.group('display_id') or embed_id
        video_id = mobj.group('id') or embed_id
        site = mobj.group('site')

        if not self._logged_in:
            self._login(site)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'data-file="([^"]+)"', webpage, 'video id')

        authorization_code = "eyJraWQiOiJCSHZsMjdjNzdGR2J5YWNyTk8xXC9yWXBPTjlzMFFPbjhtUTdzQnA5eCtvbz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxYzI2MThiNy1lN2VhLTRlN2EtYmRjMy1jNTJmNzUyOWRkM2MiLCJ3ZWJzaXRlIjoie1widXJsXCI6XCJodHRwOlwvXC93d3cudmllci5iZVwvdmlkZW9cL2RlLXNvbGxpY2l0YXRpZVwvMjAxN1wvZGUtc29sbGljaXRhdGllLWFmbGV2ZXJpbmctOFwiLFwic2l0ZU5hbWVcIjpcIlZJRVJcIixcInRpdGxlXCI6XCJEZSBTb2xsaWNpdGF0aWUgLSBBZmxldmVyaW5nIDhcIixcImFjdGlvblwiOlwid2F0Y2hcIn0iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYmlydGhkYXRlIjoiMTJcLzEyXC8xOTEyIiwiZ2VuZGVyIjoibSIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5ldS13ZXN0LTEuYW1hem9uYXdzLmNvbVwvZXUtd2VzdC0xX2RWaVNzS001WSIsImN1c3RvbTpwb3N0YWxfY29kZSI6IjEwNDMiLCJjb2duaXRvOnVzZXJuYW1lIjoibWVqbzJqYXh4OWo0cW1tOTh2IiwiYXVkIjoiNnMxaDg1MXM4dXBsY281aDZtcWgxamFjOG0iLCJldmVudF9pZCI6IjA0YmEyNTljLTU5YzgtMTFlOS04NjAyLWYzY2U2Yjc1OWI5MCIsInRva2VuX3VzZSI6ImlkIiwiY3VzdG9tOnNlbGxpZ2VudElkIjoiODE0NDQwIiwiYXV0aF90aW1lIjoxNTU0NzA1MTIyLCJleHAiOjE1Njk2ODMwNTgsImlhdCI6MTU2OTY3OTQ1OCwiZW1haWwiOiJkZXdpbmFudCt2aWVyMkBnbWFpbC5jb20ifQ.GXl6Kan4K2rXPYynfJJnGEBjB4AV9mU2NEhjq1-tZb3JxJRQyzcwxLmNKTbZ6uki_7XCBHCNIB5D_I3I2ZnkGdKDfZn0QQ9-qBYRTBSYLkKMucAhYbU3uGfLYjWCXpMJQ9MxXGczEwNcblDvtK6cVp5brvL991DnTchMcdvCkXAhMcKzyPl2nZgh9K3QM7bkuLVuP70NX7QYjshAeusySQPZCGUfRDjhIKCsihF_8gqg5GwxF6fWuOgwZR-zge-9Nii4730PGnR_txyZ8Cg9wA7tvpSU8-ApOimEDjz--PVQtQceGYVOfKu_BAVUzfdyOG70gowsPf2eSWCBj06eqg"

        json = self._download_json(
            'https://api.viervijfzes.be/content/%s' % video_id,
            video_id=video_id,
            headers={'authorization': authorization_code})
        playlist_url = json['video']['S']
        # duration = int_or_none(json['length']['N'])

        # playlist_url = video_id
        duration = None


        formats = self._extract_m3u8_formats(
            playlist_url, display_id)
        # formats = self._extract_wowza_formats(
        #     playlist_url, display_id, skip_protocols=['dash'])
        self._sort_formats(formats)
        print(formats)


        title = remove_end(self._og_search_title(webpage, default=display_id),
                           " | Vier")

        description = self._html_search_regex(
            r'''(?s)<div\b[^>]+\bclass="metadata__description">.+?
                    <p>(?P<value>.+?)\s*(?:Deze\ aflevering\ is\ te\ bekijken\ tot.+?)?</p>''',
            webpage, 'description', default=None, group='value')
        thumbnail = self._og_search_property(
            'image:url', webpage, 'thumbnail URL', fatal=False, default=None)
        # upload_date = int_or_none(self._html_search_regex(
        #     r'data-timestamp="(\d+)"',
        #     webpage, 'upload_date', default=None))
        upload_date = None

        series = self._search_regex(
            r'data-program=(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'series', default=None, group='value')
        episode_number = int_or_none(self._search_regex(
            r'(?i)aflevering (\d+)', title, 'episode number', default=None))
        tags = re.findall(r'<a\b[^>]+\bhref=["\']/tags/[^>]+>([^<]+)<', webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'series': series,
            'episode_number': episode_number,
            'tags': tags,
            'formats': formats,
            'duration': duration,
        }


class VierVideosIE(InfoExtractor):
    IE_NAME = 'vier:videos'
    _VALID_URL = r'https?://(?:www\.)?(?P<site>vier|vijf)\.be/(?P<program>[^/]+)/videos(?:\?.*\bpage=(?P<page>\d+)|$)'
    _TESTS = [{
        'url': 'http://www.vier.be/demoestuin/videos',
        'info_dict': {
            'id': 'demoestuin',
        },
        'playlist_mincount': 153,
    }, {
        'url': 'http://www.vijf.be/temptationisland/videos',
        'info_dict': {
            'id': 'temptationisland',
        },
        'playlist_mincount': 159,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=6',
        'info_dict': {
            'id': 'demoestuin-page6',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=7',
        'info_dict': {
            'id': 'demoestuin-page7',
        },
        'playlist_mincount': 13,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        program = mobj.group('program')
        site = mobj.group('site')

        page_id = mobj.group('page')
        if page_id:
            page_id = int(page_id)
            start_page = page_id
            playlist_id = '%s-page%d' % (program, page_id)
        else:
            start_page = 0
            playlist_id = program

        entries = []
        for current_page_id in itertools.count(start_page):
            current_page = self._download_webpage(
                'http://www.%s.be/%s/videos?page=%d' % (site, program, current_page_id),
                program,
                'Downloading page %d' % (current_page_id + 1))
            page_entries = [
                self.url_result('http://www.' + site + '.be' + video_url, 'Vier')
                for video_url in re.findall(
                    r'<h[23]><a href="(/[^/]+/videos/[^/]+(?:/\d+)?)">', current_page)]
            entries.extend(page_entries)
            if page_id or '>Meer<' not in current_page:
                break

        return self.playlist_result(entries, playlist_id)
