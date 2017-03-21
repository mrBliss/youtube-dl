from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    urlencode_postdata,
)


class CanvasIE(InfoExtractor):
    IE_DESC = 'canvas.be and een.be'
    _VALID_URL = r'https?://(?:www\.)?(?P<site_id>canvas|een)\.be/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.canvas.be/video/de-afspraak/najaar-2015/de-afspraak-veilt-voor-de-warmste-week',
        'md5': 'ea838375a547ac787d4064d8c7860a6c',
        'info_dict': {
            'id': 'mz-ast-5e5f90b6-2d72-4c40-82c2-e134f884e93e',
            'display_id': 'de-afspraak-veilt-voor-de-warmste-week',
            'ext': 'mp4',
            'title': 'De afspraak veilt voor de Warmste Week',
            'description': 'md5:24cb860c320dc2be7358e0e5aa317ba6',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 49.02,
        }
    }, {
        # with subtitles
        'url': 'http://www.canvas.be/video/panorama/2016/pieter-0167',
        'info_dict': {
            'id': 'mz-ast-5240ff21-2d30-4101-bba6-92b5ec67c625',
            'display_id': 'pieter-0167',
            'ext': 'mp4',
            'title': 'Pieter 0167',
            'description': 'md5:943cd30f48a5d29ba02c3a104dc4ec4e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2553.08,
            'subtitles': {
                'nl': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://www.een.be/sorry-voor-alles/herbekijk-sorry-voor-alles',
        'info_dict': {
            'id': 'mz-ast-11a587f8-b921-4266-82e2-0bce3e80d07f',
            'display_id': 'herbekijk-sorry-voor-alles',
            'ext': 'mp4',
            'title': 'Herbekijk Sorry voor alles',
            'description': 'md5:8bb2805df8164e5eb95d6a7a29dc0dd3',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 3788.06,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://www.canvas.be/check-point/najaar-2016/de-politie-uw-vriend',
        'only_matching': True,
    }]

    def _extract_info(self, site_id, video_id, display_id):
        data = self._download_json(
            'https://mediazone.vrt.be/api/v1/%s/assets/%s'
            % (site_id, video_id), display_id)

        formats = []
        for target in data['targetUrls']:
            format_url, format_type = target.get('url'), target.get('type')
            if not format_url or not format_type:
                continue
            if format_type == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, entry_protocol='m3u8_native',
                    ext='mp4', preference=0, fatal=False, m3u8_id=format_type))
            elif format_type == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url, display_id, f4m_id=format_type, fatal=False))
            elif format_type == 'MPEG_DASH':
                formats.extend(self._extract_mpd_formats(
                    format_url, display_id, mpd_id=format_type, fatal=False))
            else:
                formats.append({
                    'format_id': format_type,
                    'url': format_url,
                })
        self._sort_formats(formats)

        subtitles = {}
        subtitle_urls = data.get('subtitleUrls')
        if isinstance(subtitle_urls, list):
            for subtitle in subtitle_urls:
                subtitle_url = subtitle.get('url')
                if subtitle_url and subtitle.get('type') == 'CLOSED':
                    subtitles.setdefault('nl', []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'duration': float_or_none(data.get('duration'), 1000),
            'thumbnail': data.get('posterImageUrl'),
            'subtitles': subtitles,
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, display_id = mobj.group('site_id'), mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = (self._search_regex(
            r'<h1[^>]+class="video__body__header__title"[^>]*>(.+?)</h1>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage)).strip()

        description = self._og_search_description(webpage)

        video_id = self._html_search_regex(
            r'data-video=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage, 'video id',
            group='id')

        info = self._extract_info(site_id, video_id, display_id)
        info.update({
            'title': title,
            'description': description,
        })
        return info


class VrtNUIE(CanvasIE):
    _VALID_URL = r'https?://(?:www\.)?vrt\.be/vrtnu/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [
        {
            'url': 'https://www.vrt.be/vrtnu/a-z/trapped/1/trapped-s1a4/',
            'info_dict': {
                'id': 'md-ast-01e7d193-63ab-4d89-9ab1-96b23315ebec_1489574042173',
                'ext': 'mp4',
                'title': 'Trapped',
                'description': 'md5:6f4f779d176252f887fdd938910d6094',
                'duration': 3011.17,
                'thumbnail': r're:^https?://.*\.jpg$'
            },
            'skip': 'This video is only available for registered users'
        }
    ]
    _NETRC_MACHINE = 'vrtnu'
    _APIKEY = '3_0Z2HujMtiWq_pkAjgnS2Md2E11a1AwZjYiBETtwNE-EoEHDINgtnvcAOpNgmrVGy'
    _CONTEXT_ID = 'R1070628488'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            self.raise_login_required()

        auth_data = {
            'APIKey': self._APIKEY,
            'targetEnv': 'jssdk',
            'loginID': username,
            'password': password,
            'authMode': 'cookie',
            'context': self._CONTEXT_ID,
        }

        self._request_webpage(
            'https://accounts.eu1.gigya.com/accounts.login', None,
            note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata(auth_data),
            query={
                'context': self._CONTEXT_ID,
                'saveResponseID': self._CONTEXT_ID,
            })

        gigya_cookies = self._get_cookies('https://accounts.eu1.gigya.com')
        if 'ucid' not in gigya_cookies or 'gmid' not in gigya_cookies:
            raise ExtractorError('Unable to login: missing cookies',
                                 expected=True)

        saved_response = self._download_webpage(
            'https://accounts.eu1.gigya.com/socialize.getSavedResponse', None,
            note='Getting login response', errnote='Unable to log in',
            query={
                'APIKey': self._APIKEY,
                'saveResponseID': self._CONTEXT_ID,
                'context': self._CONTEXT_ID,
                'format': 'jsonp',
                'callback': 'DUMMY',
            })

        auth_info_js = self._search_regex(
            r'DUMMY\(({.+})\);', saved_response, 'auth_info_js',
            flags=(re.M | re.S))
        auth_info = self._parse_json(auth_info_js, None, None, 'auth_info')

        # When requesting a token, no actual token is returne, but the
        # necessary cookies are set.
        self._request_webpage(
            'https://token.vrt.be',
            None, note='Requesting a token', errnote='Could not get a token',
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://www.vrt.be',
                'Referer': 'https://www.vrt.be/vrtnu/a-z/',
            },
            data=json.dumps({
                'uid': auth_info['UID'],
                'uidsig': auth_info['UIDSignature'],
                'ts': auth_info['signatureTimestamp'],
                'email': auth_info['profile']['email'],
            }).encode('utf-8'))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = self._search_regex(
            r'<h1 class="content__heading">(.+?)</h1>',
            webpage, 'title', default=None, flags=(re.M | re.S)).strip()

        description = self._html_search_regex(
            r'<div class="content__description">(.+?)</div>',
            webpage, 'description', default=None, flags=(re.M | re.S))

        season = self._html_search_regex(
            [r'''(?xms)<div\ class="tabs__tab\ tabs__tab--active">\s*
                    <span>seizoen\ (.+?)</span>\s*
                </div>''',
             r'<option value="seizoen (.+?)" data-href="[^"]+?" selected>'],
            webpage, 'season', default=None)

        season_number = int_or_none(season)

        # Sometimes the season is the year, so don't use it as the season number
        if season_number and season_number > 1000:
            season_number = None

        episode_number = int_or_none(self._html_search_regex(
            r'''<div\ class="content__episode">\s*
                    <abbr\ title="aflevering">afl</abbr>\s*<span>(\d+)</span>
                </div>''',
            webpage, 'episode_number', default=None,
            flags=(re.X | re.M | re.S)))

        release_date = parse_iso8601(self._html_search_regex(
            r'<div class="content__broadcastdate">\s*<time\ datetime="(.+?)"',
            webpage, 'release_date', default=None, flags=(re.M | re.S)))

        # If there's a ? or a # in the URL, remove them and everything after
        clean_url = url.split('?')[0].split('#')[0].strip('/')
        securevideo_url = clean_url + '.securevideo.json'

        json = self._download_json(securevideo_url, display_id)
        # There is only one entry, but with an unknown key, so just get the
        # first one
        video_id = list(json.values())[0].get('mzid')

        info = self._extract_info('vrtvideo', video_id, display_id)
        info.update({
            'title': title,
            'description': description,
            'season': season,
            'season_number': season_number,
            'episode_number': episode_number,
            'release_date': release_date,
        })
        return info
