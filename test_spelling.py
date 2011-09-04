

from base import LmfdbTest
class SpellingTest(LmfdbTest):
  # this tests the spelling on the website
  
  
  def test_zeroes_spelling(self):
    """
        'zeroes' should be 'zeros'
    """
    for rule in self.app.url_map.iter_rules():
      
      if "GET" in rule.methods:
        try:
          tc = self.app.test_client()
          res = tc.get(rule.rule)
          assert not ("zeroes" in res.data), "rule %s failed " % rule
        except KeyError:
          pass
