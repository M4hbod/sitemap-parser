# Publishing recipes for py-sitemap-parser
# Run `just` to list recipes.

# Test PyPI URL
test_pypi_url := "https://test.pypi.org/legacy/"

# List available recipes
default:
    @just --list

# Remove build artifacts
clean:
    rm -rf dist

# Build sdist + wheel
build: clean
    uv build

# Validate built distributions
check: build
    uvx twine check dist/*

# Run the test suite
test:
    uv run pytest

# Lint and format
lint:
    uvx ruff check
    uvx ruff format --check

# Publish to Test PyPI (manual; production publish is handled by CI)
publish-test: check
    uv publish --publish-url {{test_pypi_url}}

# Run the same checks CI runs before publishing
ci-check: test lint check

# Bump version, commit, tag, push. CI publishes to PyPI on the v* tag.
# Usage: just release 2.1.0
release version: ci-check
    uv version {{version}}
    git add pyproject.toml
    git commit -m "Bump version to {{version}}"
    git tag v{{version}}
    git push origin master --tags
