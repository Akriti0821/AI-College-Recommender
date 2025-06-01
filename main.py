import streamlit as st
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv # For local testing

# --- Streamlit Page Configuration - MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="AI College Recommender", page_icon="🎓")

# Load environment variables (for local development only)
load_dotenv()

# --- Gemini API Configuration ---
# Use st.secrets for Streamlit Cloud deployment, fallback to os.getenv for local
api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API Key not found. Please set it in your .streamlit/secrets.toml or as an environment variable.")
    st.stop() # This will stop the app execution if key is missing

genai.configure(api_key=api_key)

# Initialize Gemini model (cached to avoid re-initializing on every rerun)
@st.cache_resource
def get_gemini_model():
    """Returns the Gemini model configured with tools."""
    # Define tools for the model
    tools = [
        {
            "function_declarations": [{
                "name": "get_college_data",
                "description": "Retrieves simulated data for colleges based on criteria like major, rank, location, and specific interests. Use this to find colleges.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "major": {"type": "string", "description": "Desired field of study or major (e.g., 'Computer Science', 'Business', 'Arts')."},
                        "min_rank": {"type": "integer", "description": "Optional: Minimum college rank (e.g., 1 for top 10). Smaller number means higher rank."},
                        "max_rank": {"type": "integer", "description": "Optional: Maximum college rank (e.g., 50 for top 50)."},
                        "location_preference": {"type": "string", "description": "Optional: Preferred geographic location (e.g., 'California', 'India', 'urban')."},
                        "academic_skills": {"type": "array", "items": {"type": "string"}, "description": "Optional: User's academic strengths or skills (e.g., 'coding', 'writing', 'math')."},
                        "extra_curriculars": {"type": "array", "items": {"type": "string"}, "description": "Optional: User's extra-curricular activities or interests (e.g., 'sports', 'music', 'debate')."}
                    },
                    "required": ["major"]
                }
            }]
        },
        {
            "function_declarations": [{
                "name": "search_scholarships",
                "description": "Searches for simulated scholarship opportunities based on college, major, or academic profile. Use this after college recommendations to find funding.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "college_name": {"type": "string", "description": "Optional: Name of a specific college to search scholarships for."},
                        "major": {"type": "string", "description": "Optional: Field of study relevant to the scholarship."},
                        "academic_profile": {"type": "string", "description": "Optional: User's academic profile (e.g., 'high GPA', 'research experience', 'leadership')."},
                        "skills": {"type": "array", "items": {"type": "string"}, "description": "Optional: Specific skills that might qualify for scholarships (e.g., 'robotics', 'fine arts')."}
                    },
                    "required": [] # No required fields, can be broad search
                }
            }]
        },
        {
            "function_declarations": [{
                "name": "validate_input",
                "description": "Validates if the user has provided essential information like desired major before attempting to recommend colleges. Use this when the initial query is too vague.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "required_info": {"type": "array", "items": {"type": "string"}, "description": "List of information required from the user (e.g., 'major', 'skills', 'location')."},
                        "message_to_user": {"type": "string", "description": "A polite question asking the user for the missing information."}
                    },
                    "required": ["required_info", "message_to_user"]
                }
            }]
        }
    ]
    return genai.GenerativeModel(model_name='gemini-1.5-pro', tools=tools) # Or 'gemini-1.0-pro'

model = get_gemini_model() # Now this is called AFTER set_page_config()

# --- Simulated Tool Functions ---
# These functions simulate data retrieval. Replace with real API calls for production.

