import streamlit as st
import asyncio
import os
import re
import json
import requests
import time
import random
from typing import Dict

def extract_text_from_pdf(file):
    try:
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(file)
        text = ''.join(page.extract_text() for page in pdf_reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

class GroqAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Using Llama 3 70B from Groq
        
    async def generate_response(self, prompt, system_message="You are a helpful assistant.", max_retries=5):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    # Calculate backoff time: starts at 2s and doubles each retry + some random jitter
                    wait_time = (2 ** attempt) + random.uniform(1, 3)
                    st.warning(f"Rate limit hit. Waiting {wait_time:.1f} seconds before retrying... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)  # Use asyncio.sleep in async functions
                    continue
                else:
                    st.error(f"API Error: {e}")
                    return f"Error: {str(e)}"
            except Exception as e:
                st.error(f"API Error: {e}")
                return f"Error: {str(e)}"
        
        return "Error: Maximum retry attempts reached. Please try again later."

async def process_resume_and_jd(api_key, resume_text, job_description):
    groq = GroqAPI(api_key)
    
    try:
        # Step 1: Parse resume
        st.info("Analyzing resume... (Step 1/4)")
        resume_system_message = """You are an expert resume parser. Extract key information from the resume including:
        - Technical skills and proficiencies
        - Work experience and duration
        - Education and qualifications
        - Projects and achievements
        - Certifications
        Provide the information in a structured format for easy analysis."""
        
        resume_result = await groq.generate_response(
            f"Parse this resume content and extract key information: {resume_text}",
            resume_system_message
        )
        
        # Add delay between API calls
        await asyncio.sleep(2)
        
        # Step 2: Parse job description
        st.info("Analyzing job description... (Step 2/4)")
        jd_system_message = """You are an expert job description parser. Extract key requirements from the job description including:
        - Required technical skills
        - Minimum experience needed
        - Educational requirements
        - Key responsibilities
        - Soft skills and other attributes
        Provide the information in a structured format for easy comparison."""
        
        jd_result = await groq.generate_response(
            f"Parse this job description and extract key requirements: {job_description}",
            jd_system_message
        )
        
        # Add delay between API calls
        await asyncio.sleep(2)
        
        # Step 3: Analyze match
        st.info("Calculating match score... (Step 3/4)")
        match_system_message = """You are an expert resume-job match analyzer. Compare the resume with job description requirements to determine:
        - Overall match score (percentage)
        - Key matching skills and experiences
        - Missing skills or qualifications
        - Assessment of chances of selection
        Provide a detailed analysis with specific examples."""
        
        match_result = await groq.generate_response(
            f"""Compare the following resume with the job description requirements:
            Resume information: {resume_result}
            Job requirements: {jd_result}
            
            Provide a detailed match analysis including percentage match and specific matching/missing elements.""",
            match_system_message
        )
        
        # Add delay between API calls
        await asyncio.sleep(2)
        
        # Step 4: Generate improvement suggestions
        st.info("Generating improvement suggestions... (Step 4/4)")
        improvement_system_message = """You are an expert career advisor. Based on the gaps identified, provide actionable recommendations:
        - Specific skills to acquire or highlight
        - Resume improvements and restructuring suggestions
        - How to better position existing experience
        - Suggestions for addressing missing requirements
        - Interview preparation tips specific to this role
        Provide practical, specific advice that can be implemented."""
        
        improvement_result = await groq.generate_response(
            f"""Based on the following analysis:
            Resume information: {resume_result}
            Job requirements: {jd_result}
            Match analysis: {match_result}
            
            Provide detailed recommendations for improving the match and preparing for the application/interview process.""",
            improvement_system_message
        )
        
        # Compile final report
        final_report = f"""# Resume-Job Description Match Analysis

## Match Summary
{match_result}

## Resume Overview
{resume_result}

## Job Requirements Overview
{jd_result}

## Improvement Recommendations
{improvement_result}

*Report generated by JDmatcher*
"""
        
        return {
            "resume_analysis": resume_result,
            "jd_analysis": jd_result,
            "match_analysis": match_result,
            "improvement_suggestions": improvement_result,
            "final_report": final_report
        }
    except Exception as e:
        st.error(f"An error occurred during workflow execution: {e}")
        return {
            "resume_analysis": "", 
            "jd_analysis": "",
            "match_analysis": "",
            "improvement_suggestions": "",
            "final_report": ""
        }

# Streamlit App
async def main():
    st.title("JDmatcher: Resume & Job Description Analyzer")
    st.subheader("Find your match score and improve your chances")

    st.sidebar.header("Upload Files and API Key")
    api_key = st.sidebar.text_input("Enter your Groq API key:", type="password")
    if not api_key:
        st.warning("Please provide a valid Groq API key 🙏🏻")
        return 
    
    resume_file = st.sidebar.file_uploader("Upload Resume PDF", type="pdf", accept_multiple_files=False)
    
    st.sidebar.header("Job Description")
    job_description = st.sidebar.text_area("Paste Job Description Here:", height=300)

    # Add option for reducing API calls
    st.sidebar.header("Advanced Options")
    simplified_mode = st.sidebar.checkbox("Use Simplified Mode (fewer API calls)", value=False, 
                                         help="Enable this if you encounter rate limit issues")

    if st.sidebar.button("Analyze Match"):
        if not api_key:
            st.error("Please enter a valid Groq API key to proceed. 🙏🏻")
            return
            
        if not resume_file or not job_description:
            st.error("Please upload your resume and provide a job description.")
            return

        # Show processing status
        with st.status("Processing your match...", expanded=True) as status:
            st.write("Extracting resume content...")
            # Extract text from resume PDF
            resume_text = extract_text_from_pdf(resume_file)
            
            if not resume_text:
                st.error("Failed to extract text from the uploaded resume.")
                return
            
            # Check if using simplified mode
            if simplified_mode:
                # Simplified approach - single API call
                st.write("Using simplified mode with a single API call...")
                groq = GroqAPI(api_key)
                
                system_message = """You are an expert resume and job description analyzer. 
                Your task is to analyze a resume and job description to provide:
                1. An analysis of the resume (skills, experience, education)
                2. An analysis of the job requirements
                3. A match score (percentage) between the resume and job
                4. Specific matching skills and experiences
                5. Missing skills or qualifications
                6. Recommendations for improving the match
                
                Format your response with clear headings for each section."""
                
                prompt = f"""Resume content:
                {resume_text}
                
                Job Description:
                {job_description}
                
                Please provide a comprehensive analysis including match percentage, matched skills, missing skills, and improvement recommendations."""
                
                try:
                    result = await groq.generate_response(prompt, system_message)
                    
                    # Extract match percentage
                    match_percentage = re.search(r'(\d{1,3})%', result)
                    percentage = int(match_percentage.group(1)) if match_percentage else 50
                    
                    results = {
                        "resume_analysis": "See detailed report",
                        "jd_analysis": "See detailed report",
                        "match_analysis": f"Match score: {percentage}%\n\nSee detailed report for more information.",
                        "improvement_suggestions": "See detailed report",
                        "final_report": result
                    }
                    
                except Exception as e:
                    st.error(f"API Error: {e}")
                    return
            else:
                # Use the full multi-step analysis
                st.write("Analyzing resume and job description...")
                results = await process_resume_and_jd(api_key, resume_text, job_description)
                
            status.update(label="Analysis complete!", state="complete")

        # Display results
        if results and results.get("final_report"):
            st.success("Match analysis complete!")
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Match Analysis", "Detailed Report", "Download"])
            
            with tab1:
                # Extract and display match percentage
                match_text = results["match_analysis"]
                # Look for percentage in the match analysis
                match_percentage = re.search(r'(\d{1,3})%', match_text)
                percentage = int(match_percentage.group(1)) if match_percentage else 50
                
                st.subheader("Match Score")
                st.progress(percentage/100)
                st.write(f"{percentage}% Match with Job Requirements")
                
                # Display key sections
                st.subheader("Key Matching Points")
                st.write(results["match_analysis"])
                
                st.subheader("Areas for Improvement")
                st.write(results["improvement_suggestions"])
            
            with tab2:
                st.markdown(results["final_report"])
            
            with tab3:
                # Create file for download
                report_file_path = "jdmatch_report.md"
                
                with open(report_file_path, "w", encoding="utf-8") as f:
                    f.write(results["final_report"])
                st.success("Report file created!")
                
                # Ensure download button is only shown after file is created
                if os.path.exists(report_file_path):
                    with open(report_file_path, "r", encoding="utf-8") as file:
                        st.download_button(
                            label="Download Full Analysis Report",
                            data=file,
                            file_name="jdmatch_report.md",
                            mime="text/markdown"
                        )

# Run Streamlit App
if __name__ == "__main__":
    asyncio.run(main())
