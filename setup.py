from setuptools import setup, find_packages

setup(
    name="hospital-ai-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.1",
        "langchain-core>=0.0.1",
        "langchain-groq>=0.0.1",
        "supabase>=1.0.0",
        "python-dotenv>=1.0.0",
        "cohere>=4.0.0",
        "groq>=0.1.0",
        "neo4j>=5.0.0"
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'hospital-ai = server.router:main',
        ],
    },
)
