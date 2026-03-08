# RAG Lambda CORS Fix Design

## Overview

The RAG Lambda function (`lambda/rag/rag.py`) currently includes CORS headers in all response paths (success, validation errors, throttling, and server errors), but it lacks handling for OPTIONS preflight requests. When browsers make cross-origin requests, they first send an OPTIONS request to check if the actual request is allowed. Without proper OPTIONS handling, the browser blocks the subsequent POST request, causing CORS errors in the frontend.

This bugfix adds OPTIONS preflight request handling at the beginning of the Lambda handler to return appropriate CORS headers before any request processing occurs. Additionally, we'll refactor the CORS headers into a constant to ensure consistency and make future updates easier.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when the browser sends an OPTIONS preflight request to the /chat endpoint
- **Property (P)**: The desired behavior when OPTIONS requests are received - the Lambda should return 200 with CORS headers and empty body
- **Preservation**: Existing POST request handling, error responses, and business logic that must remain unchanged by the fix
- **handler**: The Lambda entry point function in `lambda/rag/rag.py` that processes all incoming requests
- **httpMethod**: The HTTP method from the event object that determines the request type (OPTIONS, POST, GET)
- **CORS Headers**: HTTP headers (Access-Control-Allow-Origin, Access-Control-Allow-Headers, Access-Control-Allow-Methods) that enable cross-origin requests

## Bug Details

### Bug Condition

The bug manifests when a browser sends an OPTIONS preflight request to the /chat endpoint before making the actual POST request. The Lambda handler does not check for OPTIONS requests and attempts to process them as regular chat requests, which fails validation and returns an error without proper preflight response handling.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LambdaEvent
  OUTPUT: boolean
  
  RETURN input.httpMethod == 'OPTIONS'
         AND input.path CONTAINS '/chat'
         AND NOT optionsHandlerExists()
END FUNCTION
```

### Examples

- **Preflight Request**: Browser sends `OPTIONS /chat` → Lambda attempts to parse body → Returns 400 error → Browser blocks subsequent POST request
- **POST Request After Failed Preflight**: Browser sends `POST /chat` with valid payload → Request is blocked by browser due to failed preflight → Frontend receives CORS error
- **Direct POST (No Preflight)**: Simple requests without custom headers work → But modern frontends with Content-Type: application/json trigger preflight
- **Edge Case**: GET requests to /chat (if configured) → Should also return CORS headers for consistency

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- POST requests with valid chat payloads must continue to generate embeddings, perform RAG retrieval, call Bedrock Nova, and return formatted responses
- Validation logic for sessionId, message, and message length must continue to work exactly as before
- Error responses (400, 500) must continue to return appropriate error codes and messages with CORS headers
- Throttling responses must continue to return user-friendly messages with throttled flag
- Chat history storage in DynamoDB must continue to persist user and AI messages
- CloudWatch metrics logging must continue to record query metrics and performance data

**Scope:**
All inputs that are NOT OPTIONS preflight requests should be completely unaffected by this fix. This includes:
- POST requests with chat payloads (the primary use case)
- Error handling for invalid requests
- Throttling responses from Bedrock
- All business logic for RAG retrieval and response generation

## Hypothesized Root Cause

Based on the bug description and code analysis, the root cause is clear:

1. **Missing OPTIONS Handler**: The Lambda handler function does not check the `httpMethod` field in the event object at the beginning of execution. It immediately attempts to parse the request body and validate fields, which fails for OPTIONS requests that have no body.

2. **Browser Preflight Behavior**: Modern browsers automatically send OPTIONS preflight requests when making cross-origin requests with custom headers (like Content-Type: application/json). The Lambda must respond to these preflight requests with a 200 status and CORS headers before the browser will send the actual POST request.

3. **Existing CORS Headers Are Correct**: The Lambda already includes proper CORS headers in all response paths (lines 586-589, 606-609, 636-639, 694-697, 722-725), but these are only returned for POST requests that reach those code paths. OPTIONS requests fail earlier in validation.

## Correctness Properties

Property 1: Bug Condition - OPTIONS Preflight Handling

_For any_ HTTP request where the method is OPTIONS, the fixed Lambda handler SHALL immediately return a 200 response with CORS headers (Access-Control-Allow-Origin: *, Access-Control-Allow-Headers: *, Access-Control-Allow-Methods: OPTIONS,POST,GET) and an empty body, without attempting to process the request body or perform any business logic.

**Validates: Requirements 2.2**

Property 2: Preservation - POST Request Processing

_For any_ HTTP request where the method is NOT OPTIONS (e.g., POST, GET), the fixed Lambda handler SHALL process the request exactly as the original handler does, preserving all validation logic, error handling, RAG retrieval, Bedrock calls, chat history storage, and metrics logging.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**File**: `lambda/rag/rag.py`

**Function**: `handler`

**Specific Changes**:

1. **Add CORS Headers Constant** (at module level, before handler function):
   - Create a constant dictionary `CORS_HEADERS` containing the three required headers
   - This ensures consistency across all response paths and makes future updates easier
   - Location: Add after imports, around line 50

2. **Add OPTIONS Preflight Handler** (at the beginning of handler function):
   - Check if `event.get('httpMethod')` equals 'OPTIONS'
   - If true, immediately return 200 response with CORS headers and empty body
   - Location: Add as first logic in handler function, after logging start event (around line 570)

3. **Refactor Existing CORS Headers** (in all return statements):
   - Replace inline CORS header dictionaries with reference to `CORS_HEADERS` constant
   - Update 5 return statements: validation errors (2), throttling response (1), success response (1), error response (1)
   - Location: Lines 586-589, 606-609, 636-639, 694-697, 722-725

4. **Update Response Headers** (ensure consistency):
   - Verify all responses use the same CORS headers
   - Ensure Content-Type: application/json is included in all responses
   - No changes to response body structure or business logic

### Code Structure

```python
# At module level (after imports)
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}

