"""
Test script for text chunking functionality in EmbeddingLambda.
Validates that chunks meet the requirements:
- Each chunk is <= 512 tokens
- Consecutive chunks have exactly 50 token overlap

This test can be run standalone without AWS dependencies.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from embedding import chunk_text, count_tokens, CHUNK_SIZE, CHUNK_OVERLAP


def test_chunking_basic():
    """Test basic chunking functionality."""
    print("="*60)
    print("Test 1: Basic Chunking")
    print("="*60)
    
    # Sample medical text
    sample_text = """
    Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels.
    Type 1 diabetes results from autoimmune destruction of pancreatic beta cells, leading to absolute
    insulin deficiency. Type 2 diabetes is characterized by insulin resistance and relative insulin
    deficiency. Management includes lifestyle modifications, blood glucose monitoring, and medications
    such as metformin, sulfonylureas, and insulin therapy when needed. Complications include
    cardiovascular disease, nephropathy, retinopathy, and neuropathy. Regular monitoring of HbA1c,
    blood pressure, and lipid levels is essential for optimal diabetes management.
    """ * 10  # Repeat to create longer text
    
    print(f"Sample text length: {len(sample_text)} characters")
    print(f"Sample text tokens: {count_tokens(sample_text)} tokens\n")
    
    # Chunk the text
    chunks = chunk_text(sample_text)
    
    print(f"Number of chunks created: {len(chunks)}\n")
    
    # Validate each chunk
    all_valid = True
    for i, chunk in enumerate(chunks):
        token_count = chunk['token_count']
        
        # Check if chunk size is within limit
        if token_count > CHUNK_SIZE:
            print(f"❌ Chunk {i}: FAILED - {token_count} tokens (exceeds {CHUNK_SIZE})")
            all_valid = False
        else:
            print(f"✓ Chunk {i}: {token_count} tokens (within limit)")
        
        # Check overlap with next chunk
        if i < len(chunks) - 1:
            current_end = chunk['end_token']
            next_start = chunks[i + 1]['start_token']
            overlap = current_end - next_start
            
            if overlap != CHUNK_OVERLAP:
                print(f"  ❌ Overlap with next chunk: {overlap} tokens (expected {CHUNK_OVERLAP})")
                all_valid = False
            else:
                print(f"  ✓ Overlap with next chunk: {overlap} tokens")
    
    print("\n" + "="*60)
    if all_valid:
        print("✓ Test 1 PASSED: All chunks meet requirements!")
    else:
        print("❌ Test 1 FAILED: Some chunks failed validation")
    print("="*60 + "\n")
    
    return all_valid


def test_chunking_short_text():
    """Test chunking with text shorter than chunk size."""
    print("="*60)
    print("Test 2: Short Text (< 512 tokens)")
    print("="*60)
    
    short_text = "Patient presents with elevated blood glucose levels. HbA1c is 8.5%."
    
    print(f"Text length: {len(short_text)} characters")
    print(f"Text tokens: {count_tokens(short_text)} tokens\n")
    
    chunks = chunk_text(short_text)
    
    print(f"Number of chunks created: {len(chunks)}")
    
    if len(chunks) == 1:
        print(f"✓ Single chunk created as expected")
        print(f"✓ Chunk has {chunks[0]['token_count']} tokens")
        print("\n" + "="*60)
        print("✓ Test 2 PASSED")
        print("="*60 + "\n")
        return True
    else:
        print(f"❌ Expected 1 chunk, got {len(chunks)}")
        print("\n" + "="*60)
        print("❌ Test 2 FAILED")
        print("="*60 + "\n")
        return False


def test_chunking_exact_size():
    """Test chunking with text exactly at chunk size."""
    print("="*60)
    print("Test 3: Text Exactly 512 Tokens")
    print("="*60)
    
    # Create text with approximately 512 tokens
    base_text = "The patient has diabetes. "
    target_tokens = 512
    
    # Build text to target size
    text = ""
    while count_tokens(text) < target_tokens:
        text += base_text
    
    # Trim to exactly 512 tokens
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)[:512]
    exact_text = tokenizer.decode(tokens)
    
    print(f"Text tokens: {count_tokens(exact_text)} tokens\n")
    
    chunks = chunk_text(exact_text)
    
    print(f"Number of chunks created: {len(chunks)}")
    
    if len(chunks) == 1 and chunks[0]['token_count'] == 512:
        print(f"✓ Single chunk with exactly 512 tokens")
        print("\n" + "="*60)
        print("✓ Test 3 PASSED")
        print("="*60 + "\n")
        return True
    else:
        print(f"❌ Expected 1 chunk with 512 tokens, got {len(chunks)} chunks")
        if chunks:
            print(f"   First chunk: {chunks[0]['token_count']} tokens")
        print("\n" + "="*60)
        print("❌ Test 3 FAILED")
        print("="*60 + "\n")
        return False


def test_chunking_large_text():
    """Test chunking with very large text."""
    print("="*60)
    print("Test 4: Large Text (>2000 tokens)")
    print("="*60)
    
    # Create large text
    large_text = """
    Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels.
    Type 1 diabetes results from autoimmune destruction of pancreatic beta cells, leading to absolute
    insulin deficiency. Type 2 diabetes is characterized by insulin resistance and relative insulin
    deficiency. Management includes lifestyle modifications, blood glucose monitoring, and medications
    such as metformin, sulfonylureas, and insulin therapy when needed. Complications include
    cardiovascular disease, nephropathy, retinopathy, and neuropathy. Regular monitoring of HbA1c,
    blood pressure, and lipid levels is essential for optimal diabetes management.
    
    Blood pressure management is crucial for cardiovascular health. Hypertension is defined as
    systolic blood pressure ≥140 mmHg or diastolic blood pressure ≥90 mmHg. Treatment includes
    lifestyle modifications such as reduced sodium intake, regular exercise, and weight management.
    Pharmacological interventions include ACE inhibitors, ARBs, calcium channel blockers, and diuretics.
    
    Cholesterol management involves monitoring LDL, HDL, and triglyceride levels. Elevated LDL
    cholesterol increases cardiovascular risk. Statins are first-line therapy for hyperlipidemia.
    Lifestyle modifications include dietary changes, increased physical activity, and weight loss.
    """ * 20  # Repeat to create very large text
    
    print(f"Text length: {len(large_text)} characters")
    print(f"Text tokens: {count_tokens(large_text)} tokens\n")
    
    chunks = chunk_text(large_text)
    
    print(f"Number of chunks created: {len(chunks)}\n")
    
    # Validate all chunks
    all_valid = True
    for i, chunk in enumerate(chunks):
        if chunk['token_count'] > CHUNK_SIZE:
            print(f"❌ Chunk {i}: {chunk['token_count']} tokens (exceeds limit)")
            all_valid = False
        
        # Check overlap
        if i < len(chunks) - 1:
            current_end = chunk['end_token']
            next_start = chunks[i + 1]['start_token']
            overlap = current_end - next_start
            
            if overlap != CHUNK_OVERLAP:
                print(f"❌ Chunk {i} overlap: {overlap} tokens (expected {CHUNK_OVERLAP})")
                all_valid = False
    
    if all_valid:
        print(f"✓ All {len(chunks)} chunks are valid")
        print(f"✓ All overlaps are exactly {CHUNK_OVERLAP} tokens")
        print("\n" + "="*60)
        print("✓ Test 4 PASSED")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ Test 4 FAILED")
        print("="*60 + "\n")
    
    return all_valid


def run_all_tests():
    """Run all chunking tests."""
    print("\n" + "="*60)
    print("EMBEDDING LAMBDA - TEXT CHUNKING TESTS")
    print("="*60 + "\n")
    
    results = []
    
    results.append(("Basic Chunking", test_chunking_basic()))
    results.append(("Short Text", test_chunking_short_text()))
    results.append(("Exact Size", test_chunking_exact_size()))
    results.append(("Large Text", test_chunking_large_text()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
