import boto3
import datetime

# Set the global variables
globalVars  = {}
globalVars['Owner']                 = "Miztiik"
globalVars['Environment']           = "Test"
globalVars['REGION_NAME']           = "ap-south-1"
globalVars['tagName']               = "Valaxy-Serverless-EBS-Penny-Pincher"
globalVars['findNeedle']            = "DeleteOn"
globalVars['RetentionDays']         = "7"
globalVars['tagsToExclude']         = "Do-Not-Delete"

ec2_client = boto3.client('ec2')

"""
This function looks at *all* snapshots that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. This function should be run at least
daily.
"""

def janitor_for_snapshots():
    account_ids = list()
    account_ids.append( boto3.client('sts').get_caller_identity().get('Account') )

    snap_older_than_RetentionDays = ( datetime.date.today() - datetime.timedelta(days= int(globalVars['RetentionDays'])) ).strftime('%Y-%m-%d')
    delete_today = datetime.date.today().strftime('%Y-%m-%d')
    filters = [
        {'Name': 'tag-key', 'Values': [globalVars['findNeedle']]},
        {'Name': 'tag-value', 'Values': [delete_today]},
    ]
    # Get list of Snaps with Tag 'globalVars['findNeedle']'
    snaps_to_remove = ec2_client.describe_snapshots(OwnerIds=account_ids,Filters=filters)

    # Get the snaps that doesn't have the tag and are older than Retention days
    all_snaps = ec2_client.describe_snapshots(OwnerIds=account_ids)
    for snap in all_snaps['Snapshots']:
        if snap['StartTime'].strftime('%Y-%m-%d') <= snap_older_than_RetentionDays:
            snaps_to_remove['Snapshots'].append(snap)

    snapsDeleted = {'Snapshots': []}

    for snap in snaps_to_remove['Snapshots']:
        ec2_client.delete_snapshot(SnapshotId=snap['SnapshotId'])
        snapsDeleted['Snapshots'].append({'Description': snap['Description'], 'SnapshotId': snap['SnapshotId'], 'OwnerId': snap['OwnerId']})

    snapsDeleted['Status']='{} Snapshots were Deleted'.format( len(snaps_to_remove['Snapshots']))

    return snapsDeleted
def lambda_handler(event, context):
    return janitor_for_snapshots()

if __name__ == '__main__':
    lambda_handler(None, None)
