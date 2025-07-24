from setuptools import setup, find_packages

setup(
    name="analyst_crew",
    version="0.1.0",
    packages=find_packages(),
    description="An AI-powered analyst crew that can be orchestrated from Hex notebooks.",
    author="Your Name",
    author_email="your.email@example.com",
    install_requires=[
        "crewai==0.28.8",
        "langchain_openai==0.1.1",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "ipython",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)