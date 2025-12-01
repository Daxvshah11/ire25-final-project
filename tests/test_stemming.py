from src.text_utils import tokenize_and_stem

def test_stemming():
    text = "The runners are running fastly towards the destination."
    tokens = tokenize_and_stem(text)
    print(f"Original: {text}")
    print(f"Tokens: {tokens}")
    
    expected_stems = ['runner', 'run', 'fastli', 'destin'] # Approximate expectations
    for stem in expected_stems:
        if stem in tokens:
            print(f"PASS: Found stem '{stem}'")
        else:
            print(f"FAIL: Did not find stem '{stem}'")

if __name__ == "__main__":
    test_stemming()
