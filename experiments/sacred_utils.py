import pymongo

import os

try:
    pwd = os.environ['MONGOPWD']
except KeyError:
    print('You need to set the MONGOPWD variable to connect to the database.')
    import sys
    sys.exit(1)

db_client = pymongo.MongoClient(f'mongodb://rasmus:{pwd}@35.189.247.219/sacred')
sacred_db = db_client.sacred
runs      = sacred_db.runs
metrics   = sacred_db.metrics


def get_metric_for_ids(name, ids):
    metric = sacred_db.metrics.aggregate([
        {'$match': {'name': {'$regex': name}}},
        {'$match': {'run_id': {'$in': ids}}},
        {'$project': {'steps': True,
                      'values': True,
                      '_id': False}
         }
    ]
    )
    return list(metric)


def delete_invalid():
    '''Delete all experiments and associated metrics for which the result was None'''

    print('DO NOT CALL THIS WHEN THERE ARE EXPERIMENTS RUNNING! Continue? ')
    if input('[yN]') != 'y':
        return
    else:
        print('I warned you')

    pipeline = [
        {'$match': {'result': None}},
        {'$project': {'_id': True}},
    ]
    invalid_ids = list(map(lambda dickt: dickt['_id'], runs.aggregate(pipeline)))
    deleted_runs = runs.delete_many({'_id': {'$in': invalid_ids}})
    deleted_metrics = metrics.delete_many({'run_id': {'$in': invalid_ids}})

    print(f'Deleted {deleted_runs.deleted_count} runs and {deleted_metrics.deleted_count} metrics.')
