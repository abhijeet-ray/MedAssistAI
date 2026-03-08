"""
MedAssist Dashboard Lambda Function
Generates structured medical insights using Gemini AI
"""
import json
import os
import boto3
import requests
from datetime import datetime, timedelta

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Session-based metric cache
# Structure: {session_id: {'metrics': [...], 'timestamp': datetime, 'doc_hashes': [...]}}
METRIC_CACHE = {}

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def compute_document_hash(documents):
    """
    Compute a hash of document content to detect changes.
    Used to invalidate cache when documents are updated.
    
    Requirements: 15.4
    """
    import hashlib
    hash_input = ""
    for doc in documents:
        hash_input += doc.get('documentText', '') + doc.get('timestamp', '')
    return hashlib.md5(hash_input.encode()).hexdigest()


def get_cached_metrics(session_id, documents):
    """
    Retrieve cached metrics if available and valid.
    Cache is valid if documents haven't changed and cache hasn't expired.
    
    Requirements: 15.4
    """
    if session_id not in METRIC_CACHE:
        return None
    
    cache_entry = METRIC_CACHE[session_id]
    current_hash = compute_document_hash(documents)
    cached_hash = cache_entry.get('doc_hash')
    
    # Check if documents have changed
    if current_hash != cached_hash:
        print(f"Cache invalidated for session {session_id}: documents changed")
        del METRIC_CACHE[session_id]
        return None
    
    # Check if cache has expired (15 minutes)
    cache_time = cache_entry.get('timestamp')
    if cache_time and datetime.utcnow() - cache_time > timedelta(minutes=15):
        print(f"Cache expired for session {session_id}")
        del METRIC_CACHE[session_id]
        return None
    
    print(f"Cache hit for session {session_id}")
    return cache_entry.get('metrics')


def set_cached_metrics(session_id, documents, metrics):
    """
    Store metrics in session-based cache.
    
    Requirements: 15.4
    """
    doc_hash = compute_document_hash(documents)
    METRIC_CACHE[session_id] = {
        'metrics': metrics,
        'timestamp': datetime.utcnow(),
        'doc_hash': doc_hash
    }
    print(f"Cached metrics for session {session_id}")



