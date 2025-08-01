from pydantic import BaseModel, Field
from typing import Optional, List

class JobApplicationRequestModel(BaseModel):
  """The model of the incoming request with job posting """
  job_id: str = Field(..., description="job uuid")
  job_link: str = Field(..., description="Link to job posting")
  job_title: str = Field(..., description="Job title")
  job_description: str = Field(..., description="Job description")
  skills_keywords: List[str] = Field(..., description="Keywords of reference skills for this job stated by person posting the job offer")
  applicant_questions: Optional[List[str]] = Field(..., description="Questions that job candidate has to answer")
  additional_agent_instruction: Optional[str] = Field(..., description="Additional instruction passed by the user to the agent")

class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str = "processing"

class JobErrorResponse(BaseModel):
    error: str