def get_college_data(major: str, min_rank: int = None, max_rank: int = None, location_preference: str = None, academic_skills: list = None, extra_curriculars: list = None):
    """Simulated function to get college data."""
    st.info(f"DEBUG: Tool Call: get_college_data(major='{major}', rank={min_rank}-{max_rank}, loc='{location_preference}', skills='{academic_skills}')")
    
    # --- Mock Data ---
    colleges = [
        {"name": "Tech University", "major": "Computer Science", "rank": 5, "location": "California, USA", "scholarships": ["Merit Scholarship", "Research Grant"], "notes": "Strong in AI and ML. High research output.", "min_gpa": 3.8, "skills_preferred": ["coding", "algorithms"]},
        {"name": "Global Business School", "major": "Business", "rank": 12, "location": "New York, USA", "scholarships": ["Dean's Scholarship", "Diversity Scholarship"], "notes": "Excellent MBA program. Strong industry connections.", "min_gpa": 3.5, "skills_preferred": ["leadership", "finance"]},
        {"name": "Arts Institute", "major": "Fine Arts", "rank": 8, "location": "London, UK", "scholarships": ["Creative Arts Award"], "notes": "Renowned for painting and sculpture.", "min_gpa": 3.0, "skills_preferred": ["drawing", "painting"]},
        {"name": "National Engineering College", "major": "Mechanical Engineering", "rank": 25, "location": "Hyderabad, India", "scholarships": ["State Aid", "Innovation Fund"], "notes": "Hands-on projects, good industry ties in India.", "min_gpa": 3.2, "skills_preferred": ["robotics", "CAD"]},
        {"name": "Green Earth University", "major": "Environmental Science", "rank": 30, "location": "Oregon, USA", "scholarships": ["Sustainability Grant"], "notes": "Focus on renewable energy and conservation.", "min_gpa": 3.3, "skills_preferred": ["research", "environmental analysis"]},
        {"name": "City Medical School", "major": "Medicine", "rank": 3, "location": "Boston, USA", "scholarships": ["Medical Research Fellowship"], "notes": "Highly competitive, excellent hospital affiliations.", "min_gpa": 3.9, "skills_preferred": ["biology", "chemistry", "research"]},
        {"name": "Elite Tech Institute", "major": "Computer Science", "rank": 2, "location": "California, USA", "scholarships": ["Presidential Scholarship", "Engineering Grant"], "notes": "World-leading in AI and data science. Very competitive.", "min_gpa": 4.0, "skills_preferred": ["coding", "data structures", "machine learning"]},
        {"name": "Global Business School", "major": "Economics", "rank": 10, "location": "New York, USA", "scholarships": ["Fellowship for Global Studies"], "notes": "Strong quantitative economics program.", "min_gpa": 3.7, "skills_preferred": ["mathematics", "analytical thinking"]},
        {"name": "Indian Institute of Technology Bombay", "major": "Computer Science", "rank": 1, "location": "Mumbai, India", "scholarships": ["Institute Scholarship", "Private Grants"], "notes": "Premier engineering institute in India.", "min_gpa": 3.9, "skills_preferred": ["coding", "algorithms", "problem solving"]},
        {"name": "University of Delhi", "major": "History", "rank": 50, "location": "Delhi, India", "scholarships": ["University Grants"], "notes": "Strong humanities programs.", "min_gpa": 3.0, "skills_preferred": ["research", "writing", "critical thinking"]},
    ]

    results = []
    for college in colleges:
        if college["major"].lower() != major.lower():
            continue
        if min_rank is not None and college["rank"] < min_rank:
            continue
        if max_rank is not None and college["rank"] > max_rank:
            continue
        if location_preference and location_preference.lower() not in college["location"].lower():
            continue
        if academic_skills:
            skill_match = False
            for skill in academic_skills:
                if skill.lower() in [s.lower() for s in college.get("skills_preferred", [])]:
                    skill_match = True
                    break
            if not skill_match:
                continue
        results.append(college)
    
    if not results:
        return "No colleges found matching the criteria in the simulated database. Please try broadening your search or modifying criteria."
    
    results.sort(key=lambda x: x["rank"])
    return json.dumps(results[:5]) # Return top 5 matches as JSON string

def search_scholarships(college_name: str = None, major: str = None, academic_profile: str = None, skills: list = None):
    """Simulated function to search scholarship opportunities."""
    st.info(f"DEBUG: Tool Call: search_scholarships(college='{college_name}', major='{major}', profile='{academic_profile}', skills='{skills}')")
    
    # --- Mock Scholarship Data ---
    scholarships = [
        {"name": "University Merit Scholarship", "college": "Tech University", "major": "Any", "criteria": "GPA 3.8+, leadership", "amount": "$10,000/year"},
        {"name": "AI Research Fellowship", "college": "Tech University", "major": "Computer Science", "criteria": "Research experience in AI, strong coding skills", "amount": "$5,000 one-time"},
        {"name": "Global Leader Award", "college": "Global Business School", "major": "Business", "criteria": "Exceptional leadership, international experience", "amount": "$15,000/year"},
        {"name": "STEM Innovator Grant", "college": "National Engineering College", "major": "Engineering", "criteria": "Demonstrated innovation in robotics or sustainability projects", "amount": "$7,500 one-time"},
        {"name": "Environmental Champion Grant", "college": "Green Earth University", "major": "Environmental Science", "criteria": "Community involvement in environmental causes", "amount": "$8,000/year"},
        {"name": "General Excellence Scholarship", "college": "Any", "major": "Any", "criteria": "GPA 3.5+, strong essays", "amount": "Varies"},
        {"name": "Dean's Excellence Award", "college": "Elite Tech Institute", "major": "Computer Science", "criteria": "Top academic performance, competitive", "amount": "$20,000/year"},
        {"name": "Indian STEM Scholarship", "college": "Indian Institute of Technology Bombay", "major": "Any STEM", "criteria": "High scores in JEE Advanced, research aptitude", "amount": "Full Tuition"},
        {"name": "Humanities Research Grant", "college": "University of Delhi", "major": "History", "criteria": "Excellent academic record in humanities, research proposal", "amount": "Rs. 50,000 one-time"}
    ]

    results = []
    for scholarship in scholarships:
        match = True
        if college_name and college_name.lower() != "any" and college_name.lower() not in scholarship["college"].lower():
            match = False
        if major and major.lower() != "any" and major.lower() not in scholarship["major"].lower():
            match = False
        
        if academic_profile and academic_profile.lower() not in scholarship["criteria"].lower():
            match = False
        if skills:
            skill_found = False
            for s in skills:
                if s.lower() in scholarship["criteria"].lower():
                    skill_found = True
                    break
            if not skill_found:
                match = False
        
        if match:
            results.append(scholarship)
    
    if not results:
        return "No scholarships found matching your criteria in the simulated database. Try broadening your search."
    
    return json.dumps(results[:3]) # Return top 3 matches as JSON string

