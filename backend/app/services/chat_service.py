import sys
import json
from pathlib import Path
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.chat import ChatRequest, ChatResponse
from app.utils.logger import logger
from app.services.herkeyjob_service import scrape_herkey_jobs
from app.services.naukrijob_service import scrape_naukri_jobs
from app.services.herkeyevent_service import scrape_herkey_events
from app.services.herkeymentor_service import scrape_herkey_mentorship

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
sys.path.append(str(backend_dir))

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key="AIzaSyCUdGlXbW8-oq5I3QemsDERPhNvO5VL7zs"  # Replace with your actual API key
)

class ChatService:
    def __init__(self):
        # In-memory context store (session_id -> list of {query, response})
        self.session_context: Dict[str, list] = {}

    async def process_message(self, chat_request: ChatRequest) -> ChatResponse:
        # try:
        # Step 1: Detect gender bias using LLM
        print("inside chat service",chat_request)
        bias_prompt = f"""
        You must respond with ONLY a valid JSON object, with no additional text, markdown, or formatting.
        Analyze this query for gender bias: "{chat_request.query}"
        
        Return your analysis in this exact JSON format:
        {{"is_biased": false, "alternative_response": null}}
        or
        {{"is_biased": true, "alternative_response": "unbiased rephrasing here"}}
        """
        
        # Get LLM response
        bias_result = await llm.ainvoke(bias_prompt)
        
        # Log the raw response for debugging
        logger.debug(f"Raw LLM response: {bias_result.content}")
        
        # Clean and parse the response
        try:
            content = bias_result.content.strip()
            
            # Remove any markdown formatting
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            content = content.strip()
            
            # Ensure we have content to parse
            if not content:
                logger.warning("Received empty content from LLM")
                bias_response = {
                    "is_biased": False,
                    "alternative_response": None
                }
            else:
                # Try to parse JSON
                bias_response = json.loads(content)
                logger.debug(f"Successfully parsed JSON: {bias_response}")
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error. Content: '{content}'. Error: {str(e)}")
            bias_response = {
                "is_biased": False,
                "alternative_response": None
            }
        
        # Process the response
        if bias_response.get("is_biased", False):
            return ChatResponse(
                response=bias_response.get("alternative_response", "I apologize, but I need to rephrase that in a more inclusive way."),
                session_id=chat_request.session_id
            )

        # Handle the non-biased case with intent classification
        intent_prompt = f"""
        Return ONLY ONE of these exact words to classify the intent: 
        job_listing, event, mentorship, faq, unknown

        Query: {chat_request.query}
        """
        
        intent_result = await llm.ainvoke(intent_prompt)
        intent = intent_result.content.strip().lower()
        
        # Get response based on intent
        if intent == "job_listing":
            response = await self._handle_job_request(chat_request.query, "")
        elif intent == "event":
            response = await self._handle_event_request(chat_request.query, "")
        elif intent == "mentorship":
            response = await self._handle_mentorship_request(chat_request.query, "")
        elif intent == "faq":
            response = await self._handle_faq_request(chat_request.query)
        elif intent == "unknown":
            response = await self._handle_general_request(chat_request.query)    
        else:
            response = "I can help you with job listings, events, mentorship programs, and general questions. Could you please clarify what you're looking for?"

        return ChatResponse(
            response=response,
            session_id=chat_request.session_id
        )

        # except Exception as e:
        #     logger.error(f"Error processing message: {str(e)}", exc_info=True)
        #     return ChatResponse(
        #         response="I apologize, but I encountered an error. Could you please rephrase your question?",
        #         session_id=chat_request.session_id
        #     )

    async def _handle_job_request(self, query: str, context: str) -> str:
        if query.lower() == "show me current job from `naukri.com`":
            jobs,url = scrape_naukri_jobs(search_query=query)
        # Call the scrape_herkey_jobs function with the user's query
        else:
            jobs,url = scrape_herkey_jobs(search_query=query)
            print("jobs",jobs,url)
        # Validate the scraped jobs
        is_valid_output = (
            jobs and  # Check if the list is non-empty
            len(jobs) > 0 and  # Ensure there are jobs
            any(
                job.get('title', 'N/A') != 'N/A' and
                job.get('company', 'N/A') != 'N/A'
                for job in jobs
            )  # Ensure at least one job has a title and company
        )

        if is_valid_output:
            # Format valid job listings into a string for the LLM
            jobs_str = "\n".join(
                [
                    f"- {job.get('title', 'N/A')} at {job.get('company', 'N/A')} "
                    f"(Location: {job.get('details', 'N/A')}, "
                    f"Skills: {job.get('skills', 'N/A')}, "
                    f"Salary: {job.get('salary', 'Not disclosed')}, "
                    f"Apply: {job.get('apply_url', 'N/A')})"
                    for job in jobs[:8]  # Limit to 5 jobs for brevity
                ]
            )
            prompt = f"""
            Given the following user query, conversation context, and scraped job listings, generate a concise and user-friendly response.
            Query: {query}
            Context: {context}
            Job Listings:
            {jobs_str}
            Response: Return the job listings in a conversational tone and first you need to give all the data that we got through scraping Include key details (title, company, location, skills, salary, apply URL) and if you find something missing in job detail then handle it from your side.
            Note: With every job data you need to provid job link, so if available in job data then provide it otherwise add {url}.
            """
        else:
            # Handle invalid or empty output with a fallback prompt
            prompt = f"""
            Given the following user query and conversation context, generate a response as if you were retrieving job listings. No valid job listings were found, so provide a generic response with mock job data relevant to the query.
            Query: {query}
            Context: {context}
            Response: Provide a concise list of mock job listings (2-3 examples) that align with the query. Include title, company, location, skills, salary, and a placeholder apply URL.
            """

        # Call the LLM to generate the final response
        result = await llm.ainvoke(prompt)
        return result.content.strip()

    async def _handle_event_request(self, query: str, context: str) -> str:
        # Call the scrape_herkey_events function with the user's query
        events = scrape_herkey_events(search_query=query)

        # Validate the scraped events
        is_valid_output = (
            events and  # Check if the list is non-empty
            len(events) > 0 and  # Ensure there are events
            any(
                event.get('title', 'N/A') != 'N/A' and
                event.get('date', 'N/A') != 'N/A'
                for event in events
            )  # Ensure at least one event has a title and date
        )

        if is_valid_output:
            # Format valid event listings into a string for the LLM
            events_str = "\n".join(
                [
                    f"- {event.get('title', 'N/A')} "
                    f"(Date: {event.get('date', 'N/A')}, "
                    f"Location: {event.get('location', 'N/A')}, "
                    f"Description: {event.get('description', 'N/A')}, "
                    f"Register: {event.get('url', 'N/A')})"
                    for event in events[:5]  # Limit to 5 events for brevity
                ]
            )
            prompt = f"""
            Given the following user query, conversation context, and scraped event listings, generate a concise and user-friendly response.
            Query: {query}
            Context: {context}
            Event Listings:
            {events_str}
            Response: Summarize the event listings in a natural, conversational tone. Include key details (title, date, location, description, register URL) and make it engaging.
            """
        else:
            # Handle invalid or empty output with a fallback prompt
            prompt = f"""
            Given the following user query and conversation context, generate a response as if you were retrieving upcoming events. No valid event listings were found, so provide a generic response with mock event data relevant to the query.
            Query: {query}
            Context: {context}
            Response: Provide a concise list of mock event listings (2-3 examples) that align with the query. Include title, date, location, description, and a placeholder register URL.
            """

        # Call the LLM to generate the final response
        result = await llm.ainvoke(prompt)
        return result.content.strip()

    async def _handle_mentorship_request(self, query: str, context: str) -> str:
        # Call the scrape_herkey_mentorship function
        mentorships = scrape_herkey_mentorship(search_query="mentorship")

        # Validate the scraped mentorships
        is_valid_output = (
            mentorships and  # Check if the list is non-empty
            len(mentorships) > 0 and  # Ensure there are mentorships
            any(
                mentor.get('title', 'N/A') != 'N/A' or
                mentor.get('mentor_name', 'N/A') != 'N/A'
                for mentor in mentorships
            )  # Ensure at least one mentorship has a title or mentor name
        )

        if is_valid_output:
            # Format valid mentorship listings into a string for the LLM
            mentorships_str = "\n".join(
                [
                    f"- {mentor.get('title', 'N/A')} "
                    f"(Mentor: {mentor.get('mentor_name', 'N/A')}, "
                    f"Description: {mentor.get('description', 'N/A')}, "
                    f"Register: {mentor.get('url', 'N/A')})"
                    for mentor in mentorships[:5]  # Limit to 5 mentorships for brevity
                ]
            )
            prompt = f"""
            Given the following user query, conversation context, and scraped mentorship opportunities, generate a concise and user-friendly response.
            Query: {query}
            Context: {context}
            Mentorship Opportunities:
            {mentorships_str}
            Response: Summarize the mentorship opportunities in a natural, conversational tone. Include key details (title, mentor name, description, register URL) and make it engaging.
            """
        else:
            # Handle invalid or empty output with a fallback prompt
            prompt = f"""
            Given the following user query and conversation context, generate a response as if you were retrieving mentorship opportunities. No valid mentorship opportunities were found, so provide a generic response with mock mentorship data relevant to the query.
            Query: {query}
            Context: {context}
            Response: Provide a concise list of mock mentorship opportunities (2-3 examples) that align with the query. Include title, mentor name, description, and a placeholder register URL.
            """

        # Call the LLM to generate the final response
        result = await llm.ainvoke(prompt)
        return result.content.strip()
    
    async def _handle_faq_request(self, query: str) -> str:
        prompt = f"""
        Given the following user query, generate a response as if you were answering a frequently asked question.
        Query: {query}
        Response: Provide a concise answer to the query.
        """
        result = await llm.ainvoke(prompt)
        return result.content.strip()

    async def _handle_general_request(self, query: str) -> str:
        prompt = f"""
        Given the following user query, generate a response as if you were a helpful assistant.
        Query: {query}
        Response: Provide a concise answer to the query.
        And remember that you are Asha Bot to help women with career development, job opportunities, and mentorship programs.
        """
        result = await llm.ainvoke(prompt)
        return result.content.strip()
