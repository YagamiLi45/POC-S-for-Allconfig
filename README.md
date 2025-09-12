
#🚀 Jenkins Error Resolver
---------------------------------------------------------------------------------------

Goal: Automatically fetch, summarize, and resolve Jenkins build errors using AI.

##🤖 Project Description 
---------------------------------------------------------------------------------------

Jenkins Error Resolver is a Python-based tool designed to automatically fetch Jenkins build logs, 
detect and summarize errors, and provide actionable solutions using AI (Gemini). It helps developers
quickly understand build failures and take corrective steps without manually inspecting long console outputs.

The project supports:

CLI Mode: Automatically runs after a Jenkins build failure to summarize and suggest fixes.

Web Mode (Streamlit): Provides an interactive interface to explore errors and their solutions.

Persistent Storage (Pinecone): Stores errors and AI-generated solutions for future retrieval.

With this tool, Jenkins build troubleshooting becomes faster, easier, and more consistent.

##🔧 Requirements
---------------------------------------------------------------------------------------

#Python with libraries: streamlit, requests, dotenv, google-generativeai, pinecone-client

#Jenkins server with API access (using Log Parser Plugin recommended)

#Gemini AI API key and Pinecone API key


##🧩 WorkFlow
---------------------------------------------------------------------------------------
1)Getting the Error From Jenkins Console

2)Extract the error pass to the LLM

3)Get a Solution for your error

4)Storing the Error in DB for retrieval

5)Web Mode (Streamlit): Interactive UI to explore and resolve errors

##⚙️ Configuration
-------------------------------------------------------------------------------
You can set the API Keys in Jenkins Credentials

For Web UI set in the env file

##✅ Optional:
-------------------------------------------------------------------------------------
Mode = CLI

Mode = Web