def validate_input(required_info: list, message_to_user: str):
    """Simulated function to ask user for required info."""
    st.warning(f"DEBUG: Tool Call: validate_input(Required={required_info}, Message='{message_to_user}')")
    return message_to_user


# --- Streamlit UI and Agent Logic ---
st.title("🎓 AI College Recommender")
st.markdown("I can help you find suitable colleges and scholarships based on your interests, skills, and preferences!")

# Initialize chat history in session state if not already present
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
    # Add initial welcome message
    st.session_state.chat_history.append({"role": "model", "parts": ["Hello! I'm your AI College Recommender. Tell me about your academic interests, skills, desired major, preferred college rank, or anything else to help me find the best institutes for you."]})

# Initialize chat session in session state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    # Rebuild history for the chat_session if starting mid-conversation
    for message in st.session_state.chat_history:
        st.session_state.chat_session.history.append(message)


# Function to handle tool calls
def call_tool(tool_name, **kwargs):
    """Calls the appropriate simulated tool function."""
    tool_functions = {
        "get_college_data": get_college_data,
        "search_scholarships": search_scholarships,
        "validate_input": validate_input
    }
    if tool_name in tool_functions:
        return tool_functions[tool_name](**kwargs)
    else:
        return f"Error: Tool '{tool_name}' not found."


# Display chat messages from history on app rerun
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["parts"][0])
    elif message["role"] == "model":
        with st.chat_message("assistant"):
            st.markdown(message["parts"][0])


# Accept user input
user_query = st.chat_input("Ask me about colleges or scholarships...")

if user_query:
    st.session_state.chat_history.append({"role": "user", "parts": [user_query]})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_session.send_message(user_query)
                
                # Check for function calls in the response
                if response.parts and response.parts[0].function_call:
                    function_call = response.parts[0].function_call
                    tool_name = function_call.name
                    tool_args = {k: v for k, v in function_call.args.items()}

                    st.info(f"AI wants to use tool: `{tool_name}` with arguments: `{tool_args}`")

                    tool_output = call_tool(tool_name, **tool_args)
                    
                    # Send tool output back to the model
                    st.session_state.chat_session.send_message(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={
                                    "result": tool_output
                                }
                            )
                        )
                    )
                    
                    # Get the final natural language response from the model
                    final_response = st.session_state.chat_session.last.candidates[0].content.text
                    st.markdown(final_response)
                    st.session_state.chat_history.append({"role": "model", "parts": [final_response]})
                else:
                    # Model responded directly
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "model", "parts": [response.text]})

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.chat_history.append({"role": "model", "parts": [f"I apologize, I encountered an error: {e}. Please try again or rephrase your request."]})


# Reset button
if st.button("Reset Chat"):
    st.session_state.chat_history = []
    st.session_state.chat_session = model.start_chat(history=[]) # Reinitialize chat session
    st.session_state.chat_history.append({"role": "model", "parts": ["Chat has been reset! How can I help you today?"]})
    st.experimental_rerun() # Rerun the app to clear display

st.markdown("---")
st.markdown("Example queries: 'I want to study Computer Science', 'Suggest top 5 business schools', 'Find scholarships for Tech University', 'I am good at coding and research, what engineering colleges should I look at?', 'Which colleges offer history major in Delhi?'")