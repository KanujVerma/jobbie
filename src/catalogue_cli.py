"""Explicit local catalogue commands; reads never initialize or poll sources."""
import json
import sys
from datetime import datetime,timezone

from src.catalogue import Catalogue,CatalogueError


def add_catalogue_parser(subparsers):
    parser=subparsers.add_parser('catalogue',help='Local source catalogue; no delivery/cutover authority')
    commands=parser.add_subparsers(dest='catalogue_command',required=True)
    for name in ['init','stats','query','history','export','reclassify']:
        command=commands.add_parser(name)
        command.add_argument('--db',required=True,help='Explicit private local SQLite path')
        if name in {'query','export'}:
            command.add_argument('--text');command.add_argument('--employer');command.add_argument('--status')
            command.add_argument('--policy');command.add_argument('--limit',type=int,default=1000)
            command.add_argument('--offset',type=int,default=0)
        if name=='history':
            command.add_argument('--job-id');command.add_argument('--limit',type=int,default=1000)
        if name=='export':command.add_argument('--format',choices=['jsonl','csv'],default='jsonl')
        if name=='reclassify':command.add_argument('--policy-version',required=True)


def cmd_catalogue(args):
    try:
        write=args.catalogue_command in {'init','reclassify'}
        with Catalogue(args.db,create=args.catalogue_command=='init',readonly=not write) as db:
            action=args.catalogue_command
            if action in {'init','stats'}:result={'schema_version':1,**db.stats()}
            elif action=='history':result=db.history(args.job_id,limit=args.limit)
            elif action in {'query','export'}:
                query={key:getattr(args,key) for key in ['text','employer','status','policy','limit','offset']}
                if action=='export':
                    for line in db.export(args.format,**query):sys.stdout.write(line)
                    return 0
                result=db.query(**query)
            else:
                from src.config import load_config
                from src.eligibility import classify_eligibility
                config=load_config(args.config)
                def classifier(data):
                    verdict=classify_eligibility(db.job_from_snapshot(data),config.filters)
                    return {'status':verdict.status,'reasons':list(verdict.reasons)}
                result={'classified':db.reclassify(args.policy_version,classifier,datetime.now(timezone.utc)),
                        'policy':args.policy_version,'delivery_authority':'legacy_json'}
            print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except Exception as error:
        # Source descriptions/SQL/secret-bearing paths are not diagnostic output.
        print(f'Catalogue command failed: {type(error).__name__}',file=sys.stderr)
        return 1
