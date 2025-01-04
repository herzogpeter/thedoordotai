# Makefile for Transcript Chat Application

.PHONY: build push deploy

# Docker Hub username - replace with your username
DOCKER_USERNAME=your-docker-username

# Application version
VERSION=1.0.0

# Image names
BACKEND_IMAGE=$(DOCKER_USERNAME)/transcript-chat-backend:$(VERSION)
FRONTEND_IMAGE=$(DOCKER_USERNAME)/transcript-chat-frontend:$(VERSION)

# Build Docker images
build:
	docker build -t $(BACKEND_IMAGE) -f Dockerfile.backend .
	docker build -t $(FRONTEND_IMAGE) -f Dockerfile.frontend .

# Push images to Docker Hub
push:
	docker push $(BACKEND_IMAGE)
	docker push $(FRONTEND_IMAGE)

# Deploy to production
deploy:
	docker-compose -f docker-compose.prod.yml pull
	docker-compose -f docker-compose.prod.yml up -d

# View logs
logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Stop services
stop:
	docker-compose -f docker-compose.prod.yml down
