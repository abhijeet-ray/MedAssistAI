"""
MedAssist Dashboard Lambda Function
Generates role-based dashboard insights

This Lambda is triggered after document embeddings are generated.
It retrieves document embeddings and metadata, extracts medical entities,
identifies key health metrics, and uses Amazon Bedrock Nova 2 Lite to generate
role-appropriate stat card summaries.

Requirements: 7.1-7.8, 9.1-9.6, 19.3
"""
import json
import os
import boto3
from datetime import datetime
from typing import List, Dict, Optional
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Environment variables
EMBEDDINGS_TABLE = os.environ.get('EMBEDDINGS_TABLE')
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE')


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON-compatible types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_role_description(role: str) -> str:
    """
    Get role description for prompt construction.
    
    Requirements: 1.3, 1.4, 1.5
    """
    role_descriptions = {
        'doctor': 'a medical doctor who needs clinical insights with technical terminology',
        'patient': 'a patient who needs simple explanations without medical jargon',
        'asha': 'an ASHA community health worker who needs practical guidance for community health'
    }
    return role_descriptions.get(role, role_descriptions['patient'])


def retrieve_session_embeddings(session_id: str) -> List[Dict]:
    """
    Retrieve all document embeddings for a session from DynamoDB.
    
    Requirements: 7.1
    
    Args:
        session_id: Session identifier
    
    Returns:
        List of embedding records with metadata
    """
    try:
        table = dynamodb.Table(EMBEDDINGS_TABLE)
        
        # Query all embeddings for this session
        response = table.query(
            IndexName='SessionIndex',
            KeyConditionExpression='sessionId = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        
        embeddings = response.get('Items', [])
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='SessionIndex',
                KeyConditionExpression='sessionId = :sid',
                ExpressionAttributeValues={':sid': session_id},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            embeddings.extend(response.get('Items', []))
        
        print(f"Retrieved {len(embeddings)} embeddings for session {session_id}")
        return embeddings
    
    except Exception as e:
        print(f"Error retrieving embeddings: {str(e)}")
        return []


def retrieve_document_metadata(document_id: str) -> Optional[Dict]:
    """
    Retrieve document metadata from DynamoDB.
    
    Args:
        document_id: Document identifier
    
    Returns:
        Document metadata dictionary or None
    """
    try:
        table = dynamodb.Table(DOCUMENT_TABLE)
        
        response = table.get_item(
            Key={
                'PK': f'DOC#{document_id}',
                'SK': 'METADATA'
            }
        )
        
        return response.get('Item')
    
    except Exception as e:
        print(f"Error retrieving document metadata: {str(e)}")
        return None


def extract_medical_entities_from_embeddings(embeddings: List[Dict]) -> List[Dict]:
    """
    Extract medical entities from embedding metadata.
    
    Requirements: 7.1
    
    Args:
        embeddings: List of embedding records
    
    Returns:
        List of unique medical entities
    """
    entities = []
    seen_entities = set()
    
    for emb in embeddings:
        metadata = emb.get('metadata', {})
        chunk_entities = metadata.get('medicalEntities', [])
        
        for entity in chunk_entities:
            entity_text = entity if isinstance(entity, str) else entity.get('text', '')
            if entity_text and entity_text not in seen_entities:
                seen_entities.add(entity_text)
                entities.append(entity if isinstance(entity, dict) else {'text': entity_text})
    
    return entities


def identify_key_metrics(embeddings: List[Dict], documents_metadata: List[Dict]) -> Dict:
    """
    Identify key health metrics from document content.
    
    Requirements: 7.1
    
    Args:
        embeddings: List of embedding records
        documents_metadata: List of document metadata
    
    Returns:
        Dictionary of identified metrics
    """
    metrics = {
        'glucose': [],
        'hemoglobin': [],
        'cholesterol': [],
        'blood_pressure': [],
        'risk_scores': [],
        'medications': [],
        'conditions': [],
        'test_results': []
    }
    
    # Extract from document metadata
    for doc in documents_metadata:
        medical_entities = doc.get('medicalEntities', [])
        
        for entity in medical_entities:
            entity_type = entity.get('type', '')
            entity_text = entity.get('text', '').lower()
            
            # Categorize entities
            if entity_type == 'MEDICATION':
                metrics['medications'].append(entity)
            elif entity_type == 'CONDITION':
                metrics['conditions'].append(entity)
            elif entity_type == 'TEST_RESULT':
                metrics['test_results'].append(entity)
                
                # Check for specific metrics
                if 'glucose' in entity_text or 'sugar' in entity_text or 'hba1c' in entity_text:
                    metrics['glucose'].append(entity)
                elif 'hemoglobin' in entity_text or 'hgb' in entity_text or 'hb' in entity_text:
                    metrics['hemoglobin'].append(entity)
                elif 'cholesterol' in entity_text or 'ldl' in entity_text or 'hdl' in entity_text:
                    metrics['cholesterol'].append(entity)
                elif 'blood pressure' in entity_text or 'bp' in entity_text or 'systolic' in entity_text:
                    metrics['blood_pressure'].append(entity)
    
    # Extract from chunk text
    for emb in embeddings:
        chunk_text = emb.get('chunkText', '').lower()
        
        # Look for numeric values with units
        import re
        
        # Glucose patterns (mg/dL, mmol/L)
        glucose_patterns = [
            r'glucose[:\s]+(\d+\.?\d*)\s*(mg/dl|mmol/l)',
            r'blood sugar[:\s]+(\d+\.?\d*)\s*(mg/dl|mmol/l)',
            r'hba1c[:\s]+(\d+\.?\d*)%?'
        ]
        for pattern in glucose_patterns:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            for match in matches:
                metrics['glucose'].append({
                    'text': f"Glucose: {match[0]} {match[1] if len(match) > 1 else ''}",
                    'value': match[0],
                    'unit': match[1] if len(match) > 1 else ''
                })
        
        # Hemoglobin patterns (g/dL)
        hb_patterns = [
            r'hemoglobin[:\s]+(\d+\.?\d*)\s*(g/dl)',
            r'hgb[:\s]+(\d+\.?\d*)\s*(g/dl)',
            r'hb[:\s]+(\d+\.?\d*)\s*(g/dl)'
        ]
        for pattern in hb_patterns:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            for match in matches:
                metrics['hemoglobin'].append({
                    'text': f"Hemoglobin: {match[0]} {match[1]}",
                    'value': match[0],
                    'unit': match[1]
                })
        
        # Cholesterol patterns (mg/dL)
        chol_patterns = [
            r'cholesterol[:\s]+(\d+\.?\d*)\s*(mg/dl)',
            r'ldl[:\s]+(\d+\.?\d*)\s*(mg/dl)',
            r'hdl[:\s]+(\d+\.?\d*)\s*(mg/dl)'
        ]
        for pattern in chol_patterns:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            for match in matches:
                metrics['cholesterol'].append({
                    'text': f"Cholesterol: {match[0]} {match[1]}",
                    'value': match[0],
                    'unit': match[1]
                })
    
    return metrics


def construct_dashboard_prompt(role: str, metrics: Dict, entities: List[Dict]) -> str:
    """
    Construct role-specific prompt for Bedrock.
    
    Requirements: 7.1, 9.1, 9.4, 9.5, 9.6
    
    Args:
        role: User role (doctor, patient, asha)
        metrics: Dictionary of identified metrics
        entities: List of medical entities
    
    Returns:
        Formatted prompt string
    """
    role_description = get_role_description(role)
    
    # Format entities for prompt
    entities_text = '\n'.join([
        f"- {e.get('text', str(e))}" for e in entities[:20]  # Limit to top 20
    ])
    
    # Format metrics for prompt
    metrics_text = []
    for metric_type, values in metrics.items():
        if values:
            metrics_text.append(f"{metric_type.replace('_', ' ').title()}: {len(values)} entries")
    
    metrics_summary = '\n'.join(metrics_text) if metrics_text else "No specific metrics identified"
    
    prompt = f"""Role: {role}
Context: Medical document analysis for {role_description}

Extracted Medical Entities:
{entities_text if entities_text else "No entities extracted"}

Identified Metrics:
{metrics_summary}

Task: Generate 3-5 health insight stat cards appropriate for a {role}.

Guidelines:
- For Doctor: Use clinical terminology, include specific values and ranges, focus on diagnostic insights
- For Patient: Use simple language, explain what values mean, provide actionable advice
- For ASHA Worker: Focus on community health guidance, practical advice, and preventive care

Format each stat card as a JSON object with these fields:
- title: Brief metric name (e.g., "Blood Glucose Level")
- value: Numeric value or status (e.g., "120" or "Normal")
- unit: Unit of measurement (e.g., "mg/dL" or empty string)
- insight: Role-appropriate explanation (2-3 sentences)
- severity: One of "normal", "warning", or "critical"

Return ONLY a valid JSON array of stat card objects, nothing else.
Example: [{{"title": "Blood Glucose", "value": "120", "unit": "mg/dL", "insight": "Your glucose level is within normal range.", "severity": "normal"}}]"""
    
    return prompt


def call_bedrock_for_insights(prompt: str) -> List[Dict]:
    """
    Call Amazon Bedrock Nova 2 Lite to generate stat card summaries.
    
    Requirements: 7.1, 9.2
    
    Args:
        prompt: Formatted prompt string
    
    Returns:
        List of stat card dictionaries
    """
    try:
        # Prepare request for Bedrock Nova 2 Lite
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 2000,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        # Call Bedrock Nova 2 Lite model
        response = bedrock_runtime.converse(
            modelId='us.amazon.nova-lite-v1:0',
            messages=request_body['messages'],
            inferenceConfig=request_body['inferenceConfig']
        )
        
        # Extract response text
        response_text = response['output']['message']['content'][0]['text']
        
        print(f"Bedrock response: {response_text[:200]}...")
        
        # Parse JSON response
        # Clean up response text (remove markdown code blocks if present)
        response_text = response_text.strip()
        if response_text.startswith('```'):
            # Remove markdown code block markers
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
        
        stat_cards = json.loads(response_text)
        
        # Validate stat cards structure
        if not isinstance(stat_cards, list):
            raise ValueError("Response is not a list")
        
        # Ensure each card has required fields
        validated_cards = []
        for card in stat_cards:
            if all(key in card for key in ['title', 'value', 'unit', 'insight', 'severity']):
                validated_cards.append(card)
        
        return validated_cards
    
    except json.JSONDecodeError as e:
        print(f"Error parsing Bedrock response as JSON: {str(e)}")
        # Return default stat card
        return [{
            'title': 'Document Analysis',
            'value': 'Completed',
            'unit': '',
            'insight': 'Your medical documents have been analyzed. Please consult with a healthcare professional for detailed interpretation.',
            'severity': 'normal'
        }]
    
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        # Return default stat card
        return [{
            'title': 'Document Analysis',
            'value': 'Completed',
            'unit': '',
            'insight': 'Your medical documents have been analyzed. Please consult with a healthcare professional for detailed interpretation.',
            'severity': 'normal'
        }]


def format_stat_cards(stat_cards: List[Dict]) -> List[Dict]:
    """
    Format stat cards with consistent structure.
    
    Requirements: 7.1
    
    Args:
        stat_cards: List of stat card dictionaries
    
    Returns:
        Formatted stat cards
    """
    formatted_cards = []
    
    for card in stat_cards:
        formatted_card = {
            'title': str(card.get('title', 'Health Metric')),
            'value': str(card.get('value', 'N/A')),
            'unit': str(card.get('unit', '')),
            'insight': str(card.get('insight', '')),
            'severity': card.get('severity', 'normal')
        }
        
        # Validate severity
        if formatted_card['severity'] not in ['normal', 'warning', 'critical']:
            formatted_card['severity'] = 'normal'
        
        formatted_cards.append(formatted_card)
    
    return formatted_cards


def handler(event, context):
    """
    Lambda handler to generate role-based dashboard insights.
    
    This function is triggered after document embeddings are generated.
    It performs the following operations:
    1. Retrieve all document embeddings for the session from DynamoDB
    2. Extract medical entities from document metadata
    3. Identify key metrics (glucose, hemoglobin, cholesterol, risk scores)
    4. Construct role-specific prompts for Bedrock
    5. Call Amazon Bedrock Nova 2 Lite to generate stat card summaries
    6. Format stat cards with title, value, unit, insight, severity
    7. Return dashboard data as JSON
    8. Log dashboard generation metrics to CloudWatch
    
    Requirements: 7.1-7.8, 9.1-9.6, 19.3
    
    Event format:
    {
        "sessionId": "string",
        "role": "doctor|patient|asha",
        "documentId": "string" (optional)
    }
    """
    print(json.dumps({
        'event': 'dashboard_generation_start',
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    try:
        # Parse event - handle both direct invocation and API Gateway
        if 'queryStringParameters' in event and event['queryStringParameters']:
            # API Gateway GET request
            query_params = event['queryStringParameters']
            session_id = query_params.get('sessionId')
            role = query_params.get('role', 'patient')
            document_id = query_params.get('documentId')
        else:
            # Direct invocation or POST body
            session_id = event.get('sessionId')
            role = event.get('role', 'patient')
            document_id = event.get('documentId')
        
        if not session_id:
            raise ValueError('Missing required parameter: sessionId')
        
        # Validate role
        if role not in ['doctor', 'patient', 'asha']:
            role = 'patient'
        
        print(f"Generating dashboard for session {session_id}, role {role}")
        
        # Retrieve all document embeddings for session (Req 7.1)
        embeddings = retrieve_session_embeddings(session_id)
        
        if not embeddings:
            print("No embeddings found for session")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'statCards': [],
                    'lastUpdated': datetime.utcnow().isoformat(),
                    'message': 'No documents processed yet'
                })
            }
        
        # Get unique document IDs from embeddings
        document_ids = list(set([emb.get('documentId') for emb in embeddings if emb.get('documentId')]))
        
        # Retrieve document metadata for all documents
        documents_metadata = []
        for doc_id in document_ids:
            doc_meta = retrieve_document_metadata(doc_id)
            if doc_meta:
                documents_metadata.append(doc_meta)
        
        # Extract medical entities from document metadata (Req 7.1)
        entities = extract_medical_entities_from_embeddings(embeddings)
        
        # Also get entities from document metadata
        for doc in documents_metadata:
            doc_entities = doc.get('medicalEntities', [])
            for entity in doc_entities:
                if entity not in entities:
                    entities.append(entity)
        
        print(f"Extracted {len(entities)} unique medical entities")
        
        # Identify key metrics (Req 7.1)
        metrics = identify_key_metrics(embeddings, documents_metadata)
        
        print(f"Identified metrics: {json.dumps({k: len(v) for k, v in metrics.items()})}")
        
        # Construct role-specific prompt (Req 7.1, 9.1)
        prompt = construct_dashboard_prompt(role, metrics, entities)
        
        # Call Bedrock Nova 2 Lite to generate insights (Req 7.1, 9.2)
        stat_cards = call_bedrock_for_insights(prompt)
        
        # Format stat cards (Req 7.1)
        formatted_cards = format_stat_cards(stat_cards)
        
        print(f"Generated {len(formatted_cards)} stat cards")
        
        # Log dashboard generation metrics to CloudWatch (Req 19.3)
        print(json.dumps({
            'event': 'dashboard_generation_complete',
            'sessionId': session_id,
            'role': role,
            'metrics': {
                'embeddings_count': len(embeddings),
                'documents_count': len(document_ids),
                'entities_count': len(entities),
                'stat_cards_count': len(formatted_cards)
            },
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Return dashboard data as JSON (Req 7.1)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'statCards': formatted_cards,
                'lastUpdated': datetime.utcnow().isoformat(),
                'sessionId': session_id,
                'role': role
            }, cls=DecimalEncoder)
        }
    
    except Exception as e:
        # Log error with details (Req 19.3)
        import traceback
        print(json.dumps({
            'event': 'dashboard_generation_error',
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'error': {
                    'code': 'DASHBOARD_GENERATION_FAILED',
                    'message': 'Unable to generate dashboard insights. Please try again.',
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }
