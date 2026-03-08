# Implementation Plan

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - OPTIONS Preflight Request Handling
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate OPTIONS requests are not handled properly
  - **Scoped PBT Approach**: Scope the property to OPTIONS requests with httpMethod='OPTIONS' and path containing '/chat'
  - Test that OPTIONS requests return 200 with CORS headers and empty body (from Bug Condition in design)
  - The test assertions should match the Expected Behavior Properties from design:
    - statusCode == 200
    - headers['Access-Control-Allow-Origin'] == '*'
    - headers['Access-Control-Allow-Headers'] == '*'
    - headers['Access-Control-Allow-Methods'] == 'OPTIONS,POST,GET'
    - body == '{}'
  - Run test on UNFIXED code (lambda/rag/rag.py)
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found:
    - OPTIONS requests likely return 400 error with "Missing required fields"
    - OPTIONS requests attempt to parse body and validate fields instead of returning immediately
    - CORS headers may be missing or incorrect in OPTIONS response
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.2_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - POST Request Processing
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-OPTIONS inputs (POST requests)
  - Test cases to observe and capture:
    - Valid POST request with sessionId, role, message → Observe response structure and business logic execution
    - Invalid POST with missing fields → Observe 400 error response
    - POST with message > 1000 chars → Observe MESSAGE_TOO_LONG error
    - POST with various valid payloads → Observe RAG retrieval and Bedrock response generation
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For all POST requests with valid payloads, verify same response structure
    - For all POST requests with invalid payloads, verify same error responses
    - For all POST requests, verify business logic executes (embedding generation, DB calls, metrics logging)
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code (lambda/rag/rag.py)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Fix for OPTIONS preflight request handling

  - [ ] 3.1 Add CORS headers constant at module level
    - Create `CORS_HEADERS` constant dictionary after imports (around line 50)
    - Include all required headers: Content-Type, Access-Control-Allow-Origin, Access-Control-Allow-Headers, Access-Control-Allow-Methods
    - This ensures consistency across all response paths
    - _Bug_Condition: isBugCondition(input) where input.httpMethod == 'OPTIONS' AND input.path CONTAINS '/chat' AND NOT optionsHandlerExists()_
    - _Expected_Behavior: For OPTIONS requests, return 200 with CORS headers and empty body (Property 1 from design)_
    - _Preservation: POST requests must continue to process exactly as before (Property 2 from design)_
    - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 3.2 Add OPTIONS preflight handler at beginning of handler function
    - Check if `event.get('httpMethod')` equals 'OPTIONS'
    - If true, immediately return 200 response with CORS_HEADERS and empty body
    - Add after logging start event (around line 570)
    - Ensure no business logic executes for OPTIONS requests
    - _Bug_Condition: isBugCondition(input) where input.httpMethod == 'OPTIONS'_
    - _Expected_Behavior: OPTIONS requests return 200 with CORS headers immediately (Property 1 from design)_
    - _Preservation: POST requests unaffected by this early return (Property 2 from design)_
    - _Requirements: 2.2_

  - [ ] 3.3 Refactor existing CORS headers to use constant
    - Replace inline CORS header dictionaries with reference to CORS_HEADERS constant
    - Update 5 return statements:
      - Validation errors (lines 586-589, 606-609)
      - Throttling response (line 636-639)
      - Success response (line 694-697)
      - Error response (line 722-725)
    - Verify all responses use consistent CORS headers
    - _Bug_Condition: N/A (refactoring for consistency)_
    - _Expected_Behavior: All responses include consistent CORS headers_
    - _Preservation: Response structure and business logic unchanged (Property 2 from design)_
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - OPTIONS Preflight Request Handling
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify OPTIONS requests return 200 with CORS headers and empty body
    - Verify no business logic executes for OPTIONS requests
    - _Requirements: 2.2_

  - [ ] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - POST Request Processing
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all POST request tests still pass after fix (no regressions)
    - Verify valid POST requests continue to generate embeddings, perform RAG retrieval, call Bedrock, and return responses
    - Verify invalid POST requests continue to return appropriate error responses
    - Verify error handling, throttling, and metrics logging unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Package and deploy Lambda function

  - [ ] 4.1 Run all unit tests locally
    - Execute unit tests for OPTIONS handling
    - Execute unit tests for POST request preservation
    - Verify all tests pass before deployment
    - _Requirements: 2.2, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 4.2 Package Lambda function
    - Navigate to lambda/rag directory
    - Create deployment package: `zip -r rag-function.zip rag.py`
    - Verify zip file contains updated rag.py with OPTIONS handler
    - _Requirements: 2.2_

  - [ ] 4.3 Deploy to AWS Lambda
    - Update Lambda function code using AWS CLI:
      ```bash
      aws lambda update-function-code \
        --function-name medassist-rag-lambda \
        --zip-file fileb://rag-function.zip \
        --region us-east-1
      ```
    - Verify deployment success
    - _Requirements: 2.2_

  - [ ] 4.4 Verify Lambda deployment
    - Check Lambda function configuration:
      ```bash
      aws lambda get-function \
        --function-name medassist-rag-lambda \
        --region us-east-1
      ```
    - Verify LastModified timestamp is recent
    - Verify CodeSize reflects updated code
    - _Requirements: 2.2_

- [ ] 5. Post-deployment verification

  - [ ] 5.1 Test OPTIONS endpoint
    - Send OPTIONS request to /chat endpoint:
      ```bash
      curl -X OPTIONS https://api.medassist.example.com/chat \
        -H "Origin: https://frontend.medassist.example.com" \
        -v
      ```
    - Verify 200 response with CORS headers
    - Verify Access-Control-Allow-Origin: *
    - Verify Access-Control-Allow-Headers: *
    - Verify Access-Control-Allow-Methods: OPTIONS,POST,GET
    - _Requirements: 2.2_

  - [ ] 5.2 Test POST endpoint
    - Send POST request to /chat endpoint:
      ```bash
      curl -X POST https://api.medassist.example.com/chat \
        -H "Content-Type: application/json" \
        -H "Origin: https://frontend.medassist.example.com" \
        -d '{"sessionId":"test-123","role":"patient","message":"What is diabetes?"}' \
        -v
      ```
    - Verify 200 response with chat answer
    - Verify CORS headers present in response
    - Verify business logic executes correctly (RAG retrieval, Bedrock call)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 5.3 Monitor CloudWatch logs
    - Check Lambda logs for any errors or unexpected behavior
    - Verify OPTIONS requests are logged correctly
    - Verify POST requests continue to log query metrics
    - Verify no increase in error rates
    - _Requirements: 2.2, 3.5_

  - [ ] 5.4 Test frontend integration
    - Open frontend application in browser
    - Verify chat interface can make requests without CORS errors
    - Test full browser preflight flow: OPTIONS → POST → response
    - Verify no console errors related to CORS
    - _Requirements: 2.2_

  - [ ] 5.5 Verify all response paths include CORS headers
    - Test validation error response (missing fields) → Verify CORS headers present
    - Test MESSAGE_TOO_LONG error response → Verify CORS headers present
    - Test throttling response (if possible to trigger) → Verify CORS headers present
    - Test server error response (if possible to trigger) → Verify CORS headers present
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 6. Checkpoint - Ensure all tests pass and deployment is successful
  - Verify all unit tests pass
  - Verify all property-based tests pass
  - Verify OPTIONS endpoint returns 200 with CORS headers
  - Verify POST endpoint continues to work correctly
  - Verify frontend can make requests without CORS errors
  - Verify CloudWatch logs show no errors
  - Ask the user if questions arise or if rollback is needed
