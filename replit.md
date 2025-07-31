# WordPress SEO Optimizer

## Overview

WordPress SEO Optimizer is a Python-based system that automatically optimizes WordPress posts for SEO using Google Gemini AI and TMDB data. The system is designed to run on Replit and provides automated content optimization with real-time monitoring through a Flask web dashboard.

## User Preferences

Preferred communication style: Simple, everyday language.
Content Management: User ID 9 edits posts from User ID 6 (João).
SEO Rules: Titles must be plain text only (no HTML tags) for meta tags, RSS, and Google News compatibility.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components
- **Main Application**: Entry point with CLI support and scheduling capabilities
- **SEO Optimizer**: Central orchestration engine that coordinates all optimization processes
- **Database Layer**: SQLite-based storage for tracking, logging, and quota management
- **API Clients**: Separate clients for WordPress, Gemini AI, and TMDB integrations
- **Web Dashboard**: Flask-based monitoring interface with real-time updates

### Technology Stack
- **Backend**: Python 3.x with Flask web framework
- **Database**: SQLite for lightweight data persistence
- **Frontend**: Bootstrap 5 with Chart.js for visualization
- **APIs**: WordPress REST API, Google Gemini AI, TMDB API
- **Deployment**: Replit-optimized with environment variable configuration

## Key Components

### 1. Configuration Management (`config.py`)
- Centralized configuration using environment variables
- Support for multiple Gemini API keys with automatic rotation
- WordPress connection settings and TMDB API configuration
- Comprehensive logging setup

### 2. SEO Optimization Engine (`seo_optimizer.py`)
- Processes WordPress posts in controlled batches (2 posts per cycle)
- Integrates with TMDB for movie/series metadata
- Uses Gemini AI for content optimization with journalism-focused prompts
- Updates Yoast SEO fields via WordPress REST API

### 3. Database Management (`database.py`)
- SQLite schema for processing control, logs, and quota tracking
- Context managers for connection handling
- Statistics and reporting capabilities
- Gemini API quota management with key rotation

### 4. API Clients
- **WordPress Client** (`wordpress_client.py`): REST API integration with authentication
- **Gemini Client** (`gemini_client.py`): AI content generation with quota management
- **TMDB Client** (`tmdb_client.py`): Movie/series metadata retrieval

### 5. Web Dashboard (`dashboard.py`)
- Real-time system monitoring
- Processing statistics and logs
- Manual test execution capabilities
- RESTful API endpoints for frontend consumption

## Data Flow

1. **Content Discovery**: System queries WordPress for new posts by João (User ID 6)
2. **Metadata Enrichment**: TMDB API provides movie/series details and media assets
3. **AI Optimization**: Gemini AI optimizes content using journalism-focused prompts
4. **Content Update**: WordPress REST API updates posts with optimized content and Yoast SEO fields (edited by User ID 9)
5. **Tracking & Logging**: All activities logged to SQLite database for monitoring

### Post Processing Pipeline
```
WordPress Post → TMDB Lookup → Gemini AI Optimization → WordPress Update → Database Logging
```

## External Dependencies

### Required APIs
- **WordPress REST API**: Post management and Yoast SEO field updates
- **Google Gemini AI**: Content optimization and SEO enhancement
- **TMDB API**: Movie and series metadata, images, and trailers

### Environment Variables
- `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_PASSWORD`
- `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc. (multiple keys supported)
- `TMDB_API_KEY`, `TMDB_READ_TOKEN`
- Various configuration parameters for optimization limits and scheduling

### Python Dependencies
- Flask for web interface
- Requests for HTTP client operations
- Google GenAI client for Gemini integration
- Schedule for task automation
- SQLite3 for database operations

## Deployment Strategy

### Replit Optimization
- Environment variable configuration for sensitive data
- SQLite database for file-based persistence
- Flask development server suitable for Replit hosting
- Static asset serving through Flask

### Execution Modes
1. **Single Run**: Execute one optimization cycle (`python main.py --once`)
2. **Scheduled Mode**: Continuous operation with periodic execution
3. **Dashboard Mode**: Web interface for monitoring and manual control

### Resource Management
- Quota tracking prevents API limit exceeded errors
- Automatic API key rotation for Gemini service
- Batch processing limits (2 posts per cycle) for controlled resource usage
- Comprehensive logging for debugging and monitoring

### Security Considerations
- Environment variables for sensitive credentials
- WordPress App Password authentication
- Session management for dashboard access
- Input validation for all API interactions

The system is designed to be maintainable, scalable within Replit's constraints, and provides comprehensive monitoring capabilities for SEO optimization workflows.