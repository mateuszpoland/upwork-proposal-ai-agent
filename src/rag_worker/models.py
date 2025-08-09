from pydantic import BaseModel, Field
from typing import Optional, List

class JobSummary(BaseModel):
  """Summary of job title, description and skills"""
  summary: str = Field(..., description="Summary of job title and job description from the payload")

class JobBusinessIntent(BaseModel):
  """Augments the job description passed as an argument with set of criteria"""
  problem: str = Field(..., description="Business problem to solve in this job description")
  business_outcome: str = Field(..., description="Explanation of how solving the problem creates value or eleviates pain")
  domain: str = Field(..., description="Industry or vertical")

class QuerySet(BaseModel):
  vector_index_queries: List[str] = Field(..., description="List of queries to ask against vector db containing applicant professional experience data.")

class QueryAugmentationResult(BaseModel):
  job_summary: str = Field(..., description="Summary of job title and description")
  job_business_problem: str = Field(..., description="Business problem to solve in this job description")
  job_business_outcome: str = Field(..., description="Explanation of how solving the problem creates value or eleviates pain")
  skillset_required: Optional[str] = Field(..., description="Summarized skillset necessary for the job")
  applicant_questions: Optional[List[str]] = Field(..., description="Questions that job candidate has to answer")
  retrieval_queries: List[str] = Field(..., description="List of queries to ask against vector db containing applicant professional experience data.")
  additional_agent_instruction: Optional[str] = Field(..., description="Additional instruction passed by the user to the agent")