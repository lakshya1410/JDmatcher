import streamlit as st
import asyncio
import os
import re
import json
import requests
from typing import Dict
#import pdfkit
#import markdown

def extract_text_from_pdf(file):
    try:
        from PyPDF2 import PdfReader
        pdf_reader = PdfReader(file)
        text = ''.join(page.extract_text() for page in pdf_reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def convert_markdown_to_pdf(markdown_content, output_pdf_path):
    try:
        # Convert markdown to HTML
        html_content = markdown.markdown(markdown_content)
        
        # Add some basic styling
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>JDmatcher Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; margin-top: 30px; }}
                h3 {{ color: #2980b9; }}
                .match-score {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Configuration for pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
        }
        
        # Generate PDF from HTML
        pdfkit.from_string(styled_html, output_pdf_path, options=options)
        return True
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return False

class GroqAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Using Llama 3 70B from Groq
        
    async def generate_response(self, prompt, system_message="You are a helpful assistant."):
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
        
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            st.error(f"API Error: {e}")
            return f"Error: {str(e)}"

async def process_resume_and_jd(api_key, resume_text, job_description):
    groq = GroqAPI(api_key)
    
    try:
        # Step 1: Parse resume
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
        
        # Step 2: Parse job description
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
        
        # Step 3: Analyze match
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
        
        # Step 4: Generate improvement suggestions
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
                
            st.write("Analyzing resume and job description...")
            # Process resume and job description
            results = await process_resume_and_jd(api_key, resume_text, job_description)
            
            status.update(label="Analysis complete!", state="complete")

        # Display results
        if results and results["final_report"]:
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
                # Create files for download
                report_md_path = "jdmatch_report.md"
                report_pdf_path = "jdmatch_report.pdf"
                
                # Save markdown report
                with open(report_md_path, "w", encoding="utf-8") as f:
                    f.write(results["final_report"])
                
                # Create PDF from markdown
                pdf_success = convert_markdown_to_pdf(results["final_report"], report_pdf_path)
                
                # Markdown download button
                st.subheader("Download Options")
                if os.path.exists(report_md_path):
                    with open(report_md_path, "r", encoding="utf-8") as file:
                        st.download_button(
                            label="Download as Markdown (.md)",
                            data=file,
                            file_name="jdmatch_report.md",
                            mime="text/markdown"
                        )
                
                # PDF download button
                if pdf_success and os.path.exists(report_pdf_path):
                    with open(report_pdf_path, "rb") as file:
                        st.download_button(
                            label="Download as PDF",
                            data=file,
                            file_name="jdmatch_report.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.warning("PDF generation failed. You can still download the markdown version.")

# Run Streamlit App
if __name__ == "__main__":
    asyncio.run(main())
