# Makefile for building Loyalty Card App flatpak bundles
#
# Targets:
#   make build           - Build flatpak for x86_64 (default)
#   make build-x86_64    - Build flatpak for x86_64
#   make build-aarch64   - Build flatpak for aarch64 (requires qemu-user-static)
#   make bundle          - Create .flatpak bundle files for both architectures
#   make bundle-x86_64   - Create .flatpak bundle for x86_64
#   make bundle-aarch64  - Create .flatpak bundle for aarch64
#   make install         - Install locally for testing (x86_64)
#   make run             - Run the installed app
#   make clean           - Remove build artifacts

APP_ID := com.github.loyaltycardapp.LoyaltyCardApp
MANIFEST := $(APP_ID).json
RUNTIME := org.gnome.Platform//48
SDK := org.gnome.Sdk//48
REPO := dist/repo
BUILDDIR_X86_64 := build/x86_64
BUILDDIR_AARCH64 := build/aarch64
BUNDLE_DIR := dist

.PHONY: build build-x86_64 build-aarch64 bundle bundle-x86_64 bundle-aarch64 \
        install run clean setup-x86_64 setup-aarch64

build: build-x86_64

# Install SDK and runtime for x86_64
setup-x86_64:
	flatpak install --user -y flathub $(SDK) $(RUNTIME)

# Install SDK and runtime for aarch64 (requires qemu-user-static on x86_64 host)
setup-aarch64:
	@command -v qemu-aarch64-static >/dev/null 2>&1 || \
		{ echo "Error: qemu-user-static is required for aarch64 cross-builds"; exit 1; }
	flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
	flatpak --user remote-modify --no-filter flathub
	flatpak install --user -y --arch=aarch64 flathub $(SDK) $(RUNTIME)

# Build for x86_64
build-x86_64: setup-x86_64
	mkdir -p $(BUILDDIR_X86_64) $(REPO)
	flatpak-builder --arch=x86_64 --force-clean --repo=$(REPO) \
		$(BUILDDIR_X86_64) $(MANIFEST)

# Build for aarch64
build-aarch64: setup-aarch64
	mkdir -p $(BUILDDIR_AARCH64) $(REPO)
	flatpak-builder --arch=aarch64 --force-clean --repo=$(REPO) \
		$(BUILDDIR_AARCH64) $(MANIFEST)

# Create .flatpak bundle for x86_64
bundle-x86_64: build-x86_64
	mkdir -p $(BUNDLE_DIR)
	flatpak build-bundle --arch=x86_64 $(REPO) \
		$(BUNDLE_DIR)/$(APP_ID)-x86_64.flatpak $(APP_ID)

# Create .flatpak bundle for aarch64
bundle-aarch64: build-aarch64
	mkdir -p $(BUNDLE_DIR)
	flatpak build-bundle --arch=aarch64 $(REPO) \
		$(BUNDLE_DIR)/$(APP_ID)-aarch64.flatpak $(APP_ID)

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
