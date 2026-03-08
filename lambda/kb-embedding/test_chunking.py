"""
Test script for text chunking functionality.
Validates that chunks meet the requirements:
- Each chunk is <= 512 tokens
- Consecutive chunks have exactly 50 token overlap
"""
import tiktoken

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(tokenizer.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """
    Split text into chunks of specified token size with overlap.
    """
    tokens = tokenizer.encode(text)
    chunks = []
    
    start_idx = 0
    chunk_index = 0
    
    while start_idx < len(tokens):
        end_idx = min(start_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = tokenizer.decode(chunk_tokens)
        
        chunks.append({
            'text': chunk_text,
            'chunk_index': chunk_index,
            'start_token': start_idx,
            'end_token': end_idx,
            'token_count': len(chunk_tokens)
        })
        
        chunk_index += 1
        
        if end_idx >= len(tokens):
            break
        
        start_idx = end_idx - overlap
    
    return chunks


def test_chunking():
    """Test the chunking function with sample text."""
    
    # Sample medical text
    sample_text = """
    Diabetes mellitus is a chronic metabolic disorder characterized by elevated blood glucose levels.
    Type 1 diabetes results from autoimmune destruction of pancreatic beta cells, leading to absolute
    insulin deficiency. Type 2 diabetes is characterized by insulin resistance and relative insulin
    deficiency. Management includes lifestyle modifications, blood glucose monitoring, and medications
    such as metformin, sulfonylureas, and insulin therapy when needed. Complications include
    cardiovascular disease, nephropathy, retinopathy, and neuropathy. Regular monitoring of HbA1c,
    blood pressure, and lipid levels is essential for optimal diabetes management.
    """ * 20  # Repeat to create longer text
    
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
        print("✓ All chunks meet requirements!")
    else:
        print("❌ Some chunks failed validation")
    print("="*60)
    
    # Show first chunk as example
    if chunks:
        print("\nFirst chunk preview:")
        print(f"Tokens: {chunks[0]['token_count']}")
        print(f"Text: {chunks[0]['text'][:200]}...")


if __name__ == "__main__":
    test_chunking()
