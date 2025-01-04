# Transcript Chat Application

A production-ready, containerized application for chatting with transcripts using LlamaIndex and OpenAI. The application consists of a FastAPI backend for transcript processing and a Streamlit frontend for the chat interface.

## Architecture

- **Backend**: FastAPI application using LlamaIndex and OpenAI for transcript processing
- **Frontend**: Streamlit-based chat interface
- **Infrastructure**: Docker containers orchestrated with Docker Compose

## Prerequisites

- Docker Desktop installed and running (latest version)
- OpenAI API key
- (Optional) Account on your chosen cloud platform (AWS, Google Cloud, or DigitalOcean)

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
├── streamlit_app.py       # Streamlit frontend code
├── requirements.txt       # Python dependencies
├── transcripts/          # Directory for transcript files
├── storage/             # Persistent storage directory
└── .env                # Environment variables
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `BACKEND_URL`: URL of the backend service (required for production deployment)

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

2. Connection issues:
   - Verify environment variables
   - Check network connectivity
   - Ensure services are running

## License

MIT License
