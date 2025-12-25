# Instagram Content Analyzer

AI-powered system that analyzes saved Instagram posts and reels to answer natural language queries about content.

## Features

- Multi-modal content analysis (video, audio, text, images)
- Natural language query processing
- Secure Instagram authentication
- Privacy-focused data handling
- Real-time content retrieval and analysis

## Setup

1. Create virtual environment:
```bash
python3 -m venv instagram_analyzer_env
source instagram_analyzer_env/bin/activate  # On Windows: instagram_analyzer_env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
uvicorn src.main:app --reload
```

## Project Structure

- `src/` - Main application code
- `tests/` - Test suite
- `config/` - Configuration files
- `docs/` - Documentation

## Requirements

- Python 3.9+
- Chrome/Chromium browser (for Selenium)
- OpenAI API key
- MongoDB instance (local or cloud)

## License

MIT License