import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords

_stemmer = PorterStemmer()
_stop_words = set(stopwords.words('english'))

def tokenize_and_stem(text):
    """
    Tokenizes text, removes stop words, and stems tokens.
    """
    tokens = word_tokenize(text)
    # Filter out stop words and non-alphabetic tokens, then stem
    stemmed = [
        _stemmer.stem(t) 
        for t in tokens 
        if t.isalpha() and t.lower() not in _stop_words
    ]
    return stemmed
