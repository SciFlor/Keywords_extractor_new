# Keywords_extractor_new

## Overview

Keyword Extractor is a powerful tool designed to automatically extract keywords from chapters in JSON output. This project utilizes Docker containers, a Flask-based keyword extraction service, and a Streamlit web interface to provide an easy-to-use keyword extraction solution. It's particularly useful for analyzing large texts, such as books or articles, by breaking them down into their most significant terms.

## Features

- Processes JSON files containing chapter data from the Chapter Extractor app
- Extracts multiple keywords for each chapter using TF-IDF algorithm
- Calculates trust intervals and frequency for each keyword
- Provides a user-friendly web interface using Streamlit
- Offers CSV, JSON, and Excel export of extracted keywords
- Allows saving all tables in multiple formats in a dedicated folder
- Displays progress during processing
- Provides detailed view for each chapter's keywords
- Implements error handling and logging for robust operation
- Uses Docker for easy deployment and scalability
