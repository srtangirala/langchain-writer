from langchain_anthropic import ChatAnthropic
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.chains import LLMChain
from langchain_community.utilities import SerpAPIWrapper
from langchain.tools import Tool
import os

# Set your Anthropic API key
os.environ["ANTHROPIC_API_KEY"] = "<your_anthropic_api_key>"
os.environ["SERPAPI_API_KEY"] = "<your_serpapi_api_key>"

# Initialize the LLMs for all agents
researcher_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
writer_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
plagiarism_llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

search = SerpAPIWrapper(serpapi_api_key=os.environ["SERPAPI_API_KEY"])  # Add your SerpAPI key here
search_tool = Tool(
    name="Search",
    func=search.run,
    description="Useful for searching information on the internet"
)

# Define tools for the researcher agent
researcher_tools = [
    Tool(
        name="Search",
        func=lambda x: search_tool.run(x)[:500],  # Limit search results to 500 characters
        description="Useful for searching information on the internet. Use specific search terms."
    )
]

# Create the researcher agent prompt
researcher_prompt = PromptTemplate(
    input_variables=["tools", "input", "agent_scratchpad", "tool_names"],
    template="""You are a research expert. Gather 3-4 key points about this topic.

Available tools: {tool_names}
Tools details: {tools}

Research this topic: {input}

To use a tool, please use the following format:
Thought: I need to research something
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have 3-4 key points, respond with:
Thought: I have enough information
Final Answer: your final response (keep it under 300 words)

{agent_scratchpad}"""
)

# Create the researcher agent
researcher_agent = create_react_agent(
    llm=researcher_llm,
    tools=researcher_tools,
    prompt=researcher_prompt
)

researcher_executor = AgentExecutor.from_agent_and_tools(
    agent=researcher_agent,
    tools=researcher_tools,
    verbose=True,
    handle_parsing_errors=True
)

# Create the content writer prompt
writer_prompt = PromptTemplate(
    input_variables=["research"],
    template="""Create a blog post based on this research:
    
    {research}
    
    Include:
    1. A title
    2. Brief introduction
    3. Detailed points with references and examples from the research. 
    4. Short conclusion
    5. Add citations to the sources used in the research where ever necessary
    
    Format in Markdown."""
)

# Create the writer chain
writer_chain = writer_prompt | writer_llm

# Create the plagiarism checker prompt
plagiarism_prompt = PromptTemplate(
    input_variables=["blog_post", "search_results"],
    template="""Compare this blog post with search results for plagiarism:

Blog post:
{blog_post}

Search results:
{search_results}

Provide a brief analysis focusing on:
1. Direct copying
2. Similar phrasing
3. Proper attribution

Format: Brief summary followed by any found issues."""
)

# Create the plagiarism checker chain
plagiarism_chain = plagiarism_prompt | plagiarism_llm

def create_blog_post(topic, max_retries=5):
    """
    Main function to create a blog post on a given topic with improved retry logic
    """
    for attempt in range(max_retries):
        try:
            # Add exponential backoff between attempts
            if attempt > 0:
                wait_time = min(300, (2 ** attempt) * 15)  # Exponential backoff with max 300 seconds
                print(f"\n⏳ Waiting {wait_time} seconds before attempt {attempt + 1}/{max_retries}...")
                import time
                time.sleep(wait_time)
            
            # Step 1: Research with smaller chunks
            print(f"\n🔍 Researching the topic (Attempt {attempt + 1}/{max_retries})...")
            research_results = researcher_executor.invoke(
                {"input": f"Provide 3 key points about: {topic}"},  # Simplified input
                config={
                    "timeout": 120,  # Increased timeout
                    "max_iterations": 3  # Limit research iterations
                }
            )["output"]
            
            # Add a small delay between API calls
            time.sleep(5)
            
            # Step 2: Write the blog post
            print("\n✍️ Creating the blog post...")
            blog_post = writer_chain.invoke({"research": research_results[:2000]}).content  # Limit research input
            
            time.sleep(5)
            
            # Step 3: Check for plagiarism
            print("\n🔍 Checking for plagiarism...")
            search_results = search_tool.run(topic)[:800]  # Further limited search results
            plagiarism_check = plagiarism_chain.invoke({
                "blog_post": blog_post[:1500],  # Limit blog post size for checking
                "search_results": search_results
            }).content
            
            # Save files
            blog_filename = f"{topic.lower().replace(' ', '_')}.md"
            plagiarism_filename = f"{topic.lower().replace(' ', '_')}_plagiarism_check.md"
            
            with open(blog_filename, 'w', encoding='utf-8') as f:
                f.write(blog_post)
            print(f"\n💾 Blog post saved to {blog_filename}")
            
            with open(plagiarism_filename, 'w', encoding='utf-8') as f:
                f.write(plagiarism_check)
            print(f"💾 Plagiarism check saved to {plagiarism_filename}")
            
            return blog_post
            
        except Exception as e:
            error_message = str(e).lower()
            print(f"\n⚠️ Attempt {attempt + 1} failed with error: {error_message}")
            
            if any(err in error_message for err in ["overloaded", "timeout", "rate_limit"]):
                if attempt < max_retries - 1:
                    continue
                
            if "overloaded" in error_message:
                print("\n❌ API is currently overloaded. Please try again later.")
            else:
                print(f"\n❌ Error: {str(e)}")
                
            if attempt == max_retries - 1:
                raise Exception(f"Maximum retries ({max_retries}) reached. Last error: {str(e)}")

# Example usage
if __name__ == "__main__":
    topic = "Cinema and AI"
    blog_post = create_blog_post(topic)
    print("\n📝 Final Blog Post:")
    print(blog_post)