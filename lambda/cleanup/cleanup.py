"""
MedAssist Session Cleanup Lambda Function
Handles session termination and data cleanup
Requirements: 12.6, 22.5, 22.6
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DOCUMENTS_BUCKET = os.environ.get('DOCUMENTS_BUCKET', 'medassist-documents')
SESSION_TABLE = os.environ.get('SESSION_TABLE', 'MedAssist-Sessions')
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')
EMBEDDING_TABLE = os.environ.get('EMBEDDING_TABLE', 'MedAssist-Embeddings')

def handler(event, context):
    """
    Clean up expired sessions and associated data
    
    This function can be triggered by:
    1. EventBridge scheduled rule (runs every hour)
    2. Manual invocation for specific session
    """
    try:
        # Check if this is a manual cleanup for specific session
        if 'sessionId' in event:
            session_id = event['sessionId']
            cleanup_session(session_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'message': f'Session {session_id} cleaned up successfully'
                })
            }
        
        # Otherwise, clean up all expired sessions (older than 24 hours)
        cleanup_expired_sessions()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Expired sessions cleaned up successfully'
            })
        }
        
    except Exception as e:
        print(f"Error in cleanup: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': {
                    'code': 'CLEANUP_FAILED',
                    'message': 'Session cleanup failed',
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }

def cleanup_expired_sessions():
    """Clean up sessions older than 24 hours"""
    session_table = dynamodb.Table(SESSION_TABLE)
    
    # Calculate cutoff time (24 hours ago)
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    cutoff_timestamp = cutoff_time.isoformat()
    
    # Scan for expired sessions
    response = session_table.scan(
        FilterExpression='lastAccessedAt < :cutoff',
        ExpressionAttributeValues={
            ':cutoff': cutoff_timestamp
        }
    )
    
    expired_sessions = response.get('Items', [])
    print(f"Found {len(expired_sessions)} expired sessions")
    
    for session in expired_sessions:
        session_id = session.get('sessionId')
        if session_id:
            cleanup_session(session_id)

def cleanup_session(session_id):
    """Clean up all data for a specific session"""
    print(f"Cleaning up session: {session_id}")
    
    # 1. Delete documents from S3
    delete_session_documents_from_s3(session_id)
    
    # 2. Delete document records from DynamoDB
    delete_session_documents_from_dynamodb(session_id)
    
    # 3. Delete embeddings from DynamoDB
    delete_session_embeddings(session_id)
    
    # 4. Delete session record
    delete_session_record(session_id)
    
    print(f"Session {session_id} cleanup complete")

def delete_session_documents_from_s3(session_id):
    """Delete all documents for a session from S3"""
    try:
        prefix = f'sessions/{session_id}/'
        
        # List all objects with this prefix
        response = s3.list_objects_v2(
            Bucket=DOCUMENTS_BUCKET,
            Prefix=prefix
        )
        
        objects = response.get('Contents', [])
        
        if objects:
            # Delete all objects
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            s3.delete_objects(
                Bucket=DOCUMENTS_BUCKET,
                Delete={'Objects': delete_keys}
            )
            print(f"Deleted {len(delete_keys)} objects from S3 for session {session_id}")
        
    except Exception as e:
        print(f"Error deleting S3 objects for session {session_id}: {str(e)}")

def delete_session_documents_from_dynamodb(session_id):
    """Delete all document records for a session from DynamoDB"""
    try:
        document_table = dynamodb.Table(DOCUMENT_TABLE)
        
        # Query all documents for this session
        response = document_table.scan(
            FilterExpression='sessionId = :sid',
            ExpressionAttributeValues={
                ':sid': session_id
            }
        )
        
        documents = response.get('Items', [])
        
        # Delete each document
        for doc in documents:
            document_table.delete_item(
                Key={
                    'PK': doc['PK'],
                    'SK': doc['SK']
                }
            )
        
        print(f"Deleted {len(documents)} document records for session {session_id}")
        
    except Exception as e:
        print(f"Error deleting documents for session {session_id}: {str(e)}")

def delete_session_embeddings(session_id):
    """Delete all embeddings for a session from DynamoDB"""
    try:
        embedding_table = dynamodb.Table(EMBEDDING_TABLE)
        
        # Query all embeddings for this session
        response = embedding_table.scan(
            FilterExpression='sessionId = :sid',
            ExpressionAttributeValues={
                ':sid': session_id
            }
        )
        
        embeddings = response.get('Items', [])
        
        # Delete each embedding
        for emb in embeddings:
            embedding_table.delete_item(
                Key={
                    'PK': emb['PK'],
                    'SK': emb['SK']
                }
            )
        
        print(f"Deleted {len(embeddings)} embeddings for session {session_id}")
        
    except Exception as e:
        print(f"Error deleting embeddings for session {session_id}: {str(e)}")

def delete_session_record(session_id):
    """Delete the session record from DynamoDB"""
    try:
        session_table = dynamodb.Table(SESSION_TABLE)
        
        session_table.delete_item(
            Key={
                'PK': f'SESSION#{session_id}',
                'SK': 'METADATA'
            }
        )
        
        print(f"Deleted session record for {session_id}")
        
    except Exception as e:
        print(f"Error deleting session record for {session_id}: {str(e)}")
