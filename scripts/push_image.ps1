# Build and push Docker image
cd E:\stock\TavilyProxy

# Create builder if not exists
docker buildx create --use 2>$null

# Build and push
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/kore-01/tavily:latest -t ghcr.io/kore-01/tavily:main --push .
