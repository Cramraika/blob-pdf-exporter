# blob-pdf-exporter — release Makefile.
#
# Mirror of the pulseboard Make-target shape but for Chrome Web Store.
# All targets are idempotent. Credentials live in env vars (see
# docs/store/SETUP.md) — never hardcoded.

VERSION := $(shell python3 -c "import json; print(json.load(open('manifest.json'))['version'])")
ZIP     := dist/blob-pdf-exporter-v$(VERSION).zip
PUBLISHER := python3 scripts/chrome-store-publisher.py

# ---------------------------------------------------------------------------
.PHONY: help
help:                       ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

.PHONY: pack
pack:                       ## Build dist/blob-pdf-exporter-v$(VERSION).zip from current tree.
	@mkdir -p dist
	@rm -f $(ZIP)
	@zip -q -r $(ZIP) \
		manifest.json src/ vendor/ icons/ LICENSE README.md \
		-x "*.DS_Store" "chrome-store-assets/*" "docs/*" "*.md.skeleton*"
	@echo "wrote $(ZIP)"
	@ls -la $(ZIP)
	@shasum -a 256 $(ZIP)

.PHONY: clean
clean:                      ## Remove dist/ and any local zips.
	@rm -rf dist/
	@rm -f blob-pdf-exporter-*.zip

# ---------------------------------------------------------------------------
# Chrome Web Store API ops (require env vars per docs/store/SETUP.md)
# ---------------------------------------------------------------------------

.PHONY: doctor
doctor:                     ## Verify env + tooling for a release.
	@echo "manifest version: $(VERSION)"
	@command -v python3 >/dev/null && echo "python3: OK ($$(python3 --version 2>&1))" || echo "python3: MISSING"
	@command -v zip >/dev/null && echo "zip:     OK" || echo "zip: MISSING"
	@command -v gh   >/dev/null && echo "gh:      OK ($$(gh --version | head -1))" || echo "gh: MISSING"
	@if [ -n "$$CHROME_OAUTH_CLIENT_ID" ];     then echo "CHROME_OAUTH_CLIENT_ID:     set"; else echo "CHROME_OAUTH_CLIENT_ID:     MISSING"; fi
	@if [ -n "$$CHROME_OAUTH_CLIENT_SECRET" ]; then echo "CHROME_OAUTH_CLIENT_SECRET: set"; else echo "CHROME_OAUTH_CLIENT_SECRET: MISSING"; fi
	@if [ -n "$$CHROME_OAUTH_REFRESH_TOKEN" ]; then echo "CHROME_OAUTH_REFRESH_TOKEN: set"; else echo "CHROME_OAUTH_REFRESH_TOKEN: MISSING"; fi
	@if [ -n "$$CHROME_EXTENSION_ID" ];        then echo "CHROME_EXTENSION_ID:        set"; else echo "CHROME_EXTENSION_ID:        MISSING"; fi
	@echo "(see docs/store/SETUP.md if any are MISSING)"

.PHONY: auth-bootstrap
auth-bootstrap:             ## One-time browser dance to capture refresh_token (local only).
	@$(PUBLISHER) auth-bootstrap

.PHONY: status
status:                     ## GET item state (uploadState + status array).
	@$(PUBLISHER) status

.PHONY: upload
upload: pack                ## Pack + PUT zip to Chrome Web Store (no publish).
	@$(PUBLISHER) upload --zip $(ZIP)

.PHONY: publish-trusted
publish-trusted:            ## Publish current draft → trustedTesters track.
	@$(PUBLISHER) publish --target trustedTesters

.PHONY: publish-public
publish-public:             ## Publish current draft → public (PRODUCTION).
	@$(PUBLISHER) publish --target default

# ---------------------------------------------------------------------------
# Composed release flows
# ---------------------------------------------------------------------------

.PHONY: ship-trusted
ship-trusted: upload publish-trusted ## Pack + upload + publish to trustedTesters.

.PHONY: ship-public
ship-public: upload publish-public ## Pack + upload + publish public. ⚠️ Reaches end users.

# ---------------------------------------------------------------------------
# Tag flow (triggers GitHub Actions store-release.yml)
# ---------------------------------------------------------------------------

.PHONY: tag
tag:                        ## Tag v$(VERSION) — triggers CI release workflow.
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
		echo "Tag v$(VERSION) already exists. Bump manifest.json version first."; \
		exit 1; \
	fi
	@git tag -a "v$(VERSION)" -m "v$(VERSION)"
	@git push origin "v$(VERSION)"
	@echo "Pushed tag v$(VERSION). CI is now packing + uploading."

.PHONY: bump-patch
bump-patch:                 ## Bump manifest.json patch version (0.1.0 → 0.1.1). No commit.
	@python3 -c "import json,pathlib; m=json.load(open('manifest.json')); parts=m['version'].split('.'); parts[2]=str(int(parts[2])+1); m['version']='.'.join(parts); pathlib.Path('manifest.json').write_text(json.dumps(m,indent=2)+'\n'); print(f\"bumped to {m['version']}\")"

.PHONY: bump-minor
bump-minor:                 ## Bump manifest.json minor version (0.1.0 → 0.2.0). No commit.
	@python3 -c "import json,pathlib; m=json.load(open('manifest.json')); parts=m['version'].split('.'); parts[1]=str(int(parts[1])+1); parts[2]='0'; m['version']='.'.join(parts); pathlib.Path('manifest.json').write_text(json.dumps(m,indent=2)+'\n'); print(f\"bumped to {m['version']}\")"

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

.PHONY: lint
lint:                       ## Validate manifest.json + JS syntax.
	@python3 -c "import json; json.load(open('manifest.json')); print('manifest.json OK')"
	@for f in src/*.js; do node --check "$$f" && echo "$$f OK"; done

.PHONY: test-load
test-load:                  ## Print the chrome://extensions load-unpacked instructions.
	@echo "1. Open Chrome → chrome://extensions/"
	@echo "2. Toggle Developer mode (top right)."
	@echo "3. Click 'Load unpacked'."
	@echo "4. Select $$(pwd)"
	@echo "5. The Blob PDF Exporter icon appears in the toolbar."

# ---------------------------------------------------------------------------
.DEFAULT_GOAL := help