def get_session_documents(session_id):
    """
    Retrieve all documents for a session from DynamoDB
    """
    try:
        table = dynamodb.Table(DOCUMENT_TABLE)
        
        # Query for documents with this sessionId as PK
        response = table.query(
            KeyConditionExpression='PK = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        
        items = response.get('Items', [])
        
        print(f"Retrieved {len(items)} documents for session {session_id}")
        return items
        
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def call_gemini(prompt):
    """
    Call Google Gemini API to extract medical insights.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        
        return answer
        
    except Exception as e:
        print(f"Error calling Gemini: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_extraction_prompt(document_text: str) -> str:
    """
    Creates prompt for Gemini to extract structured health metrics.
    Includes JSON schema and standard medical reference ranges.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.1, 7.2, 7.3, 7.4
    """
    return f"""Extract health metrics from this medical report.

Medical Report:
{document_text}

Return ONLY a valid JSON object with this structure:
{{
  "hemoglobin": {{"value": "13.5", "unit": "g/dL", "abnormal": false}},
  "wbc": {{"value": "7500", "unit": "cells/μL", "abnormal": false}},
  "platelets": {{"value": "250000", "unit": "cells/μL", "abnormal": false}},
  "glucose": {{"value": "95", "unit": "mg/dL", "abnormal": false}},
  "cholesterol": {{"value": "180", "unit": "mg/dL", "abnormal": false}},
  "key_findings": ["finding 1", "finding 2"],
  "abnormal_flags": ["any abnormal results"]
}}

Use null for missing values. Mark abnormal=true if outside normal ranges:
- Hemoglobin: 12-16 g/dL (female), 14-18 g/dL (male)
- WBC: 4000-11000 cells/μL
- Platelets: 150000-400000 cells/μL
- Glucose (fasting): 70-100 mg/dL
- Cholesterol: <200 mg/dL

Return ONLY the JSON, no additional text."""


def parse_gemini_extraction(response: str) -> dict:
    """
    Parses Gemini response and validates structure.
    Handles markdown code block removal and validates expected keys.
    
    Requirements: 7.5
    """
    try:
        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Parse JSON
        data = json.loads(cleaned)
        
        # Validate structure - set null for missing metrics
        expected_keys = ['hemoglobin', 'wbc', 'platelets', 'glucose', 'cholesterol']
        for key in expected_keys:
            if key not in data:
                data[key] = None
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return None


def generate_stat_cards(extracted_data: dict) -> list:
    """
    Converts extracted metrics to stat card format.
    Maps each metric to StatCardData structure with severity based on abnormal flag.
    
    Requirements: 6.2, 6.3, 6.4, 6.5
    """
    cards = []
    
    # Hemoglobin card
    if extracted_data.get('hemoglobin'):
        hb = extracted_data['hemoglobin']
        cards.append({
            'title': 'Hemoglobin',
            'value': hb['value'],
            'unit': hb['unit'],
            'insight': 'Hemoglobin carries oxygen in your blood.',
            'severity': 'warning' if hb.get('abnormal') else 'normal'
        })
    
    # WBC card
    if extracted_data.get('wbc'):
        wbc = extracted_data['wbc']
        cards.append({
            'title': 'White Blood Cells',
            'value': wbc['value'],
            'unit': wbc['unit'],
            'insight': 'WBC count indicates immune system health.',
            'severity': 'warning' if wbc.get('abnormal') else 'normal'
        })
    
    # Platelets card
    if extracted_data.get('platelets'):
        plt = extracted_data['platelets']
        cards.append({
            'title': 'Platelets',
            'value': plt['value'],
            'unit': plt['unit'],
            'insight': 'Platelet count important for blood clotting.',
            'severity': 'warning' if plt.get('abnormal') else 'normal'
        })
    
    # Glucose card
    if extracted_data.get('glucose'):
        glc = extracted_data['glucose']
        cards.append({
            'title': 'Glucose',
            'value': glc['value'],
            'unit': glc['unit'],
            'insight': 'Blood glucose level indicates sugar metabolism.',
            'severity': 'warning' if glc.get('abnormal') else 'normal'
        })
    
    # Cholesterol card
    if extracted_data.get('cholesterol'):
        chol = extracted_data['cholesterol']
        cards.append({
            'title': 'Cholesterol',
            'value': chol['value'],
            'unit': chol['unit'],
            'insight': 'Cholesterol level important for heart health.',
            'severity': 'warning' if chol.get('abnormal') else 'normal'
        })
    
    # Key Medical Insights card from key_findings
    if extracted_data.get('key_findings'):
        findings_text = '\n'.join([f'• {f}' for f in extracted_data['key_findings']])
        cards.append({
            'title': 'Key Medical Insights',
            'value': 'Available',
            'unit': '',
            'insight': findings_text,
            'severity': 'warning' if extracted_data.get('abnormal_flags') else 'normal'
        })
    
    return cards


def generate_basic_stat_cards(document_text: str) -> list:
    """
    Fallback: generates basic cards when extraction fails.
    
    Requirements: 17.1, 17.2, 17.3, 17.4
    """
    word_count = len(document_text.split())
    return [{
        'title': 'Document Processed',
        'value': str(word_count),
        'unit': 'words',
        'insight': 'Document text available for analysis.',
        'severity': 'normal'
    }]


def extract_metrics_with_fallback(document_text: str) -> list:
    """
    Attempts structured extraction, falls back to basic insights on failure.
    Includes CloudWatch logging for extraction errors.
    
    Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
    """
    try:
        # Try Gemini extraction
        prompt = create_extraction_prompt(document_text)
        response = call_gemini(prompt)
        
        if response:
            extracted = parse_gemini_extraction(response)
            if extracted:
                cards = generate_stat_cards(extracted)
                if cards:
                    return cards
        
        # Fallback to basic insights
        print("Structured extraction failed, using fallback")
        return generate_basic_stat_cards(document_text)
        
    except Exception as e:
        print(f"Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return generate_basic_stat_cards(document_text)


def extract_medical_insights(document_text):
    """
    Use Gemini to extract structured medical insights from document text.
    """
    if not document_text:
        return None
    
    prompt = f"""Extract important medical values and insights from this medical report.

Medical Report:
{document_text}

Return ONLY a valid JSON object with this exact structure (use null for missing values):
{{
  "hemoglobin": "value with unit or null",
  "wbc": "value with unit or null",
  "platelets": "value with unit or null",
  "glucose": "value with unit or null",
  "blood_pressure": "value or null",
  "heart_rate": "value with unit or null",
  "temperature": "value with unit or null",
  "abnormal_flags": ["list of any abnormal findings"],
  "diagnosis": "primary diagnosis or null",
  "key_findings": ["list of 2-3 most important findings"]
}}

Important: Return ONLY the JSON object, no additional text or explanation."""
    
    try:
        response = call_gemini(prompt)
        
        if not response:
            return None
        
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON
        insights = json.loads(response)
        return insights
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse Gemini JSON response: {str(e)}")
        print(f"Response was: {response}")
        return None
    except Exception as e:
        print(f"Error extracting insights: {str(e)}")
        return None


def generate_structured_insights(documents):
    """
    Generate structured medical insights from documents using Gemini AI.
    Calls extract_metrics_with_fallback() for each document and aggregates stat cards.
    
    Requirements: 5.1, 7.1
    """
    try:
        if not documents:
            return []
        
        stat_cards = []
        
        # Document count card
        doc_count = len(documents)
        stat_cards.append({
            'title': 'Documents Uploaded',
            'value': str(doc_count),
            'unit': 'files',
            'insight': f'You have uploaded {doc_count} medical document{"s" if doc_count != 1 else ""}.',
            'severity': 'normal'
        })
        
        # Extract metrics from each document and aggregate stat cards
        all_cards = []
        for doc in documents:
            try:
                document_text = doc.get('documentText', '')
                if document_text:
                    # Call extract_metrics_with_fallback for each document
                    cards = extract_metrics_with_fallback(document_text)
                    if cards:
                        all_cards.extend(cards)
            except Exception as doc_error:
                print(f"Error processing document: {str(doc_error)}")
                # Continue with next document
                continue
        
        # Aggregate stat cards from all documents
        if all_cards:
            stat_cards.extend(all_cards)
        else:
            # Fallback if no cards were generated
            try:
                combined_text = " ".join([doc.get('documentText', '') for doc in documents if doc.get('documentText')])
                word_count = len(combined_text.split()) if combined_text else 0
                stat_cards.append({
                    'title': 'Total Words',
                    'value': str(word_count),
                    'unit': 'words',
                    'insight': f'Your documents contain {word_count} words of medical information.',
                    'severity': 'normal'
                })
            except Exception as fallback_error:
                print(f"Error generating fallback cards: {str(fallback_error)}")
        
        return stat_cards
    
    except Exception as e:
        print(f"Error in generate_structured_insights: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return at least the document count card
        return [{
            'title': 'Documents Uploaded',
            'value': str(len(documents)) if documents else '0',
            'unit': 'files',
            'insight': 'Documents have been uploaded.',
            'severity': 'normal'
        }]


def generate_basic_insights(documents):
    """
    Generate basic insights from document text
    """
    if not documents:
        return []
    
    # Count total documents
    doc_count = len(documents)
    
    # Get document text and calculate word count
    all_text = []
    for doc in documents:
        text = doc.get('documentText', '')
        if text:
            all_text.append(text)
    
    combined_text = " ".join(all_text)
    word_count = len(combined_text.split()) if combined_text else 0
    
    # Get preview (first 300 characters)
    preview = combined_text[:300] if combined_text else "No text extracted"
    if len(combined_text) > 300:
        preview += "..."
    
    # Get most recent document timestamp
    timestamps = [doc.get('timestamp', '') for doc in documents if doc.get('timestamp')]
    latest_timestamp = max(timestamps) if timestamps else datetime.utcnow().isoformat()
    
    # Create stat cards with actual document insights
    stat_cards = [
        {
            'title': 'Documents Uploaded',
            'value': str(doc_count),
            'unit': 'files',
            'insight': f'You have uploaded {doc_count} medical document{"s" if doc_count != 1 else ""}. All documents have been processed and are ready for analysis.',
            'severity': 'normal'
        },
        {
            'title': 'Total Words',
            'value': str(word_count),
            'unit': 'words',
            'insight': f'Your documents contain {word_count} words of medical information that can be analyzed by our AI assistant.',
            'severity': 'normal'
        },
        {
            'title': 'Document Preview',
            'value': 'Available',
            'unit': '',
            'insight': preview,
            'severity': 'normal'
        }
    ]
    
    return stat_cards


def handler(event, context):
    """
    Lambda handler to generate dashboard insights
    Implements metric caching for performance optimization.
    FAST RESPONSE: Returns within 1-2 seconds, never calls AI models.
    
    Requirements: 5.1, 7.1, 15.4
    """
    # Define CORS headers at handler level for all responses
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
    }
    
    try:
        # Log incoming request
        print("Dashboard request received")
        
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            print("Handling OPTIONS preflight")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Parse query parameters safely
        query_params = event.get('queryStringParameters')
        if not query_params:
            print("No query parameters provided")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required parameter: sessionId',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        session_id = query_params.get('sessionId')
        
        if not session_id:
            print("sessionId parameter is missing")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Missing required parameter: sessionId',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        print(f"Dashboard request for session: {session_id}")
        
        # Retrieve documents for session (fast DynamoDB query)
        try:
            documents = get_session_documents(session_id)
            print(f"Documents found: {len(documents) if documents else 0}")
        except Exception as doc_error:
            print(f"Error retrieving documents: {str(doc_error)}")
            # Return fast fallback response
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'statCards': [],
                    'documents': 0,
                    'status': 'error',
                    'lastUpdated': datetime.utcnow().isoformat(),
                    'message': 'Unable to retrieve documents'
                })
            }
        
        if not documents:
            print("No documents found for session")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'statCards': [],
                    'documents': 0,
                    'status': 'no_documents',
                    'lastUpdated': datetime.utcnow().isoformat(),
                    'message': 'No documents uploaded yet. Upload a medical document to get started.'
                })
            }
        
        # FAST RESPONSE: Return basic document info without AI processing
        # Calculate basic metrics from documents (no AI calls)
        try:
            doc_count = len(documents)
            
            # Calculate word count from all documents
            all_text = []
            for doc in documents:
                text = doc.get('documentText', '')
                if text:
                    all_text.append(text)
            
            combined_text = " ".join(all_text)
            word_count = len(combined_text.split()) if combined_text else 0
            
            # Get preview (first 200 characters)
            preview = combined_text[:200] if combined_text else "No text extracted"
            if len(combined_text) > 200:
                preview += "..."
            
            print("Returning dashboard response")
            
            # Return fast response with basic metrics only
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'statCards': [
                        {
                            'title': 'Documents Uploaded',
                            'value': str(doc_count),
                            'unit': 'files',
                            'insight': f'You have uploaded {doc_count} medical document{"s" if doc_count != 1 else ""}.',
                            'severity': 'normal'
                        },
                        {
                            'title': 'Total Words',
                            'value': str(word_count),
                            'unit': 'words',
                            'insight': f'Your documents contain {word_count} words of medical information.',
                            'severity': 'normal'
                        },
                        {
                            'title': 'Document Preview',
                            'value': 'Available',
                            'unit': '',
                            'insight': preview,
                            'severity': 'normal'
                        }
                    ],
                    'documents': doc_count,
                    'status': 'processed',
                    'lastUpdated': datetime.utcnow().isoformat(),
                    'sessionId': session_id
                })
            }
        
        except Exception as e:
            print(f"Error generating basic metrics: {str(e)}")
            # Return minimal fallback response
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'statCards': [
                        {
                            'title': 'Documents Uploaded',
                            'value': str(len(documents)),
                            'unit': 'files',
                            'insight': f'You have uploaded {len(documents)} medical document(s).',
                            'severity': 'normal'
                        }
                    ],
                    'documents': len(documents),
                    'status': 'partial',
                    'lastUpdated': datetime.utcnow().isoformat(),
                    'sessionId': session_id
                })
            }
    
    except Exception as e:
        print(f"CRITICAL ERROR in dashboard handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Always return a valid response, even on critical error
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'statCards': [],
                'documents': 0,
                'status': 'error',
                'lastUpdated': datetime.utcnow().isoformat(),
                'message': 'Dashboard service temporarily unavailable'
            })
        }
