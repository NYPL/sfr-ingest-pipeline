import os
from datetime import datetime

from sfrCore import Work, Instance, Item, Identifier

from lib.queryManager import queryWork
from lib.outputManager import OutputManager

from helpers.logHelpers import createLog

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
        work = Work.lookupWork(session, workData['identifiers'], primaryID)
        if work is not None:
            workUUID = work.uuid
            logger.info('Found exsting work {}. Placing record in update stream'.format(
                workUUID
            ))
            workData['primary_identifier'] = {
                'type': 'uuid',
                'identifier': workUUID.hex,
                'weight': 1
            }
            # TODO Create stream and make configurable in env file
            OutputManager.putKinesis(workData, 'sfr-db-update-development')
            return 'Existing work {}'.format(workUUID)
        dbWork = Work(session=session)
        epubsToLoad = dbWork.insert(workData)

        queryWork(session, dbWork, dbWork.uuid.hex)
        for deferredEpub in epubsToLoad: 
            OutputManager.putKinesis(
                deferredEpub,
                os.environ['EPUB_STREAM'],
                recType='item'
            )

        return dbWork.uuid.hex

    elif record['type'] == 'instance':
        logger.info('Ingesting instance record')
        instanceData = record['data']

        instanceID = Identifier.getByIdentifier(Instance, session, instanceData['identifiers'])
        if instanceID is not None:
            logger.info('Found exsting instance {}. Placing in update stream'.format(
                instanceID
            ))
            instanceData['primary_identifier'] = {
                'type': 'row_id',
                'identifier': instanceID,
                'weight': 1
            }
            OutputManager.putKinesis(
                instanceData,
                'sfr-db-update-development',
                recType='instance'
            )
            return 'Existing instance Row ID {}'.format(instanceID)

        dbInstance, epubsToLoad = Instance.createNew(session, instanceData)

        dbInstance.work.date_modfied = datetime.utcnow()

        for deferredEpub in epubsToLoad: 
            OutputManager.putKinesis(
                deferredEpub,
                os.environ['EPUB_STREAM'],
                recType='item'
            )

        return 'Instance #{}'.format(dbInstance.id)

    elif record['type'] == 'item':
        logger.info('Ingesting item record')
        itemData = record['data']
        
        itemID = Identifier.getByIdentifier(Item, session, itemData['identifiers'])
        if itemID is not None:
            logger.info('Found exsting item {}. Placing in update stream'.format(
                itemID
            ))
            itemData['primary_identifier'] = {
                'type': 'row_id',
                'identifier': itemID,
                'weight': 1
            }
            OutputManager.putKinesis(
                itemData,
                'sfr-db-update-development',
                recType='item'
            )
            return 'Existing item Row ID {}'.format(itemID)

        instanceID = itemData.pop('instance_id', None)

        dbItem = Item.createItem(session, itemData)

        logger.debug('Got new item record, adding to instance')
        Instance.addItemRecord(session, instanceID, dbItem)
        
        dbItem.instance.work.date_modified = datetime.utcnow()

        return 'Item #{}'.format(dbItem.id)

    elif record['type'] == 'access_report':
        logger.info('Ingest Accessibility Report')
        reportData = record['data']

        dbItem = Item.addReportData(session, reportData)
        
        if dbItem is not None:
            dbItem.instance.work.date_modified = datetime.utcnow()
