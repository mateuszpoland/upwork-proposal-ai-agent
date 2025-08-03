# src/rag_worker/pipeline.py
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from supabase import create_client
from .payloads import JobApplicationRequestModel
from .models import (
    JobSummary,
    JobBusinessIntent,
    QuerySet,
    QueryAugmentationResult
)
from .node_postprocessors import KeywordBoost
from llama_index.postprocessor.cohere_rerank import CohereRerank
from .prompts import (
   SUMMARY_PROMPT,
   BUSINESS_DESCRIPTION_PROMPT,
   CREATE_QUERY_SET_PROMPT
)
import os
import logging
from typing import List, Dict, Optional
import json
from .util import timed

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_USER = os.environ.get("WEBHOOK_USER")
WEBHOOK_PASS = os.environ.get("WEBHOOK_PASS")

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
SUPABASE_PASS = os.getenv('SUPABASE_PASSWORD')

OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL') or 'text-embedding-3-small'
OPENAI_MODEL = os.getenv('OPENAI_MODEL') or 'gpt-4.1-mini'

##### VectorStoreIndex and connection setup #####

from llama_index.vector_stores.supabase import SupabaseVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding

class JobDataAugmenter:
    def __init__(self, llm=None) -> None:
        self._llm = llm or OpenAI(model="gpt-4.1-mini")

    def augment(self, req: JobApplicationRequestModel) -> QueryAugmentationResult:
        summ_input = dict(
            job_title=req.job_title,
            job_description=req.job_description,
            skills_keywords=", ".join(req.skills_keywords),
        )
        summary = self._generate_summary(summ_input).raw
        business = self._generate_business_intent_desc(req.job_description).raw
        qset    = self._generate_query_set(summary, business.business_outcome, business.problem).raw

        return QueryAugmentationResult(
            job_summary=summary.summary,
            job_business_problem=business.problem,
            job_business_outcome=business.business_outcome,
            skillset_required=summary.skills_for_the_job,
            applicant_questions=req.applicant_questions,
            retrieval_queries=qset.vector_index_queries,
            additional_agent_instruction=req.additional_agent_instruction,
        )

    def _generate_summary(self, data: dict) -> JobSummary:
      try:
        sllm = self._llm.as_structured_llm(JobSummary, strict=True)
        return sllm.complete(SUMMARY_PROMPT.format(**data))
      except AttributeError as e:
        print(f"Invalid JSON returned from LLM")
        raise e

    def _generate_business_intent_desc(self, jd: str) -> JobBusinessIntent:
        sllm = self._llm.as_structured_llm(JobBusinessIntent)
        return sllm.complete(BUSINESS_DESCRIPTION_PROMPT.format(job_description=jd))

    def _generate_query_set(self, summary: JobSummary, business_outcome: str, business_problem: str) -> QuerySet:
        sllm = self._llm.as_structured_llm(QuerySet)
        return sllm.complete(
            CREATE_QUERY_SET_PROMPT.format(
                summary=summary.summary,
                business_outcome=business_outcome,
                business_problem=business_problem,
                skillset_required=summary.skills_for_the_job,
            )
    )

from llama_index.core import QueryBundle
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.vector_stores import VectorStoreQuery
from typing import List, Dict, Optional

class RelevantExperienceRetriever(BaseRetriever):
  def __init__(
      self,
      vector_store: SupabaseVectorStore,
      embed_model: OpenAIEmbedding,
      query_mode: str = "default",
      similarity_top_k: int = 2
  ) -> None:
    self._vector_store = vector_store
    self._embed_model = embed_model
    self._query_mode = query_mode
    self._similarity_top_k = similarity_top_k

  def _retrieve(self, query_bundle: QueryBundle | str) -> List[NodeWithScore]:
    """Retrieve nodes given query."""

    if isinstance(query_bundle, str):
      query_embedding = self._embed_model.get_query_embedding(query_bundle)
    else:
      query_embedding = query_bundle.embedding

    vector_store_query = VectorStoreQuery(
        query_embedding=query_embedding,
        mode=self._query_mode,
        similarity_top_k=self._similarity_top_k
    )

    result = self._vector_store.query(vector_store_query)
    nodes_with_scores: Dict[str, NodeWithScore] = {}
    #add scores to retrieved nodes
    for index, node in enumerate(result.nodes):
      existing = nodes_with_scores.get(node.id_)
      if existing is None and result.similarities is not None:
          score: Optional[float] = result.similarities[index]
          nodes_with_scores[node.id_] = NodeWithScore(node=node, score=score)

    output = []
    [output.append(node) for k, node in nodes_with_scores.items()]
    return output

