"""Conservative public posting URLs; titles/locations never establish identity."""
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import re
from src.adapters.public_board import public_https_url

_TRACKING = {'gh_src', 'lever-source', 'lever-origin', 'fbclid', 'gclid', 'trk', 'referrer', 'trackingid'}


def canonical_job_url(value):
    safe = public_https_url(value)
    if not safe:
        return None
    p = urlsplit(safe)
    pairs = [(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True)
             if not k.casefold().startswith('utm_') and k.casefold() not in _TRACKING]
    pairs.sort(key=lambda pair: pair[0])  # preserve order of repeated same-key values
    host = p.hostname.lower()
    path = p.path or '/'
    if host == 'jobs.ashbyhq.com' and re.fullmatch(r'/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/application/?',path):
        path = path.rstrip('/').removesuffix('/application')
    if host in ('boards.greenhouse.io','job-boards.greenhouse.io'):
        match = re.fullmatch(r'/[A-Za-z0-9_-]+/jobs/([0-9]+)/?',path)
        if match:
            host = 'job-boards.greenhouse.io'
            path = path.rstrip('/')
            # Drop only a redundant copy of the same path ID. A conflicting
            # requisition value remains part of identity and needs review.
            pairs = [(k,v) for k,v in pairs if not (k == 'gh_jid' and v == match.group(1))]
    return urlunsplit(('https',host,path,urlencode(pairs),''))
