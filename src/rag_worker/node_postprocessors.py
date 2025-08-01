from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.core import QueryBundle
from typing import List

class KeywordBoost(BaseNodePostprocessor):
  """Boost nodes by keyword overlap."""

  def __init__(self, boost: float = 0.25) -> None:
     super().__init__()
     self._boost = boost

  def _postprocess_nodes(self, nodes: List[NodeWithScore], query_str: QueryBundle|str):
    # turn query into individual words
    query_str= query_str.query_str if isinstance(query_str, QueryBundle) else query_str
    q_tokens = {q.lower() for q in query_str.split()}

    for node in nodes:
      node_keywords = {keyword.lower() for keyword in node.metadata.get('keywords', [])}
      #get the intersection (try to get keywords from query)
      overlap = q_tokens.intersection(node_keywords)
      if overlap:
        #add score to the retrieved node if there is a keyword overlap
        node.score += self._boost * len(overlap)

    return nodes