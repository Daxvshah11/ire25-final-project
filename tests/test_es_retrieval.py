import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock elasticsearch module if not present
if 'elasticsearch' not in sys.modules:
    sys.modules['elasticsearch'] = MagicMock()

from src.retriever import ElasticsearchRetriever

class TestElasticsearchRetriever(unittest.TestCase):
    def test_retrieve(self):
        # We need to patch where it is imported. 
        # Since it is imported inside __init__, we can patch sys.modules['elasticsearch'].Elasticsearch
        # or better, since we already mocked the module above (if missing), we can just configure that mock.
        # But to be safe and explicit for both cases (installed or not), let's use patch on the module.
        
        with patch('elasticsearch.Elasticsearch') as mock_es_class:
            # Setup mock
            mock_es_instance = MagicMock()
            mock_es_class.return_value = mock_es_instance
            
            # Mock search response
            mock_response = {
                'hits': {
                    'hits': [
                        {
                            '_source': {'uuid': 'doc1'},
                            '_score': 1.5
                        },
                        {
                            '_source': {'uuid': 'doc2'},
                            '_score': 1.2
                        }
                    ]
                }
            }
            mock_es_instance.search.return_value = mock_response

            # Initialize retriever
            retriever = ElasticsearchRetriever(host="http://localhost:9200", index_name="test_index")
            
            # Test retrieve
            results = retriever.retrieve("test query", top_k=2)
            
            # Verify results
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], ('doc1', 1.5))
            self.assertEqual(results[1], ('doc2', 1.2))
            
            # Verify ES call
            mock_es_instance.search.assert_called_once()
            call_args = mock_es_instance.search.call_args
            self.assertEqual(call_args.kwargs['index'], "test_index")
            self.assertEqual(call_args.kwargs['size'], 2)
            self.assertEqual(call_args.kwargs['query']['match']['text'], "test query")

if __name__ == '__main__':
    unittest.main()
