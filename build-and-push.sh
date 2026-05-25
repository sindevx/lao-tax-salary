#!/bin/bash
set -e  # ถ้ามี error ให้หยุดทันที

# ------------ Config พื้นฐาน (ปรับได้เอง) ------------
# ถ้าไม่ตั้ง env ไว้ จะใช้ค่า default เหล่านี้
REGISTRY="${REGISTRY:-66.42.61.60:5000}"
IMAGE_REPO="${IMAGE_REPO:-lao_salary}"
IMAGE_TAG="${IMAGE_TAG:-1.0.1}"

IMAGE_NAME="${REGISTRY}/${IMAGE_REPO}:${IMAGE_TAG}"

echo "==> Building image: ${IMAGE_NAME}"

# ------------ ตรวจ prerequisites ------------
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "ERROR: Dockerfile not found in current directory"
    exit 1
fi

# ------------ Docker build (มี retry เล็กน้อย) ------------
MAX_RETRIES=3
RETRY_COUNT=0
BUILD_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "==> Docker build (linux/amd64), attempt $((RETRY_COUNT + 1))/$MAX_RETRIES ..."
    if docker build --platform linux/amd64 -f Dockerfile -t "$IMAGE_NAME" .; then
        BUILD_SUCCESS=true
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "Build failed, retrying in 5s..."
            sleep 5
        else
            echo "ERROR: Docker build failed after $MAX_RETRIES attempts"
            exit 1
        fi
    fi
done

if [ "$BUILD_SUCCESS" = false ]; then
    echo "ERROR: Failed to build Docker image"
    exit 1
fi

# ------------ ตรวจว่ามี image จริงก่อน push ------------
echo "==> Verifying image exists locally..."
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo "ERROR: Image $IMAGE_NAME does not exist locally"
    exit 1
fi

# ------------ Push ขึ้น registry ------------
echo "==> Pushing image to registry: $REGISTRY ..."
if ! docker push "$IMAGE_NAME"; then
    echo "ERROR: Failed to push image to registry"
    exit 1
fi

echo "==> Success! Image $IMAGE_NAME has been built and pushed."

