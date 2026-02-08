# Makefile for building Loyalty Card App flatpak bundles
#
# Targets:
#   make build           - Build flatpak for x86_64 (default)
#   make build-x86_64    - Build flatpak for x86_64
#   make build-aarch64   - Build flatpak for aarch64 (Docker + QEMU emulation)
#   make bundle          - Create .flatpak bundle files for both architectures
#   make bundle-x86_64   - Create .flatpak bundle for x86_64
#   make bundle-aarch64  - Create .flatpak bundle for aarch64 (Docker + QEMU)
#   make install         - Install locally for testing (x86_64)
#   make run             - Run the installed app
#   make clean           - Remove build artifacts

APP_ID := com.github.loyaltycardapp.LoyaltyCardApp
MANIFEST := $(APP_ID).json
RUNTIME := org.gnome.Platform//48
SDK := org.gnome.Sdk//48
REPO := dist/repo
BUILDDIR_X86_64 := build/x86_64
BUNDLE_DIR := dist
DOCKER_IMAGE := loyalty-card-app-aarch64-builder

.PHONY: build build-x86_64 build-aarch64 bundle bundle-x86_64 bundle-aarch64 \
        install run clean setup-x86_64 setup-binfmt

build: build-x86_64

# Install SDK and runtime for x86_64
setup-x86_64:
	flatpak install --user -y flathub $(SDK) $(RUNTIME)

# Ensure QEMU binfmt_misc is registered for aarch64 emulation
setup-binfmt:
	docker run --privileged --rm tonistiigi/binfmt --install arm64

# Build for x86_64 (native, on host)
build-x86_64: setup-x86_64
	mkdir -p $(BUILDDIR_X86_64) $(REPO)
	flatpak-builder --arch=x86_64 --force-clean --repo=$(REPO) \
		$(BUILDDIR_X86_64) $(MANIFEST)

# Build for aarch64 inside Docker container with QEMU emulation
build-aarch64: setup-binfmt
	mkdir -p $(BUNDLE_DIR)
	docker buildx build --platform linux/arm64 \
		-f Dockerfile.aarch64-builder \
		--output type=local,dest=$(BUNDLE_DIR)/ .
	@echo "Bundle created: $(BUNDLE_DIR)/$(APP_ID)-aarch64.flatpak"

# Create .flatpak bundle for x86_64
bundle-x86_64: build-x86_64
	mkdir -p $(BUNDLE_DIR)
	flatpak build-bundle --arch=x86_64 $(REPO) \
		$(BUNDLE_DIR)/$(APP_ID)-x86_64.flatpak $(APP_ID)

# Create .flatpak bundle for aarch64 (same as build-aarch64, Docker produces the bundle)
bundle-aarch64: build-aarch64

# Create bundles for both architectures
bundle: bundle-x86_64 bundle-aarch64

# Install locally for testing (x86_64)
install: build-x86_64
	flatpak-builder --user --install --force-clean --arch=x86_64 \
		$(BUILDDIR_X86_64) $(MANIFEST)

# Run the installed app
run:
	flatpak run $(APP_ID)

# Remove all build artifacts
clean:
	rm -rf build/ dist/ .flatpak-builder/
