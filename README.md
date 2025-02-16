# AI-Powered Blog Post Generator

This project implements an automated blog post generation system using LangChain and Anthropic's Claude 3.5 Sonnet model. The system follows a three-stage process to create well-researched, original blog posts on any given topic.

## Features

- 🔍 Automated research gathering using web searches
- ✍️ AI-powered content writing
- 🕵️ Plagiarism detection and source verification
- 🔄 Built-in retry mechanism with exponential backoff
- 💾 Automatic file saving for both blog posts and plagiarism reports

## System Architecture

The system uses three specialized AI agents:

1. **Research Agent**
   - Utilizes SerpAPI for web searches
   - Gathers 3-4 key points about the given topic
   - Limits search results to maintain focus

2. **Content Writer**
   - Creates structured blog posts with:
     - Title
     - Introduction
     - Detailed body content
     - Conclusion
     - Source citations

3. **Plagiarism Checker**
   - Compares generated content with web sources
   - Checks for:
     - Direct copying
     - Similar phrasing
     - Proper attribution

## Usage

1. Install dependencies:
   ```bash
   pip install langchain anthropic serpapi-python
   ```

2. Set environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export SERPAPI_API_KEY="your_serpapi_api_key"
   ```

3. Run the script:
   ```bash
   python main.py
   ```

