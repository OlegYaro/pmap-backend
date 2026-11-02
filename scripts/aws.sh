#!/usr/bin/env bash
# AWS commands of the backend service. Called by make: see infra/RUNBOOK.md.
set -euo pipefail

P=pmap-${PMAP_ENV:-dev}
STACK=$P-backend
CLUSTER=$P-backend
export AWS_REGION=${AWS_REGION:-eu-north-1}

die() { echo "$*" >&2; exit 1; }

update_stack() {
	aws cloudformation deploy --stack-name "$STACK" --template-file infra/backend.yaml \
		--capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
		--parameter-overrides ImageTag="$1" DesiredCount="$2"
}

deploy() {
	local tag repo
	[ -z "$(git status --porcelain)" ] || die "commit or stash your changes: the image is tagged with the commit"
	tag=$(git rev-parse --short HEAD)
	# First deploy: create the stack with nothing running, so the ECR repository exists.
	aws cloudformation describe-stacks --stack-name "$STACK" >/dev/null 2>&1 || update_stack latest 0
	repo=$(aws cloudformation describe-stacks --stack-name "$STACK" \
		--query "Stacks[0].Outputs[?OutputKey=='RepositoryUri'].OutputValue" --output text)
	if aws ecr describe-images --repository-name "$STACK" --image-ids imageTag="$tag" >/dev/null 2>&1; then
		echo "image $tag is already in ECR"
	else
		aws ecr get-login-password | docker login --username AWS --password-stdin "${repo%%/*}"
		docker buildx build --platform linux/amd64 -f dockerfile -t "$repo:$tag" --push .
	fi
	update_stack "$tag" 1
}

check() {
	local down
	aws ecs wait services-stable --cluster "$CLUSTER" --services api worker
	down=$(aws ecs describe-services --cluster "$CLUSTER" --services api worker \
		--query 'services[?runningCount!=desiredCount || desiredCount==`0`].serviceName' --output text)
	[ -z "$down" ] || die "not running: $down"
	echo "OK: api and worker are running"
}

api_url() {
	local task eni ip
	task=$(aws ecs list-tasks --cluster "$CLUSTER" --service-name api --query 'taskArns[0]' --output text)
	[ "$task" != None ] || die "api is not running"
	eni=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task" \
		--query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
	ip=$(aws ec2 describe-network-interfaces --network-interface-ids "$eni" \
		--query 'NetworkInterfaces[0].Association.PublicIp' --output text)
	echo "http://$ip:8000"
}

case ${1:-} in
deploy | check | api_url) "$1" ;;
*) die "usage: $0 deploy|check|api_url" ;;
esac
