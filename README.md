# JDmatcher - Resume & Job Description Analyzer

![JDmatcher Logo](https://img.shields.io/badge/JDmatcher-Resume%20Analyzer-blue)
![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

JDmatcher is a powerful AI-powered tool that analyzes your resume against job descriptions to provide match scores, detailed analysis, and personalized recommendations to help you improve your job applications.

## 🌟 Features

- **Smart Analysis**: Uses Groq's Llama 3.3 70B model to analyze resume-job description compatibility
- **Match Scoring**: Get a precise percentage match score between your resume and target job
- **Skills Gap Analysis**: Identify missing skills and qualifications needed for the role
- **Resume Enhancement**: Receive personalized recommendations to improve your application
- **Downloadable Reports**: Export analysis in Markdown or plain text formats
- **Session Caching**: Results are cached to provide consistent scores and reduce API calls

## 📋 Requirements

- Python 3.8+
- Streamlit 1.32.0+
- PyPDF2 3.0.1+
- Requests 2.31.0+
- Asyncio 3.4.3+
- A Groq API key (register at [groq.com](https://groq.com))

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/jdmatcher.git
   cd jdmatcher
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## 💡 How to Use

1. **Get your API Key**: Sign up for a free Groq API key at [groq.com](https://groq.com)
2. **Launch the App**: Run the application using Streamlit
3. **Enter your API Key**: Input your Groq API key in the sidebar
4. **Upload Resume**: Upload your resume in PDF format
5. **Add Job Description**: Copy and paste the job description text into the sidebar
6. **Analyze**: Click "Analyze Match" and wait for the results
7. **Review Report**: Check your match score, strengths, and improvement areas
8. **Download Report**: Save your analysis as either Markdown or Text format

## 📊 How It Works

JDmatcher follows a sophisticated 4-step analysis process:

1. **Resume Analysis**: The AI extracts key information from your PDF resume
2. **Job Description Analysis**: The AI parses essential requirements from the job posting
3. **Match Calculation**: A detailed comparison generates a precise match percentage
4. **Improvement Suggestions**: Personalized recommendations to enhance your application

All processing is done with deterministic settings to ensure consistent, reliable results.

## 📝 Example

```
Match Score: 78%

Key Matching Points:
- 5 years of Python development experience (Requirement: 3+ years)
- Strong background in data science and machine learning
- Experience with cloud deployment on AWS
- Project management and team leadership experience

Areas for Improvement:
- Missing experience with Kubernetes (mentioned as preferred)
- Consider highlighting database optimization skills more prominently
- Add examples of CI/CD implementation in previous roles
```

## ⚙️ Configuration

The application uses Groq's Llama 3.3 70B model by default. The key parameters are:
- `temperature: 0` (for deterministic outputs)
- `seed: 42` (for consistent results)
- `max_tokens: 2048` (for comprehensive responses)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Streamlit](https://streamlit.io/) for the intuitive UI framework
- [Groq](https://groq.com/) for the powerful AI API
- [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing capabilities

---

Made with ❤️ by Lakshya Tripathi - Happy job hunting!