def handler(event, context):
    """Lambda handler for chat queries using hybrid RAG retrieval."""
    start_time = time.time()
    
    print(json.dumps({
        'event': 'rag_start',
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    # Handle OPTIONS preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({})
        }
    
    try:
        # Existing request processing logic...
        # All return statements now use CORS_HEADERS constant
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (OPTIONS requests failing), then verify the fix works correctly (OPTIONS returns 200) and preserves existing behavior (POST requests unchanged).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that OPTIONS requests are not handled properly.

**Test Plan**: Write tests that simulate OPTIONS requests to the Lambda handler. Run these tests on the UNFIXED code to observe failures and confirm the root cause.

**Test Cases**:
1. **OPTIONS Preflight Test**: Send OPTIONS request with httpMethod='OPTIONS' → Expect 400 error on unfixed code (missing sessionId/message)
2. **OPTIONS with Empty Body**: Send OPTIONS request with empty body → Expect validation error on unfixed code
3. **OPTIONS Response Headers**: Check if OPTIONS response includes CORS headers → Expect missing or incorrect headers on unfixed code
4. **Browser Preflight Simulation**: Simulate full browser preflight flow (OPTIONS then POST) → Expect preflight failure blocks POST on unfixed code

**Expected Counterexamples**:
- OPTIONS requests return 400 error with "Missing required fields" message
- OPTIONS requests attempt to parse body and validate fields instead of returning immediately
- Possible causes: no httpMethod check, no early return for OPTIONS, validation runs before method check

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (OPTIONS requests), the fixed function produces the expected behavior (200 response with CORS headers).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := handler_fixed(input, context)
  ASSERT result.statusCode == 200
  ASSERT result.headers['Access-Control-Allow-Origin'] == '*'
  ASSERT result.headers['Access-Control-Allow-Headers'] == '*'
  ASSERT result.headers['Access-Control-Allow-Methods'] == 'OPTIONS,POST,GET'
  ASSERT result.body == '{}'
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (POST requests), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT handler_original(input, context) == handler_fixed(input, context)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (valid/invalid POST requests)
- It catches edge cases that manual unit tests might miss (empty fields, long messages, special characters)
- It provides strong guarantees that behavior is unchanged for all non-OPTIONS inputs

**Test Plan**: Observe behavior on UNFIXED code first for POST requests with various payloads, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Valid POST Preservation**: Send valid POST request with sessionId, role, message → Verify same response structure and business logic execution
2. **Invalid POST Preservation**: Send POST with missing fields → Verify same 400 error response
3. **Long Message Preservation**: Send POST with message > 1000 chars → Verify same MESSAGE_TOO_LONG error
4. **Throttling Preservation**: Simulate embedding generation failure → Verify same throttling response with throttled flag
5. **Error Handling Preservation**: Simulate exception in handler → Verify same 500 error response

### Unit Tests

- Test OPTIONS request returns 200 with CORS headers and empty body
- Test OPTIONS request does not execute business logic (no embedding generation, no DB calls)
- Test POST request with valid payload continues to work correctly
- Test POST request with invalid payload returns appropriate 400 error
- Test POST request with long message returns MESSAGE_TOO_LONG error
- Test error handling returns 500 with CORS headers

### Property-Based Tests

- Generate random OPTIONS requests with various headers and paths → Verify all return 200 with CORS headers
- Generate random valid POST requests with different sessionIds, roles, messages → Verify all process correctly
- Generate random invalid POST requests (missing fields, wrong types) → Verify all return appropriate errors
- Generate random message lengths (0-2000 chars) → Verify validation works correctly

### Integration Tests

- Test full browser preflight flow: OPTIONS → 200 → POST → 200 with chat response
- Test CORS headers are present in all response types (success, validation error, throttling, server error)
- Test Lambda deployment and API Gateway integration with CORS configuration
- Test frontend can successfully make requests after fix is deployed

## Deployment Steps

### Pre-Deployment Validation

1. **Run Unit Tests**: Execute all unit tests locally to verify OPTIONS handling and preservation of POST behavior
2. **Run Integration Tests**: Test Lambda function locally using AWS SAM or LocalStack
3. **Code Review**: Verify CORS_HEADERS constant is used consistently in all return statements
4. **Verify No Breaking Changes**: Confirm all existing POST request tests pass

### Deployment Process

1. **Update Lambda Code**:
   - Modify `lambda/rag/rag.py` with OPTIONS handler and CORS_HEADERS constant
   - Commit changes to version control

2. **Package Lambda Function**:
   ```bash
   cd lambda/rag
   zip -r rag-function.zip rag.py
   ```

3. **Deploy to AWS Lambda**:
   ```bash
   aws lambda update-function-code \
     --function-name medassist-rag-lambda \
     --zip-file fileb://rag-function.zip \
     --region us-east-1
   ```

4. **Verify Deployment**:
   ```bash
   aws lambda get-function \
     --function-name medassist-rag-lambda \
     --region us-east-1
   ```

5. **Test OPTIONS Endpoint**:
   ```bash
   curl -X OPTIONS https://api.medassist.example.com/chat \
     -H "Origin: https://frontend.medassist.example.com" \
     -v
   ```
   Expected: 200 response with CORS headers

6. **Test POST Endpoint**:
   ```bash
   curl -X POST https://api.medassist.example.com/chat \
     -H "Content-Type: application/json" \
     -H "Origin: https://frontend.medassist.example.com" \
     -d '{"sessionId":"test-123","role":"patient","message":"What is diabetes?"}' \
     -v
   ```
   Expected: 200 response with chat answer and CORS headers

### Post-Deployment Validation

1. **Monitor CloudWatch Logs**: Check for any errors or unexpected behavior in Lambda logs
2. **Test Frontend Integration**: Verify frontend application can successfully make requests without CORS errors
3. **Monitor Error Rates**: Check CloudWatch metrics for any increase in 4xx or 5xx errors
4. **Verify Metrics**: Confirm query metrics are still being logged correctly
5. **Test All Response Paths**: Verify CORS headers are present in success, validation error, throttling, and server error responses

### Rollback Plan

If issues are detected after deployment:

1. **Immediate Rollback**:
   ```bash
   aws lambda update-function-code \
     --function-name medassist-rag-lambda \
     --zip-file fileb://rag-function-previous.zip \
     --region us-east-1
   ```

2. **Investigate Issues**: Review CloudWatch logs and error messages

3. **Fix and Redeploy**: Address issues in code and follow deployment process again

### API Gateway Configuration (If Needed)

If CORS issues persist after Lambda fix, verify API Gateway CORS configuration:

1. **Enable CORS in API Gateway**:
   - Navigate to API Gateway console
   - Select the /chat resource
   - Click "Enable CORS"
   - Configure allowed origins, headers, and methods

2. **Deploy API Gateway Changes**:
   - Click "Actions" → "Deploy API"
   - Select deployment stage (e.g., prod)
   - Confirm deployment

Note: The Lambda fix should be sufficient if API Gateway is configured to proxy requests directly to Lambda. API Gateway CORS configuration is only needed if using Lambda proxy integration without CORS handling in Lambda code.
