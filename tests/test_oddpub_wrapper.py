import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import inspect
from dsst_etl.oddpub_wrapper import OddpubWrapper
from dsst_etl.models import OddpubMetrics
from dsst_etl.db import get_db_session, init_db
from dsst_etl import get_db_engine


class TestOddpubWrapper(unittest.TestCase):

    def setUp(self):
        self.engine = get_db_engine(is_test=True)
        init_db(self.engine)
        self.session = get_db_session(self.engine)
        self.wrapper = OddpubWrapper(self.session)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_oddpub_wrapper(self):
        self.wrapper.process_pdfs("test_pdfs", "test_output")

        # Check if the OddpubMetrics table exists
        inspector = inspect(self.session.bind)
        self.assertTrue("oddpub_metrics" in inspector.get_table_names())
    
        # Check if the data was inserted correctly
        result = self.session.query(OddpubMetrics).first()
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