@timed
def query_rag_pipeline(job_request: JobApplicationRequestModel) -> dict:
    """Perform RAG inference"""
    try:
        index = _get_vector_store_index()
        augmenter = JobDataAugmenter(OpenAI(model=OPENAI_MODEL))
        augmented_query = augmenter.augment(job_request)
        embed_model = OpenAIEmbedding(model=OPENAI_EMBEDDING_MODEL)
        nodes_with_scores = _retrieve_and_rerank_nodes(embed_model, index, augmented_query)
        nodes_keyword_boosted = KeywordBoost()._postprocess_nodes(nodes_with_scores, augmented_query.job_summary)

        response = _generate_response(nodes_keyword_boosted, augmented_query)
        _update_db(job_request.job_id, response)

        return response
    except Exception as e:
       logging.error(e)
       raise e

def _get_vector_store_index() -> VectorStoreIndex:
   SUPABASE_PASS = os.environ.get("SUPABASE_PASSWORD")
   postgres_url = f'postgresql://postgres.lvhumxpipledgimerzxd:{SUPABASE_PASS}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'

   vector_store = SupabaseVectorStore(
      postgres_connection_string=postgres_url,
      collection_name="awsomedevs_professional_information",
      dimension=1536,
    )
   
   index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=OpenAIEmbedding(model="text-embedding-3-small")
   )

   logging.info("Index loaded from Supabase storage.")
   
   return index


def _retrieve_and_rerank_nodes(embed_model: OpenAIEmbedding, index: VectorStoreIndex, input: QueryAugmentationResult) -> List[NodeWithScore]:
  """Retrieve nodes from vector index."""
  cohere_reranker = CohereRerank(api_key=COHERE_API_KEY, top_n=3)
  retriever = RelevantExperienceRetriever(
      vector_store=index.vector_store,
      embed_model=embed_model,
      similarity_top_k=3
  )

  seen_texts = set()
  retrieved_deduplicated_nodes: List[NodeWithScore] = []

  for question in input.retrieval_queries:
    retrieved_nodes = retriever._retrieve(question)
    for node in retrieved_nodes:
       normalized_text = node.text.strip()
       if normalized_text not in seen_texts:
          seen_texts.add(normalized_text)
          retrieved_deduplicated_nodes.append(node) 
  
  
  reranked_nodes = cohere_reranker.postprocess_nodes(retrieved_deduplicated_nodes, query_str=" ".join(input.retrieval_queries))
  
  return reranked_nodes


def _generate_response(nodes: List[NodeWithScore], augmented_query: QueryAugmentationResult) -> dict:
  """Generate response for proposal building agent."""
  import re
  def normalize_text(text: str) -> str:
     text = text.strip()
     text = re.sub(r'\s+', ' ', text)
     return text
  
  response = {
      "job_description": augmented_query.job_summary,
      "business_problem": augmented_query.job_business_problem,
      "business_outcome": augmented_query.job_business_outcome,
      "skillset_required": augmented_query.skillset_required,
      "applicant_questions": augmented_query.applicant_questions,
      "additional_agent_instruction": augmented_query.additional_agent_instruction,
      "retrieval_nodes": [normalize_text(node.text) for node in nodes],
  }

  return response

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def _update_db(job_uuid: str, response: dict) -> None:
   try:
      json.dumps(response, ensure_ascii=False)  # UTF-8 safe
   except (TypeError, ValueError) as e:
      raise Exception(f"❌ Failed to serialize JSON: {e}")
   
   supabase_connection = create_client(SUPABASE_URL, SUPABASE_KEY)
   response =supabase_connection.table('upwork_jobs_data').update({
      "processed": response,
      "stage": "PROCESSED"
   }).eq('job_uuid', job_uuid).execute()

   print("✅ Supabase update response:", response)



   