# Transcript Chat Application

A production-ready, containerized application for chatting with transcripts using LlamaIndex and Anthropic's Claude. The application consists of a FastAPI backend for transcript processing and a Streamlit frontend for the chat interface.

## Architecture

- **Backend**: FastAPI application using LlamaIndex and Claude for transcript processing
- **Frontend**: Streamlit-based chat interface
- **Infrastructure**: Docker containers orchestrated with Docker Compose
- **Vector Index**: Pre-built during Docker image creation for optimal performance

## Prerequisites

- Docker Desktop installed and running (latest version)
- Anthropic API key
- (Optional) Account on your chosen cloud platform (AWS, Google Cloud, or DigitalOcean)

## Transcript Indexing

The application uses a pre-built vector index to enable efficient searching and querying of transcripts. This index is built during the Docker image creation process, not at runtime, which provides several benefits:

1. **Faster Startup**: The application loads a pre-built index instead of creating it at runtime
2. **Consistent Results**: Every deployment uses the same index
3. **Build-time Validation**: The Docker build fails if indexing encounters errors

### How Indexing Works

1. Place your transcript files in the `transcripts/` directory
2. During Docker build:
   - `build_index.py` runs and processes all transcripts
   - Creates embeddings using HuggingFace's sentence transformers
   - Saves the index to the `storage/` directory
   - Verifies index files exist before completing the build

### Updating Transcripts

When you need to update the transcripts:

1. Add/modify files in the `transcripts/` directory
2. Rebuild the Docker image:
   ```bash
   docker compose build --no-cache backend
   docker compose up backend
   ```

### Local Development

For local development without Docker:

1. Create and activate a Python virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Run the index builder: `python build_index.py`
4. Start the backend: `uvicorn main:app --reload`

## Local Development

1. Clone the repository
2. Copy `.env.template` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.template .env
   # Edit .env and add your OpenAI API key
   ```

3. Build and run the containers:
   ```bash
   docker compose build --no-cache
   docker compose up
   ```

4. Access the applications:
   - Streamlit Frontend: http://localhost:8501
   - FastAPI Backend: http://localhost:8000/docs

## Project Structure

```
.
├── Dockerfile.backend        # Backend container configuration
├── Dockerfile.frontend      # Frontend container configuration
├── docker-compose.yml      # Container orchestration
├── main.py                # FastAPI backend code
├── build_index.py        # Script to build vector index
├── streamlit_app.py      # Streamlit frontend code
├── requirements.txt      # Python dependencies
├── transcripts/         # Directory for transcript files
├── storage/            # Vector index storage directory
└── .env               # Environment variables
```

## Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `BACKEND_URL`: URL of the backend service (required for production deployment)
- `PORT`: Port for the backend service (defaults to 10000)

## Production Deployment

### Option 1: AWS Elastic Container Service (ECS)

1. Push images to Amazon ECR:
   ```bash
   aws ecr create-repository --repository-name transcript-chat-backend
   aws ecr create-repository --repository-name transcript-chat-frontend
   
   # Build and push images
   docker compose build
   docker tag transcript-chat-backend:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/transcript-chat-backend:latest
   docker tag transcript-chat-frontend:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/transcript-chat-frontend:latest
   
   aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
   
   docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/transcript-chat-backend:latest
   docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/transcript-chat-frontend:latest
   ```

2. Create ECS cluster and task definitions
3. Configure environment variables in ECS task definitions
4. Deploy services and set up load balancers

### Option 2: Google Cloud Run

1. Push images to Google Container Registry:
   ```bash
   gcloud auth configure-docker
   
   docker tag transcript-chat-backend:latest gcr.io/$PROJECT_ID/transcript-chat-backend:latest
   docker tag transcript-chat-frontend:latest gcr.io/$PROJECT_ID/transcript-chat-frontend:latest
   
   docker push gcr.io/$PROJECT_ID/transcript-chat-backend:latest
   docker push gcr.io/$PROJECT_ID/transcript-chat-frontend:latest
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy transcript-chat-backend \
     --image gcr.io/$PROJECT_ID/transcript-chat-backend:latest \
     --platform managed \
     --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY"
   
   gcloud run deploy transcript-chat-frontend \
     --image gcr.io/$PROJECT_ID/transcript-chat-frontend:latest \
     --platform managed \
     --set-env-vars "BACKEND_URL=https://transcript-chat-backend-url"
   ```

## Production Best Practices

1. Security:
   - Use secrets management for API keys
   - Enable HTTPS
   - Implement rate limiting
   - Regular security updates

2. Monitoring:
   - Set up logging
   - Monitor application metrics
   - Configure alerts

3. Scaling:
   - Configure auto-scaling
   - Use appropriate instance sizes
   - Implement caching where appropriate

## Troubleshooting

Common issues and solutions:

1. Container startup issues:
   ```bash
   # View logs
   docker compose logs backend
   docker compose logs frontend
   
   # Rebuild containers
   docker compose build --no-cache
   ```

2. Index-related issues:
   - Verify transcripts exist in `transcripts/` directory
   - Check `storage/` directory for index files
   - Review logs for indexing errors: `docker compose logs backend`

3. Connection issues:
   - Verify environment variables
   - Check network connectivity
   - Ensure services are running

## License

MIT License

## Deployment on Render.com

The application is configured for deployment on Render.com using `render.yaml`. To deploy:

1. Push your code to a Git repository (GitHub, GitLab, etc.)
2. Create a new account on [Render.com](https://render.com) if you haven't already
3. Connect your Git repository to Render
4. Click "New +" and select "Blueprint"
5. Select your repository
6. Render will automatically detect the `render.yaml` and create both services

### Environment Variables

The following environment variables need to be set in Render:

Backend Service:
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude

Frontend Service:
- No additional variables needed (BACKEND_URL is pre-configured in render.yaml)

### Build Process

The backend service will:
1. Install Python dependencies
2. Run `build_index.py` to create the vector index
3. Start the FastAPI server

The frontend service will:
1. Install Python dependencies
2. Start the Streamlit application

### Monitoring

You can monitor both services in the Render dashboard. Each service has its own logs and metrics.

### Local Development

For local development:
1. Create a `.env` file with your `ANTHROPIC_API_KEY`
2. Run `python build_index.py` to create the index
3. Start the backend: `uvicorn main:app --reload`
4. Start the frontend: `streamlit run streamlit_app.py`
