import os
from datetime import datetime
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sfrCore import Work, Instance, Item, Identifier

from lib.outputManager import OutputManager

from helpers.logHelpers import createLog
from helpers.errorHelpers import DBError

logger = createLog('db_manager')


def importRecord(session, record):
    """Import a generic record. Fields within the record, type and method
    control exactly what methods are invoked. Specifically this process will be
    implemented to insert and update:
    - works
    - instances
    - items
    - agents
    - subjects
    - access_reports"""
    
    if 'type' not in record:
        record['type'] = 'work'

    if record['type'] == 'work':
        workData = (record['data'])
        if 'data' in workData:
            record = workData
            workData = workData['data']

        primaryID = workData.pop('primary_identifier', None)

        existingWork = Work.lookupWork(
            session,
            workData.get('identifiers', []),
            primaryID
        )

        epubsToLoad = existingWork.update(workData, session=session)

        existingWork.date_modified = datetime.utcnow()

        for deferredEpub in epubsToLoad: 
            OutputManager.putKinesis(
                epubPayload,
                os.environ['EPUB_STREAM'],
                recType='item'
            )
        
        return 'Work {}'.format(existingWork.uuid.hex)

    elif record['type'] == 'instance':
        logger.info('Ingesting instance record')
        instanceData = record['data']

        existingID = Instance.lookup(
            session,
            instanceData.get('identifiers', []),
            instanceData.get('volume', None),
            instanceData.pop('primary_identifier', None)
        )
        if existingID is None:
            logger.warning('Could not locate instance, skipping record')
            raise DBError('instances', 'Could not locate instance in database, skipping')

        existing = session.query(Instance).get(existingID)

        epubsToLoad = existing.update(session, instanceData)

        for deferredEpub in epubsToLoad: 
            OutputManager.putKinesis(
                epubPayload,
                os.environ['EPUB_STREAM'],
                recType='item'
            )
        
        return 'Instance #{}'.format(existing.id)

    elif record['type'] == 'item':
        itemData = record['data']
        instanceID = itemData.pop('instance_id', None)
        primaryID = itemData.pop('primary_identifier', None)
        logger.debug('Ingesting Item #{}'.format(
            primaryID['identifier'] if primaryID else 'unknown'
        ))
        existing = Item.lookup(
            session,
            itemData.get('identifiers', []),
            primaryID
        )

        if existing is None:
            logger.warning('Could not locate item, waiting 5 seconds for retry')
            time.sleep(5)
            existing = Item.lookup(
                session,
                itemData.get('identifiers', []),
                primaryID
            
            )
            if existing is None:
                logger.error('Item still not present, raise error')
                raise DBError(
                    'items',
                    'Could not locate item in database, skipping'
                )

        existing.update(session, itemData)

        existing.instance.work.date_modified = datetime.utcnow()

        return 'Item #{}'.format(existing.id)
