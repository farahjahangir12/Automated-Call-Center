from setuptools import setup, find_packages

setup(
    name="hospital-ai-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-groq>=0.1.0",
        "langchain-cohere>=0.1.0",
        "langchain-neo4j>=0.1.0",
        "supabase>=1.0.0",
        "python-dotenv>=1.0.0",
        "numpy>=1.24.0",
        "asyncio>=3.4.3",
        "langchain-core>=0.1.0"
    ],
    python_requires=">=3.8",
)
