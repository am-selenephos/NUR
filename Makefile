.PHONY: doctor bootstrap start stop status seed open logs package test

doctor:
	bash infra/scripts/dev-doctor.sh

bootstrap:
	bash infra/scripts/bootstrap-dev.sh

start:
	bash infra/scripts/start-nur.sh disabled

start-openai:
	bash infra/scripts/start-nur.sh openai

stop:
	bash infra/scripts/stop-nur.sh

status:
	bash infra/scripts/status-nur.sh

seed:
	bash infra/scripts/seed-demo-nur.sh

open:
	bash infra/scripts/open-nur.sh

logs:
	bash infra/scripts/logs-nur.sh

package:
	bash infra/scripts/package-bootable.sh

test:
	python -m pytest apps/api/app/tests -q
	npm --workspace apps/web run typecheck
	npm --workspace apps/web test -- --run
