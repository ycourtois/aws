import logging
import sys
import unittest


class UtilTestCase(unittest.TestCase):
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def assertRaisesWithMessage(self, exception, msg, func, *args, **kwargs):
        with self.assertRaises(exception) as context:
            func(*args, **kwargs)
        self.assertTrue(msg in str(context.exception),
                        f"Exception message does not match expected one. Got [{str(context.exception)}], was expecting [{msg}]")
