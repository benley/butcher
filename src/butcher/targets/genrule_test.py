"""Unit tests for genrules."""
import re
import unittest

from butcher.targets import genrule
#from twitter.common import app
#from twitter.common import log


class TestGenrule(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_regexes(self):
        """Verifies that those obnoxious regexes do what they're meant to."""
        rdata = {
            genrule.GenRuleBuilder.paren_tag_re: [
                ('   $(fancystuff inside.blabla)', 'fancystuff inside.blabla'),
                ('asdf$(foobarbas)asdf', 'foobarbas'),
                ('$( location //foo/bar:bla  )', ' location //foo/bar:bla  '),
                ('$(@D)', '@D'),
                ('$(@)', '@'),
                ('$(SRCS)', 'SRCS'),
                ],
            genrule.GenRuleBuilder.noparen_tag_re: [
                ('$@', '@'),
                (' $@ ', '@'),
                ('$@Dfoo', '@Dfoo'),
                (' $@D ', '@D'),
                ('foo$bar_foo%guh bla', 'bar_foo'),
                (' $$blarg', None),
                ],
            }
        for regex in rdata:
            for (instr, outstr) in rdata[regex]:
                if outstr:
                    expected_output = [outstr]
                else:
                    expected_output = []
                match = re.findall(regex, instr)
                self.assertEqual(
                    expected_output, match,
                    '\nRegex: %s\n'
                    'Input: %s\n'
                    'Expected output: %s\n'
                    'Actual output: %s' % (repr(regex.pattern), repr(instr),
                                           expected_output, match))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGenrule)
    unittest.TextTestRunner(verbosity=2).run(suite)
