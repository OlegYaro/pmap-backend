#!/usr/bin/env bash
# AWS commands of the backend service. Called by make: see infra/RUNBOOK.md.
set -euo pipefail

P=pmap-${PMAP_ENV:-dev}
STACK=$P-backend
CLUSTER=$P-backend
export AWS_REGION=${AWS_REGION:-eu-north-1}

die() { echo "$*" >&2; exit 1; }
exported() { aws cloudformation list-exports --query "Exports[?Name=='$1'].Value" --output text; }

update_stack() {
	aws cloudformation deploy --stack-name "$STACK" --template-file infra/backend.yaml \
		--capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
		--parameter-overrides ImageTag="$1" DesiredCount="$2"
}

# One-off task from the worker task definition with another command; fails if the command fails.
run_once() {
	local task status
	task=$(aws ecs run-task --cluster "$CLUSTER" --launch-type FARGATE \
		--task-definition "$P-backend-worker" \
		--network-configuration "awsvpcConfiguration={subnets=[$(exported "$P-PublicSubnets")],securityGroups=[$(exported "$P-BackendSecurityGroup")],assignPublicIp=ENABLED}" \
		--overrides "{\"containerOverrides\":[$1]}" \
		--query 'tasks[0].taskArn' --output text)
	echo "task ${task##*/}"
	until [ "$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task" \
		--query 'tasks[0].lastStatus' --output text)" = STOPPED ]; do sleep 10; done
	status=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task" \
		--query 'tasks[0].[containers[0].exitCode,stoppedReason]' --output text)
	[ "${status%%[[:space:]]*}" = 0 ] || die "task failed: $status. Logs: make aws-logs"
}

migrate() {
	run_once '{"name":"app","command":["alembic","upgrade","head"]}'
}

create_user() {
	local password
	[ -n "${1:-}" ] || die "usage: make aws-create-user LOGIN=<login> [ROLE=admin|user]"
	read -rsp "password for $1: " password && echo
	# json.dumps, so quotes in the password do not break the overrides.
	run_once "$(LOGIN=$1 ROLE=${2:-admin} USER_PASSWORD=$password python3 -c 'import json, os
e = os.environ
print(json.dumps({"name": "app",
    "command": ["python", "-m", "database.create_user", e["LOGIN"], "--role", e["ROLE"]],
    "environment": [{"name": "USER_PASSWORD", "value": e["USER_PASSWORD"]}]}))')"
}

gateway() {
	aws cloudformation deploy --stack-name "$P-gateway" --template-file infra/gateway.yaml \
		--capabilities CAPABILITY_IAM --no-fail-on-empty-changeset
	aws cloudformation describe-stacks --stack-name "$P-gateway" \
		--query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text
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
	# The migration runs from the new task definition before the new code starts.
	update_stack "$tag" 0
	migrate
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
deploy | migrate | check | api_url | gateway) "$1" ;;
create_user) create_user "${2:-}" "${3:-}" ;;
*) die "usage: $0 deploy|migrate|check|api_url|gateway|create_user <login> [role]" ;;
esac
